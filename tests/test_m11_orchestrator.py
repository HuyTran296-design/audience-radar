from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
import uuid
from datetime import datetime, timezone

from audience_radar.storage.models import Base, Topic
from audience_radar.orchestration.opportunities import OpportunityOrchestrator

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

def test_score_insights(db_session):
    topic = Topic(
        id=uuid.uuid4().hex,
        audience_id="test_aud",
        slug=uuid.uuid4().hex[:8],
        status="detected",
        confidence=0.8,
        label="Test Topic",
        description="Test Desc",
        item_count=10
    )
    db_session.add(topic)
    db_session.commit()
    
    orchestrator = OpportunityOrchestrator(db_session)
    count = orchestrator.score_insights()
    
    assert count == 1
    
    updated_topic = db_session.query(Topic).filter_by(id=topic.id).first()
    assert updated_topic.status == "analyzed"
