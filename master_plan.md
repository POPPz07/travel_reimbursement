# Travel Reimbursement Approval Agent
## Master Context, Architecture Plan & Implementation Spec

---

## SECTION 1: ASSIGNMENT (Verbatim Requirements)

### Purpose
Assess hands-on ability to build a practical GenAI and Agentic AI solution, not just describe one.

### Business Scenario
Review employee travel reimbursement claims against policy, receipts, limits, and approval rules.

### Build Objective
Create a working AI-assisted agent that evaluates a claim and returns a structured recommendation.

### Expected Effort
Designed to be completed in 2–3 days using free-tier, open-source, or local tools.

### Minimum Functional Expectations

1. **Claim intake** — Accept a reimbursement claim from JSON, CSV, form input, or API request.
2. **Context grounding** — Retrieve or reference relevant policy/rule context before making a decision.
3. **Tool/function usage** — Use at least two meaningful tools or functions such as:
   - policy lookup
   - receipt completeness check
   - per-diem/limit checker
   - duplicate detector
   - approval threshold check
   - output validator
4. **GenAI/Agentic workflow** — Show how the LLM decides when to use tools, combines results, and handles missing or conflicting information.
5. **Structured output** — Return consistent JSON with:
   - `decision` (Approve / Partially Approve / Reject / Manual Review)
   - `approved_amount`
   - `rejected_amount` / `deductions`
   - `missing_documents`
   - `policy_references` (rule basis)
   - `confidence`
   - `reasoning` (short explanation)
6. **Manual Review handling** — Route uncertain, incomplete, or policy-exception cases to Manual Review rather than forcing a decision.

### Required Deliverables
- Runnable code in a Git repository or zip
- README with setup steps, environment variables, how to run, key design choices
- Sample outputs: at least 3 example claims with generated decisions
- Demo evidence: screenshots, API responses, or notebook output
- Assumptions and limitations section

### Evaluation Criteria
1. **Hands-on implementation quality** — runnable, understandable, reasonably organized code
2. **Practical use of GenAI and Agentic AI** — tool calling, workflow control, prompting, context handling
3. **Business correctness** — sensible reimbursement decisions grounded in policy/rule context
4. **Reliability** — structured outputs, validation, fallbacks, manual review for uncertain cases
5. **Developer judgement** — clear trade-offs, simple design, avoidable over-engineering removed

### Optional Enhancements (Do These If Time Allows)
- Simple UI or chatbot interface
- **Audit trail** showing retrieved context, tools called, and intermediate checks ← HIGH PRIORITY
- Basic test cases or evaluation script for sample claims
- Confidence score or reason codes for manual review
- MCP-based tool integration ← SKIP (too time-expensive)

---

## SECTION 2: JOB DESCRIPTION CONTEXT (HCL Tech — GenAI Developer)

### Role Summary
Embedded GenAI expert within a squad of 7–10 traditional software engineers. Single point of contact for all GenAI decisions, implementation, and mentoring. Works under a GenAI Architect, translates architectural decisions into production-grade implementations, uplifts team capabilities.

### Key Responsibilities Relevant to This Assignment
- Design, develop, and optimize production-grade GenAI and Agentic AI applications in Python
- Integrate LLMs (OpenAI, Azure OpenAI, Anthropic, Cohere) into enterprise workflows
- Design and implement RAG pipelines, multi-agent orchestration, Agentic AI flows
- Train and mentor squad members on GenAI concepts — make AI understandable to non-AI devs
- Champion Safe AI, AI governance, and responsible AI development
- Monitor, test, and troubleshoot deployed GenAI models

### Required Skills Being Evaluated Through This Assignment
- Python proficiency with production-grade patterns
- Hands-on with LangChain, LangGraph, LlamaIndex, AutoGen, CrewAI, or equivalent
- RAG architectures, vector search, multi-agent systems
- Structured output, prompt engineering, chain-of-thought
- Solid software engineering: Git, API design, modular code
- Communication — README should be explainable to non-AI engineers

### What This Submission Must Signal
The reviewer is asking: "Could this person explain every design choice to 8 backend engineers? Do they think like an architect, not just a coder?" The submission has two audiences — the code reviewer (does it run and is it clean?) and the hiring manager (does this person reason at the right level?).

---

## SECTION 3: HCL TECH CONTEXT (What Aligns You With Them)

