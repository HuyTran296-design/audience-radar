import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from audience_radar.storage.models import Base, Source, AuditLog
from audience_radar.storage.repositories import SourceRepository
from audience_radar.config.models import SourceConfig

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_source_sync(db_session):
    repo = SourceRepository(db_session)
    
    # Create mock source config
    source_cfg = SourceConfig(
        id="test_source",
        platform="reddit",
        type="subreddit",
        name="Test",
        url="http://reddit.com/r/test"
    )
    
    added, updated, unchanged = repo.sync_sources("test_audience", [source_cfg])
    assert added == 1
    assert updated == 0
    assert unchanged == 0
    
    # Verify DB state
    sources = repo.list_sources()
    assert len(sources) == 1
    assert sources[0].id == "test_source"
    
    # Audit log check
    logs = db_session.query(AuditLog).all()
    assert len(logs) == 1
    assert logs[0].event_type == "source_created"
    
    # Run sync again without changes
    added, updated, unchanged = repo.sync_sources("test_audience", [source_cfg])
    assert added == 0
    assert updated == 0
    assert unchanged == 1
    
    # Modify source and sync
    source_cfg.priority = "high"
    added, updated, unchanged = repo.sync_sources("test_audience", [source_cfg])
    assert added == 0
    assert updated == 1
    assert unchanged == 0
    
    logs = db_session.query(AuditLog).all()
    assert len(logs) == 2
    assert logs[1].event_type == "source_updated"
