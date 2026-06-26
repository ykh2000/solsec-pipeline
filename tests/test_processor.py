import pytest
from backend.core.models import Finding, Severity, FindingSet
from backend.core.processor import Processor

def test_deduplication_exact_match():
    processor = Processor()
    target = "test.sol"
    
    finding1 = Finding(
        title="Reentrancy",
        description="Tool A found it",
        severity=Severity.HIGH,
        tool="ToolA",
        file_path=target,
        line_number=[10]
    )
    
    finding2 = Finding(
        title="Reentrancy",
        description="Tool B found it",
        severity=Severity.MEDIUM,
        tool="ToolB",
        file_path=target,
        line_number=[10]
    )
    
    fs1 = FindingSet(target_file=target, findings=[finding1])
    fs2 = FindingSet(target_file=target, findings=[finding2])
    
    final_report = processor.process_results(target, [fs1, fs2])
    
    # Should merge into 1 finding
    assert len(final_report.findings) == 1
    # Should keep highest severity
    assert final_report.findings[0].severity == Severity.HIGH
    # Should track both tools
    assert "ToolA" in final_report.findings[0].metadata["tools"]
    assert "ToolB" in final_report.findings[0].metadata["tools"]

def test_deduplication_no_overlap():
    processor = Processor()
    target = "test.sol"
    
    finding1 = Finding(
        title="Reentrancy",
        description="Found at line 10",
        severity=Severity.HIGH,
        tool="ToolA",
        file_path=target,
        line_number=[10]
    )
    
    finding2 = Finding(
        title="Reentrancy",
        description="Found at line 20",
        severity=Severity.HIGH,
        tool="ToolB",
        file_path=target,
        line_number=[20]
    )
    
    fs = FindingSet(target_file=target, findings=[finding1, finding2])
    final_report = processor.process_results(target, [fs])
    
    # Should NOT merge because line numbers don't overlap
    assert len(final_report.findings) == 2

def test_scoring():
    processor = Processor()
    target = "test.sol"
    
    finding = Finding(
        title="Bug",
        description="...",
        severity=Severity.CRITICAL,
        tool="Tool",
        file_path=target,
        line_number=[1]
    )
    
    fs = FindingSet(target_file=target, findings=[finding])
    final_report = processor.process_results(target, [fs])
    
    assert final_report.findings[0].metadata["security_score"] == 100