### HCL's AI Philosophy
- HCL's AI Force platform (just launched AI Force 2.0, April 2026) is built around: autonomous AI agents, RAG pipelines, governance guardrails, observability, and multi-LLM flexibility
- HCL describes its Agentic AI as: "AI agents operating in a structured, step-by-step manner for deterministic processes — ideal for end-to-end, significantly autonomous processes in dynamic environments involving reasoning and decision-making"
- AI Force 2.0 emphasizes: context-aware reasoning within governance boundaries, modular plug-and-play design, embedded responsible AI controls
- Key HCL vocabulary: **auditability**, **responsible AI**, **governance guardrails**, **modular architecture**, **enterprise-grade**, **RAG**, **multi-LLM flexibility**

### How to Mirror HCL's Architecture at Prototype Scale
| HCL AI Force Concept | What to Build in This Prototype |
|---|---|
| Governance guardrails | Pydantic output validation, confidence threshold enforcement |
| Auditability | Audit trail in every output (tools called, policy cited, reasoning chain) |
| Modular design | Tools, nodes, schemas, prompts each in their own files |
| RAG / context grounding | Policy context loaded from JSON files, cited by rule name in output |
| Responsible AI | Manual Review routing instead of forced decisions, confidence score |
| Multi-LLM flexibility | LLM abstracted via LangChain's interface — swap provider via env var |

---

## SECTION 4: ARCHITECTURE DECISIONS

### Framework: LangGraph (Not LangChain chains, Not CrewAI)

**Why LangGraph:**
- Explicitly listed in the JD required skills
- Provides stateful graph execution — every node's output is persisted in state, giving full auditability
- Conditional edges allow explicit Manual Review routing based on confidence or flags
- Human-in-the-loop capability is built-in (shows enterprise readiness without needing to implement it)
- Maps 1:1 to how HCL AI Force describes its Agentic AI architecture
- LangGraph 1.x is now production-proven (used by Klarna, LinkedIn, Uber)

**Why not CrewAI/AutoGen:** Too much abstraction for a single, well-bounded use case. LangGraph gives explicit node-by-node visibility that enterprise auditability requires.

**Why not simple LangChain chain:** A chain always executes the same steps in the same order. An agent must decide *which* tools to call based on what it finds in the claim — that requires a ReAct loop, which LangGraph handles natively.

### LLM: OpenAI gpt-4o-mini (or Groq llama-3-70b for free tier)
- gpt-4o-mini is cheap, reliable tool-calling, strong structured output via `.with_structured_output()`
- Groq is free-tier fallback: llama-3-70b-8192 via `langchain-groq`
- LLM provider abstracted via environment variable — demonstrates multi-LLM awareness

### Output Validation: Pydantic v2
- All outputs enforced via Pydantic schema — no hoping the LLM formats correctly
- Validator node is a separate graph node (shows enterprise reliability thinking)

### Policy Context: JSON files (Mock RAG)
- Policy loaded from `data/travel_policy.json` filtered by claim category
- This is described in README as "simulated policy retrieval — in production this would be a vector store query against an indexed policy document corpus"
- Policy rules are cited by rule ID in every output (e.g., `"TRAVEL-POL-003 §2.1"`)

### Interface: CLI (Primary) + FastAPI endpoint (Bonus)
- `python cli.py --claim data/sample_claims/claim_a.json` — clean, fast to demo
- Optional `api.py` with `POST /evaluate-claim` — adds enterprise integration signal

---

## SECTION 5: FULL PROJECT STRUCTURE

```
travel-reimbursement-agent/
│
├── README.md                          ← Primary deliverable document
├── .env.example                       ← OPENAI_API_KEY or GROQ_API_KEY
├── .env                               ← actual keys (gitignored)
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── travel_policy.json             ← Policy rules indexed by category + rule_id
│   ├── approval_matrix.json           ← Employee grade → approval thresholds
│   ├── per_diem_table.json            ← Destination tier → daily limits by category
│   ├── processed_claims.json          ← Existing claims (seeded for duplicate detection)
│   └── sample_claims/
│       ├── claim_a_approve.json       ← All valid → Approved
│       ├── claim_b_partial.json       ← Meals exceed per-diem → Partially Approved
│       ├── claim_c_reject.json        ← Missing receipts + over limit → Rejected
│       ├── claim_d_manual.json        ← Amount exceeds auto-approve threshold → Manual Review
│       └── claim_e_duplicate.json     ← Already submitted claim_id → Rejected (duplicate)
│
├── agent/
│   ├── __init__.py
│   ├── graph.py                       ← LangGraph StateGraph definition + compilation
│   ├── nodes.py                       ← All node functions (intake, policy_retrieval, llm_reasoning, synthesizer, validator)
│   ├── tools.py                       ← All 4 @tool decorated functions
│   ├── schemas.py                     ← All Pydantic models
│   └── prompts.py                     ← System prompt + tool-use instructions
│
├── api.py                             ← FastAPI app (BONUS — build after core is done)
├── cli.py                             ← CLI entry point
│
└── outputs/
    └── sample_outputs.json            ← Pre-run results for all 5 claims (demo evidence)
```

