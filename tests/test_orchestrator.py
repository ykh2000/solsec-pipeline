import pytest
from backend.core.orchestrator import Orchestrator
from backend.plugins.slither_analyzer import SlitherAnalyzer
from backend.plugins.solhint_analyzer import SolhintAnalyzer

def test_plugin_discovery():
    orchestrator = Orchestrator()
    analyzer_names = [cls.__name__ for cls in orchestrator.analyzer_classes]
    
    assert "SlitherAnalyzer" in analyzer_names
    assert "SolhintAnalyzer" in analyzer_names
    assert len(orchestrator.analyzer_classes) >= 2

def test_run_analysis_returns_finding_set():
    orchestrator = Orchestrator()
    # Using a non-existent file just to see if it handles failure correctly
    # or we can use the sample one.
    report = orchestrator.run_analysis("tests/sample_vulnerable.sol")
    
    from backend.core.models import FindingSet
    assert isinstance(report, FindingSet)
    assert report.target_file == "tests/sample_vulnerable.sol"
