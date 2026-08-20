import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
import json

from audience_radar.storage.models import Base, Conversation, Topic, PainPoint
from audience_radar.config.models import WorkspaceConfig, AudienceProfile
from audience_radar.agents.insight import InsightGenerator, InsightResult
from audience_radar.observability.cost import CostLedger
from audience_radar.orchestration.insights import InsightOrchestrator

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
def test_config():
    aud = AudienceProfile(
        id="test_aud", name="Test", description="Test", goals=["Test"],
        not_our_audience=[], segments=[], languages=["en"], primary_countries=[]
    )
    return WorkspaceConfig(version=1, audience=aud, sources=[], defaults={})

class MockGenerator(InsightGenerator):
    def __init__(self):
        super().__init__(CostLedger(1.0))
        
    def generate(self, conversations, aud):
        return InsightResult(
            topics=[{"label": "Topic A", "description": "Desc A"}],
            pain_points=[{"title": "Pain A", "severity_score": 90, "topic_label": "Topic A"}],
            tokens_in=10,
            tokens_out=10,
            cost_usd=0.01
        )

def test_orchestrator_success(db_session, test_config):
    # Setup data
    from audience_radar.storage.models import Source, CollectionJob, RawPayload
    src = Source(id="src_1", audience_id="test_aud", platform="reddit", type="subreddit", name="test", config_json={}, config_hash="h1", priority="high", collection_frequency="daily", health="ok")
    db_session.add(src)
    db_session.flush()
    job = CollectionJob(id="job_1", source_id="src_1", started_at=datetime.now(timezone.utc), status="running", trigger="manual")
    db_session.add(job)
    db_session.flush()
    payload = RawPayload(id="raw_1", collection_job_id="job_1", platform_item_id="item_1", payload_gz=b"", payload_hash="h", fetched_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc))
    db_session.add(payload)
    db_session.flush()
    
    conv = Conversation(
        id="conv_1", audience_id="test_aud", source_id="src_1", raw_payload_id="raw_1",
        platform="reddit", platform_item_id="item_1", url="http",
        title="Test 1", body="Body 1", body_hash="h", simhash=0,
        posted_at=datetime.now(timezone.utc), collected_at=datetime.now(timezone.utc),
        word_count=10, content_type="post"
    )
    db_session.add(conv)
    db_session.commit()
    
    generator = MockGenerator()
    orchestrator = InsightOrchestrator(db_session, test_config, generator)
    
    count = orchestrator.run()
    assert count == 1
    
    # Verify tables
    topics = db_session.query(Topic).all()
    assert len(topics) == 1
    assert topics[0].label == "Topic A"
    
    pain_points = db_session.query(PainPoint).all()
    assert len(pain_points) == 1
    assert pain_points[0].title == "Pain A"
    assert pain_points[0].topic_id == topics[0].id

def test_orchestrator_no_data(db_session, test_config):
    generator = MockGenerator()
    orchestrator = InsightOrchestrator(db_session, test_config, generator)
    
    count = orchestrator.run()
    assert count == 0
    
    topics = db_session.query(Topic).all()
    assert len(topics) == 0
