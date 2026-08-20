from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime, LargeBinary, ForeignKey, func, text, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Source(Base):
    __tablename__ = "source"
    id = Column(String, primary_key=True)
    audience_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    tier = Column(Integer, nullable=False, default=4)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String)
    query = Column(String)
    enabled = Column(Boolean, nullable=False, default=True)
    priority = Column(String, nullable=False)
    collection_frequency = Column(String, nullable=False)
    config_json = Column(JSON, nullable=False)
    config_hash = Column(String, nullable=False)
    last_run_at = Column(DateTime(timezone=True))
    last_success_at = Column(DateTime(timezone=True))
    last_cursor = Column(String)
    consecutive_failures = Column(Integer, nullable=False, default=0)
    health = Column(String, nullable=False)
    items_collected_total = Column(Integer, nullable=False, default=0)
    relevant_rate_30d = Column(Float)
    trusted_insights_attributed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_source_audience_id_enabled_frequency", "audience_id", "enabled", "collection_frequency"),
        Index("ix_source_health", "health"),
    )

class CollectionJob(Base):
    __tablename__ = "collection_job"
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("source.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True))
    status = Column(String, nullable=False)
    trigger = Column(String, nullable=False)
    cursor_before = Column(String)
    cursor_after = Column(String)
    items_fetched = Column(Integer, nullable=False, default=0)
    items_new = Column(Integer, nullable=False, default=0)
    items_duplicate = Column(Integer, nullable=False, default=0)
    items_rejected = Column(Integer, nullable=False, default=0)
    api_calls = Column(Integer, nullable=False, default=0)
    quota_units_used = Column(Integer, nullable=False, default=0)
    error_class = Column(String)
    error_detail = Column(String)
    window_start = Column(DateTime(timezone=True))
    window_end = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_collection_job_source_started", "source_id", "started_at"),
        Index("ix_collection_job_status_started", "status", "started_at"),
    )

class RawPayload(Base):
    __tablename__ = "raw_payload"
    id = Column(String, primary_key=True)
    collection_job_id = Column(String, ForeignKey("collection_job.id"), nullable=False)
    platform_item_id = Column(String, nullable=False)
    payload_gz = Column(LargeBinary, nullable=False)
    payload_hash = Column(String, nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("collection_job_id", "platform_item_id", name="uq_raw_payload_job_item"),
        Index("ix_raw_payload_expires_at", "expires_at"),
    )

class Author(Base):
    __tablename__ = "author"
    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)
    author_hash = Column(String, nullable=False)
    platform_author_id = Column(String)
    display_handle = Column(String)
    first_seen_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)
    item_count = Column(Integer, nullable=False, default=0)
    is_likely_bot = Column(Boolean, nullable=False, default=False)
    is_creator = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("platform", "author_hash", name="uq_author_platform_hash"),
        Index("ix_author_hash", "author_hash"),
    )

class Conversation(Base):
    __tablename__ = "conversation"
    id = Column(String, primary_key=True)
    audience_id = Column(String, nullable=False)
    source_id = Column(String, ForeignKey("source.id"), nullable=False)
    raw_payload_id = Column(String, ForeignKey("raw_payload.id"), nullable=False)
    platform = Column(String, nullable=False)
    platform_item_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    title = Column(String)
    body = Column(String)
    body_hash = Column(String, nullable=False)
    simhash = Column(Integer, nullable=False)
    author_id = Column(String, ForeignKey("author.id"))
    posted_at = Column(DateTime(timezone=True), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    language = Column(String)
    detected_language = Column(String)
    engagement = Column(JSON)
    comment_count = Column(Integer, nullable=False, default=0)
    is_duplicate_of = Column(String, ForeignKey("conversation.id"))
    word_count = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("source_id", "platform_item_id", name="uq_conversation_source_item"),
        Index("ix_conversation_audience_posted", "audience_id", "posted_at"),
        Index("ix_conversation_body_hash", "body_hash"),
        Index("ix_conversation_simhash", "simhash"),
        Index("ix_conversation_is_duplicate", "is_duplicate_of"),
    )

class Comment(Base):
    __tablename__ = "comment"
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversation.id"), nullable=False)
    parent_comment_id = Column(String, ForeignKey("comment.id"))
    depth = Column(Integer, nullable=False)
    body = Column(String, nullable=False)
    body_hash = Column(String, nullable=False)
    simhash = Column(Integer, nullable=False)
    author_id = Column(String, ForeignKey("author.id"))
    posted_at = Column(DateTime(timezone=True), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    engagement = Column(JSON)
    is_author_reply = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("conversation_id", "id", name="uq_comment_conv_item"),
        Index("ix_comment_conversation_posted", "conversation_id", "posted_at"),
    )

