import math
from typing import Optional

def log_scale(value: int, saturated_at: int) -> float:
    if value <= 1:
        return 0.0
    return min(100.0, 100 * (math.log(value) / math.log(saturated_at)))

def pain_score(severity_score: int, frequency_score: int, is_critical: bool = False, critical_weight: float = 0.8) -> int:
    score = (0.6 * severity_score) + (0.4 * frequency_score)
    if is_critical:
        score = (critical_weight * 100) + ((1.0 - critical_weight) * score)
    return round(score)

def frequency_score(distinct_authors: int, weighted_frequency: float, platforms: int, single_thread_share: float = 0.0, author_concentration: float = 0.0) -> int:
    platform_spread_factor = 100 * min(1.0, (platforms - 1) / 2.0)
    score = (0.60 * log_scale(distinct_authors, 25)) + \
            (0.25 * log_scale(weighted_frequency, 60)) + \
            (0.15 * platform_spread_factor)
            
    if author_concentration > 0.5:
        score *= 0.8
    if single_thread_share > 0.6:
        score *= 0.75
        
    return round(score)

def trend_score(growth_rate: float, z_score: float, acceleration: float, baseline_mean: float, platform_spread: int, sustained_weeks: int, confidence_multiplier: float, saturated: bool = False) -> Optional[int]:
    score = (35 * min(1.0, growth_rate / 1.0)) + \
            (25 * min(1.0, max(0.0, z_score) / 3.0)) + \
            (20 * min(1.0, max(0.0, acceleration) / max(1.0, 0.5 * baseline_mean))) + \
            (10 * min(1.0, (platform_spread - 1) / 2.0)) + \
            (10 * min(1.0, sustained_weeks / 3.0))
            
    score = score * confidence_multiplier
    if saturated:
        score = min(score, 40)
        
    return round(max(0.0, min(100.0, score)))

def intent_score(intent_class: str, has_timing: bool = False, has_budget: bool = False, specific_products: bool = False, is_hypothetical: bool = False, is_rhetorical: bool = False, intent_confidence: float = 1.0) -> int:
    base_scores = {
        "purchase_intent": 100, "comparison": 85, "commercial": 75,
        "implementation": 70, "troubleshooting": 65, "educational": 50,
        "informational": 40, "opinion": 25
    }
    
    score = base_scores.get(intent_class, 0)
    
    if has_timing: score += 10
    if has_budget: score += 10
    if specific_products: score += 5
    if is_hypothetical: score -= 10
    if is_rhetorical: score -= 15
    
    score = max(0, min(100, score))
    confidence_factor = 0.7 + 0.3 * intent_confidence
    return round(score * confidence_factor)

def coverage_score(items_on_topic: int, depth_percentile: float, max_age_days: int, directness: float) -> float:
    if max_age_days <= 30: recency_component = 100
    elif max_age_days <= 90: recency_component = 70
    elif max_age_days <= 180: recency_component = 40
    elif max_age_days <= 365: recency_component = 10
    else: recency_component = 0
    
    score = (0.35 * log_scale(items_on_topic, 8)) + \
            (0.25 * depth_percentile) + \
            (0.25 * recency_component) + \
            (0.15 * directness * 100)
    return max(0.0, min(100.0, score))

def competition_score(market_coverage: float, items_examined: int, one_competitor_partial: bool, any_unavailable: bool, max_data_age_days: int) -> int:
    if any_unavailable or items_examined < 50: penalty = 0.70
    elif max_data_age_days > 60: penalty = 0.55
    elif one_competitor_partial: penalty = 0.85
    else: penalty = 1.00
    
    return round(market_coverage * penalty)

def search_demand_score(popularity: Optional[int], growth: Optional[float], impressions: Optional[int], conversions: Optional[int], intent_score: float) -> int:
    score = 0.0
    weight = 0.0
    
    if popularity is not None:
        score += popularity * 0.4
        weight += 0.4
        
    if growth is not None:
        growth_val = min(100.0, max(0.0, 50.0 + (growth * 50.0)))
        score += growth_val * 0.2
        weight += 0.2
        
    if impressions is not None:
        imp_val = log_scale(impressions, 10000)
        score += imp_val * 0.15
        weight += 0.15
        
    if conversions is not None and conversions > 0:
        score += min(100.0, conversions * 5.0) * 0.1
        weight += 0.1
        
    score += intent_score * 0.15
    weight += 0.15
    
    if weight == 0:
        return 0
    return round(score / weight)

def opportunity_score(pain: float, frequency: float, trend: Optional[float], intent: float, business_relevance: float, competition: float, search_demand: float, distinct_authors: int, platforms: int, confidence: float) -> int:
    if distinct_authors < 3 and search_demand < 50:
        return 0
        
    trend_val = trend if trend is not None else 0.0
    content_gap = 100.0 - competition
    
    base = (0.18 * pain) + \
           (0.12 * frequency) + \
           (0.12 * trend_val) + \
           (0.12 * intent) + \
           (0.16 * business_relevance) + \
           (0.12 * content_gap) + \
           (0.18 * search_demand)
           
    if distinct_authors >= 8 and platforms >= 2:
        evidence_multiplier = 1.00
    elif (5 <= distinct_authors <= 7) or platforms == 1:
        evidence_multiplier = 0.85
    else: # 3 to 4
        evidence_multiplier = 0.70
        
    competition_penalty = 1.0 - (0.30 * competition / 100.0)
    confidence_multiplier = 0.7 + (0.3 * confidence)
    
    score = base * evidence_multiplier * competition_penalty * confidence_multiplier
    return round(score)
