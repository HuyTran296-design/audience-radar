from sqlalchemy.orm import Session
from datetime import datetime, timezone
import structlog
import uuid
import json

from audience_radar.storage.models import Source, CollectionJob, RawPayload
from audience_radar.storage.repositories import SourceRepository, ItemRepository
from audience_radar.adapters.reddit import RedditAdapter
from audience_radar.adapters.base import AdapterException
from audience_radar.config.models import SourceConfig

logger = structlog.get_logger(__name__)

class CollectionRunner:
    def __init__(self, db: Session):
        self.db = db
        self.item_repo = ItemRepository(db)

    def run_source(self, source: Source, trigger: str = "manual") -> CollectionJob:
        logger.info("collection_starting", source_id=source.id, platform=source.platform)
        
        job_id = uuid.uuid4().hex
        started_at = datetime.now(timezone.utc)
        
        job = CollectionJob(
            id=job_id,
            source_id=source.id,
            started_at=started_at,
            status="running",
            trigger=trigger,
            cursor_before=source.last_cursor,
            items_fetched=0,
            items_new=0,
            items_duplicate=0,
            items_rejected=0,
            api_calls=0,
            quota_units_used=0
        )
        self.db.add(job)
        self.db.commit()

        try:
            config = SourceConfig(**source.config_json)
            
            if source.platform == "reddit":
                # In production, tokens come from secure config/vault
                adapter = RedditAdapter(config, auth_token="mock")
            else:
                raise AdapterException("unsupported_platform", f"No adapter for {source.platform}")

            max_items = config.max_items_per_run or 100
            current_cursor = source.last_cursor
            total_fetched = 0
            
            while total_fetched < max_items:
                fetch_amount = max_items - total_fetched
                result = adapter.fetch(cursor=current_cursor, max_items=fetch_amount)
                
                job.api_calls += result.api_calls_made
                job.quota_units_used += result.quota_units_used
                
                for item in result.items:
                    payload = RawPayload(
                        id=uuid.uuid4().hex,
                        collection_job_id=job.id,
                        platform_item_id=item.platform_item_id,
                        payload_gz=json.dumps(item.raw_data).encode("utf-8"), # normally gzip
                        payload_hash=item.platform_item_id, # Simplified hash for now
                        fetched_at=item.fetched_at,
                        expires_at=item.expires_at
                    )
                    try:
                        self.item_repo.save_raw_payload(payload)
                        job.items_new += 1
                        total_fetched += 1
                    except Exception as e:
                        # Idempotency constraint or DB error
                        self.db.rollback()
                        job.items_duplicate += 1
                        
                job.items_fetched = total_fetched
                current_cursor = result.next_cursor
                
                if not current_cursor or len(result.items) == 0:
                    break
                    
            job.status = "success"
            job.cursor_after = current_cursor
            
            # Update source
            source.last_run_at = datetime.now(timezone.utc)
            source.last_success_at = datetime.now(timezone.utc)
            source.last_cursor = current_cursor
            source.consecutive_failures = 0
            
            self.db.commit()
            logger.info("collection_success", job_id=job.id, fetched=job.items_fetched)
            return job
            
        except AdapterException as e:
            self.db.rollback()
            job.status = "error"
            job.error_class = e.error_class
            job.error_detail = e.detail
            
            # Record failure on source
            source.last_run_at = datetime.now(timezone.utc)
            source.consecutive_failures += 1
            if source.consecutive_failures >= 3:
                source.health = "failing"
                
            self.db.commit()
            logger.error("collection_adapter_error", job_id=job.id, error=e.error_class)
            return job
        except Exception as e:
            self.db.rollback()
            job.status = "error"
            job.error_class = "internal_error"
            job.error_detail = str(e)
            source.consecutive_failures += 1
            self.db.commit()
            logger.error("collection_internal_error", job_id=job.id, error=str(e))
            return job
        finally:
            job.finished_at = datetime.now(timezone.utc)
            self.db.commit()