---

## SECTION 6: DATA SCHEMAS

### Claim Input Schema (`ClaimInput`)
```python
class ReceiptMetadata(BaseModel):
    receipt_id: str
    date: str                    # ISO format YYYY-MM-DD
    vendor: str
    category: str                # "hotel", "meal", "transport", "misc"
    amount: float
    currency: str                # "INR", "USD", etc.
    attachment_present: bool
    attachment_type: Optional[str]  # "pdf", "image", None

class ClaimInput(BaseModel):
    claim_id: str
    employee_id: str
    employee_name: str
    employee_grade: str          # "L1", "L2", "L3", "L4", "L5" (L5 = senior)
    department: str
    trip_purpose: str
    travel_start_date: str
    travel_end_date: str
    destination: str             # city name — used for per-diem lookup
    destination_tier: str        # "domestic_tier1", "domestic_tier2", "international"
    total_claimed_amount: float
    currency: str
    receipts: List[ReceiptMetadata]
    notes: Optional[str]
```

### Output Schema (`ReimbursementDecision`)
```python
class DeductionItem(BaseModel):
    receipt_id: str
    category: str
    claimed_amount: float
    approved_amount: float
    deducted_amount: float
    reason: str
    policy_rule: str             # e.g., "MEAL-POL-001 §3.2"

class AuditEntry(BaseModel):
    step: int
    tool_name: str
    input_summary: str
    output_summary: str
    policy_rules_triggered: List[str]

class ReimbursementDecision(BaseModel):
    claim_id: str
    decision: Literal["Approved", "Partially Approved", "Rejected", "Manual Review"]
    approved_amount: float
    rejected_amount: float
    deductions: List[DeductionItem]
    missing_documents: List[str]
    policy_references: List[str]      # All policy rule IDs cited
    confidence: float                  # 0.0 to 1.0
    reasoning: str                     # Human-readable explanation
    manual_review_reason: Optional[str]  # Populated if decision == "Manual Review"
    audit_trail: List[AuditEntry]      # Full tool call log
    processed_at: str                  # ISO timestamp
```

### LangGraph State Schema (`AgentState`)
```python
class AgentState(TypedDict):
    claim: ClaimInput
    policy_context: List[dict]         # Filtered policy rules for this claim
    messages: Annotated[List[BaseMessage], add_messages]
    tool_results: dict                 # Accumulated tool outputs
    decision: Optional[ReimbursementDecision]
    requires_manual_review: bool
    error: Optional[str]
```

---

## SECTION 7: TOOLS SPECIFICATION

### Tool 1: `policy_lookup`
```
Name: policy_lookup
Input: category (str), destination_tier (str)
Action: Reads data/travel_policy.json, filters rules matching category + tier
Returns: List of applicable policy rules with rule_id, limit, conditions
Purpose: Grounds the LLM in specific policy constraints before evaluating amounts
```

### Tool 2: `receipt_completeness_check`
```
Name: receipt_completeness_check
Input: receipts (List[ReceiptMetadata])
Action: Checks each receipt for: attachment_present, date within trip dates, valid category, amount > 0, vendor name present
Returns: {
  "complete_receipts": [...],
  "incomplete_receipts": [...],
  "missing_attachment_ids": [...],
  "issues": ["receipt_id X: missing attachment", ...]
}
Purpose: Validates documentation completeness before amount evaluation
```

### Tool 3: `per_diem_limit_check`
```
Name: per_diem_limit_check
Input: category (str), claimed_amount (float), destination_tier (str), trip_days (int)
Action: Reads data/per_diem_table.json, computes allowed total = daily_limit × trip_days
Returns: {
  "category": "meal",
  "daily_limit": 800,
  "trip_days": 3,
  "total_allowed": 2400,
  "claimed_amount": 2800,
  "within_limit": false,
  "excess_amount": 400,
  "policy_rule": "MEAL-POL-001 §3.2"
}
Purpose: Enforces per-diem daily limits — most common source of deductions
```

