import uuid
from datetime import datetime, timezone
from audience_radar.storage.db import SessionLocal, engine
from audience_radar.storage.models import Base, Topic, PainPoint, Question, Objection, AudiencePhrase

# Create tables
import sqlalchemy
@sqlalchemy.event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

Base.metadata.create_all(engine)
db = SessionLocal()

# Seed Topics
aud_id = "aud_meditation"

topics = [
    Topic(id="t1", audience_id=aud_id, slug="t1", status="analyzed", confidence=0.9, label="Mindfulness Bells & Chimes", description="Discussions about the effectiveness and types of mindfulness bells.", item_count=150),
    Topic(id="t2", audience_id=aud_id, slug="t2", status="analyzed", confidence=0.85, label="Morning Meditation Habits", description="Struggles and routines around morning meditation.", item_count=85)
]

for t in topics:
    if not db.query(Topic).filter_by(id=t.id).first():
        db.add(t)
db.commit()

# Seed Pain Points
pains = [
    PainPoint(id="p1", audience_id=aud_id, slug="p1", status="analyzed", confidence=0.8, topic_id="t1", title="Bells are too startling", severity_score=80, frequency=45),
    PainPoint(id="p2", audience_id=aud_id, slug="p2", status="analyzed", confidence=0.75, topic_id="t2", title="Falling back asleep during morning meditation", severity_score=90, frequency=60)
]
for p in pains:
    if not db.query(PainPoint).filter_by(id=p.id).first():
        db.add(p)

# Seed Questions
questions = [
    Question(id="q1", audience_id=aud_id, slug="q1", status="analyzed", confidence=0.9, question="How often should my mindfulness bell chime?", urgency_score=70, intent="informational"),
    Question(id="q2", audience_id=aud_id, slug="q2", status="analyzed", confidence=0.8, question="Best sounding meditation bells under $50?", urgency_score=85, intent="purchase_intent")
]
for q in questions:
    if not db.query(Question).filter_by(id=q.id).first():
        db.add(q)

# Seed Objections
objections = [
    Objection(id="o1", audience_id=aud_id, slug="o1", status="analyzed", confidence=0.85, objection="Digital bells feel artificial and distracting.", objection_type="quality", stated_concern="It takes me out of the moment instead of grounding me."),
    Objection(id="o2", audience_id=aud_id, slug="o2", status="analyzed", confidence=0.75, objection="I don't have 20 minutes in the morning.", objection_type="time", stated_concern="Too busy to meditate before work.")
]
for o in objections:
    if not db.query(Objection).filter_by(id=o.id).first():
        db.add(o)

# Seed Phrases (AudienceLanguage)
phrases = [
    AudiencePhrase(id="ap1", audience_id=aud_id, slug="ap1", status="analyzed", confidence=0.95, exact_text="jarring digital ding", exact_context="I hate that jarring digital ding on my phone app.", occurrences=25, distinct_authors=18, category="complaint"),
    AudiencePhrase(id="ap2", audience_id=aud_id, slug="ap2", status="analyzed", confidence=0.88, exact_text="gentle grounding anchor", exact_context="The bell acts as a gentle grounding anchor when my mind wanders.", occurrences=40, distinct_authors=32, category="desired_outcome")
]
for ph in phrases:
    if not db.query(AudiencePhrase).filter_by(id=ph.id).first():
        db.add(ph)

db.commit()
db.close()
print("Seeding complete.")
