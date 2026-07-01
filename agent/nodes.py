import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from agent.schemas import AgentState, ClaimInput, ReimbursementDecision, AuditEntry
from agent.tools import (
    policy_lookup, 
    receipt_completeness_check, 
    per_diem_limit_check, 
    approval_threshold_check
)
from agent.prompts import build_system_prompt, SYNTHESIZER_PROMPT

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

def get_llm():
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    
    if provider == "groq" or (not os.environ.get("OPENAI_API_KEY") and os.environ.get("GROQ_API_KEY")):
        return ChatGroq(model="mixtral-8x7b-32768", temperature=0)
    elif provider == "openai" or os.environ.get("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    else:
        raise ValueError("Please set LLM_PROVIDER to 'openai' or 'groq', and provide the corresponding API key in .env")

def intake_node(state: AgentState) -> dict:
    claim_raw = state.get("claim")
    
    # Validate claim is a valid ClaimInput
    if isinstance(claim_raw, dict):
        claim = ClaimInput.model_validate(claim_raw)
    else:
        claim = claim_raw
        
    start_date = datetime.strptime(claim.travel_start_date, "%Y-%m-%d")
    end_date = datetime.strptime(claim.travel_end_date, "%Y-%m-%d")
    trip_days = (end_date - start_date).days + 1
    
    tool_results = state.get("tool_results") or {}
    tool_results["trip_days"] = trip_days
    
    return {
        "claim": claim,
        "tool_results": tool_results
    }

def policy_retrieval_node(state: AgentState) -> dict:
    claim = state["claim"]
    claim_id = claim.claim_id
    receipts = claim.receipts
        
    processed_claims_path = DATA_DIR / "processed_claims.json"
    
    if processed_claims_path.exists():
        with open(processed_claims_path, "r", encoding="utf-8") as f:
            processed_data = json.load(f)
            processed_ids = processed_data.get("processed_claim_ids", [])
            
        if claim_id in processed_ids:
            # Duplicate claim detected
            decision = ReimbursementDecision(
                claim_id=claim_id,
                decision="Rejected",
                approved_amount=0.0,
                rejected_amount=claim.total_claimed_amount,
                deductions=[],
                missing_documents=[],
                policy_references=[],
                confidence=1.0,
                reasoning="Duplicate claim detected \u2014 this claim ID has already been processed",
                manual_review_reason=None,
                audit_trail=[
                    AuditEntry(
                        step=0,
                        tool_name="policy_retrieval_node",
                        input_summary=f"Checking duplicate for {claim_id}",
                        output_summary="Duplicate detected",
                        policy_rules_triggered=["SYSTEM"]
                    )
                ],
                processed_at=datetime.utcnow().isoformat() + "Z"
            )
            return {
                "decision": decision,
                "requires_manual_review": False,
                "policy_context": []
            }

    # Not duplicate, load policy rules for categories in the claim receipts
    categories = {r.category for r in receipts}
            
    policy_context = []
    policy_path = DATA_DIR / "travel_policy.json"
    if policy_path.exists():
        with open(policy_path, "r", encoding="utf-8") as f:
            policy_data = json.load(f)
            for rule in policy_data.get("rules", []):
                if rule.get("category") in categories:
                    policy_context.append(rule)
                    
    return {
        "policy_context": policy_context
    }

def llm_reasoning_node(state: AgentState) -> dict:
    llm = get_llm()
    tools = [policy_lookup, receipt_completeness_check, per_diem_limit_check, approval_threshold_check]
    llm_with_tools = llm.bind_tools(tools)
    
    claim = state["claim"]
    claim_json = claim.model_dump_json()
        
    messages = state.get("messages", [])
    
    if not messages:
        system_prompt = build_system_prompt(state.get("policy_context", []))
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please evaluate this claim: {claim_json}")
        ]
        
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def synthesizer_node(state: AgentState) -> dict:
    llm = get_llm()
    llm_structured = llm.with_structured_output(ReimbursementDecision)
    
    messages = state.get("messages", [])
    synth_messages = list(messages)
    synth_messages.append(HumanMessage(content=SYNTHESIZER_PROMPT))
    
    decision = llm_structured.invoke(synth_messages)
    
    return {"decision": decision}

def output_validator_node(state: AgentState) -> dict:
    decision: ReimbursementDecision = state.get("decision")
    if not decision:
        return {}
        
    claim = state["claim"]
    total_claimed = claim.total_claimed_amount
        
    requires_manual_review = False
    
    # Check 1: Math validation
    total_calculated = decision.approved_amount + decision.rejected_amount
    if abs(total_calculated - total_claimed) > 1.0:
        decision.decision = "Manual Review"
        decision.manual_review_reason = "Automated validation failed \u2014 human review required (amount mismatch)"
        requires_manual_review = True
        
    # Check 2: Manual review reason
    if decision.decision == "Manual Review" and not decision.manual_review_reason:
        decision.manual_review_reason = "Automated validation failed \u2014 human review required (reason missing)"
        requires_manual_review = True
        
    # Check 3: Confidence score
    if decision.confidence < 0.0 or decision.confidence > 1.0:
        decision.decision = "Manual Review"
        decision.manual_review_reason = "Automated validation failed \u2014 human review required (invalid confidence)"
        requires_manual_review = True
        
    # Force manual review if confidence is low
    if decision.confidence < 0.5 and decision.decision != "Manual Review":
        decision.decision = "Manual Review"
        if not decision.manual_review_reason:
            decision.manual_review_reason = f"Low confidence ({decision.confidence}) \u2014 human review required"
        requires_manual_review = True
        
    # Also set requires_manual_review flag explicitly
    if decision.decision == "Manual Review":
        requires_manual_review = True
        
    return {
        "decision": decision,
        "requires_manual_review": requires_manual_review
    }

def output_node(state: AgentState) -> dict:
    decision = state.get("decision")
    if decision:
        decision.processed_at = datetime.utcnow().isoformat() + "Z"
        
    return {"decision": decision}
