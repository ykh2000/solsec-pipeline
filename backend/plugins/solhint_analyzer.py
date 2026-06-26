import json
import subprocess
from typing import Dict, Any, List
from ..core.base_analyzer import BaseAnalyzer
from ..core.models import Finding, FindingSet, Severity

"""
ANALYZER FOR SOLHINT LINTER.
RUNS SOLHINT AND PARSES THE JSON OUTPUT.
"""

class SolhintAnalyzer(BaseAnalyzer):
    def run(self) -> FindingSet:
        # Run solhint with JSON formatter
        cmd = ["solhint", self.target_path, "-f", "json"]
        try:
            # Solhint might return non-zero exit code if findings are found, 
            # so we handle it gracefully.
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Use index finding to grab only the JSON array block
            # Solhint often prints update warnings or node warnings to stdout
            raw_output = result.stdout.strip()
            start_idx = raw_output.find('[')
            end_idx = raw_output.rfind(']')
            
            # If no JSON array is found, return empty results
            if start_idx == -1 or end_idx == -1:
                return FindingSet(target_file=self.target_path, findings=[], metadata={"success": True})

            json_str = raw_output[start_idx:end_idx+1]
            raw_data = json.loads(json_str)
            return self._parse_results(raw_data)
        except Exception as e:
            return FindingSet(
                target_file=self.target_path,
                metadata={"error": str(e), "tool": "Solhint"}
            )
            
    def _parse_results(self, raw_data: List[Dict[str, Any]]) -> FindingSet:
        """
        Map Solhint's JSON output to our FindingSet Model.
        """
        findings = []
        
        for item in raw_data:
            # Skip the 'conclusion' object Solhint adds at the end
            if "conclusion" in item:
                continue
                
            finding = Finding(
                title=item.get("ruleId", "solhint-rule"),
                description=item.get("message", "No description provided"),
                severity=self._map_severity(item.get("severity")),
                tool="Solhint",
                file_path=self.target_path,
                # Ensure line_number is a List[int] and not [None]
                line_number=[item["line"]] if "line" in item and item["line"] is not None else [],
                raw_tool_output=item
            )
            findings.append(finding)
            
        return FindingSet(
            target_file=self.target_path,
            findings=findings,
            metadata={"success": True}
        )

    def _map_severity(self, solhint_severity: str) -> Severity:
        """
        Map Solhint's severity to our standard Severity Enum.
        """
        mapping = {
            "Error": Severity.HIGH,
            "Warning": Severity.MEDIUM,
            "Info": Severity.INFORMATIONAL
        }
        return mapping.get(solhint_severity, Severity.LOW)
