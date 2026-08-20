import pytest
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import uuid

from audience_radar.storage.models import (
    Base, Source, CollectionJob, RawPayload, Conversation, Comment, 
    ItemAnalysis, Embedding, Content
)
from audience_radar.storage.repositories import ItemRepository, AnalysisRepository

from sqlalchemy.pool import StaticPool

@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
    # Enable foreign keys for SQLite
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

def test_writing_items_and_analysis(db_session):
    import sqlalchemy
    
    # 1. Setup Source
    src = Source(
        id="src_1", audience_id="aud_1", platform="reddit", type="subreddit",
        name="Test", config_json={}, config_hash="h1", priority="high", 
        collection_frequency="daily", health="ok"
    )
    db_session.add(src)
    db_session.flush()
    
    job = CollectionJob(
        id="job_1", source_id="src_1", started_at=datetime.now(timezone.utc),
        status="running", trigger="manual"
    )
    db_session.add(job)
    
    raw = RawPayload(
        id="raw_1", collection_job_id="job_1", platform_item_id="item_1",
        payload_gz=b"gzdata", payload_hash="phash",
        fetched_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc)
    )
    db_session.add(raw)
    db_session.commit()
    
    # 2. Save Conversation
    item_repo = ItemRepository(db_session)
    conv = Conversation(
        id="conv_1", audience_id="aud_1", source_id="src_1", raw_payload_id="raw_1",
        platform="reddit", platform_item_id="item_1", url="http://x",
        body_hash="bhash", simhash=123, posted_at=datetime.now(timezone.utc),
        collected_at=datetime.now(timezone.utc), word_count=10, content_type="post"
    )
    saved_conv = item_repo.save_conversation(conv)
    assert saved_conv.id == "conv_1"
    
    # 3. Save Comment
    cmt = Comment(
        id="cmt_1", conversation_id="conv_1", depth=1, body="test",
        body_hash="bhash2", simhash=456, posted_at=datetime.now(timezone.utc),
        collected_at=datetime.now(timezone.utc)
    )
    saved_cmt = item_repo.save_comment(cmt)
    assert saved_cmt.id == "cmt_1"
    
    # 4. Save Analysis
    content = Content(
        id="content_1", origin_type="conversation", origin_id="conv_1",
        audience_id="aud_1", text="test", text_hash="thash",
        posted_at=datetime.now(timezone.utc), platform="reddit", source_id="src_1"
    )
    db_session.add(content)
    db_session.commit()
    
    analysis_repo = AnalysisRepository(db_session)
    analysis = ItemAnalysis(
        id="ana_1", content_id="content_1", prompt_version="v1",
        model="gpt", model_tier="cheap", relevance_score=80,
        relevance_stage="pass", is_relevant=True,
        analyzed_at=datetime.now(timezone.utc)
    )
    saved_analysis = analysis_repo.save_analysis(analysis)
    assert saved_analysis.id == "ana_1"
    
    # 5. Save Vector Embedding (Mock test)
    import struct
    emb_data = struct.pack('f'*3, 0.1, 0.2, 0.3)
    emb = Embedding(
        id="emb_1", content_id="content_1", owner_type="content",
        owner_id="content_1", vector=emb_data, model="ada", dimensions=3
    )
    saved_emb = analysis_repo.save_embedding(emb)
    assert saved_emb.id == "emb_1"


def test_invalid_source_id_fails(db_session):
    import sqlalchemy
    item_repo = ItemRepository(db_session)
    
    # Trying to save conversation with non-existent source_id
    conv = Conversation(
        id="conv_2", audience_id="aud_1", source_id="invalid_src", 
        raw_payload_id="raw_1", platform="reddit", platform_item_id="item_2", 
        url="http://y", body_hash="bhash", simhash=123, 
        posted_at=datetime.now(timezone.utc), collected_at=datetime.now(timezone.utc), 
        word_count=10, content_type="post"
    )
    
    with pytest.raises(IntegrityError):
        item_repo.save_conversation(conv)


def test_duplicate_platform_item_id_fails(db_session):
    import sqlalchemy
    # Setup source and payload
    src = Source(
        id="src_2", audience_id="aud_1", platform="reddit", type="subreddit",
        name="Test", config_json={}, config_hash="h1", priority="high", 
        collection_frequency="daily", health="ok"
    )
    db_session.add(src)
    db_session.flush()
    
    job = CollectionJob(
        id="job_2", source_id="src_2", started_at=datetime.now(timezone.utc),
        status="running", trigger="manual"
    )
    db_session.add(job)
    
    raw = RawPayload(
        id="raw_2", collection_job_id="job_2", platform_item_id="item_3",
        payload_gz=b"gzdata", payload_hash="phash",
        fetched_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc)
    )
    db_session.add(raw)
    db_session.commit()
    
    item_repo = ItemRepository(db_session)
    conv1 = Conversation(
        id="conv_3", audience_id="aud_1", source_id="src_2", raw_payload_id="raw_2",
        platform="reddit", platform_item_id="item_3", url="http://x",
        body_hash="bhash1", simhash=123, posted_at=datetime.now(timezone.utc),
        collected_at=datetime.now(timezone.utc), word_count=10, content_type="post"
    )
    item_repo.save_conversation(conv1)
    
    conv2 = Conversation(
        id="conv_4", audience_id="aud_1", source_id="src_2", raw_payload_id="raw_2",
        platform="reddit", platform_item_id="item_3", url="http://y",
        body_hash="bhash2", simhash=456, posted_at=datetime.now(timezone.utc),
        collected_at=datetime.now(timezone.utc), word_count=10, content_type="post"
    )
    
    with pytest.raises(IntegrityError):
        item_repo.save_conversation(conv2)
