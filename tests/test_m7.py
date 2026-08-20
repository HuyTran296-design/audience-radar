import pytest
import json
from audience_radar.agents.relevance import RelevanceScorer
from audience_radar.observability.cost import CostLedger, BudgetExceeded
from audience_radar.config.models import AudienceProfile, SourceConfig

@pytest.fixture
def test_audience():
    return AudienceProfile(
        id="test_aud",
        name="Test",
        description="Test",
        goals=["Test"],
        not_our_audience=["Test"],
        segments=[],
        languages=["en"],
        primary_countries=["US"]
    )
    
@pytest.fixture
def test_config():
    return SourceConfig(
        id="test_src",
        platform="reddit",
        type="subreddit",
        name="test",
        url="http://x",
        priority="high",
        min_relevance_score=50
    )

def test_scorer_success(monkeypatch, test_audience, test_config):
    ledger = CostLedger(monthly_cap_usd=1.0)
    scorer = RelevanceScorer(ledger)
    
    # Mock LLM response
    def mock_call_llm(prompt):
        return {
            "content": json.dumps({
                "relevance_score": 85,
                "relevance_stage": "pass",
                "relevance_reason": "Matches.",
                "intent": "test",
                "intent_confidence": 0.9,
                "is_rhetorical": False
            }),
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
        
    monkeypatch.setattr(scorer, "_call_llm", mock_call_llm)
    
    result = scorer.score("This is a test post.", test_audience, test_config)
    assert result.is_relevant is True
    assert result.score == 85
    assert result.tokens_in == 100
    assert result.cost_usd > 0
    assert ledger.get_current_spend(2026, 8) > 0 # Some spend was recorded

def test_scorer_rejects_low_score(monkeypatch, test_audience, test_config):
    ledger = CostLedger(monthly_cap_usd=1.0)
    scorer = RelevanceScorer(ledger)
    
    # Mock LLM response
    def mock_call_llm(prompt):
        return {
            "content": json.dumps({
                "relevance_score": 30,
                "relevance_stage": "fail",
                "relevance_reason": "No match."
            }),
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
        
    monkeypatch.setattr(scorer, "_call_llm", mock_call_llm)
    
    result = scorer.score("Irrelevant", test_audience, test_config)
    assert result.is_relevant is False
    assert result.score == 30

def test_scorer_invalid_schema(monkeypatch, test_audience, test_config):
    ledger = CostLedger(monthly_cap_usd=1.0)
    scorer = RelevanceScorer(ledger)
    
    def mock_call_llm(prompt):
        return {
            "content": "This is not JSON",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
        
    monkeypatch.setattr(scorer, "_call_llm", mock_call_llm)
    
    with pytest.raises(ValueError) as exc:
        scorer.score("Test", test_audience, test_config)
    assert "Failed to parse LLM response schema" in str(exc.value)

def test_scorer_cost_cap(monkeypatch, test_audience, test_config):
    ledger = CostLedger(monthly_cap_usd=0.0000001) # Extremely low cap
    scorer = RelevanceScorer(ledger)
    
    with pytest.raises(BudgetExceeded):
        scorer.score("Very long text that will exceed the tiny budget", test_audience, test_config)