class Content(Base):
    __tablename__ = "content"
    id = Column(String, primary_key=True)
    origin_type = Column(String, nullable=False)
    origin_id = Column(String, nullable=False)
    audience_id = Column(String, nullable=False)
    text = Column(String, nullable=False)
    text_hash = Column(String, nullable=False)
    posted_at = Column(DateTime(timezone=True), nullable=False)
    platform = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    author_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("origin_type", "origin_id", name="uq_content_origin"),
        Index("ix_content_audience_posted", "audience_id", "posted_at"),
        Index("ix_content_text_hash", "text_hash"),
        Index("ix_content_author_hash", "author_hash"),
    )

class Review(Base):
    __tablename__ = "review"
    id = Column(String, primary_key=True)
    audience_id = Column(String, nullable=False)
    source_id = Column(String, ForeignKey("source.id"), nullable=False)
    platform = Column(String, nullable=False)
    app_id = Column(String, nullable=False)
    platform_item_id = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    title = Column(String)
    text = Column(String, nullable=False)
    app_version = Column(String)
    country = Column(String)
    language = Column(String)
    author_id = Column(String, ForeignKey("author.id"))
    posted_at = Column(DateTime(timezone=True), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    developer_response = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("platform", "platform_item_id", name="uq_review_platform_item"),
        Index("ix_review_app_posted", "app_id", "posted_at"),
    )

class Video(Base):
    __tablename__ = "video"
    id = Column(String, primary_key=True)
    audience_id = Column(String, nullable=False)
    source_id = Column(String, ForeignKey("source.id"), nullable=False)
    platform = Column(String, nullable=False, default="youtube")
    platform_video_id = Column(String, nullable=False)
    channel_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    url = Column(String, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    views = Column(Integer)
    likes = Column(Integer)
    comments_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("platform", "platform_video_id", name="uq_video_platform_id"),
    )

class SearchSignal(Base):
    __tablename__ = "search_signal"
    id = Column(String, primary_key=True)
    audience_id = Column(String, nullable=False)
    source_id = Column(String, ForeignKey("source.id"), nullable=False)
    keyword = Column(String, nullable=False)
    keyword_type = Column(String, nullable=False)
    normalized_keyword = Column(String)
    topic_id = Column(String)
    intent = Column(String)
    country = Column(String)
    language = Column(String)
    date = Column(DateTime(timezone=True), nullable=False)
    search_popularity = Column(Integer)
    impressions = Column(Integer)
    taps = Column(Integer)
    conversions = Column(Integer)
    spend = Column(Float)
    trend = Column(String)
    growth_rate = Column(Float)
    confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("source_id", "keyword", "keyword_type", "country", "date", name="uq_search_signal"),
        Index("ix_search_signal_date", "date"),
    )

class Signal(Base):
    __tablename__ = "signal"
    id = Column(String, primary_key=True)
    audience_id = Column(String, nullable=False)
    signal_type = Column(String, nullable=False)
    content = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    evidence_count = Column(Integer, nullable=False, default=1)
    sources = Column(JSON, nullable=False)
    cross_source_validation = Column(String)
    metadata_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ItemAnalysis(Base):
    __tablename__ = "item_analysis"
    id = Column(String, primary_key=True)
    content_id = Column(String, ForeignKey("content.id"), nullable=False)
    prompt_version = Column(String, nullable=False)
    model = Column(String, nullable=False)
    model_tier = Column(String, nullable=False)
    relevance_score = Column(Integer, nullable=False)
    relevance_stage = Column(String, nullable=False)
    relevance_reason = Column(String)
    is_relevant = Column(Boolean, nullable=False)
    intent = Column(String)
    intent_confidence = Column(Float)
    segments = Column(JSON)
    extracted = Column(JSON)
    is_rhetorical = Column(Boolean, nullable=False, default=False)
    is_creator_content = Column(Boolean, nullable=False, default=False)
    is_spam = Column(Boolean, nullable=False, default=False)
    tokens_in = Column(Integer, nullable=False, default=0)
    tokens_out = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    analyzed_at = Column(DateTime(timezone=True), nullable=False)
    error = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("content_id", "prompt_version", name="uq_item_analysis_content_prompt"),
        Index("ix_item_analysis_is_relevant_analyzed", "is_relevant", "analyzed_at"),
        Index("ix_item_analysis_relevance_score", "relevance_score"),
    )