### Tool 4: `approval_threshold_check`
```
Name: approval_threshold_check
Input: total_amount (float), employee_grade (str)
Action: Reads data/approval_matrix.json, looks up grade's auto_approve_limit and escalation_limit
Returns: {
  "employee_grade": "L2",
  "total_claimed": 45000,
  "auto_approve_limit": 25000,
  "escalation_limit": 75000,
  "routing": "manager_approval_required",
  "policy_rule": "APPR-POL-002 §1.4"
}
Routing values: "auto_approve" | "manager_approval_required" | "director_approval_required" | "manual_review"
Purpose: Enforces financial approval matrix — determines if claim needs escalation
```

---

## SECTION 8: MOCK DATA SPECIFICATION

### `data/travel_policy.json`
```json
{
  "version": "2024-Q4",
  "rules": [
    {
      "rule_id": "HOTEL-POL-001",
      "category": "hotel",
      "section": "§2.1",
      "description": "Hotel accommodation limit per night",
      "tiers": {
        "domestic_tier1": {"limit_per_night": 5000, "currency": "INR"},
        "domestic_tier2": {"limit_per_night": 3500, "currency": "INR"},
        "international": {"limit_per_night": 150, "currency": "USD"}
      },
      "conditions": "Receipts mandatory. Pre-approval required above 1.5x limit.",
      "exceptions": "Executive grade L5 may exceed by 20% with manager approval."
    },
    {
      "rule_id": "MEAL-POL-001",
      "category": "meal",
      "section": "§3.2",
      "description": "Daily meal allowance",
      "tiers": {
        "domestic_tier1": {"daily_limit": 800, "currency": "INR"},
        "domestic_tier2": {"daily_limit": 600, "currency": "INR"},
        "international": {"daily_limit": 50, "currency": "USD"}
      },
      "conditions": "Receipts required above INR 200 per transaction. Alcohol not reimbursable.",
      "exceptions": "Client entertainment meals follow ENTERTAIN-POL-001 instead."
    },
    {
      "rule_id": "TRANSPORT-POL-001",
      "category": "transport",
      "section": "§4.1",
      "description": "Local transport (taxi/cab) per day",
      "tiers": {
        "domestic_tier1": {"daily_limit": 1000, "currency": "INR"},
        "domestic_tier2": {"daily_limit": 750, "currency": "INR"},
        "international": {"daily_limit": 40, "currency": "USD"}
      },
      "conditions": "Receipts mandatory for amounts above INR 300.",
      "exceptions": "Airport transfers exempt from daily limit."
    },
    {
      "rule_id": "MISC-POL-001",
      "category": "misc",
      "section": "§5.1",
      "description": "Miscellaneous expenses per trip",
      "tiers": {
        "domestic_tier1": {"trip_limit": 1500, "currency": "INR"},
        "domestic_tier2": {"trip_limit": 1000, "currency": "INR"},
        "international": {"trip_limit": 75, "currency": "USD"}
      },
      "conditions": "Must be business-purpose justified. Receipts required.",
      "exceptions": "None."
    }
  ]
}
```

### `data/approval_matrix.json`
```json
{
  "version": "2024-Q4",
  "policy_rule": "APPR-POL-002",
  "matrix": [
    {"grade": "L1", "auto_approve_limit": 10000, "manager_limit": 25000, "director_limit": 50000, "above_director": "manual_review"},
    {"grade": "L2", "auto_approve_limit": 25000, "manager_limit": 50000, "director_limit": 100000, "above_director": "manual_review"},
    {"grade": "L3", "auto_approve_limit": 40000, "manager_limit": 75000, "director_limit": 150000, "above_director": "manual_review"},
    {"grade": "L4", "auto_approve_limit": 60000, "manager_limit": 120000, "director_limit": 250000, "above_director": "manual_review"},
    {"grade": "L5", "auto_approve_limit": 100000, "manager_limit": 200000, "director_limit": 500000, "above_director": "manual_review"}
  ]
}
```

### `data/per_diem_table.json`
```json
{
  "tiers": {
    "domestic_tier1": {
      "cities": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune"],
      "daily_limits": {
        "hotel": 5000,
        "meal": 800,
        "transport": 1000,
        "misc": 500
      }
    },
    "domestic_tier2": {
      "cities": ["Nashik", "Nagpur", "Jaipur", "Lucknow", "Bhopal", "Indore"],
      "daily_limits": {
        "hotel": 3500,
        "meal": 600,
        "transport": 750,
        "misc": 333
      }
    },
    "international": {
      "daily_limits_usd": {
        "hotel": 150,
        "meal": 50,
        "transport": 40,
        "misc": 25
      }
    }
  }
}
```

