#!/usr/bin/env python3
"""
create_indexes.py
==================
MongoDB Index Optimization for Facesyma AI

Creates all critical missing indexes to improve query performance:
- User authentication (email, date_joined)
- Analysis history (user_id + created_at compound)
- AI conversations (user_id + updated_at compound)
- Assessment results (user_id + created_at compound)
- Compatibility queries (user1_id, user2_id)
- Community operations (community_id, user_id, member status)

SAFE TO RE-RUN: MongoDB's createIndex is idempotent.
Can be run against production with zero downtime.

Usage:
    python create_indexes.py

Environment:
    Requires MONGO_URI to be set in environment or .env file
"""

import os
import sys
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# Load environment
load_dotenv()
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    log.error("MONGO_URI environment variable not set. Please set it before running.")
    sys.exit(1)


def create_indexes():
    """Create all critical indexes for Facesyma AI MongoDB."""

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    try:
        # Test connection
        client.admin.command('ping')
        log.info(f"✓ Connected to MongoDB")
    except Exception as e:
        log.error(f"✗ Failed to connect to MongoDB: {e}")
        sys.exit(1)

    db = client["facesyma-backend"]

    # ──────────────────────────────────────────────────────────────────────────
    # USERS COLLECTION — appfaceapi_myuser
    # ──────────────────────────────────────────────────────────────────────────

    users = db["appfaceapi_myuser"]

    log.info("📍 Creating indexes for appfaceapi_myuser...")

    # Unique index on email (required for login/registration)
    try:
        users.create_index(
            [("email", ASCENDING)],
            unique=True,
            name="idx_email_unique",
            sparse=True
        )
        log.info("  ✓ idx_email_unique")
    except Exception as e:
        log.warning(f"  ⚠ idx_email_unique: {e}")

    # Unique index on id (auto-increment PKobject)
    try:
        users.create_index(
            [("id", ASCENDING)],
            unique=True,
            name="idx_id_unique"
        )
        log.info("  ✓ idx_id_unique")
    except Exception as e:
        log.warning(f"  ⚠ idx_id_unique: {e}")

    # Index on date_joined (used for time-window queries in admin)
    try:
        users.create_index(
            [("date_joined", DESCENDING)],
            name="idx_date_joined_desc"
        )
        log.info("  ✓ idx_date_joined_desc")
    except Exception as e:
        log.warning(f"  ⚠ idx_date_joined_desc: {e}")

    # Index on top_sifats (used in compatibility filtering)
    try:
        users.create_index(
            [("top_sifats", ASCENDING)],
            sparse=True,
            name="idx_top_sifats"
        )
        log.info("  ✓ idx_top_sifats")
    except Exception as e:
        log.warning(f"  ⚠ idx_top_sifats: {e}")

    # Index on golden_ratio (used in compatibility scoring)
    try:
        users.create_index(
            [("golden_ratio", ASCENDING)],
            sparse=True,
            name="idx_golden_ratio"
        )
        log.info("  ✓ idx_golden_ratio")
    except Exception as e:
        log.warning(f"  ⚠ idx_golden_ratio: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # ANALYSIS HISTORY
    # ──────────────────────────────────────────────────────────────────────────

    history = db["analysis_history"]

    log.info("📍 Creating indexes for analysis_history...")

    # Compound index: user_id + created_at DESC (covers history queries)
    try:
        history.create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)],
            name="idx_user_created"
        )
        log.info("  ✓ idx_user_created")
    except Exception as e:
        log.warning(f"  ⚠ idx_user_created: {e}")

    # Index on created_at for time-based queries
    try:
        history.create_index(
            [("created_at", DESCENDING)],
            name="idx_created_desc"
        )
        log.info("  ✓ idx_created_desc")
    except Exception as e:
        log.warning(f"  ⚠ idx_created_desc: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # AI CONVERSATIONS (chat history)
    # ──────────────────────────────────────────────────────────────────────────

    convs = db["ai_conversations"]

    log.info("📍 Creating indexes for ai_conversations...")

    # Compound index: user_id + updated_at DESC (covers history endpoint)
    try:
        convs.create_index(
            [("user_id", ASCENDING), ("updated_at", DESCENDING)],
            name="idx_user_updated"
        )
        log.info("  ✓ idx_user_updated")
    except Exception as e:
        log.warning(f"  ⚠ idx_user_updated: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # COMPATIBILITY (user-to-user matching)
    # ──────────────────────────────────────────────────────────────────────────

    compat = db["compatibility"]

    log.info("📍 Creating indexes for compatibility...")

    # Unique compound index on user pair
    try:
        compat.create_index(
            [("user1_id", ASCENDING), ("user2_id", ASCENDING)],
            unique=True,
            name="idx_pair_unique"
        )
        log.info("  ✓ idx_pair_unique")
    except Exception as e:
        log.warning(f"  ⚠ idx_pair_unique: {e}")

    # Index on user1_id (for compatibility filtering)
    try:
        compat.create_index(
            [("user1_id", ASCENDING)],
            name="idx_user1"
        )
        log.info("  ✓ idx_user1")
    except Exception as e:
        log.warning(f"  ⚠ idx_user1: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # COMMUNITY MEMBERS
    # ──────────────────────────────────────────────────────────────────────────

    members = db["community_members"]

    log.info("📍 Creating indexes for community_members...")

    # Compound unique index: community_id + user_id
    try:
        members.create_index(
            [("community_id", ASCENDING), ("user_id", ASCENDING)],
            unique=True,
            name="idx_community_user"
        )
        log.info("  ✓ idx_community_user")
    except Exception as e:
        log.warning(f"  ⚠ idx_community_user: {e}")

    # Index on user_id (for member lookups)
    try:
        members.create_index(
            [("user_id", ASCENDING)],
            name="idx_user"
        )
        log.info("  ✓ idx_user")
    except Exception as e:
        log.warning(f"  ⚠ idx_user: {e}")

    # Index on status (for membership filtering)
    try:
        members.create_index(
            [("status", ASCENDING)],
            name="idx_status"
        )
        log.info("  ✓ idx_status")
    except Exception as e:
        log.warning(f"  ⚠ idx_status: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # ASSESSMENT RESULTS
    # ──────────────────────────────────────────────────────────────────────────

    assessments = db["assessment_results"]

    log.info("📍 Creating indexes for assessment_results...")

    # Compound index: user_id + created_at DESC
    try:
        assessments.create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)],
            name="idx_user_created"
        )
        log.info("  ✓ idx_user_created")
    except Exception as e:
        log.warning(f"  ⚠ idx_user_created: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # RESULT SUMMARY
    # ──────────────────────────────────────────────────────────────────────────

    log.info("\n" + "="*60)
    log.info("INDEX CREATION COMPLETE")
    log.info("="*60)

    # List all indexes
    collections_to_check = [
        "appfaceapi_myuser",
        "analysis_history",
        "ai_conversations",
        "compatibility",
        "community_members",
        "assessment_results"
    ]

    for col_name in collections_to_check:
        col = db[col_name]
        indexes = list(col.list_indexes())
        log.info(f"\n{col_name} ({len(indexes)} indexes):")
        for idx in indexes:
            log.info(f"  • {idx['name']}")

    client.close()
    log.info("\n✓ All indexes created successfully!")


if __name__ == "__main__":
    create_indexes()
