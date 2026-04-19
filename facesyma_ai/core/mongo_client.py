"""
facesyma_ai/core/mongo_client.py
=================================
Merkezi MongoDB Client Singleton for Facesyma AI

Tüm AI modülü tarafından kullanılan merkezi MongoDB client'ı.
Connection pooling, analytics, memory, insights vb. koleksiyonları için.

Kullanım:
    from facesyma_ai.core.mongo_client import get_db, get_ai_users_col, get_ai_insights_col

    # AI Users
    users_col = get_ai_users_col()
    user_doc = users_col.find_one({"user_id": 123})

    # Analytics Insights
    insights_col = get_ai_insights_col()
    insights_col.update_one({"user_id": 123}, {"$inc": {"total_conversations": 1}})
"""

import os
import logging
from pymongo import MongoClient

log = logging.getLogger(__name__)

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/"
    "myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE"
)

_mongo_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    """
    Get shared MongoDB client singleton with connection pooling.

    Connection pooling reuses established connections across all requests,
    dramatically improving performance over creating new MongoClient per request.

    Returns:
        MongoClient instance with pool size 5-50 connections
    """
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(
            MONGO_URI,
            maxPoolSize=50,
            minPoolSize=5,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            retryWrites=True,
        )
        log.info("✓ MongoDB client initialized for AI module (pool: 5-50 connections)")
    return _mongo_client


def get_db():
    """Get facesyma-backend database with pooled connection"""
    return get_mongo_client()["facesyma-backend"]


# ── AI Module Collections ──────────────────────────────────────────────────────

def get_ai_users_col():
    """
    ai_users collection — User profiles and metadata for AI module.
    Unique on user_id and email for fast lookups.
    """
    return get_db()["ai_users"]


def get_ai_insights_col():
    """
    ai_insights collection — Analytics per user (conversations, preferences, metrics).
    Unique on user_id for atomic $inc operations.
    """
    return get_db()["ai_insights"]


def get_ai_metrics_col():
    """
    ai_metrics collection — Aggregated metrics (daily, weekly, monthly stats).
    Unique on user_id for fast metric updates.
    """
    return get_db()["ai_metrics"]


def get_ai_conv_memory_col():
    """
    ai_conv_memory collection — Conversation history and message memory.
    Unique on conversation_id for atomic message append/trim.
    Indexed on user_id for user's conversation list.
    """
    return get_db()["ai_conv_memory"]


def get_ai_embeddings_col():
    """
    ai_embeddings collection — Cached embeddings (for knowledge base docs).
    Indexed on text_hash for fast retrieval.
    """
    return get_db()["ai_embeddings"]