### `data/processed_claims.json`
```json
{
  "processed_claim_ids": [
    "CLM-2024-001",
    "CLM-2024-002",
    "CLM-2024-003",
    "CLM-2024-009"
  ]
}
```

---

## SECTION 9: SAMPLE CLAIMS SPECIFICATION

### Claim A — Expected: `Approved`
```json
{
  "claim_id": "CLM-2024-010",
  "employee_id": "EMP-1042",
  "employee_name": "Ananya Sharma",
  "employee_grade": "L3",
  "department": "Sales",
  "trip_purpose": "Client meeting — Bangalore",
  "travel_start_date": "2024-11-04",
  "travel_end_date": "2024-11-06",
  "destination": "Bangalore",
  "destination_tier": "domestic_tier1",
  "total_claimed_amount": 18500,
  "currency": "INR",
  "receipts": [
    {"receipt_id": "R-001", "date": "2024-11-04", "vendor": "Hotel Leela", "category": "hotel", "amount": 4800, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-002", "date": "2024-11-05", "vendor": "Hotel Leela", "category": "hotel", "amount": 4800, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-003", "date": "2024-11-04", "vendor": "Cafe Coffee Day", "category": "meal", "amount": 750, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-004", "date": "2024-11-05", "vendor": "Mainland China", "category": "meal", "amount": 780, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-005", "date": "2024-11-06", "vendor": "Ola Cab", "category": "transport", "amount": 850, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-006", "date": "2024-11-05", "vendor": "Uber", "category": "transport", "amount": 920, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-007", "date": "2024-11-06", "vendor": "Airport Duty Free", "category": "misc", "amount": 600, "currency": "INR", "attachment_present": true, "attachment_type": "image"}
  ],
  "notes": "All receipts attached. Standard client visit."
}
```

### Claim B — Expected: `Partially Approved`
```json
{
  "claim_id": "CLM-2024-011",
  "employee_id": "EMP-2201",
  "employee_name": "Rahul Desai",
  "employee_grade": "L2",
  "department": "Engineering",
  "trip_purpose": "Training — Mumbai",
  "travel_start_date": "2024-11-10",
  "travel_end_date": "2024-11-13",
  "destination": "Mumbai",
  "destination_tier": "domestic_tier1",
  "total_claimed_amount": 32000,
  "currency": "INR",
  "receipts": [
    {"receipt_id": "R-010", "date": "2024-11-10", "vendor": "Taj Hotels", "category": "hotel", "amount": 4900, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-011", "date": "2024-11-11", "vendor": "Taj Hotels", "category": "hotel", "amount": 4900, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-012", "date": "2024-11-12", "vendor": "Taj Hotels", "category": "hotel", "amount": 4900, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-013", "date": "2024-11-10", "vendor": "The Table Restaurant", "category": "meal", "amount": 1800, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-014", "date": "2024-11-11", "vendor": "Zomato Order", "category": "meal", "amount": 1400, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-015", "date": "2024-11-12", "vendor": "Social Restaurant", "category": "meal", "amount": 1600, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-016", "date": "2024-11-13", "vendor": "Uber", "category": "transport", "amount": 980, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-017", "date": "2024-11-11", "vendor": "Rapido", "category": "transport", "amount": 850, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-018", "date": "2024-11-13", "vendor": "Stationery", "category": "misc", "amount": 670, "currency": "INR", "attachment_present": true, "attachment_type": "image"}
  ],
  "notes": "Meals were slightly over due to team dinner on first night."
}
```
*Note: Meal total = 4800 INR across 4 days. Per-diem allows 800/day × 4 = 3200. Excess = 1600 INR. Should be deducted. Hotel is within 5000/night limit. Transport within limit. Total approved should be ~30400.*

