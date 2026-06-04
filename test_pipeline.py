from backend.core.orchestrator import Orchestrator

"""
UNIFIED TEST SCRIPT.
Updated to test Deduplication and Scoring.
"""

def test_unified_pipeline():
    target = "tests/sample_vulnerable.sol"
    print(f"--- [Unified Pipeline] Starting Analysis on {target} ---")
    
    # 1. Initialize the Orchestrator
    orchestrator = Orchestrator()
    
    # 2. Run the analysis (This handles all tools and deduplication)
    final_report = orchestrator.run_analysis(target)
    
    # 3. Report the findings
    print("\n" + "="*50)
    print("FINAL CONSOLIDATED REPORT")
    print("="*50)
    print(f"Target: {final_report.target_file}")
    print(f"Total Raw Alerts: {final_report.metadata.get('total_raw_findings')}")
    print(f"Deduplicated Findings: {len(final_report.findings)}")
    print("="*50)
    
    for i, finding in enumerate(final_report.findings, 1):
        score = finding.metadata.get("security_score", 0)
        tools = finding.metadata.get("tools", [finding.tool])
        print(f"\n{i}. [{finding.severity}] {finding.title} (Score: {score})")
        print(f"   Detected by: {', '.join(tools)}")
        print(f"   Location: {finding.file_path} (Lines: {finding.line_number})")
        print(f"   Summary: {finding.description[:100]}...")

    print("\n" + "="*50)
    print(f"ANALYSIS SUMMARY: Found {len(final_report.findings)} unique issues.")
    print("="*50)

if __name__ == "__main__":
    test_unified_pipeline()
