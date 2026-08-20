import os
import csv
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from audience_radar.adapters.base import BaseAdapter
from audience_radar.storage.models import SearchSignal, RawPayload

class AppleAdsAdapter(BaseAdapter):
    """Tier 2 Adapter for Apple Ads (Search Demand) using CSV Import."""
    
    def collect(self) -> List[RawPayload]:
        csv_path = self.config.options.get("csv_path")
        if not csv_path or not os.path.exists(csv_path):
            self.handle_error(Exception(f"CSV file not found at {csv_path}"))
            return []

        raw_payloads = []
        try:
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            raw_payloads.append(RawPayload(
                id=uuid.uuid4().hex[:8],
                collection_job_id="job_id",
                platform_item_id=f"csv_{int(datetime.utcnow().timestamp())}",
                payload_gz=json.dumps({"type": "csv", "data": rows}).encode('utf-8'),
                payload_hash=str(hash(str(rows))),
                fetched_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30)
            ))
            return raw_payloads
            
        except Exception as e:
            self.handle_error(e)
            return raw_payloads

    def normalize(self, raw_data: List[RawPayload]) -> List[SearchSignal]:
        signals = []
        
        for payload in raw_data:
            content = json.loads(payload.payload_gz.decode('utf-8'))
            data_type = content.get("type")
            rows = content.get("data", [])
            
            if data_type == "csv":
                for row in rows:
                    keyword = row.get("keyword")
                    country = row.get("country", "US")
                    popularity_score = row.get("popularity_score")
                    pulled_at = row.get("pulled_at")
                    
                    try:
                        popularity_score = int(popularity_score) if popularity_score else 0
                    except ValueError:
                        popularity_score = 0
                        
                    try:
                        date_val = datetime.fromisoformat(pulled_at) if pulled_at else datetime.utcnow()
                    except ValueError:
                        date_val = datetime.utcnow()

                    signals.append(SearchSignal(
                        id=uuid.uuid4().hex[:8],
                        audience_id=self.db_source.audience_id,
                        source_id=self.config.id,
                        keyword=keyword,
                        keyword_type="user_search_term",
                        country=country,
                        date=date_val,
                        search_popularity=popularity_score,
                        confidence=0.8
                    ))
                    
        return signals

    def validate(self, normalized_data: List[SearchSignal]) -> List[SearchSignal]:
        # Validate that required fields exist
        return [s for s in normalized_data if s.keyword and s.search_popularity is not None]
        
    def deduplicate(self, validated_data: List[SearchSignal]) -> List[SearchSignal]:
        seen = set()
        unique = []
        for s in validated_data:
            # Deduplicate by keyword, country, and date
            key = f"{s.keyword}_{s.country}_{s.date.strftime('%Y-%m-%d')}"
            if key not in seen:
                seen.add(key)
                unique.append(s)
        return unique
