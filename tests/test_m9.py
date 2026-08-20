import pytest
import json
from datetime import datetime, timezone
from audience_radar.agents.insight import InsightGenerator
from audience_radar.observability.cost import CostLedger, BudgetExceeded
from audience_radar.config.models import AudienceProfile
from audience_radar.storage.models import Conversation

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
def test_conversations():
    return [
        Conversation(
            id="conv_1", audience_id="test_aud", source_id="src_1", raw_payload_id="raw_1",
            platform="reddit", platform_item_id="item_1", url="http",
            title="Test 1", body="Body 1", body_hash="h", simhash=0,
            posted_at=datetime.now(timezone.utc), collected_at=datetime.now(timezone.utc),
            word_count=10, content_type="post"
        ),
        Conversation(
            id="conv_2", audience_id="test_aud", source_id="src_1", raw_payload_id="raw_2",
            platform="reddit", platform_item_id="item_2", url="http",
            title="Test 2", body="Body 2", body_hash="h", simhash=0,
            posted_at=datetime.now(timezone.utc), collected_at=datetime.now(timezone.utc),
            word_count=10, content_type="post"
        )
    ]

def test_insight_generator_success(monkeypatch, test_audience, test_conversations):
    ledger = CostLedger(monthly_cap_usd=5.0)
    generator = InsightGenerator(ledger)
    
    # Mock LLM response
    def mock_call_llm(prompt):
        return {
            "content": json.dumps({
                "topics": [{"label": "T1", "description": "Desc1"}],
                "pain_points": [{"title": "P1", "severity_score": 90, "topic_label": "T1"}]
            }),
            "usage": {"prompt_tokens": 200, "completion_tokens": 100}
        }
        
    monkeypatch.setattr(generator, "_call_llm", mock_call_llm)
    
    result = generator.generate(test_conversations, test_audience)
    assert len(result.topics) == 1
    assert result.topics[0]["label"] == "T1"
    assert len(result.pain_points) == 1
    assert result.pain_points[0]["title"] == "P1"
    assert result.tokens_in == 200
    assert result.cost_usd > 0
    assert ledger.get_current_spend(2026, 8) > 0

def test_insight_generator_invalid_schema(monkeypatch, test_audience, test_conversations):
    ledger = CostLedger(monthly_cap_usd=5.0)
    generator = InsightGenerator(ledger)
    
    def mock_call_llm(prompt):
        return {
            "content": "Not JSON",
            "usage": {"prompt_tokens": 200, "completion_tokens": 100}
        }
        
    monkeypatch.setattr(generator, "_call_llm", mock_call_llm)
    
    with pytest.raises(ValueError) as exc:
        generator.generate(test_conversations, test_audience)
    assert "Failed to parse LLM insight schema" in str(exc.value)

def test_insight_generator_budget_exceeded(test_audience, test_conversations):
    ledger = CostLedger(monthly_cap_usd=0.00000001)
    generator = InsightGenerator(ledger)
    
    with pytest.raises(BudgetExceeded):
        generator.generate(test_conversations, test_audience)