class Embedding(Base):
    __tablename__ = "embedding"
    id = Column(String, primary_key=True)
    content_id = Column(String, ForeignKey("content.id"))
    owner_type = Column(String, nullable=False)
    owner_id = Column(String, nullable=False)
    # Using LargeBinary for sqlite-vec
    vector = Column(LargeBinary, nullable=False)
    model = Column(String, nullable=False)
    dimensions = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("owner_type", "owner_id", "model", name="uq_embedding_owner_model"),
    )

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(String, primary_key=True)
    insight_type = Column(String, nullable=False)
    insight_id = Column(String, nullable=False)
    content_id = Column(String, ForeignKey("content.id"), nullable=False)
    conversation_id = Column(String, ForeignKey("conversation.id"))
    url = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    author_hash = Column(String)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    posted_at = Column(DateTime(timezone=True), nullable=False)
    exact_phrasing = Column(String)
    contribution = Column(String, nullable=False)
    relevance_score = Column(Integer, nullable=False)
    evidence_expired = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("insight_type", "insight_id", "content_id", name="uq_evidence_insight_content"),
        Index("ix_evidence_insight", "insight_type", "insight_id"),
        Index("ix_evidence_content", "content_id"),
        Index("ix_evidence_author_hash", "author_hash"),
        CheckConstraint("LENGTH(exact_phrasing) <= 120", name="ck_evidence_phrasing_len"),
    )

# Common block for aggregate insight tables
class InsightBase(Base):
    __abstract__ = True
    audience_id = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    status = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    supersedes = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    reviewed_at = Column(DateTime(timezone=True))
    reviewed_by = Column(String)
    review_notes = Column(String)
    observed_fact = Column(String)
    ai_interpretation = Column(String)
    hypothesis = Column(String)
    recommended_action = Column(String)
    first_detected = Column(DateTime(timezone=True))
    last_detected = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        CheckConstraint("status IN ('detected', 'analyzed', 'candidate', 'reviewed', 'trusted', 'archived', 'rejected')", name="ck_insight_status"),
    )

class Topic(InsightBase):
    __tablename__ = "topic"
    id = Column(String, primary_key=True)
    label = Column(String)
    description = Column(String)
    cluster_id = Column(String)
    centroid_embedding_id = Column(String) # foreign key concept
    cohesion = Column(Float)
    item_count = Column(Integer)
    distinct_authors = Column(Integer)
    platforms = Column(JSON)
    share_of_voice = Column(Float)
    superseded_by = Column(String)
    
    __table_args__ = (
        InsightBase.__table_args__ + (
            Index("ix_topic_audience_status", "audience_id", "status"),
            Index("ix_topic_cluster", "cluster_id"),
        )
    )

class PainPoint(InsightBase):
    __tablename__ = "pain_point"
    id = Column(String, primary_key=True)
    title = Column(String)
    category = Column(JSON)
    severity = Column(String)
    severity_score = Column(Integer)
    frequency = Column(Integer)
    frequency_distinct_authors = Column(Integer)
    frequency_change = Column(Float)
    trend = Column(String)
    platform_spread = Column(Integer)
    topic_id = Column(String, ForeignKey("topic.id"))
    cluster_id = Column(String)
    affected_segments = Column(JSON)
    representative_quotes = Column(JSON)
    paraphrased_examples = Column(JSON)
    related_pains = Column(JSON)
    single_thread = Column(Boolean)
    
    __table_args__ = (
        InsightBase.__table_args__ + (
            UniqueConstraint("audience_id", "slug", name="uq_pain_point_slug"),
            Index("ix_pain_point_audience_status_severity", "audience_id", "status", "severity_score"),
            Index("ix_pain_point_topic", "topic_id"),
            Index("ix_pain_point_last_detected", "last_detected"),
        )
    )

class Question(InsightBase):
    __tablename__ = "question"
    id = Column(String, primary_key=True)
    question = Column(String)
    normalized_question = Column(String)
    question_variants = Column(JSON)
    intent = Column(String)
    intent_confidence = Column(Float)
    secondary_intent = Column(String)
    urgency_score = Column(Integer)
    answered_in_thread_rate = Column(Float)
    content_potential = Column(Integer)
    business_potential = Column(Integer)
    platform_distribution = Column(JSON)
    competitor_coverage = Column(JSON)
    suggested_formats = Column(JSON)
    hooks = Column(JSON)
    asked_by = Column(String)
    is_rhetorical = Column(Boolean)
    
    __table_args__ = (
        InsightBase.__table_args__ + (
            UniqueConstraint("audience_id", "slug", name="uq_question_slug"),
            Index("ix_question_audience_status_urgency", "audience_id", "status", "urgency_score"),
            Index("ix_question_intent", "intent"),
        )
    )

