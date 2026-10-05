"""Priority engine unit tests."""
import pytest
from app.services.priority.engine import compute_priority_score


def test_priority_score_calculation():
    # Base calculation with low severity
    result = compute_priority_score(
        severity_score=20,
        urgency_score=20,
        impact_score=20,
        hazard_risk_score=10,
        vulnerability_score=10,
        confidence_score=0.9,
        duplicate_count=1,
    )
    assert "priority_score" in result
    assert "priority_level" in result
    assert 0 <= result["priority_score"] <= 100


def test_priority_critical_threshold():
    # Calculation with critical severity
    result = compute_priority_score(
        severity_score=95,
        urgency_score=90,
        impact_score=90,
        hazard_risk_score=95,
        vulnerability_score=85,
        confidence_score=0.95,
        duplicate_count=10,
    )
    assert result["priority_score"] >= 80
    assert result["priority_level"].value.upper() == "CRITICAL"
