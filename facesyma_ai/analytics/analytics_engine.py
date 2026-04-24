"""
Analytics & Insights Module
Tracks personality insights, conversation patterns, and user behavior
"""
import json
import os
from datetime import datetime
from operator import itemgetter, attrgetter
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

log = logging.getLogger(__name__)

class PersonalityInsight:
    """Single personality insight record"""
    def __init__(self, user_id: str, category: str, insight: str, confidence: float = 0.8):
        self.timestamp = datetime.now().isoformat()
        self.user_id = user_id
        self.category = category
        self.insight = insight
        self.confidence = confidence
        self.tags = []

class ConversationMetrics:
    """Conversation statistics"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.total_conversations = 0
        self.total_messages = 0
        self.average_response_length = 0
        self.favorite_categories = defaultdict(int)
        self.favorite_modules = defaultdict(int)
        self.languages_used = defaultdict(int)
        self.engagement_score = 0.0  # 0-100

class AnalyticsEngine:
    """Analytics and insights tracking"""
    def __init__(self, analytics_db_path: str = "./analytics_db.json"):
        self.analytics_db_path = analytics_db_path
        self.insights: Dict[str, List[PersonalityInsight]] = defaultdict(list)
        self.metrics: Dict[str, ConversationMetrics] = {}
        self.load_analytics()

    def load_analytics(self):
        """Load analytics from database"""
        if os.path.exists(self.analytics_db_path):
            try:
                with open(self.analytics_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    _dget = data.get
                    # Load insights
                    for user_id, user_insights in _dget("insights", {}).items():
                        for insight_data in user_insights:
                            insight = PersonalityInsight(**insight_data)
                            self.insights[user_id].append(insight)
                    # Load metrics
                    for user_id, metrics_data in _dget("metrics", {}).items():
                        metrics = ConversationMetrics(user_id)
                        metrics.__dict__.update(metrics_data)
                        self.metrics[user_id] = metrics
                log.info(f"Loaded analytics for {len(self.insights)} users")
            except Exception as e:
                log.error(f"Error loading analytics: {e}")

    def save_analytics(self):
        """Save analytics to database"""
        try:
            data = {
                "insights": {},
                "metrics": {}
            }
            # Save insights
            for user_id, insights in self.insights.items():
                data["insights"][user_id] = [
                    {
                        "timestamp": i.timestamp,
                        "user_id": i.user_id,
                        "category": i.category,
                        "insight": i.insight,
                        "confidence": i.confidence,
                        "tags": i.tags
                    }
                    for i in insights
                ]
            # Save metrics
            for user_id, metrics in self.metrics.items():
                data["metrics"][user_id] = metrics.__dict__

            with open(self.analytics_db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.info("Analytics saved to database")
        except Exception as e:
            log.error(f"Error saving analytics: {e}")

    def record_insight(self, user_id: str, category: str, insight: str,
                      confidence: float = 0.8, tags: List[str] = None):
        """Record a personality insight"""
        insight_obj = PersonalityInsight(user_id, category, insight, confidence)
        if tags:
            insight_obj.tags = tags
        self.insights[user_id].append(insight_obj)
        self.save_analytics()
        log.info(f"Insight recorded for user {user_id}: {category}")

    def record_conversation(self, user_id: str, category: str, module: str,
                           language: str, message_count: int = 1):
        """Record conversation metrics"""
        _met = self.metrics
        if user_id not in _met:
            _met[user_id] = ConversationMetrics(user_id)

        metrics = _met[user_id]
        metrics.total_conversations += 1
        metrics.total_messages += message_count
        metrics.favorite_categories[category] += 1
        metrics.favorite_modules[module] += 1
        metrics.languages_used[language] += 1

        # Calculate engagement (0-100)
        _mtc = metrics.total_conversations
        _mtm = metrics.total_messages
        metrics.engagement_score = min(100, (_mtc * 5) + (_mtm * 0.5))
        self.save_analytics()

    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get all insights for a user"""
        user_insights = self.insights.get(user_id, [])
        insights_by_category = defaultdict(list)

        for insight in user_insights:
            insights_by_category[insight.category].append({
                "timestamp": insight.timestamp,
                "insight": insight.insight,
                "confidence": insight.confidence,
                "tags": insight.tags
            })

        return {
            "total_insights": len(user_insights),
            "by_category": dict(insights_by_category),
            "latest": [
                {
                    "timestamp": i.timestamp,
                    "category": i.category,
                    "insight": i.insight,
                    "confidence": i.confidence
                }
                for i in sorted(user_insights, key=attrgetter('timestamp'), reverse=True)[:10]
            ]
        }

    def get_user_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get conversation metrics for a user"""
        metrics = self.metrics.get(user_id)
        if not metrics:
            return None

        return {
            "total_conversations": metrics.total_conversations,
            "total_messages": metrics.total_messages,
            "favorite_categories": dict(sorted(metrics.favorite_categories.items(),
                                              key=itemgetter(1), reverse=True)[:5]),
            "favorite_modules": dict(sorted(metrics.favorite_modules.items(),
                                           key=itemgetter(1), reverse=True)[:5]),
            "languages_used": dict(metrics.languages_used),
            "engagement_score": metrics.engagement_score
        }

    def get_top_insights(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top insights by confidence"""
        user_insights = self.insights.get(user_id, [])
        sorted_insights = sorted(user_insights, key=attrgetter('confidence'), reverse=True)

        return [
            {
                "insight": i.insight,
                "category": i.category,
                "confidence": i.confidence,
                "timestamp": i.timestamp
            }
            for i in sorted_insights[:limit]
        ]

    def generate_personality_summary(self, user_id: str) -> Dict[str, Any]:
        """Generate personality summary from insights"""
        insights = self.get_user_insights(user_id)
        metrics = self.get_user_metrics(user_id)

        if not insights or not metrics:
            return {"error": "Insufficient data"}

        _eng = metrics["engagement_score"]
        return {
            "user_id": user_id,
            "total_insights": insights["total_insights"],
            "dominant_categories": list(insights["by_category"].keys())[:3],
            "engagement_level": "high" if _eng > 70 else "medium" if _eng > 40 else "low",
            "engagement_score": _eng,
            "favorite_modules": list(metrics["favorite_modules"].keys())[:3],
            "primary_languages": list(metrics["languages_used"].keys()),
            "top_insights": self.get_top_insights(user_id, limit=5),
            "generated_at": datetime.now().isoformat()
        }