class Objection(InsightBase):
    __tablename__ = "objection"
    id = Column(String, primary_key=True)
    objection = Column(String)
    normalized_objection = Column(String)
    objection_type = Column(String)
    secondary_type = Column(String)
    raised_at_stage = Column(String)
    directed_at = Column(String)
    stated_concern = Column(String)
    likely_underlying_concern = Column(String)
    underlying_confidence = Column(Float)
    evidence_for_underlying = Column(JSON)
    severity_to_conversion = Column(String)
    possible_responses = Column(JSON)
    responses_to_avoid = Column(JSON)
    addressability = Column(Integer)
    objection_priority = Column(Integer)
    
    __table_args__ = (
        InsightBase.__table_args__ + (
            CheckConstraint("underlying_confidence <= confidence", name="ck_objection_underlying_conf"),
        )
    )

class AudiencePhrase(InsightBase):
    __tablename__ = "audience_phrase"
    id = Column(String, primary_key=True)
    exact_text = Column(String, nullable=False)
    exact_context = Column(String)
    category = Column(String)
    normalized_concept = Column(String)
    normalized_label = Column(String)
    marketing_interpretation = Column(JSON)
    occurrences = Column(Integer)
    distinct_authors = Column(Integer)
    variants = Column(JSON)
    distinctiveness = Column(Float)
    resonance_signal = Column(Float)
    language = Column(String)
    detected_language = Column(String)
    translated_interpretation = Column(JSON)
    suppressed = Column(Boolean, default=False)

    __table_args__ = (
        InsightBase.__table_args__ + (
            UniqueConstraint("audience_id", "exact_text", "category", name="uq_audience_phrase_text_cat"),
            Index("ix_audience_phrase_distinctiveness", "audience_id", "distinctiveness"),
            Index("ix_audience_phrase_concept", "normalized_concept"),
        )
    )

class Trend(Base):
    __tablename__ = "trend"
    id = Column(String, primary_key=True)
    topic_id = Column(String, ForeignKey("topic.id"), nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    window_completeness = Column(Float)
    current_frequency = Column(Integer)
    previous_frequency = Column(Integer)
    baseline_mean = Column(Float)
    baseline_stdev = Column(Float)
    growth_rate = Column(Float)
    velocity = Column(Float)
    acceleration = Column(Float)
    z_score = Column(Float)
    classification = Column(String)
    trend_score = Column(Integer)
    significance_score = Column(Integer)
    guards_fired = Column(JSON)
    author_concentration = Column(Float)
    external_trigger = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("topic_id", "window_end", name="uq_trend_topic_window"),
        Index("ix_trend_window_significance", "window_end", "significance_score"),
    )

class Competitor(Base):
    __tablename__ = "competitor"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)
    priority = Column(String)
    website = Column(String)
    blog_feed = Column(String)
    sitemap = Column(String)
    youtube_channel = Column(String)
    social_accounts = Column(JSON)
    brand_terms = Column(JSON)
    product = Column(JSON)
    pricing = Column(JSON)
    pricing_last_verified = Column(DateTime(timezone=True))
    monitor = Column(JSON)
    data_quality = Column(String)
    content_items_total = Column(Integer, default=0)
    last_run_at = Column(DateTime(timezone=True))
    health = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class CompetitorContent(Base):
    __tablename__ = "competitor_content"
    id = Column(String, primary_key=True)
    competitor_id = Column(String, ForeignKey("competitor.id"), nullable=False)
    url = Column(String, nullable=False)
    title = Column(String)
    format = Column(String)
    published_at = Column(DateTime(timezone=True))
    collected_at = Column(DateTime(timezone=True))
    summary = Column(String)
    word_count = Column(Integer)
    duration_seconds = Column(Integer)
    engagement = Column(JSON)
    engagement_percentile = Column(Integer)
    topic_id = Column(String, ForeignKey("topic.id"))
    topic_confidence = Column(Float)
    is_primary_topic = Column(Boolean)
    promoted_offers = Column(JSON)
    data_quality = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("competitor_id", "url", name="uq_competitor_content_url"),
        Index("ix_competitor_content_pub", "competitor_id", "published_at"),
        Index("ix_competitor_content_topic", "topic_id"),
    )