### Claim C — Expected: `Rejected`
```json
{
  "claim_id": "CLM-2024-012",
  "employee_id": "EMP-3301",
  "employee_name": "Vikram Nair",
  "employee_grade": "L1",
  "department": "Operations",
  "trip_purpose": "Site visit — Nashik",
  "travel_start_date": "2024-11-15",
  "travel_end_date": "2024-11-16",
  "destination": "Nashik",
  "destination_tier": "domestic_tier2",
  "total_claimed_amount": 22000,
  "currency": "INR",
  "receipts": [
    {"receipt_id": "R-020", "date": "2024-11-15", "vendor": "Hotel Unnamed", "category": "hotel", "amount": 8000, "currency": "INR", "attachment_present": false, "attachment_type": null},
    {"receipt_id": "R-021", "date": "2024-11-16", "vendor": "Unknown Dhaba", "category": "meal", "amount": 2500, "currency": "INR", "attachment_present": false, "attachment_type": null},
    {"receipt_id": "R-022", "date": "2024-11-15", "vendor": "Random Cab", "category": "transport", "amount": 3500, "currency": "INR", "attachment_present": false, "attachment_type": null},
    {"receipt_id": "R-023", "date": "2024-11-16", "vendor": "Unknown", "category": "misc", "amount": 8000, "currency": "INR", "attachment_present": false, "attachment_type": null}
  ],
  "notes": ""
}
```
*Note: All receipts missing attachments. Hotel 8000 > tier2 limit 3500. Meal 2500 > daily limit 600. Transport 3500 > daily limit 750. Misc 8000 >> trip limit 1000. All 4 receipts fail. Should be Rejected.*

### Claim D — Expected: `Manual Review`
```json
{
  "claim_id": "CLM-2024-013",
  "employee_id": "EMP-1155",
  "employee_name": "Priya Menon",
  "employee_grade": "L2",
  "department": "Business Development",
  "trip_purpose": "International client conference — Singapore",
  "travel_start_date": "2024-11-18",
  "travel_end_date": "2024-11-22",
  "destination": "Singapore",
  "destination_tier": "international",
  "total_claimed_amount": 68000,
  "currency": "INR",
  "receipts": [
    {"receipt_id": "R-030", "date": "2024-11-18", "vendor": "Marina Bay Sands", "category": "hotel", "amount": 12000, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-031", "date": "2024-11-19", "vendor": "Marina Bay Sands", "category": "hotel", "amount": 12000, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-032", "date": "2024-11-20", "vendor": "Marina Bay Sands", "category": "hotel", "amount": 12000, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-033", "date": "2024-11-21", "vendor": "Marina Bay Sands", "category": "hotel", "amount": 12000, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-034", "date": "2024-11-19", "vendor": "Hawker Centre", "category": "meal", "amount": 3500, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-035", "date": "2024-11-20", "vendor": "Lau Pa Sat", "category": "meal", "amount": 3200, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-036", "date": "2024-11-21", "vendor": "Grab Transport", "category": "transport", "amount": 4200, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-037", "date": "2024-11-22", "vendor": "Airport Transfer", "category": "transport", "amount": 3100, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-038", "date": "2024-11-20", "vendor": "Conference Registration", "category": "misc", "amount": 6000, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"}
  ],
  "notes": "International conference trip. All receipts attached."
}
```
*Note: Total 68,000 INR. L2 auto_approve_limit = 25,000, manager_limit = 50,000. 68,000 > 50,000 → needs director approval → routes to Manual Review.*

### Claim E — Expected: `Rejected` (Duplicate)
```json
{
  "claim_id": "CLM-2024-009",
  "employee_id": "EMP-0887",
  "employee_name": "Suresh Kumar",
  "employee_grade": "L3",
  "department": "Finance",
  "trip_purpose": "Finance team offsite — Pune",
  "travel_start_date": "2024-10-28",
  "travel_end_date": "2024-10-30",
  "destination": "Pune",
  "destination_tier": "domestic_tier1",
  "total_claimed_amount": 15000,
  "currency": "INR",
  "receipts": [
    {"receipt_id": "R-040", "date": "2024-10-28", "vendor": "Marriott Pune", "category": "hotel", "amount": 4800, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-041", "date": "2024-10-29", "vendor": "Marriott Pune", "category": "hotel", "amount": 4800, "currency": "INR", "attachment_present": true, "attachment_type": "pdf"},
    {"receipt_id": "R-042", "date": "2024-10-29", "vendor": "Pune Restaurant", "category": "meal", "amount": 750, "currency": "INR", "attachment_present": true, "attachment_type": "image"},
    {"receipt_id": "R-043", "date": "2024-10-30", "vendor": "Ola Cab", "category": "transport", "amount": 650, "currency": "INR", "attachment_present": true, "attachment_type": "image"}
  ],
  "notes": "Re-submitting as previous was said to be lost."
}
```
*Note: CLM-2024-009 is in processed_claims.json. Should detect duplicate and Reject immediately.*

---

## SECTION 10: LANGGRAPH GRAPH DEFINITION

### Node Descriptions

