import pytest
from typer.testing import CliRunner
from audience_radar.cli import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import responses

from audience_radar.storage.models import Base, Source
from audience_radar.config.models import SourceConfig
import audience_radar.storage.db

runner = CliRunner()

@pytest.fixture
def db_session(monkeypatch):
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
    
    # Mock SessionLocal and engine to use our in-memory DB
    monkeypatch.setattr(audience_radar.storage.db, "SessionLocal", lambda: session)
    monkeypatch.setattr(audience_radar.storage.db, "engine", engine)
    
    yield session
    session.close()

@pytest.fixture
def test_source(db_session):
    config = SourceConfig(
        id="test_reddit", platform="reddit", type="subreddit",
        name="r/test", url="http://reddit.com/r/test", priority="high",
        max_items_per_run=1
    )
    src = Source(
        id="test_reddit", audience_id="test_aud", platform="reddit", type="subreddit",
        name="test", config_json=config.model_dump(), config_hash="hash",
        priority="high", collection_frequency="daily", health="ok", enabled=True
    )
    db_session.add(src)
    db_session.commit()
    return src

@responses.activate
def test_jobs_run_single(db_session, test_source):
    responses.add(
        responses.GET,
        "https://oauth.reddit.com/r/test/new",
        json={"data": {"children": [{"data": {"name": "t3_a"}}], "after": "t3_a"}},
        status=200
    )
    
    result = runner.invoke(app, ["jobs", "run", "test_reddit"])
    assert result.exit_code == 0
    assert "Job finished with status: success" in result.stdout

@responses.activate
def test_jobs_run_all(db_session, test_source):
    responses.add(
        responses.GET,
        "https://oauth.reddit.com/r/test/new",
        json={"data": {"children": [{"data": {"name": "t3_b"}}], "after": "t3_b"}},
        status=200
    )
    
    result = runner.invoke(app, ["jobs", "run", "--all"])
    assert result.exit_code == 0
    assert "Job finished with status: success" in result.stdout