class CompetitorCoverage(Base):
    __tablename__ = "competitor_coverage"
    id = Column(String, primary_key=True)
    competitor_id = Column(String, ForeignKey("competitor.id"), nullable=False)
    topic_id = Column(String, ForeignKey("topic.id"), nullable=False)
    computed_at = Column(DateTime(timezone=True), nullable=False)
    coverage_score = Column(Integer)
    volume_component = Column(Float)
    depth_component = Column(Float)
    recency_component = Column(Float)
    directness_component = Column(Float)
    items_on_topic = Column(Integer)
    last_seen = Column(DateTime(timezone=True))
    performance_index = Column(Float)
    low_sample = Column(Boolean)
    data_quality = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class CompetitorGap(Base):
    __tablename__ = "competitor_gap"
    id = Column(String, primary_key=True)
    gap_type = Column(String)
    topic_id = Column(String, ForeignKey("topic.id"))
    demand_score = Column(Integer)
    market_coverage = Column(Integer)
    coverage_by_competitor = Column(JSON)
    competitors_checked = Column(JSON)
    competitors_uncheckable = Column(JSON)
    items_examined = Column(Integer)
    examination_window_start = Column(DateTime(timezone=True))
    examination_window_end = Column(DateTime(timezone=True))
    unanswered_questions = Column(JSON)
    opportunity_score = Column(Integer)
    score_components = Column(JSON)
    confidence_caps_applied = Column(JSON)
    claims_requiring_verification = Column(JSON)
    addressed_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Opportunity(Base):
    __tablename__ = "opportunity"
    id = Column(String, primary_key=True)
    audience_id = Column(String, nullable=False)
    opportunity_class = Column(String)
    title = Column(String)
    slug = Column(String)
    core_idea = Column(String)
    audience_segments = Column(JSON)
    problem_ref = Column(String)
    audience_language = Column(JSON)
    scores = Column(JSON)
    opportunity_score = Column(Integer)
    score_band = Column(String)
    recommended_platform = Column(JSON)
    format = Column(JSON)
    angle = Column(String)
    hook_ideas = Column(JSON)
    structure_suggestion = Column(JSON)
    cta_idea = Column(String)
    do_not_say = Column(JSON)
    claims_requiring_verification = Column(JSON)
    blocked = Column(Boolean, default=False)
    decision = Column(String)
    decision_reason = Column(String)
    outcome = Column(JSON)
    exported_at = Column(DateTime(timezone=True))
    export_schema_version = Column(String)
    thresholds_met = Column(JSON)
    gate_status = Column(String)
    status = Column(String, nullable=False, default='candidate')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("ix_opportunity_audience_score", "audience_id", "status", "opportunity_score"),
        Index("ix_opportunity_decision", "decision"),
    )

class ReviewAction(Base):
    __tablename__ = "review_action"
    id = Column(String, primary_key=True)
    insight_type = Column(String, nullable=False)
    insight_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    from_status = Column(String)
    to_status = Column(String)
    reason_code = Column(String)
    notes = Column(String)
    field_changes = Column(JSON)
    actor = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_review_action_insight", "insight_type", "insight_id", "created_at"),
        Index("ix_review_action_action", "action", "created_at"),
    )

class Report(Base):
    __tablename__ = "report"
    id = Column(String, primary_key=True)
    report_type = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    file_path = Column(String)
    word_count = Column(Integer)
    insight_refs = Column(JSON)
    validation_status = Column(String)
    caveats = Column(JSON)
    generated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class CostLedger(Base):
    __tablename__ = "cost_ledger"
    id = Column(String, primary_key=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    agent = Column(String, nullable=False)
    model = Column(String, nullable=False)
    model_tier = Column(String, nullable=False)
    tokens_in = Column(Integer, nullable=False)
    tokens_out = Column(Integer, nullable=False)
    cost_usd = Column(Float, nullable=False)
    content_id = Column(String)
    cache_hit = Column(Boolean, nullable=False)
    job_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("ix_cost_ledger_occurred_at", "occurred_at"),
        Index("ix_cost_ledger_agent", "agent"),
    )

class QuotaLedger(Base):
    __tablename__ = "quota_ledger"
    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    units_used = Column(Integer, nullable=False)
    units_limit = Column(Integer, nullable=False)
    requests = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("platform", "date", name="uq_quota_ledger_platform_date"),
    )

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    detail = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
