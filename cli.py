import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Load .env automatically
load_dotenv()

from agent.graph import run_claim

console = Console()

ROOT_DIR = Path(__file__).parent
SAMPLE_CLAIMS_DIR = ROOT_DIR / "data" / "sample_claims"

def get_decision_color(decision: str) -> str:
    decision_lower = decision.lower()
    if "partially approved" in decision_lower or "manual review" in decision_lower:
        return "yellow"
    elif "approved" in decision_lower:
        return "green"
    elif "rejected" in decision_lower:
        return "red"
    return "white"

def process_single_claim(claim_path: Path, verbose: bool, output_path: Path = None) -> dict:
    if not claim_path.exists():
        console.print(f"[bold red]Error: File not found {claim_path}[/bold red]")
        sys.exit(1)
        
    try:
        with open(claim_path, "r", encoding="utf-8") as f:
            claim_data = json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error parsing JSON {claim_path}: {e}[/bold red]")
        sys.exit(1)
        
    claim_id = claim_data.get("claim_id", "UNKNOWN")
    console.print(f"Processing claim [bold cyan]{claim_id}[/bold cyan] from {claim_path.name}...")
    
    try:
        result = run_claim(claim_data)
    except Exception as e:
        console.print(f"[bold red]Error processing claim {claim_id}: {e}[/bold red]")
        sys.exit(1)
        
    decision = result.get("decision", "UNKNOWN")
    color = get_decision_color(decision)
    
    body = (
        f"Approved Amount : [bold]{result.get('approved_amount', 0)}[/bold]\n"
        f"Rejected Amount : [bold]{result.get('rejected_amount', 0)}[/bold]\n"
        f"Confidence      : {result.get('confidence', 0)}\n"
        f"\n[bold]Reasoning:[/bold] {result.get('reasoning', '')}"
    )
    
    if decision == "Manual Review" and result.get("manual_review_reason"):
        body += f"\n\n[bold red]Manual Review Reason:[/bold red] {result.get('manual_review_reason')}"
        
    panel = Panel(
        body,
        title=f"Claim {claim_id} — [{color}]{decision}[/{color}]",
        border_style=color
    )
    console.print(panel)
    
    if verbose and "audit_trail" in result:
        table = Table(title=f"Audit Trail for {claim_id}")
        table.add_column("Step", style="cyan", justify="right")
        table.add_column("Tool Name", style="magenta")
        table.add_column("Output Summary", style="green")
        table.add_column("Rules", style="yellow")
        
        for entry in result["audit_trail"]:
            table.add_row(
                str(entry.get("step")),
                entry.get("tool_name"),
                entry.get("output_summary", "")[:80] + ("..." if len(entry.get("output_summary", "")) > 80 else ""),
                ", ".join(entry.get("policy_rules_triggered", []))
            )
        console.print(table)
        
    if output_path:
        # Save JSON result to output path
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            console.print(f"[dim]Result saved to {output_path}[/dim]")
        except Exception as e:
            console.print(f"[bold red]Failed to write to {output_path}: {e}[/bold red]")
            
    return result

def main():
    parser = argparse.ArgumentParser(description="Travel Reimbursement Approval Agent CLI")
    parser.add_argument("--claim", type=str, help="Path to a single claim JSON file")
    parser.add_argument("--all", action="store_true", help="Run all sample claims in data/sample_claims/")
    parser.add_argument("--verbose", action="store_true", help="Print the full audit_trail in output")
    parser.add_argument("--output", type=str, help="Save JSON result to this file path (only used with --claim)")
    
    args = parser.parse_args()
    
    if args.all:
        if not SAMPLE_CLAIMS_DIR.exists():
            console.print(f"[bold red]Sample claims directory not found: {SAMPLE_CLAIMS_DIR}[/bold red]")
            sys.exit(1)
            
        claim_files = list(SAMPLE_CLAIMS_DIR.glob("*.json"))
        if not claim_files:
            console.print("[yellow]No json files found in sample claims directory.[/yellow]")
            sys.exit(0)
            
        summary_table = Table(title="Batch Processing Summary")
        summary_table.add_column("File", style="cyan")
        summary_table.add_column("Claim ID", style="blue")
        summary_table.add_column("Decision", style="bold")
        summary_table.add_column("Approved", style="green")
        summary_table.add_column("Rejected", style="red")
        
        all_results = []
        for cf in sorted(claim_files):
            result = process_single_claim(cf, args.verbose)
            all_results.append(result)
            decision = result.get("decision", "UNKNOWN")
            color = get_decision_color(decision)
            summary_table.add_row(
                cf.name,
                result.get("claim_id", "UNKNOWN"),
                f"[{color}]{decision}[/{color}]",
                str(result.get("approved_amount", 0)),
                str(result.get("rejected_amount", 0))
            )
            console.print("-" * 50)
            
        console.print(summary_table)
        
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(all_results, f, indent=2)
                console.print(f"[dim]Batch results saved to {args.output}[/dim]")
            except Exception as e:
                console.print(f"[bold red]Failed to write batch output: {e}[/bold red]")
                
    elif args.claim:
        claim_path = Path(args.claim)
        out_path = Path(args.output) if args.output else None
        process_single_claim(claim_path, args.verbose, out_path)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
