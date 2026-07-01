import json
from pathlib import Path
from typing import Dict, Any, List
from langchain_core.tools import tool

# Root directory of the project
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

def _create_audit_entry(tool_name: str, input_summary: str, output_summary: str, policy_rules: List[str]) -> Dict[str, Any]:
    return {
        "step": 0,  # Step can be updated by the graph state manager later
        "tool_name": tool_name,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "policy_rules_triggered": policy_rules
    }

@tool
def policy_lookup(category: str, destination_tier: str) -> dict:
    """
    Looks up travel policy rules for a specific expense category and destination tier.
    Use this tool to ground the evaluation in specific company rules before evaluating amounts.
    
    Args:
        category (str): The expense category (e.g., 'hotel', 'meal', 'transport', 'misc').
        destination_tier (str): The destination tier (e.g., 'domestic_tier1', 'domestic_tier2', 'international').
        
    Returns:
        dict: A dictionary containing the matching policy rules and an audit entry.
    """
    file_path = DATA_DIR / "travel_policy.json"
    input_summary = f"category={category}, destination_tier={destination_tier}"
    
    if not file_path.exists():
        return {
            "error": f"File not found: {file_path}",
            "audit_entry": _create_audit_entry("policy_lookup", input_summary, "Error: File not found", [])
        }
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        matching_rules = []
        rule_ids = []
        for rule in data.get("rules", []):
            if rule.get("category") == category:
                rule_info = {
                    "rule_id": rule.get("rule_id"),
                    "description": rule.get("description"),
                    "conditions": rule.get("conditions"),
                    "exceptions": rule.get("exceptions"),
                    "limit_info": rule.get("tiers", {}).get(destination_tier)
                }
                matching_rules.append(rule_info)
                rule_ids.append(rule.get("rule_id"))
                
        output_summary = f"Found {len(matching_rules)} rules for {category}"
        return {
            "rules": matching_rules,
            "audit_entry": _create_audit_entry("policy_lookup", input_summary, output_summary, rule_ids)
        }
    except Exception as e:
        return {
            "error": str(e),
            "audit_entry": _create_audit_entry("policy_lookup", input_summary, f"Error: {str(e)}", [])
        }

@tool
def receipt_completeness_check(receipts_json: str) -> dict:
    """
    Checks each receipt in a claim for completeness (attachment, date, vendor, amount).
    Use this tool to validate documentation completeness before amount evaluation.
    
    Args:
        receipts_json (str): A JSON string representation of the list of receipts.
        
    Returns:
        dict: Complete receipts, incomplete receipts, missing attachment IDs, and issues.
    """
    input_summary = f"receipts_json payload of length {len(receipts_json)}"
    try:
        receipts = json.loads(receipts_json)
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON provided: {e}",
            "audit_entry": _create_audit_entry("receipt_completeness_check", input_summary, "JSON parsing error", [])
        }
        
    complete_receipts = []
    incomplete_receipts = []
    missing_attachment_ids = []
    issues = []
    
    for r in receipts:
        if not isinstance(r, dict):
            return {
                "error": "You must pass a JSON string containing a list of FULL receipt objects (dictionaries), not just IDs or strings.",
                "audit_entry": _create_audit_entry("receipt_completeness_check", input_summary, "Invalid format: list of strings instead of dicts", [])
            }
        r_id = r.get("receipt_id", "UNKNOWN")
        r_issues = []
        
        if not r.get("attachment_present"):
            r_issues.append("missing attachment")
            missing_attachment_ids.append(r_id)
        if not r.get("date"):
            r_issues.append("missing date")
        if not r.get("vendor"):
            r_issues.append("missing vendor")
        if r.get("amount", 0) <= 0:
            r_issues.append("amount <= 0")
            
        if r_issues:
            issues.append(f"receipt_id {r_id}: {', '.join(r_issues)}")
            incomplete_receipts.append(r)
        else:
            complete_receipts.append(r)
            
    output_summary = f"{len(complete_receipts)} complete, {len(incomplete_receipts)} incomplete"
    return {
        "complete_receipts": complete_receipts,
        "incomplete_receipts": incomplete_receipts,
        "missing_attachment_ids": missing_attachment_ids,
        "issues": issues,
        "audit_entry": _create_audit_entry("receipt_completeness_check", input_summary, output_summary, [])
    }

