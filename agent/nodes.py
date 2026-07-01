import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from dotenv import load_dotenv

from agent.schemas import AgentState, ClaimInput, ReimbursementDecision, AuditEntry
from agent.tools import (
    policy_lookup, 
    receipt_completeness_check, 
    per_diem_limit_check, 
    approval_threshold_check
)
from agent.prompts import build_system_prompt, SYNTHESIZER_PROMPT

load_dotenv(override=True)

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

def _is_valid_key(k):
    v = os.environ.get(k, "").strip()
    if not v:
        return False
    placeholders = ["your_", "_here", "sk-xxx", "gsk_xxx"]
    return not any(p in v.lower() for p in placeholders)

def get_available_providers():
    """Returns list of available provider names in priority order."""
    providers = []
    if _is_valid_key("GROQ_API_KEY"):
        providers.append("groq")
    if _is_valid_key("GEMINI_API_KEY"):
        providers.append("gemini")
    if _is_valid_key("OPENAI_API_KEY"):
        providers.append("openai")
    return providers

def get_llm(provider_override=None):
    """Returns a single LLM instance for the given provider."""
    provider = provider_override or os.environ.get("LLM_PROVIDER", "groq").strip().lower()
    
    if provider == "groq" and _is_valid_key("GROQ_API_KEY"):
        return ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    elif provider == "gemini" and _is_valid_key("GEMINI_API_KEY"):
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            temperature=0, 
            api_key=os.environ.get("GEMINI_API_KEY"),
            convert_system_message_to_human=True
        )
    elif provider == "openai" and _is_valid_key("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # If requested provider unavailable, try any available one
    available = get_available_providers()
    if not available:
        raise ValueError("No valid API keys found. Set GROQ_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY in .env")
    return get_llm(provider_override=available[0])


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
                        step=1,
                        tool_name="duplicate_check",
                        input_summary=f"Checking claim_id {claim_id} against processed claims",
                        output_summary=f"DUPLICATE DETECTED \u2014 claim_id {claim_id} already exists in processed_claims.json",
                        policy_rules_triggered=["FRAUD-POL-001 \u00a71.1"]
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
        # First call: build the initial prompt and persist it in state
        system_prompt = build_system_prompt(state.get("policy_context", []))
        initial_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please evaluate this claim: {claim_json}")
        ]
        response = llm_with_tools.invoke(initial_messages)
        # Return ALL messages (system + human + AI response) so they're in state
        # for subsequent ReAct iterations. Gemini requires a user turn before
        # any function call turn.
        return {"messages": initial_messages + [response]}
    else:
        # Subsequent calls: state already has full history
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

def synthesizer_node(state: AgentState) -> dict:
    llm = get_llm()
    llm_structured = llm.with_structured_output(ReimbursementDecision)
    
    claim = state["claim"]
    if isinstance(claim, ClaimInput):
        total_claimed = claim.total_claimed_amount
        claim_json = claim.model_dump_json()
    else:
        total_claimed = claim.get("total_claimed_amount", 0.0)
        claim_json = json.dumps(claim)
        
    messages = state.get("messages", [])
    
    # Extract tool results from the conversation history
    tool_results_text = ""
    for msg in messages:
        if isinstance(msg, ToolMessage):
            tool_results_text += f"- {msg.name}: {msg.content}\n"
            
    if not tool_results_text:
        tool_results_text = "No tool checks were performed."
        
    system_prompt = build_system_prompt(state.get("policy_context", []))
    synth_prompt = SYNTHESIZER_PROMPT.format(total_claimed_amount=total_claimed)
    
    # Construct a single comprehensive prompt to avoid Gemini strict sequence validation bugs
    final_content = (
        f"{system_prompt}\n\n"
        f"--- CLAIM DATA ---\n{claim_json}\n\n"
        f"--- TOOL RESULTS / AUDIT TRAIL ---\n{tool_results_text}\n\n"
        f"--- INSTRUCTIONS ---\n{synth_prompt}"
    )
    
    decision = llm_structured.invoke([HumanMessage(content=final_content)])
    
    audit_entries = []
    step = 1
    
    # Track tool call arguments to map to ToolMessages
    tool_call_map = {}
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_call_map[tc["id"]] = tc.get("args", {})
                
        if isinstance(msg, ToolMessage):
            tool_id = msg.tool_call_id
            args = tool_call_map.get(tool_id, {})
            args_str = ", ".join(f"{k}={v}" for k, v in args.items())
            input_summary = f"Executed with parameters: {args_str}" if args_str else "No parameters"
            
            audit_entries.append(AuditEntry(
                step=step,
                tool_name=msg.name,
                input_summary=input_summary,
                output_summary=str(msg.content)[:300] + ("..." if len(str(msg.content)) > 300 else ""),
                policy_rules_triggered=[]
            ))
            step += 1
            
    if not decision.audit_trail:
        decision.audit_trail = audit_entries
    
    return {"decision": decision}

def output_validator_node(state: AgentState) -> dict:
    decision: ReimbursementDecision = state.get("decision")
    if not decision:
        return {}
        
    claim = state["claim"]
    total_claimed = claim.total_claimed_amount
        
    requires_manual_review = False
    
    if decision.decision == "Manual Review":
        decision.approved_amount = 0.0
        decision.rejected_amount = 0.0
        audit_entry = AuditEntry(
            step=len(decision.audit_trail) + 1 if decision.audit_trail else 1,
            tool_name="output_validator_node",
            input_summary=f"Manual Review routing: approved/rejected amounts set to 0.0 pending human decision. Total claim value: {total_claimed}",
            output_summary="Amounts zeroed for manual review",
            policy_rules_triggered=["SYSTEM-MANUAL-REVIEW"]
        )
        if decision.audit_trail is None:
            decision.audit_trail = []
        decision.audit_trail.append(audit_entry)
    else:
        # Check 1: Math validation
        total_calculated = decision.approved_amount + decision.rejected_amount
        if abs(total_calculated - total_claimed) > 1.0:
            # Auto-correct instead of routing to manual review
            corrected_rejected = total_claimed - decision.approved_amount
            decision.rejected_amount = corrected_rejected
            
            # Log the correction in the audit_trail
            audit_entry = AuditEntry(
                step=len(decision.audit_trail) + 1 if decision.audit_trail else 1,
                tool_name="output_validator_node",
                input_summary=f"Sum mismatch: approved {decision.approved_amount} + rejected {decision.rejected_amount} != {total_claimed}",
                output_summary=f"Auto-corrected rejected_amount to {corrected_rejected}",
                policy_rules_triggered=["SYSTEM-MATH-FIX"]
            )
            
            if decision.audit_trail is None:
                decision.audit_trail = []
            decision.audit_trail.append(audit_entry)
        
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