```
Node 1: intake_node
  - Validates ClaimInput against Pydantic schema
  - Computes trip_days from start/end dates
  - Sets initial state
  - On validation error: sets error field and routes to error_output node

Node 2: policy_retrieval_node
  - Reads data/travel_policy.json
  - Filters rules matching the categories present in the claim's receipts
  - Adds filtered rules to state.policy_context
  - Also checks processed_claims.json for duplicate claim_id
  - If duplicate: immediately sets decision to Rejected (duplicate) and skips to output

Node 3: llm_reasoning_node (ReAct loop)
  - LLM is bound with all 4 tools via llm.bind_tools([...])
  - System prompt instructs: evaluate the claim against loaded policy context, call tools as needed
  - Runs tool calls until LLM emits a final message (no more tool_calls)
  - Tool results accumulate in state.messages via ToolMessages
  - This is the core agentic loop — LLM decides WHICH tools to call and in what order

Node 4: synthesizer_node
  - LLM receives full conversation (claim + policy + all tool results)
  - Uses .with_structured_output(ReimbursementDecision) for reliable JSON
  - Produces the complete decision object
  - Sets state.decision

Node 5: output_validator_node
  - Validates state.decision is a valid ReimbursementDecision
  - Checks: approved_amount + rejected_amount ≈ total_claimed_amount
  - Checks: if decision == "Manual Review" then manual_review_reason must be populated
  - If validation fails: forces decision to "Manual Review" with reason = "Output validation failed — human review required"

Node 6: output_node
  - Formats and returns the final ReimbursementDecision
  - Adds processed_at timestamp
```

### Conditional Edges

```
After output_validator_node:
  - if state.decision.confidence < 0.5 → override decision to "Manual Review"
  - if state.error is set → route to error_output
  - else → route to output_node (terminal)

After policy_retrieval_node:
  - if duplicate detected → skip to synthesizer_node with pre-filled Rejected decision
  - else → proceed to llm_reasoning_node

After llm_reasoning_node:
  - if last message has tool_calls → loop back to llm_reasoning_node (tool execution via ToolNode)
  - if last message has no tool_calls → proceed to synthesizer_node
```

---

## SECTION 11: PROMPTS

### System Prompt (for llm_reasoning_node)
```
You are an enterprise travel reimbursement evaluation agent for a large IT services company.

Your job is to evaluate employee travel reimbursement claims against company policy and produce a fair, accurate, and well-reasoned decision.

You have access to the following tools:
- policy_lookup: retrieve policy rules for a specific expense category
- receipt_completeness_check: verify all receipts are complete and have attachments
- per_diem_limit_check: check if claimed amounts are within per-diem daily limits
- approval_threshold_check: check if the total amount requires escalation based on employee grade

EVALUATION WORKFLOW:
1. First call receipt_completeness_check on all receipts to understand documentation status
2. For each unique category in the claim, call per_diem_limit_check
3. Call approval_threshold_check on the total amount
4. Use policy_lookup if you need to verify specific policy rules

DECISION RULES:
- APPROVED: All receipts complete, all amounts within limits, amount within auto-approve threshold
- PARTIALLY APPROVED: Some receipts valid, some amounts exceed limits (approve the within-limit portion)
- REJECTED: Critical issues — missing receipts for all items, or gross policy violation, or duplicate claim
- MANUAL REVIEW: Amount exceeds auto-approve but is otherwise valid, OR borderline policy cases, OR confidence below 0.6

IMPORTANT:
- Always cite specific policy rule IDs (e.g., MEAL-POL-001 §3.2) in your reasoning
- Calculate exact approved and rejected amounts — do not approximate
- If a receipt is missing its attachment, that line item cannot be reimbursed
- Partial approval = approve only the within-policy portion of each category
- Your confidence score reflects how clear-cut the case is: 0.9+ = straightforward, 0.6-0.9 = some judgment required, below 0.6 = route to manual review

CONTEXT: The following policy rules apply to this claim:
{policy_context}
```

### Synthesizer Prompt (for synthesizer_node)
```
Based on the complete evaluation above (claim data, policy context, and all tool results), 
produce a final structured reimbursement decision.

Calculate:
- approved_amount: sum of all approved line items
- rejected_amount: sum of all rejected/deducted amounts  
- deductions: detailed breakdown per receipt
- missing_documents: list of receipt_ids with missing attachments
- policy_references: all rule IDs cited during evaluation
- confidence: 0.0–1.0 based on clarity of the case
- reasoning: 2–3 sentence plain-English explanation suitable for the employee
- manual_review_reason: if routing to Manual Review, explain exactly why

Ensure approved_amount + rejected_amount = total_claimed_amount.
```