@tool
def per_diem_limit_check(category: str, claimed_amount: float, destination_tier: str, trip_days: int) -> dict:
    """
    Checks if claimed amounts are within the per-diem daily limits based on category and tier.
    Use this tool to enforce per-diem limits and calculate potential deductions.
    
    Args:
        category (str): Expense category (e.g., 'hotel', 'meal', 'transport').
        claimed_amount (float): Total amount claimed for this category.
        destination_tier (str): Destination tier (e.g., 'domestic_tier1', 'international').
        trip_days (int): Number of days in the trip.
        
    Returns:
        dict: Limit check results including whether it's within limits and any excess amount.
    """
    file_path = DATA_DIR / "per_diem_table.json"
    input_summary = f"category={category}, claimed={claimed_amount}, tier={destination_tier}, days={trip_days}"
    
    if not file_path.exists():
        return {
            "error": f"File not found: {file_path}",
            "audit_entry": _create_audit_entry("per_diem_limit_check", input_summary, "Error: File not found", [])
        }
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        tier_data = data.get("tiers", {}).get(destination_tier, {})
        limits = tier_data.get("daily_limits", tier_data.get("daily_limits_usd", {}))
        
        daily_limit = limits.get(category)
        if daily_limit is None:
            # If no limit is found in the table for this category, assume no limit check is applicable
            return {
                "category": category,
                "daily_limit": None,
                "trip_days": trip_days,
                "total_allowed": None,
                "claimed_amount": claimed_amount,
                "within_limit": True,
                "excess_amount": 0.0,
                "policy_rule": "NO_LIMIT_DEFINED",
                "audit_entry": _create_audit_entry("per_diem_limit_check", input_summary, "No limit defined for category", [])
            }
            
        total_allowed = float(daily_limit * trip_days)
        excess = float(claimed_amount) - total_allowed
        within_limit = excess <= 0
        
        # Policy rule mapping based on category for audit trail
        rule_map = {
            "hotel": "HOTEL-POL-001 §2.1",
            "meal": "MEAL-POL-001 §3.2",
            "transport": "TRANSPORT-POL-001 §4.1",
            "misc": "MISC-POL-001 §5.1"
        }
        policy_rule = rule_map.get(category, "UNKNOWN-POL")
        
        output_summary = f"Allowed: {total_allowed}, Claimed: {claimed_amount}, Excess: {max(0, excess)}"
        return {
            "category": category,
            "daily_limit": daily_limit,
            "trip_days": trip_days,
            "total_allowed": total_allowed,
            "claimed_amount": claimed_amount,
            "within_limit": within_limit,
            "excess_amount": max(0.0, excess),
            "policy_rule": policy_rule,
            "audit_entry": _create_audit_entry("per_diem_limit_check", input_summary, output_summary, [policy_rule.split()[0]])
        }
    except Exception as e:
        return {
            "error": str(e),
            "audit_entry": _create_audit_entry("per_diem_limit_check", input_summary, f"Error: {str(e)}", [])
        }

@tool
def approval_threshold_check(total_amount: float, employee_grade: str) -> dict:
    """
    Checks if the total amount requires escalation based on employee grade.
    Use this tool to enforce the financial approval matrix.
    
    Args:
        total_amount (float): Total claimed amount for the trip.
        employee_grade (str): Grade of the employee (e.g., 'L1', 'L2').
        
    Returns:
        dict: Routing requirement (e.g., 'auto_approve', 'manual_review') and threshold info.
    """
    file_path = DATA_DIR / "approval_matrix.json"
    input_summary = f"total_amount={total_amount}, grade={employee_grade}"
    
    if not file_path.exists():
        return {
            "error": f"File not found: {file_path}",
            "audit_entry": _create_audit_entry("approval_threshold_check", input_summary, "Error: File not found", [])
        }
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        policy_rule = data.get("policy_rule", "APPR-POL-002")
        matrix = data.get("matrix", [])
        
        grade_info = next((row for row in matrix if row.get("grade") == employee_grade), None)
        
        if not grade_info:
            return {
                "error": f"Grade {employee_grade} not found in matrix.",
                "audit_entry": _create_audit_entry("approval_threshold_check", input_summary, f"Grade {employee_grade} unknown", [])
            }
            
        auto_limit = grade_info.get("auto_approve_limit", 0)
        manager_limit = grade_info.get("manager_limit", 0)
        director_limit = grade_info.get("director_limit", 0)
        
        if total_amount <= auto_limit:
            routing = "auto_approve"
        elif total_amount <= manager_limit:
            routing = "manager_approval_required"
        elif total_amount <= director_limit:
            routing = "director_approval_required"
        else:
            routing = "manual_review"
            
        output_summary = f"Routing: {routing}"
        return {
            "employee_grade": employee_grade,
            "total_claimed": total_amount,
            "auto_approve_limit": auto_limit,
            "manager_limit": manager_limit,
            "director_limit": director_limit,
            "routing": routing,
            "policy_rule": policy_rule,
            "audit_entry": _create_audit_entry("approval_threshold_check", input_summary, output_summary, [policy_rule])
        }
    except Exception as e:
        return {
            "error": str(e),
            "audit_entry": _create_audit_entry("approval_threshold_check", input_summary, f"Error: {str(e)}", [])
        }

if __name__ == "__main__":
    print("Testing policy_lookup:")
    print(json.dumps(policy_lookup.invoke({"category": "hotel", "destination_tier": "domestic_tier1"}), indent=2))
    print("\n" + "="*50 + "\n")
    
    print("Testing receipt_completeness_check:")
    test_receipts = [
        {"receipt_id": "R1", "date": "2024-11-04", "vendor": "Hotel Leela", "amount": 4800, "attachment_present": True},
        {"receipt_id": "R2", "vendor": "No Date Vendor", "amount": -10, "attachment_present": False}
    ]
    print(json.dumps(receipt_completeness_check.invoke({"receipts_json": json.dumps(test_receipts)}), indent=2))
    print("\n" + "="*50 + "\n")
    
    print("Testing per_diem_limit_check:")
    print(json.dumps(per_diem_limit_check.invoke({"category": "meal", "claimed_amount": 3500.0, "destination_tier": "domestic_tier1", "trip_days": 4}), indent=2))
    print("\n" + "="*50 + "\n")
    
    print("Testing approval_threshold_check:")
    print(json.dumps(approval_threshold_check.invoke({"total_amount": 45000.0, "employee_grade": "L2"}), indent=2))
    print("\n" + "="*50 + "\n")
