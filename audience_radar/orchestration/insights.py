from sqlalchemy.orm import Session
from datetime import datetime, timezone
import structlog
import uuid

from audience_radar.storage.models import Conversation, Topic, PainPoint
from audience_radar.storage.repositories import InsightRepository
from audience_radar.agents.insight import InsightGenerator
from audience_radar.config.models import WorkspaceConfig

logger = structlog.get_logger(__name__)

class InsightOrchestrator:
    def __init__(self, db: Session, config: WorkspaceConfig, generator: InsightGenerator):
        self.db = db
        self.config = config
        self.generator = generator
        self.insight_repo = InsightRepository(db)

    def run(self, batch_size: int = 50) -> int:
        """Process unaggregated conversations and generate insights."""
        
        # We can implement a tracking table for which conversations were aggregated,
        # but for MVP let's do a time-based approach or just fetch conversations 
        # that don't have associated Topic relationships yet.
        # MVP data model doesn't explicitly link Conversation <-> Topic many-to-many, 
        # it just aggregates them based on time windows.
        
        # For simplicity, we just grab recent conversations (e.g. last 7 days) 
        # and generate insights for them.
        
        conversations = self.db.query(Conversation).order_by(Conversation.collected_at.desc()).limit(batch_size).all()
        
        if not conversations:
            logger.info("no_conversations_to_aggregate")
            return 0
            
        try:
            result = self.generator.generate(conversations, self.config.audience)
            
            # Save topics and pain points
            # We map the string topic names to their DB IDs to link pain points
            topic_map = {}
            
            for t in result.topics:
                topic = Topic(
                    id=uuid.uuid4().hex,
                    audience_id=self.config.audience.id,
                    slug=uuid.uuid4().hex[:8],
                    status="detected",
                    confidence=0.8,
                    label=t.get("label", "Unknown Topic"),
                    description=t.get("description", ""),
                    item_count=len(conversations)
                )
                self.insight_repo.save_topic(topic)
                topic_map[topic.label] = topic.id
                
            for p in result.pain_points:
                topic_label = p.get("topic_label")
                topic_id = topic_map.get(topic_label)
                
                if not topic_id:
                    # Create a default topic if the LLM hallucinated a topic name
                    topic = Topic(
                        id=uuid.uuid4().hex,
                        audience_id=self.config.audience.id,
                        slug=uuid.uuid4().hex[:8],
                        status="detected",
                        confidence=0.5,
                        label=topic_label or "General Pain Points",
                        description="Auto-generated for orphaned pain points",
                        item_count=len(conversations)
                    )
                    self.insight_repo.save_topic(topic)
                    topic_id = topic.id
                    topic_map[topic.label] = topic_id
                
                pain_point = PainPoint(
                    id=uuid.uuid4().hex,
                    audience_id=self.config.audience.id,
                    slug=uuid.uuid4().hex[:8],
                    status="detected",
                    confidence=0.8,
                    topic_id=topic_id,
                    title=p.get("title", ""),
                    severity_score=p.get("severity_score", 50)
                )
                self.insight_repo.save_pain_point(pain_point)
                
            self.db.commit()
            logger.info("insights_generated", topics=len(result.topics), pain_points=len(result.pain_points))
            return len(result.topics)
            
        except Exception as e:
            self.db.rollback()
            logger.error("insight_orchestration_error", error=str(e))
            raise e
