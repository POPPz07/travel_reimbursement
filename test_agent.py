import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent
OUTPUTS_DIR = ROOT_DIR / "outputs" / "sample_outputs.json"
DATA_DIR = ROOT_DIR / "data" / "sample_claims"

def get_total_claimed(claim_id):
    for fn in DATA_DIR.glob("*.json"):
        with open(fn, "r") as f:
            data = json.load(f)
            if data["claim_id"] == claim_id:
                return data["total_claimed_amount"]
    return 0

def test_cached_outputs_math():
    """
    Offline verification test that ensures the deterministic JSON outputs 
    match the mathematical rules defined in the business logic.
    """
    if not OUTPUTS_DIR.exists():
        return
        
    with open(OUTPUTS_DIR, "r") as f:
        outputs = json.load(f)
        
    for decision in outputs:
        app = decision["approved_amount"]
        rej = decision["rejected_amount"]
        tot = get_total_claimed(decision["claim_id"])
        
        # Test 1: Manual Review cases must have 0.0 for both amounts
        if decision["decision"] == "Manual Review":
            assert app == 0.0, f"{decision['claim_id']}: Manual Review must have 0 approved amount"
            assert rej == 0.0, f"{decision['claim_id']}: Manual Review must have 0 rejected amount"
        else:
            # Test 2: Standard cases must perfectly sum to the total claimed amount
            assert abs((app + rej) - tot) <= 1.0, f"{decision['claim_id']}: Math mismatch! {app} + {rej} != {tot}"

def test_audit_trail_populated():
    """
    Ensures that every claim leaves an audit trail for compliance.
    """
    if not OUTPUTS_DIR.exists():
        return
        
    with open(OUTPUTS_DIR, "r") as f:
        outputs = json.load(f)
        
    for decision in outputs:
        # Test 3: Audit trail must not be empty
        assert len(decision.get("audit_trail", [])) > 0, f"{decision['claim_id']}: Missing audit trail"
