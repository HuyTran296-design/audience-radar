import os
import pytest
from unittest.mock import patch, MagicMock
from audience_radar.adapters.apple_ads import AppleAdsAdapter
from audience_radar.storage.models import Source, SearchSignal, RawPayload
from audience_radar.config.models import SourceConfig
from audience_radar.scoring.formulas import search_demand_score

@pytest.fixture
def mock_config():
    return SourceConfig(
        id="test_ads",
        name="Test Apple Ads",
        platform="apple_ads",
        tier=2,
        type="search_demand",
        options={"campaign_id": "123", "keywords": ["meditation"]}
    )

@pytest.fixture
def mock_source():
    return Source(id="test_ads", audience_id="test_audience")

def test_apple_ads_missing_credentials(mock_config, mock_source):
    # Should not crash, just return empty and log error
    adapter = AppleAdsAdapter(mock_config, mock_source)
    payloads = adapter.collect()
    assert len(payloads) == 0

def test_apple_ads_csv_import(mock_config, mock_source, monkeypatch):
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        tmp.write("keyword,country,popularity_score,pulled_at\n")
        tmp.write("meditation timer,US,85,2023-10-01T12:00:00\n")
        tmp.write("sleep sounds,UK,60,\n")
        tmp_path = tmp.name
        
    try:
        mock_config.options["csv_path"] = tmp_path
        adapter = AppleAdsAdapter(mock_config, mock_source)
        
        payloads = adapter.collect()
        assert len(payloads) == 1
        
        signals = adapter.normalize(payloads)
        assert len(signals) == 2
        assert signals[0].keyword == "meditation timer"
        assert signals[0].search_popularity == 85
        assert signals[1].keyword == "sleep sounds"
        assert signals[1].country == "UK"
        assert signals[1].search_popularity == 60
    finally:
        import os
        os.unlink(tmp_path)

def test_search_demand_score():
    # Popular keyword with good growth
    score1 = search_demand_score(popularity=80, growth=0.5, impressions=5000, conversions=5, intent_score=90)
    assert score1 > 70
    
    # Missing optional metrics shouldn't break it
    score2 = search_demand_score(popularity=40, growth=None, impressions=None, conversions=None, intent_score=60)
    assert 40 <= score2 <= 60
