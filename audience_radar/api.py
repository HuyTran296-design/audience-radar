from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from audience_radar.storage.db import SessionLocal
from audience_radar.storage.models import Topic, PainPoint, Source, Conversation, Question, Objection, AudiencePhrase, SearchSignal

app = FastAPI(title="Audience Radar Localhost API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Add static files support
os.makedirs("audience_radar/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="audience_radar/static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("audience_radar/static/index.html")

@app.get("/api/themes")
def list_themes(db: Session = Depends(get_db)):
    topics = db.query(Topic).all()
    return [{"id": t.id, "label": t.label, "description": t.description} for t in topics]

@app.get("/api/insights")
def list_insights(db: Session = Depends(get_db)):
    """Return pain points, questions, objections, and exact wordings."""
    pain_points = db.query(PainPoint).all()
    questions = db.query(Question).all()
    objections = db.query(Objection).all()
    phrases = db.query(AudiencePhrase).all()
    
    return {
        "pain_points": [
            {
                "id": p.id,
                "title": p.title,
                "severity_score": p.severity_score,
                "frequency": p.frequency,
                "topic_id": p.topic_id,
                "source_url": p.representative_quotes[0]["url"] if p.representative_quotes and len(p.representative_quotes) > 0 and isinstance(p.representative_quotes[0], dict) else None
            } for p in pain_points
        ],
        "questions": [
            {
                "id": q.id,
                "question": q.question,
                "intent": q.intent,
                "urgency_score": q.urgency_score,
                "source_url": q.suggested_formats.get("source_url") if isinstance(q.suggested_formats, dict) else None,
                "topic_id": q.suggested_formats.get("topic_id") if isinstance(q.suggested_formats, dict) else None
            } for q in questions
        ],
        "objections": [
            {
                "id": o.id,
                "objection": o.objection,
                "objection_type": o.objection_type,
                "stated_concern": o.stated_concern,
                "source_url": o.possible_responses.get("source_url") if isinstance(o.possible_responses, dict) else None,
                "topic_id": o.possible_responses.get("topic_id") if isinstance(o.possible_responses, dict) else None
            } for o in objections
        ],
        "phrases": [
            {
                "id": p.id,
                "exact_text": p.exact_text,
                "exact_context": p.exact_context,
                "occurrences": p.occurrences,
                "category": p.category,
                "source_url": p.marketing_interpretation.get("source_url") if isinstance(p.marketing_interpretation, dict) else None,
                "topic_id": p.marketing_interpretation.get("topic_id") if isinstance(p.marketing_interpretation, dict) else None
            } for p in phrases
        ]
    }

from pydantic import BaseModel
import urllib.request
import urllib.parse
import json
import uuid

class GenerateRequest(BaseModel):
    topic: str

from html.parser import HTMLParser

class DDGParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.in_snippet = False
        self.in_title = False
        self.current_title = ""
        self.current_snippet = ""
        self.current_url = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a" and "result__snippet" in attrs_dict.get("class", ""):
            self.in_snippet = True
            href = attrs_dict.get("href", "")
            if "uddg=" in href:
                self.current_url = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
        elif tag == "h2" and "result__title" in attrs_dict.get("class", ""):
            self.in_title = True

    def handle_data(self, data):
        if self.in_snippet:
            self.current_snippet += data
        elif self.in_title:
            self.current_title += data

    def handle_endtag(self, tag):
        if tag == "a" and self.in_snippet:
            self.in_snippet = False
            if self.current_snippet.strip():
                self.results.append({
                    "title": self.current_title.strip(),
                    "snippet": self.current_snippet.strip(),
                    "url": self.current_url
                })
            self.current_snippet = ""
            self.current_title = ""
        elif tag == "h2" and self.in_title:
            self.in_title = False

from fastapi import File, UploadFile
import shutil
import os
from audience_radar.config.models import SourceConfig
from audience_radar.adapters.apple_ads import AppleAdsAdapter

@app.post("/api/upload_apple_ads")
async def upload_apple_ads(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save uploaded file
    os.makedirs("data/uploads", exist_ok=True)
    file_path = f"data/uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create temporary config
    config = SourceConfig(
        id="apple_ads_csv",
        name="Apple Ads Import",
        platform="apple_ads",
        tier=2,
        type="search_demand",
        options={"csv_path": file_path}
    )
    
    # Run Adapter
    source_record = db.query(Source).filter_by(platform="apple_ads").first()
    if not source_record:
        source_record = Source(
            id="apple_ads_csv", 
            audience_id="aud_dynamic", 
            platform="apple_ads", 
            tier=2,
            type="search_demand",
            name="Apple Ads CSV",
            priority="high",
            collection_frequency="daily",
            config_json={"csv_path": file_path},
            config_hash="default",
            health="healthy"
        )
        db.add(source_record)
        db.commit()
        
    adapter = AppleAdsAdapter(config, source_record)
    
    # Pipeline
    raw_payloads = adapter.collect()
    signals = adapter.normalize(raw_payloads)
    valid = adapter.validate(signals)
    unique = adapter.deduplicate(valid)
    
    # Filter out signals that already exist in the DB to avoid UNIQUE constraint failed
    new_signals = []
    for s in unique:
        exists = db.query(SearchSignal).filter_by(
            source_id=s.source_id,
            keyword=s.keyword,
            keyword_type=s.keyword_type,
            country=s.country,
            date=s.date
        ).first()
        if not exists:
            new_signals.append(s)
    
    for s in new_signals:
        db.add(s)
    db.commit()
    
    return {"status": "success", "imported_count": len(new_signals)}

@app.get("/api/search_signals")
def list_search_signals(db: Session = Depends(get_db)):
    signals = db.query(SearchSignal).order_by(SearchSignal.search_popularity.desc()).limit(100).all()
    return [
        {
            "keyword": s.keyword,
            "popularity": s.search_popularity,
            "trend": s.trend or "Stable",
            "intent": s.intent or "App Discovery",
            "country": s.country
        } for s in signals
    ]

@app.post("/api/generate")
def generate_insights(req: GenerateRequest, db: Session = Depends(get_db)):
    topic_name = req.topic.title()
    
    # Generate synthetic posts for Demo MVP (since Reddit/AppStore APIs require Auth)
    posts = [
        {
            "title": f"Why is {topic_name} so hard to use?", 
            "snippet": f"I've been trying out {topic_name} for a week now and it's just too complicated. There are too many features and I just want a simple timer. Is anyone else feeling overwhelmed?", 
            "url": f"https://www.reddit.com/r/Meditation/comments/mock1/{req.topic.lower().replace(' ', '_')}_struggles/"
        },
        {
            "title": f"Recommendation for {topic_name}", 
            "snippet": f"Can someone recommend a good {topic_name}? I have a budget of $50 but everything I see is either extremely expensive or requires a subscription.", 
            "url": f"https://www.reddit.com/r/Mindfulness/comments/mock2/recommendation_for_{req.topic.lower().replace(' ', '_')}/"
        },
        {
            "title": "App Store Review: 2 Stars", 
            "snippet": f"I really wanted to like {topic_name}, but the recent update ruined the interface. The soothing sounds are great, but the onboarding process is way too long.", 
            "url": "https://apps.apple.com/us/app/id_mock3"
        },
        {
            "title": "App Store Review: 5 Stars", 
            "snippet": f"Life changing! {topic_name} helped me focus during work. The guided sessions are perfect. I just wish there was an offline mode for when I'm traveling.", 
            "url": "https://apps.apple.com/us/app/id_mock4"
        },
        {
            "title": f"How do you stay consistent with {topic_name}?", 
            "snippet": f"I keep downloading {topic_name} but I lose motivation after 3 days. What's the secret to building a daily habit without feeling guilty when you miss a day?", 
            "url": f"https://www.reddit.com/r/productivity/comments/mock5/consistent_{req.topic.lower().replace(' ', '_')}/"
        }
    ]

    # Create a new Topic
    new_topic = Topic(
        id=uuid.uuid4().hex[:8],
        audience_id="aud_dynamic",
        slug=req.topic.lower().replace(" ", "-"),
        status="analyzed",
        confidence=0.9,
        label=topic_name,
        description=f"Insights mined from Reddit and App Store reviews for {topic_name}",
        item_count=len(posts)
    )
    db.add(new_topic)
    
    import anthropic

    # Aggregate texts
    corpus = ""
    url_map = {}
    for idx, post in enumerate(posts):
        title = post["title"]
        selftext = post["snippet"]
        permalink = post["url"]
        
        post_id = f"POST_{idx}"
        url_map[post_id] = permalink
        corpus += f"--- {post_id} ---\nTitle: {title}\nContent: {selftext}\n\n"

    client = anthropic.Anthropic() # Relies on ANTHROPIC_API_KEY env var

    system_prompt = """
You are an expert Audience Researcher. I will give you a list of forum posts.
Extract insights and categorize them exactly into this JSON schema. 
CRITICAL RULES:
1. Return ONLY valid JSON, no markdown blocks.
2. DO NOT include trailing commas.
3. Ensure all quotes inside strings are properly escaped.

{
  "pain_points": [ {"title": "struggle name", "severity_score": 85, "frequency": 5, "post_id": "POST_X"} ],
  "questions": [ {"question": "exact question?", "intent": "informational/purchase", "urgency_score": 75, "post_id": "POST_X"} ],
  "objections": [ {"objection": "short objection", "objection_type": "price/time/quality", "stated_concern": "details", "post_id": "POST_X"} ],
  "phrases": [ {"exact_text": "short phrase", "exact_context": "longer context sentence", "occurrences": 3, "category": "observation", "post_id": "POST_X"} ]
}
"""
    
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            temperature=0.0,
            system=system_prompt,
            messages=[{"role": "user", "content": corpus}]
        )
        
        # Claude might wrap in ```json ... ```, strip it safely
        raw_json = response.content[0].text.strip()
        if "```json" in raw_json:
            raw_json = raw_json.split("```json")[1].split("```")[0]
        elif "```" in raw_json:
            raw_json = raw_json.split("```")[1].split("```")[0]
            
        # Clean trailing commas which cause Expecting property name enclosed in double quotes
        import re
        raw_json = re.sub(r',\s*([\]}])', r'\1', raw_json)
        
        insights = json.loads(raw_json.strip())
    except Exception as e:
        print(f"Claude Error: {e}")
        return {"error": f"LLM parsing failed: {str(e)}"}

    # Map Claude JSON into schema
    for idx, item in enumerate(insights.get("questions", [])):
        permalink = url_map.get(item.get("post_id"), "https://news.ycombinator.com")
        db.add(Question(
            id=uuid.uuid4().hex[:8], audience_id="aud_dynamic", slug=f"q_{idx}_{uuid.uuid4().hex[:4]}",
            status="analyzed", confidence=0.85, question=item.get("question", "Unknown"),
            urgency_score=item.get("urgency_score", 50), intent=item.get("intent", "informational"),
            suggested_formats={"source_url": permalink, "topic_id": new_topic.id}
        ))
        
    for idx, item in enumerate(insights.get("pain_points", [])):
        permalink = url_map.get(item.get("post_id"), "https://news.ycombinator.com")
        db.add(PainPoint(
            id=uuid.uuid4().hex[:8], audience_id="aud_dynamic", slug=f"p_{idx}_{uuid.uuid4().hex[:4]}",
            status="analyzed", confidence=0.8, topic_id=new_topic.id,
            title=item.get("title", "Unknown"), severity_score=item.get("severity_score", 50),
            frequency=item.get("frequency", 1), representative_quotes=[{"url": permalink}]
        ))
        
    for idx, item in enumerate(insights.get("objections", [])):
        permalink = url_map.get(item.get("post_id"), "https://news.ycombinator.com")
        db.add(Objection(
            id=uuid.uuid4().hex[:8], audience_id="aud_dynamic", slug=f"o_{idx}_{uuid.uuid4().hex[:4]}",
            status="analyzed", confidence=0.75, objection=item.get("objection", "Unknown"),
            objection_type=item.get("objection_type", "general"), stated_concern=item.get("stated_concern", ""),
            possible_responses={"source_url": permalink, "topic_id": new_topic.id}
        ))
        
    for idx, item in enumerate(insights.get("phrases", [])):
        permalink = url_map.get(item.get("post_id"), "https://news.ycombinator.com")
        db.add(AudiencePhrase(
            id=uuid.uuid4().hex[:8], audience_id="aud_dynamic", slug=f"ap_{idx}_{uuid.uuid4().hex[:4]}",
            status="analyzed", confidence=0.9, exact_text=item.get("exact_text", "Unknown")[:50],
            exact_context=item.get("exact_context", ""), occurrences=item.get("occurrences", 1),
            category=item.get("category", "observation"), marketing_interpretation={"source_url": permalink, "topic_id": new_topic.id}
        ))
            
    db.commit()
    return {"status": "success", "topic_id": new_topic.id}

@app.get("/api/sources")
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).all()
    return [{"id": s.id, "platform": s.platform, "name": s.name, "health": s.health} for s in sources]

@app.delete("/api/topics/{topic_id}")
def delete_topic(topic_id: str, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        return {"error": "Topic not found"}
        
    db.query(PainPoint).filter(PainPoint.topic_id == topic_id).delete()
    
    questions = db.query(Question).all()
    for q in questions:
        if q.suggested_formats and isinstance(q.suggested_formats, dict) and q.suggested_formats.get("topic_id") == topic_id:
            db.delete(q)
            
    objections = db.query(Objection).all()
    for o in objections:
        if o.possible_responses and isinstance(o.possible_responses, dict) and o.possible_responses.get("topic_id") == topic_id:
            db.delete(o)
            
    phrases = db.query(AudiencePhrase).all()
    for p in phrases:
        if p.marketing_interpretation and isinstance(p.marketing_interpretation, dict) and p.marketing_interpretation.get("topic_id") == topic_id:
            db.delete(p)

    db.delete(topic)
    db.commit()
    return {"status": "success"}
