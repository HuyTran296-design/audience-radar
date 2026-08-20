from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
import hashlib
import uuid
import json

from .models import (
    Source, AuditLog, CollectionJob, RawPayload, Author,
    Conversation, Comment, Content, ItemAnalysis, Embedding,
    Topic, PainPoint, Question
)

# Existing SourceRepository here
class SourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def _compute_hash(self, config_dict: dict) -> str:
        config_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(config_str.encode('utf-8')).hexdigest()

    def sync_sources(self, audience_id: str, source_configs: list) -> tuple:
        added = 0
        updated = 0
        unchanged = 0
        existing_sources = {s.id: s for s in self.db.query(Source).filter(Source.audience_id == audience_id).all()}
        
        for sc in source_configs:
            config_dict = sc.model_dump()
            new_hash = self._compute_hash(config_dict)
            
            existing = existing_sources.get(sc.id)
            if not existing:
                new_source = Source(
                    id=sc.id, audience_id=audience_id, platform=sc.platform,
                    type=sc.type, name=sc.name, url=sc.url, query=sc.query,
                    enabled=sc.enabled, priority=sc.priority,
                    collection_frequency=sc.collection_frequency,
                    config_json=config_dict, config_hash=new_hash, health="ok"
                )
                self.db.add(new_source)
                audit = AuditLog(
                    id=uuid.uuid4().hex, event_type="source_created",
                    entity_type="Source", entity_id=sc.id, detail={"new": config_dict}
                )
                self.db.add(audit)
                added += 1
            else:
                if existing.config_hash != new_hash:
                    old_config = existing.config_json
                    for k, v in config_dict.items():
                        if hasattr(existing, k) and k not in ["id", "audience_id"]:
                            setattr(existing, k, v)
                    existing.config_json = config_dict
                    existing.config_hash = new_hash
                    
                    audit = AuditLog(
                        id=uuid.uuid4().hex, event_type="source_updated",
                        entity_type="Source", entity_id=sc.id,
                        detail={"old": old_config, "new": config_dict}
                    )
                    self.db.add(audit)
                    updated += 1
                else:
                    unchanged += 1
        self.db.commit()
        return added, updated, unchanged

    def list_sources(self) -> List[Source]:
        return self.db.query(Source).all()

    def get(self, id: str) -> Source:
        return self.db.query(Source).filter(Source.id == id).first()


class ItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_conversation(self, conv: Conversation) -> Conversation:
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def save_comment(self, comment: Comment) -> Comment:
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment
        
    def save_raw_payload(self, payload: RawPayload) -> RawPayload:
        self.db.add(payload)
        self.db.commit()
        self.db.refresh(payload)
        return payload

class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_analysis(self, analysis: ItemAnalysis) -> ItemAnalysis:
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def save_embedding(self, embedding: Embedding) -> Embedding:
        self.db.add(embedding)
        self.db.commit()
        self.db.refresh(embedding)
        return embedding

class InsightRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_topic(self, topic: Topic) -> Topic:
        self.db.add(topic)
        self.db.commit()
        self.db.refresh(topic)
        return topic

    def save_pain_point(self, pain_point: PainPoint) -> PainPoint:
        self.db.add(pain_point)
        self.db.commit()
        self.db.refresh(pain_point)
        return pain_point
