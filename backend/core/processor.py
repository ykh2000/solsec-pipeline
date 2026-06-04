from typing import List, Dict, Any
from .models import Finding, FindingSet, Severity

class Processor:
    """
    Handles Normalization, Deduplication, and Scoring of findings.
    """
    
    SEVERITY_SCORE = {
        Severity.CRITICAL: 100,
        Severity.HIGH: 70,
        Severity.MEDIUM: 40,
        Severity.LOW: 20,
        Severity.INFORMATIONAL: 5,
        Severity.OPTIMIZATION: 1
    }

    def process_results(self, target_file: str, finding_sets: List[FindingSet]) -> FindingSet:
        """
        Takes multiple FindingSets and returns a single, deduplicated, and scored FindingSet.
        """
        all_findings = []
        for fs in finding_sets:
            all_findings.extend(fs.findings)
            
        deduplicated = self._deduplicate(all_findings)
        scored = self._apply_scoring(deduplicated)
        
        # Sort by severity score descending
        scored.sort(key=lambda x: self.SEVERITY_SCORE.get(x.severity, 0), reverse=True)
        
        return FindingSet(
            target_file=target_file,
            findings=scored,
            metadata={
                "original_tool_count": len(finding_sets),
                "total_raw_findings": len(all_findings),
                "deduplicated_count": len(scored)
            }
        )

    def _deduplicate(self, findings: List[Finding]) -> List[Finding]:
        """
        Merges findings that are likely the same issue.
        Criteria: Same file, similar title, and overlapping line numbers.
        """
        processed_findings: List[Finding] = []
        
        for f in findings:
            found_match = False
            for existing in processed_findings:
                # Check if it's the same file and same vulnerability type
                if f.file_path == existing.file_path and f.title.lower() == existing.title.lower():
                    # Check for line number overlap
                    f_lines = set(f.line_number)
                    ex_lines = set(existing.line_number)
                    
                    # If there's an overlap or both are empty (file-level issues)
                    if f_lines.intersection(ex_lines) or (not f_lines and not ex_lines):
                        found_match = True
                        self._merge_findings(existing, f)
                        break
            
            if not found_match:
                new_finding = f.model_copy()
                if not new_finding.metadata:
                    new_finding.metadata = {}
                new_finding.metadata["tools"] = [f.tool]
                processed_findings.append(new_finding)

        # Update tool field for display
        for f in processed_findings:
            tools_found = f.metadata.get("tools", [])
            if len(tools_found) > 1:
                f.tool = f"Multiple ({', '.join(tools_found)})"
            
        return processed_findings

    def _merge_findings(self, existing: Finding, new: Finding):
        """
        Helper to merge a new finding into an existing one.
        """
        if existing.metadata is None:
            existing.metadata = {"tools": [existing.tool]}
            
        if new.tool not in existing.metadata["tools"]:
            existing.metadata["tools"].append(new.tool)
        
        # Keep highest severity
        if self.SEVERITY_SCORE.get(new.severity, 0) > self.SEVERITY_SCORE.get(existing.severity, 0):
            existing.severity = new.severity
        
        # Keep longest description
        if len(new.description) > len(existing.description):
            existing.description = new.description
            
        # Merge line numbers
        existing.line_number = sorted(list(set(existing.line_number).union(set(new.line_number))))

    def _apply_scoring(self, findings: List[Finding]) -> List[Finding]:
        """
        Adds a numerical score to metadata based on severity.
        """
        for f in findings:
            score = self.SEVERITY_SCORE.get(f.severity, 0)
            if f.metadata is None:
                f.metadata = {}
            f.metadata["security_score"] = score
        return findings
