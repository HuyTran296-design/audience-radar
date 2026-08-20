import typer
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import structlog

from audience_radar.storage.models import Topic, PainPoint
from audience_radar.scoring.formulas import (
    opportunity_score, log_scale, frequency_score, trend_score, 
    intent_score, competition_score, coverage_score
)

logger = structlog.get_logger(__name__)

class OpportunityOrchestrator:
    def __init__(self, db: Session):
        self.db = db

    def score_insights(self) -> int:
        """
        Iterate over topics/pain points and apply the scoring formulas.
        In the full system, this would merge with competitor data and business intent.
        For MVP, we apply a baseline scoring pass using available metrics.
        """
        topics = self.db.query(Topic).filter(Topic.status == "detected").all()
        scored_count = 0
        
        for topic in topics:
            # MVP mock calculations for missing dimensions
            pain = 50.0
            freq = 50.0 
            trend = 50.0
            intent = 50.0
            business = 50.0
            comp = 50.0
            authors = topic.item_count or 0
            platforms_count = 1
            confidence_val = topic.confidence or 0.5
            
            # Use pure function
            final_score = opportunity_score(
                pain=pain,
                frequency=freq,
                trend=trend,
                intent=intent,
                business_relevance=business,
                competition=comp,
                distinct_authors=authors,
                platforms=platforms_count,
                confidence=confidence_val
            )
            
            # In the full data model, opportunity has its own table, but we can store 
            # the composite score on the topic or pain point for ranking purposes.
            # Here we just mark it reviewed and log it.
            topic.status = "analyzed"
            topic.confidence = confidence_val
            
            scored_count += 1
            logger.info("scored_topic", topic_id=topic.id, score=final_score, authors=authors)
            
        self.db.commit()
        return scored_count
