import json
import subprocess
from typing import Dict, Any
from ..core.base_analyzer import BaseAnalyzer
from ..core.models import Finding, FindingSet, Severity

"""
ANALYZER FOR SLITHER ANALYSIS TOOL.
IT RUNS THE SLITHER COMMAND AND PARSE THE JSON INTO OUR MODELS
"""

class SlitherAnalyzer(BaseAnalyzer):
    def run(self) -> FindingSet:
        # Using --json to get the output in the console instead of a file
        cmd = ["slither", self.target_path, "--json", "-"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            raw_data = json.loads(result.stdout)
            return self._parse_results(raw_data)
        except Exception as e:
            return FindingSet(
                target_file=self.target_path,
                metadata={"error": str(e)}
            )
            
    def _parse_results(self, raw_data: Dict[str, Any]) -> FindingSet:
        """
        Map Slither's JSON (output) to our FindingSet Model.
        """
        findings = []
        detectors = raw_data.get("results", {}).get("detectors", [])
        
        for d in detectors:
            # Extract line numbers from all elements
            lines = set()
            for element in d.get("elements", []):
                source_mapping = element.get("source_mapping", {})
                element_lines = source_mapping.get("lines", [])
                lines.update(element_lines)
            
            finding = Finding(
                title=d.get("check"),
                description=d.get("description"),
                severity=self._map_severity(d.get("impact")),
                tool="Slither",
                file_path=self.target_path,
                line_number=sorted(list(lines)),
                raw_tool_output=d
            )
            findings.append(finding)
            
        return FindingSet(
            target_file=self.target_path,
            findings=findings,
            metadata={"success": raw_data.get("success", False)}
        )

    def _map_severity(self, slither_impact: str) -> Severity:
        """
        Map Slither's 'Impact' level to our standard 'Severity' Enum.
        """
        mapping = {
            "High": Severity.HIGH,
            "Medium": Severity.MEDIUM,
            "Low": Severity.LOW,
            "Informational": Severity.INFORMATIONAL,
            "Optimization": Severity.OPTIMIZATION
        }
        return mapping.get(slither_impact, Severity.INFORMATIONAL)

"""
map_severity and parse_results acts as a translator for 
slither's Impact and our Enum (Severity).

If Slither Fails or file is invalid then it returns a FindingSet(Models.py) with an 
error in the metadata.
"""
