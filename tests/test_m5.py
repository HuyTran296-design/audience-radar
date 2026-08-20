import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import responses
from datetime import datetime

from audience_radar.storage.models import Base, Source, CollectionJob, RawPayload
from audience_radar.orchestration.runner import CollectionRunner
from audience_radar.config.models import SourceConfig

@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
    import sqlalchemy
    @sqlalchemy.event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def test_source(db_session):
    config = SourceConfig(
        id="test_reddit", platform="reddit", type="subreddit",
        name="r/test", url="http://reddit.com/r/test", priority="high",
        max_items_per_run=2
    )
    src = Source(
        id="test_reddit", audience_id="test_aud", platform="reddit", type="subreddit",
        name="test", config_json=config.model_dump(), config_hash="hash",
        priority="high", collection_frequency="daily", health="ok"
    )
    db_session.add(src)
    db_session.commit()
    return src

@responses.activate
def test_runner_success(db_session, test_source):
    # Mock Reddit response
    responses.add(
        responses.GET,
        "https://oauth.reddit.com/r/test/new",
        json={
            "data": {
                "children": [
                    {"data": {"name": "t3_a"}},
                    {"data": {"name": "t3_b"}}
                ],
                "after": "t3_b"
            }
        },
        status=200
    )
    
    runner = CollectionRunner(db_session)
    job = runner.run_source(test_source)
    
    assert job.status == "success"
    assert job.items_fetched == 2
    assert job.items_new == 2
    assert job.cursor_after == "t3_b"
    assert job.api_calls == 1
    
    # Check payload is saved
    payloads = db_session.query(RawPayload).all()
    assert len(payloads) == 2
    
    # Verify source was updated
    db_session.refresh(test_source)
    assert test_source.last_cursor == "t3_b"
    assert test_source.last_success_at is not None

@responses.activate
def test_runner_rate_limit(db_session, test_source):
    responses.add(
        responses.GET,
        "https://oauth.reddit.com/r/test/new",
        json={"message": "Too Many Requests"},
        status=429,
        headers={"Retry-After": "60"}
    )
    
    runner = CollectionRunner(db_session)
    job = runner.run_source(test_source)
    
    assert job.status == "error"
    assert job.error_class == "rate_limit_exceeded"
    
    # Check source failure increment
    db_session.refresh(test_source)
    assert test_source.consecutive_failures == 1
