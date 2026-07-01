import json
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from agent.schemas import AgentState, ReimbursementDecision
from agent.tools import (
    policy_lookup,
    receipt_completeness_check,
    per_diem_limit_check,
    approval_threshold_check
)
from agent.nodes import (
    intake_node,
    policy_retrieval_node,
    llm_reasoning_node,
    synthesizer_node,
    output_validator_node,
    output_node
)

def route_after_policy(state: AgentState) -> str:
    # If decision is already set (duplicate detected), skip to output validator
    if state.get("decision") is not None:
        return "output_validator_node"
    return "llm_reasoning_node"

def build_graph():
    # 1. Create: graph_builder = StateGraph(AgentState)
    graph_builder = StateGraph(AgentState)

    # 2. Add all 6 nodes + a tool_node
    graph_builder.add_node("intake_node", intake_node)
    graph_builder.add_node("policy_retrieval_node", policy_retrieval_node)
    graph_builder.add_node("llm_reasoning_node", llm_reasoning_node)
    
    tool_node = ToolNode([
        policy_lookup, 
        receipt_completeness_check, 
        per_diem_limit_check, 
        approval_threshold_check
    ])
    graph_builder.add_node("tool_node", tool_node)
    
    graph_builder.add_node("synthesizer_node", synthesizer_node)
    graph_builder.add_node("output_validator_node", output_validator_node)
    graph_builder.add_node("output_node", output_node)

    # 3. Add edges
    graph_builder.add_edge(START, "intake_node")
    graph_builder.add_edge("intake_node", "policy_retrieval_node")
    
    graph_builder.add_conditional_edges(
        "policy_retrieval_node",
        route_after_policy,
        {
            "output_validator_node": "output_validator_node",
            "llm_reasoning_node": "llm_reasoning_node"
        }
    )
    
    graph_builder.add_conditional_edges(
        "llm_reasoning_node",
        tools_condition,
        {
            "tools": "tool_node",
            "__end__": "synthesizer_node"
        }
    )
    
    graph_builder.add_edge("tool_node", "llm_reasoning_node")
    graph_builder.add_edge("synthesizer_node", "output_validator_node")
    graph_builder.add_edge("output_validator_node", "output_node")
    graph_builder.add_edge("output_node", END)

    # 4. Compile: app = graph_builder.compile()
    app = graph_builder.compile()
    return app

# Singleton compiled app
app = build_graph()

def run_claim(claim_dict: dict) -> dict:
    """
    Creates initial state from claim_dict, invokes app with that state,
    and returns state["decision"].model_dump()
    """
    # Create initial state
    initial_state = {
        "claim": claim_dict,
        "messages": [],
        "tool_results": {}
    }
    
    # Invoke app
    final_state = app.invoke(initial_state)
    
    # Extract decision
    decision = final_state.get("decision")
    
    if decision and isinstance(decision, ReimbursementDecision):
        return decision.model_dump()
    elif decision and isinstance(decision, dict):
        return decision
    return {}

if __name__ == "__main__":
    # Test with claim_a_approve.json
    root_dir = Path(__file__).parent.parent
    claim_path = root_dir / "data" / "sample_claims" / "claim_a_approve.json"
    
    print(f"Loading claim from {claim_path}...")
    with open(claim_path, "r", encoding="utf-8") as f:
        claim_data = json.load(f)
        
    print("Running graph... (This may take a minute depending on LLM latency)")
    result = run_claim(claim_data)
    
    print("\n--- FINAL DECISION ---")
    print(json.dumps(result, indent=2))
