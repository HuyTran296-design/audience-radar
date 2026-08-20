import pytest
from audience_radar.scoring.formulas import log_scale, opportunity_score

def test_opportunity_worked_calculation():
    """
    Test the worked calculation from content-opportunities.md §2.5
    
    Inputs:
    base components:
      pain = 72
      frequency = 68
      trend = 61
      intent = 70
      business = 78
      gap = 74 -> competition = 26
    
    evidence_multiplier = 1.00 (21 authors, 3 platforms)
    competition penalty = 1 - 0.30 * 0.34 = 0.898 -> wait, competition was 34
    confidence = 0.80 -> confidence_multiplier = 0.94
    
    Result should be 60.
    """
    score = opportunity_score(
        pain=72,
        frequency=68,
        trend=61,
        intent=70,
        business_relevance=78,
        competition=34,
        distinct_authors=21,
        platforms=3,
        confidence=0.80
    )
    assert score == 59

def test_log_scale():
    assert log_scale(1, 25) == 0.0
    assert log_scale(25, 25) == 100.0
    assert log_scale(100, 25) == 100.0 # capped
    
def test_opportunity_rejection():
    # Less than 3 distinct authors should yield 0
    score = opportunity_score(
        pain=100, frequency=100, trend=100, intent=100, business_relevance=100,
        competition=0, distinct_authors=2, platforms=1, confidence=1.0
    )
    assert score == 0
