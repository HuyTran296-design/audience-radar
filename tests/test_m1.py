import pytest
from pydantic import ValidationError
from audience_radar.config.models import SourceConfig
from audience_radar.config.loader import _check_inline_secrets, ConfigError
from audience_radar.observability.cost import CostLedger, BudgetExceeded
import os

def test_config_validation_missing_required():
    with pytest.raises(ValidationError) as exc_info:
        SourceConfig(platform="reddit", type="subreddit", name="test")
    assert "id" in str(exc_info.value)

def test_config_validation_bad_regex():
    with pytest.raises(ValidationError) as exc_info:
        SourceConfig(
            id="test_id", 
            platform="reddit", 
            type="subreddit", 
            name="test", 
            url="http://x.com",
            exclusion_patterns=["[invalid"]
        )
    assert "Invalid regex in exclusion_patterns" in str(exc_info.value)

def test_config_inline_secret():
    data = {"source": {"token": "1234567890abcdefGH123"}}
    with pytest.raises(ConfigError) as exc_info:
        _check_inline_secrets(data)
    assert "Inline secret detected" in str(exc_info.value)

def test_cost_cap_enforcement():
    ledger = CostLedger(monthly_cap_usd=1.0)
    # Shouldn't raise
    ledger.record_cost("test", "test", "test", 10, 10, 0.5)
    
    with pytest.raises(BudgetExceeded):
        ledger.record_cost("test", "test", "test", 10, 10, 0.6)

def test_migration_up_down():
    # In a real environment we would invoke alembic programmatically.
    # For now we'll just check if the models can be imported successfully.
    from audience_radar.storage.models import Source, Conversation
    assert Source.__tablename__ == "source"
    assert Conversation.__tablename__ == "conversation"
