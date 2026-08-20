from sqlalchemy.orm import Session
from datetime import datetime, timezone
import structlog
import uuid
import json

from audience_radar.storage.models import Source, RawPayload, Conversation, ItemAnalysis, Content
from audience_radar.storage.repositories import ItemRepository, AnalysisRepository
from audience_radar.agents.relevance import RelevanceScorer
from audience_radar.config.models import WorkspaceConfig, SourceConfig
from sqlalchemy import not_

logger = structlog.get_logger(__name__)

class AnalysisPipeline:
    def __init__(self, db: Session, config: WorkspaceConfig, scorer: RelevanceScorer):
        self.db = db
        self.config = config
        self.scorer = scorer
        self.item_repo = ItemRepository(db)
        self.analysis_repo = AnalysisRepository(db)
        
        # Map of source ID to SourceConfig for quick lookup
        self.source_configs = {s.id: s for s in config.sources}

    def run(self, batch_size: int = 50) -> int:
        """Process unanalyzed payloads and score them."""
        # Find raw payloads that don't have a conversation yet 
        # (For MVP, we use a simple subquery or outer join, but let's do a simple check)
        
        # Wait, if it's NOT relevant, it won't have a conversation. It will have an ItemAnalysis.
        # But wait, ItemAnalysis points to Content. So we need a Content record even if it's not a Conversation?
        # Architecture says: "If irrelevant, drops the item (only logging ItemAnalysis)."
        # Let's say ItemAnalysis references Content. We create a Content row, run analysis. 
        # If relevant, create Conversation.
        
        # Fetch raw payloads not in Content
        # Using a subquery for performance in SQLite
        subq = self.db.query(Content.origin_id).filter(Content.origin_type == "raw_payload")
        
        payloads = self.db.query(RawPayload).filter(
            not_(RawPayload.id.in_(subq))
        ).limit(batch_size).all()
        
        processed_count = 0
        
        for payload in payloads:
            try:
                self._process_payload(payload)
                processed_count += 1
            except Exception as e:
                self.db.rollback()
                logger.error("pipeline_error", payload_id=payload.id, error=str(e))
                
        return processed_count
        
    def _process_payload(self, payload: RawPayload):
        # We need the Source to get the config
        from audience_radar.storage.models import CollectionJob
        job = self.db.query(CollectionJob).filter(CollectionJob.id == payload.collection_job_id).first()
        if not job:
            logger.warning("missing_job_for_payload", payload_id=payload.id)
            return
        
        source_id = job.source_id
        source_config = self.source_configs.get(source_id)
        
        if not source_config:
            logger.warning("missing_source_config", source_id=source_id)
            return
            
        raw_data = json.loads(payload.payload_gz.decode('utf-8'))
        
        # Extract text based on platform
        text = ""
        url = ""
        if source_config.platform == "reddit":
            text = raw_data.get("title", "") + "\n" + raw_data.get("selftext", "")
            url = f"https://reddit.com{raw_data.get('permalink', '')}"
            
        import hashlib
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        content = Content(
            id=uuid.uuid4().hex,
            origin_type="raw_payload",
            origin_id=payload.id,
            audience_id=self.config.audience.id,
            text=text,
            text_hash=text_hash,
            posted_at=payload.fetched_at, # mock
            platform=source_config.platform,
            source_id=source_id
        )
        self.db.add(content)
        self.db.flush()
        
        # Score it
        result = self.scorer.score(text, self.config.audience, source_config)
        
        analysis = ItemAnalysis(
            id=uuid.uuid4().hex,
            content_id=content.id,
            prompt_version="1.0",
            model=self.scorer.model,
            model_tier=self.scorer.tier,
            relevance_score=result.score,
            relevance_stage="scored",
            relevance_reason=result.reason,
            is_relevant=result.is_relevant,
            intent=result.intent,
            intent_confidence=result.confidence,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            analyzed_at=datetime.now(timezone.utc)
        )
        self.analysis_repo.save_analysis(analysis)
        
        if result.is_relevant:
            conv = Conversation(
                id=uuid.uuid4().hex,
                audience_id=self.config.audience.id,
                source_id=source_id,
                raw_payload_id=payload.id,
                platform=source_config.platform,
                platform_item_id=payload.platform_item_id,
                url=url,
                title=raw_data.get("title", ""),
                body=raw_data.get("selftext", ""),
                body_hash=text_hash,
                simhash=0, # mock
                posted_at=payload.fetched_at, # mock
                collected_at=payload.fetched_at,
                word_count=len(text.split()),
                content_type="post"
            )
            self.item_repo.save_conversation(conv)
            
        self.db.commit()
