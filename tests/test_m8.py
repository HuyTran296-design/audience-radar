import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone

from audience_radar.storage.models import Base, Source, CollectionJob, RawPayload, Conversation, ItemAnalysis, Content
from audience_radar.config.models import WorkspaceConfig, SourceConfig, AudienceProfile
from audience_radar.agents.relevance import RelevanceScorer, RelevanceResult
from audience_radar.observability.cost import CostLedger
from audience_radar.orchestration.pipeline import AnalysisPipeline

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
    src = SourceConfig(
        id="test_src", platform="reddit", type="subreddit",
        name="test", url="http://x", priority="high", min_relevance_score=50
    )
    aud = AudienceProfile(
        id="test_aud", name="Test", description="Test", goals=["Test"],
        not_our_audience=[], segments=[], languages=["en"], primary_countries=[]
    )
    return WorkspaceConfig(version=1, audience=aud, sources=[src], defaults={})

class MockScorer(RelevanceScorer):
    def __init__(self):
        super().__init__(CostLedger(1.0))
        self.mock_score = 80
        
    def score(self, text, aud, config):
        return RelevanceResult(
            is_relevant=self.mock_score >= (config.min_relevance_score or 50),
            score=self.mock_score,
            intent="test",
            confidence=0.9,
            reason="test",
            tokens_in=10,
            tokens_out=10,
            cost_usd=0.01
        )

def test_pipeline_relevant(db_session, test_config):
    # Setup Data
    src = Source(id="test_src", audience_id="test_aud", platform="reddit", type="subreddit", name="test", config_json={}, config_hash="h1", priority="high", collection_frequency="daily", health="ok")
    db_session.add(src)
    db_session.flush()
    
    job = CollectionJob(id="job_1", source_id="test_src", started_at=datetime.now(timezone.utc), status="running", trigger="manual")
    db_session.add(job)
    
    raw_data = {"title": "Test Title", "selftext": "Test Body", "permalink": "/r/test/123"}
    payload = RawPayload(id="raw_1", collection_job_id="job_1", platform_item_id="item_1", payload_gz=json.dumps(raw_data).encode(), payload_hash="h", fetched_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc))
    db_session.add(payload)
    db_session.commit()
    
    scorer = MockScorer()
    scorer.mock_score = 80 # Relevant
    
    pipeline = AnalysisPipeline(db_session, test_config, scorer)
    count = pipeline.run(batch_size=10)
    
    assert count == 1
    
    # Verify Content, Analysis, and Conversation created
    content = db_session.query(Content).first()
    assert content is not None
    assert content.origin_id == "raw_1"
    
    analysis = db_session.query(ItemAnalysis).first()
    assert analysis is not None
    assert analysis.is_relevant is True
    assert analysis.relevance_score == 80
    
    conv = db_session.query(Conversation).first()
    assert conv is not None
    assert conv.title == "Test Title"

def test_pipeline_irrelevant(db_session, test_config):
    # Setup Data
    src = Source(id="test_src", audience_id="test_aud", platform="reddit", type="subreddit", name="test", config_json={}, config_hash="h1", priority="high", collection_frequency="daily", health="ok")
    db_session.add(src)
    db_session.flush()
    
    job = CollectionJob(id="job_1", source_id="test_src", started_at=datetime.now(timezone.utc), status="running", trigger="manual")
    db_session.add(job)
    
    raw_data = {"title": "Bad Title", "selftext": "Bad Body", "permalink": "/r/test/456"}
    payload = RawPayload(id="raw_2", collection_job_id="job_1", platform_item_id="item_2", payload_gz=json.dumps(raw_data).encode(), payload_hash="h", fetched_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc))
    db_session.add(payload)
    db_session.commit()
    
    scorer = MockScorer()
    scorer.mock_score = 30 # Irrelevant
    
    pipeline = AnalysisPipeline(db_session, test_config, scorer)
    count = pipeline.run(batch_size=10)
    
    assert count == 1
    
    # Verify Content, Analysis created, but NO Conversation
    content = db_session.query(Content).first()
    assert content is not None
    
    analysis = db_session.query(ItemAnalysis).first()
    assert analysis is not None
    assert analysis.is_relevant is False
    assert analysis.relevance_score == 30
    
    conv = db_session.query(Conversation).first()
    assert conv is None
