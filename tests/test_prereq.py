"""Basic tests for the prerequisite checker (run on Windows for full coverage)."""

import sys
from pathlib import Path

# Make src importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.prereq_checker import PrerequisiteChecker, CheckResult


def test_checker_runs():
    checker = PrerequisiteChecker()
    report = checker.run_all()
    assert len(report.results) > 0
    assert isinstance(report.overall_passed, bool)


def test_check_result():
    r = CheckResult(name="test", passed=True, message="ok")
    assert r.passed is True


if __name__ == "__main__":
    test_checker_runs()
    test_check_result()
    print("Basic tests passed.")
