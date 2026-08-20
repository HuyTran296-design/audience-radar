import urllib.request
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from dateutil.parser import parse
from audience_radar.adapters.base import BaseAdapter
from audience_radar.storage.models import Review, RawPayload

class AppStoreAdapter(BaseAdapter):
    """
    Tier 1 Adapter for Apple App Store Reviews.
    Uses the official iTunes RSS feed for customer reviews.
    """
    
    def collect(self) -> List[RawPayload]:
        # Options from config
        app_id = self.config.options.get("app_id")
        country = self.config.options.get("country", "us")
        if not app_id:
            raise ValueError("AppStoreAdapter requires an 'app_id' in options")
            
        url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'AudienceRadar/1.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
            # Create a single payload object for this fetch
            payload = RawPayload(
                id=uuid.uuid4().hex[:8],
                collection_job_id="dummy_job_id", # Should be injected by orchestration
                platform_item_id=f"{app_id}_{datetime.utcnow().timestamp()}",
                payload_gz=json.dumps(data).encode('utf-8'), # Normally gzipped
                payload_hash=str(hash(str(data))),
                fetched_at=datetime.utcnow(),
                expires_at=datetime.utcnow() # Configured properly in prod
            )
            return [payload]
        except Exception as e:
            self.handle_error(e)
            return []

    def normalize(self, raw_data: List[RawPayload]) -> List[Review]:
        reviews = []
        app_id = self.config.options.get("app_id")
        country = self.config.options.get("country", "us")
        
        for payload in raw_data:
            data = json.loads(payload.payload_gz.decode('utf-8'))
            feed = data.get("feed", {})
            entries = feed.get("entry", [])
            
            # The first entry is usually the app itself, reviews follow
            for entry in entries:
                if "author" not in entry:
                    continue
                    
                review_id = entry.get("id", {}).get("label")
                if not review_id:
                    continue
                    
                title = entry.get("title", {}).get("label")
                content = entry.get("content", {}).get("label")
                rating = int(entry.get("im:rating", {}).get("label", 0))
                version = entry.get("im:version", {}).get("label")
                
                # Apple RSS doesn't give precise timestamps in all regions, we fallback
                # For this MVP architecture we just set UTC now if missing
                posted_at = datetime.utcnow()
                
                reviews.append(Review(
                    id=uuid.uuid4().hex[:8],
                    audience_id=self.db_source.audience_id,
                    source_id=self.config.id,
                    platform="app_store",
                    app_id=str(app_id),
                    platform_item_id=str(review_id),
                    rating=rating,
                    title=title,
                    text=content,
                    app_version=version,
                    country=country,
                    posted_at=posted_at,
                    collected_at=datetime.utcnow()
                ))
        return reviews

    def validate(self, normalized_data: List[Review]) -> List[Review]:
        # Filter out empty text or zero ratings
        return [r for r in normalized_data if r.text and r.rating > 0]
        
    def deduplicate(self, validated_data: List[Review]) -> List[Review]:
        # Deduplication based on platform_item_id
        seen = set()
        unique = []
        for r in validated_data:
            if r.platform_item_id not in seen:
                seen.add(r.platform_item_id)
                unique.append(r)
        return unique
