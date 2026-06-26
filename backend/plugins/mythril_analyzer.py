import json
import subprocess
from typing import Dict, Any, List
from ..core.base_analyzer import BaseAnalyzer
from ..core.models import Finding, FindingSet, Severity

"""
ANALYZER FOR MYTHRIL SECURITY TOOL.
RUNS MYTH ANALYZE AND PARSES THE JSON OUTPUT.
"""

class MythrilAnalyzer(BaseAnalyzer):
    def run(self) -> FindingSet:
        # Run mythril analyze with JSON output
        # Using --execution-timeout to prevent long runs in MVP
        cmd = ["myth", "analyze", self.target_path, "-o", "json", "--execution-timeout", "60"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Mythril might output some text before the JSON if there are warnings
            stdout = result.stdout.strip()
            start_idx = stdout.find('{')
            end_idx = stdout.rfind('}')
            
            if start_idx == -1 or end_idx == -1:
                return FindingSet(target_file=self.target_path, findings=[], metadata={"success": True, "raw_output": stdout})

            json_str = stdout[start_idx:end_idx+1]
            raw_data = json.loads(json_str)
            return self._parse_results(raw_data)
        except Exception as e:
            return FindingSet(
                target_file=self.target_path,
                metadata={"error": str(e), "tool": "Mythril"}
            )
            
    def _parse_results(self, raw_data: Dict[str, Any]) -> FindingSet:
        """
        Map Mythril's JSON output to our FindingSet Model.
        """
        findings = []
        issues = raw_data.get("issues", [])
        
        for issue in issues:
            finding = Finding(
                title=issue.get("title", "Mythril Issue"),
                description=issue.get("description", "No description provided"),
                severity=self._map_severity(issue.get("severity")),
                tool="Mythril",
                file_path=self.target_path,
                line_number=[issue.get("lineno")] if issue.get("lineno") is not None else [],
                raw_tool_output=issue
            )
            findings.append(finding)
            
        return FindingSet(
            target_file=self.target_path,
            findings=findings,
            metadata={"success": raw_data.get("success", False)}
        )

    def _map_severity(self, myth_severity: str) -> Severity:
        """
        Map Mythril's severity to our standard Severity Enum.
        Mythril uses: High, Medium, Low
        """
        mapping = {
            "High": Severity.HIGH,
            "Medium": Severity.MEDIUM,
            "Low": Severity.LOW
        }
        return mapping.get(myth_severity, Severity.LOW)
