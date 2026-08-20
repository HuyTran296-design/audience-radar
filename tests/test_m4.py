import pytest
import responses
from audience_radar.config.models import SourceConfig
from audience_radar.adapters.reddit import RedditAdapter
from audience_radar.adapters.base import AdapterException

@pytest.fixture
def subreddit_config():
    return SourceConfig(
        id="reddit_mindfulness",
        platform="reddit",
        type="subreddit",
        name="r/Mindfulness",
        url="https://www.reddit.com/r/Mindfulness/",
        priority="high"
    )

@pytest.fixture
def keyword_config():
    return SourceConfig(
        id="reddit_search",
        platform="reddit",
        type="keyword",
        name="Reddit search: meditation reminder",
        query="meditation reminder",
        priority="high",
        platform_options={"sort": "new", "time_filter": "week"}
    )

@responses.activate
def test_reddit_adapter_subreddit(subreddit_config):
    adapter = RedditAdapter(subreddit_config)
    
    # Mock Reddit API response
    responses.add(
        responses.GET,
        "https://oauth.reddit.com/r/Mindfulness/new",
        json={
            "data": {
                "children": [
                    {"data": {"name": "t3_12345", "title": "Test Post 1"}},
                    {"data": {"name": "t3_67890", "title": "Test Post 2"}}
                ],
                "after": "t3_67890"
            }
        },
        status=200
    )
    
    result = adapter.fetch(max_items=2)
    assert len(result.items) == 2
    assert result.next_cursor == "t3_67890"
    assert result.items[0].platform_item_id == "t3_12345"
    assert result.api_calls_made == 1

@responses.activate
def test_reddit_adapter_keyword(keyword_config):
    adapter = RedditAdapter(keyword_config)
    
    responses.add(
        responses.GET,
        "https://oauth.reddit.com/search",
        json={
            "data": {
                "children": [
                    {"data": {"name": "t3_abcde", "title": "Keyword match"}}
                ],
                "after": None
            }
        },
        status=200
    )
    
    result = adapter.fetch()
    assert len(result.items) == 1
    assert result.next_cursor is None
    assert result.items[0].platform_item_id == "t3_abcde"
    
    # Verify the query params used by looking at the mock
    assert len(responses.calls) == 1
    req_url = responses.calls[0].request.url
    assert "q=meditation+reminder" in req_url or "q=meditation%20reminder" in req_url
    assert "t=week" in req_url

@responses.activate
def test_reddit_adapter_rate_limit(subreddit_config):
    adapter = RedditAdapter(subreddit_config)
    
    responses.add(
        responses.GET,
        "https://oauth.reddit.com/r/Mindfulness/new",
        json={"message": "Too Many Requests"},
        headers={"Retry-After": "120"},
        status=429
    )
    
    with pytest.raises(AdapterException) as exc_info:
        adapter.fetch()
        
    assert exc_info.value.error_class == "rate_limit_exceeded"
    assert exc_info.value.retry_after == 120
