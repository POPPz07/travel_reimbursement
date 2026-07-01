from typing import List, Optional, Literal, Dict, Any, TypedDict, Annotated
from pydantic import BaseModel, Field, ConfigDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class ReceiptMetadata(BaseModel):
    receipt_id: str = Field(description="Unique identifier for the receipt")
    date: str = Field(description="Date of the receipt in ISO format YYYY-MM-DD")
    vendor: str = Field(description="Name of the vendor")
    category: str = Field(description="Category of the expense (e.g., hotel, meal, transport, misc)")
    amount: float = Field(description="Amount claimed for this receipt")
    currency: str = Field(description="Currency of the amount (e.g., INR, USD)")
    attachment_present: bool = Field(description="Indicates if a receipt attachment is provided")
    attachment_type: Optional[str] = Field(None, description="Type of the attachment (e.g., pdf, image) if present")

class ClaimInput(BaseModel):
    claim_id: str = Field(description="Unique identifier for the reimbursement claim")
    employee_id: str = Field(description="Employee ID of the claimant")
    employee_name: str = Field(description="Name of the employee")
    employee_grade: str = Field(description="Grade of the employee (e.g., L1, L2, L3, L4, L5)")
    department: str = Field(description="Department of the employee")
    trip_purpose: str = Field(description="Purpose of the travel")
    travel_start_date: str = Field(description="Start date of travel in ISO format YYYY-MM-DD")
    travel_end_date: str = Field(description="End date of travel in ISO format YYYY-MM-DD")
    destination: str = Field(description="Destination city")
    destination_tier: str = Field(description="Tier of the destination (e.g., domestic_tier1, domestic_tier2, international)")
    total_claimed_amount: float = Field(description="Total amount claimed for the entire trip")
    currency: str = Field(description="Currency of the total claimed amount")
    receipts: List[ReceiptMetadata] = Field(description="List of receipts associated with the claim")
    notes: Optional[str] = Field(None, description="Additional notes or comments from the employee")

class DeductionItem(BaseModel):
    receipt_id: str = Field(description="ID of the receipt for which the deduction is made")
    category: str = Field(description="Category of the receipt expense")
    claimed_amount: float = Field(description="Original amount claimed for this item")
    approved_amount: float = Field(description="Amount approved for reimbursement")
    deducted_amount: float = Field(description="Amount deducted or rejected")
    reason: str = Field(description="Human-readable reason for the deduction")
    policy_rule: str = Field(description="Policy rule ID cited for this deduction (e.g., MEAL-POL-001 §3.2)")

class AuditEntry(BaseModel):
    step: int = Field(description="Step number in the agentic workflow")
    tool_name: str = Field(description="Name of the tool called")
    input_summary: str = Field(description="Summary of the inputs provided to the tool")
    output_summary: str = Field(description="Summary of the outputs from the tool")
    policy_rules_triggered: List[str] = Field(description="List of policy rule IDs triggered or checked during this step")

class ReimbursementDecision(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    claim_id: str = Field(description="ID of the evaluated claim")
    decision: Literal["Approved", "Partially Approved", "Rejected", "Manual Review"] = Field(description="Final decision for the claim")
    approved_amount: float = Field(description="Total approved amount across all line items")
    rejected_amount: float = Field(description="Total rejected or deducted amount")
    deductions: List[DeductionItem] = Field(description="Detailed breakdown of deductions per receipt")
    missing_documents: List[str] = Field(description="List of receipt IDs with missing attachments")
    policy_references: List[str] = Field(description="All policy rule IDs cited during the evaluation")
    confidence: float = Field(description="Confidence score of the decision, from 0.0 to 1.0")
    reasoning: str = Field(description="Short, plain-English explanation of the decision suitable for the employee")
    manual_review_reason: Optional[str] = Field(None, description="Reason for routing to manual review, if applicable")
    audit_trail: List[AuditEntry] = Field(description="Full log of tool calls and intermediate checks")
    processed_at: str = Field(description="ISO timestamp of when the claim was processed")

class AgentState(TypedDict):
    claim: ClaimInput
    policy_context: List[Dict[str, Any]]
    messages: Annotated[List[BaseMessage], add_messages]
    tool_results: Dict[str, Any]
    decision: Optional[ReimbursementDecision]
    requires_manual_review: bool
    error: Optional[str]
