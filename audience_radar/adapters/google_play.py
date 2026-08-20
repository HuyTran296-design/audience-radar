import uuid
import json
from datetime import datetime
from typing import List, Dict, Any
from audience_radar.adapters.base import BaseAdapter
from audience_radar.storage.models import Review, RawPayload

class GooglePlayAdapter(BaseAdapter):
    """
    Tier 1 Adapter for Google Play Reviews.
    Designed to use the official Google Play Developer API:
    https://developers.google.com/android-publisher/reply-to-reviews
    """
    
    def collect(self) -> List[RawPayload]:
        # Google Play Developer API requires OAuth
        package_name = self.config.options.get("package_name")
        if not package_name:
            raise ValueError("GooglePlayAdapter requires 'package_name' in options")
            
        # In a real implementation, this would use google-api-python-client
        # to call androidpublisher_v3.reviews().list(packageName=package_name)
        # Here we mock the architecture flow as requested.
        
        # Mock payload
        mock_data = {
            "reviews": []
        }
        
        payload = RawPayload(
            id=uuid.uuid4().hex[:8],
            collection_job_id="dummy_job_id",
            platform_item_id=f"{package_name}_{datetime.utcnow().timestamp()}",
            payload_gz=json.dumps(mock_data).encode('utf-8'),
            payload_hash=str(hash(str(mock_data))),
            fetched_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )
        return [payload]

    def normalize(self, raw_data: List[RawPayload]) -> List[Review]:
        reviews = []
        package_name = self.config.options.get("package_name")
        
        for payload in raw_data:
            data = json.loads(payload.payload_gz.decode('utf-8'))
            api_reviews = data.get("reviews", [])
            
            for item in api_reviews:
                review_id = item.get("reviewId")
                author_name = item.get("authorName")
                comments = item.get("comments", [])
                
                if not comments:
                    continue
                    
                user_comment = comments[0].get("userComment", {})
                developer_comment = None
                if len(comments) > 1:
                    developer_comment = comments[1].get("developerComment", {}).get("text")
                    
                text = user_comment.get("text", "")
                rating = user_comment.get("starRating", 0)
                app_version = user_comment.get("appVersionName", "")
                
                # Google Play API returns seconds and nanos
                last_modified_seconds = user_comment.get("lastModified", {}).get("seconds", 0)
                posted_at = datetime.fromtimestamp(int(last_modified_seconds)) if last_modified_seconds else datetime.utcnow()
                
                reviews.append(Review(
                    id=uuid.uuid4().hex[:8],
                    audience_id=self.db_source.audience_id,
                    source_id=self.config.id,
                    platform="google_play",
                    app_id=str(package_name),
                    platform_item_id=str(review_id),
                    rating=rating,
                    title=None, # Google Play doesn't have review titles
                    text=text,
                    app_version=app_version,
                    posted_at=posted_at,
                    collected_at=datetime.utcnow(),
                    developer_response=developer_comment
                ))
        return reviews

    def validate(self, normalized_data: List[Review]) -> List[Review]:
        return [r for r in normalized_data if r.text and r.rating > 0]
        
    def deduplicate(self, validated_data: List[Review]) -> List[Review]:
        seen = set()
        unique = []
        for r in validated_data:
            if r.platform_item_id not in seen:
                seen.add(r.platform_item_id)
                unique.append(r)
        return unique