---

## SECTION 12: CLI AND API SPECIFICATION

### `cli.py` Usage
```bash
# Evaluate a single claim
python cli.py --claim data/sample_claims/claim_a_approve.json

# Evaluate all sample claims
python cli.py --all

# Verbose mode (shows audit trail)
python cli.py --claim data/sample_claims/claim_b_partial.json --verbose

# Save output to file
python cli.py --claim data/sample_claims/claim_c_reject.json --output outputs/result.json
```

### `api.py` Endpoints (FastAPI — Bonus)
```
POST /evaluate-claim
  Body: ClaimInput JSON
  Response: ReimbursementDecision JSON

GET /health
  Response: {"status": "ok", "version": "1.0.0"}

GET /policy
  Response: Full policy document

GET /sample-claims
  Response: List of available sample claim filenames
```

---

## SECTION 13: README STRUCTURE

The README must include these sections IN THIS ORDER:

1. **Overview** — What the agent does, decision framework, 2 sentences
2. **Architecture** — LangGraph graph explanation with ASCII or description of nodes/edges
3. **Tools** — What each of the 4 tools does and the business logic it enforces
4. **Policy Grounding** — How policy is loaded, filtered, and cited in outputs
5. **Setup** — Prerequisites, installation, environment variables
6. **Running the Agent** — CLI commands with expected output
7. **Sample Outputs** — Paste or describe all 5 decisions with key fields shown
8. **Design Choices & Trade-offs** — This section is critical:
   - Why LangGraph over simple chains
   - Why Pydantic output validation
   - Why mock JSON files over vector DB (and what production would look like)
   - Why 4 tools instead of 2 (and where the line is)
   - Audit trail: why it matters for enterprise AI governance
9. **Assumptions & Limitations** — Be honest, be specific
10. **What's Next (Production Roadmap)** — Shows enterprise thinking

---

## SECTION 14: REQUIREMENTS.TXT

```
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-groq>=0.2.0          # free tier fallback
langgraph>=0.2.0
pydantic>=2.0.0
fastapi>=0.115.0               # for api.py bonus
uvicorn>=0.32.0               # for api.py bonus
python-dotenv>=1.0.0
rich>=13.0.0                   # for pretty CLI output
pytest>=8.0.0                  # for optional test file
```

---

## SECTION 15: IMPLEMENTATION SEQUENCE (Build Order)

Build in this exact order — each step is independently testable:

```
Phase 1 — Foundation (no LLM needed)
  Step 1: Create project structure and all data/ JSON files
  Step 2: Write schemas.py — all Pydantic models
  Step 3: Write tools.py — all 4 tool functions with unit-testable logic
  Step 4: Manually test tools with sample inputs in a Python shell

Phase 2 — Agent Core
  Step 5: Write prompts.py — system prompt and synthesizer prompt
  Step 6: Write nodes.py — all 6 node functions
  Step 7: Write graph.py — StateGraph, add nodes, add edges, compile

Phase 3 — Interface
  Step 8: Write cli.py — argument parsing, pretty output with rich
  Step 9: Run all 5 sample claims, capture output to outputs/sample_outputs.json

Phase 4 — Polish (if time)
  Step 10: Write api.py — FastAPI wrapper
  Step 11: Write README.md
  Step 12: Write basic pytest tests for tools
```

---

## SECTION 16: KEY CONSTRAINTS AND RULES

- **DO NOT** build a frontend — adds no signal for this role
- **DO NOT** implement MCP integration — too time-expensive for the signal it adds
- **DO NOT** use a real vector database — mock JSON files are appropriate and simpler
- **DO NOT** make the agent call tools in a hardcoded sequence — the LLM must decide
- **DO** include an audit trail in every output — highest-signal optional enhancement
- **DO** cite policy rule IDs (e.g., MEAL-POL-001 §3.2) in all deduction items
- **DO** route to Manual Review instead of forcing a decision when confidence < 0.5
- **DO** make the README explainable to a non-AI backend engineer
- **DO** use Pydantic v2 for all schema validation
- **DO** abstract the LLM behind an environment variable (OPENAI_API_KEY or GROQ_API_KEY)
- **DO** keep all code modular — one concern per file
- **DO** include .env.example (never commit actual .env)
- **DO** run all 5 sample claims and include the outputs as demo evidence

---

*End of Master Context and Plan*
*This document is the single source of truth for the Travel Reimbursement Approval Agent build.*