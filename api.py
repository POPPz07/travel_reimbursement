"""
Travel Reimbursement Approval Agent API

Usage:
1. Start the API server:
   python api.py
2. POST a claim to evaluate:
   curl -X POST http://localhost:8000/evaluate-claim \
     -H "Content-Type: application/json" \
     -d @data/sample_claims/claim_a_approve.json
"""

import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env
load_dotenv()

from agent.schemas import ClaimInput
from agent.graph import run_claim

app = FastAPI(
    title="Travel Reimbursement Approval Agent API",
    description="GenAI policy-based travel reimbursement evaluation agent API.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
SAMPLE_CLAIMS_DIR = DATA_DIR / "sample_claims"

@app.post("/evaluate-claim")
def evaluate_claim(claim: ClaimInput):
    """
    Accepts ClaimInput JSON body, calls run_claim(),
    and returns the ReimbursementDecision JSON.
    """
    try:
        # Convert Pydantic object to dict for the agent
        claim_dict = claim.model_dump()
        result = run_claim(claim_dict)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}"
        )

@app.get("/health")
def health():
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "version": "1.0.0"}

@app.get("/policy")
def get_policy():
    """
    Returns the full travel policy document.
    """
    policy_path = DATA_DIR / "travel_policy.json"
    if not policy_path.exists():
        raise HTTPException(status_code=404, detail="Policy file not found.")
    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read policy: {str(e)}")

@app.get("/sample-claims")
def get_sample_claims():
    """
    Returns a list of available sample claim filenames.
    """
    if not SAMPLE_CLAIMS_DIR.exists():
        raise HTTPException(status_code=404, detail="Sample claims directory not found.")
    try:
        return [f.name for f in SAMPLE_CLAIMS_DIR.glob("*.json")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sample claims: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
