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

    _info = log.info
    _warn = log.warning
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    try:
        # Test connection
        client.admin.command('ping')
        _info(f"✓ Connected to MongoDB")
    except Exception as e:
        log.error(f"✗ Failed to connect to MongoDB: {e}")
        sys.exit(1)

    db = client["facesyma-backend"]

    # ──────────────────────────────────────────────────────────────────────────
    # USERS COLLECTION — appfaceapi_myuser
    # ──────────────────────────────────────────────────────────────────────────

    users = db["appfaceapi_myuser"]
    _uidx = users.create_index

    _info("📍 Creating indexes for appfaceapi_myuser...")

    # Unique index on email (required for login/registration)
    try:
        _uidx(
            [("email", ASCENDING)],
            unique=True,
            name="idx_email_unique",
            sparse=True
        )
        _info("  ✓ idx_email_unique")
    except Exception as e:
        _warn(f"  ⚠ idx_email_unique: {e}")

    # Unique index on id (auto-increment PKobject)
    try:
        _uidx(
            [("id", ASCENDING)],
            unique=True,
            name="idx_id_unique"
        )
        _info("  ✓ idx_id_unique")
    except Exception as e:
        _warn(f"  ⚠ idx_id_unique: {e}")

    # Index on date_joined (used for time-window queries in admin)
    try:
        _uidx(
            [("date_joined", DESCENDING)],
            name="idx_date_joined_desc"
        )
        _info("  ✓ idx_date_joined_desc")
    except Exception as e:
        _warn(f"  ⚠ idx_date_joined_desc: {e}")

    # Index on top_sifats (used in compatibility filtering)
    try:
        _uidx(
            [("top_sifats", ASCENDING)],
            sparse=True,
            name="idx_top_sifats"
        )
        _info("  ✓ idx_top_sifats")
    except Exception as e:
        _warn(f"  ⚠ idx_top_sifats: {e}")

    # Index on golden_ratio (used in compatibility scoring)
    try:
        _uidx(
            [("golden_ratio", ASCENDING)],
            sparse=True,
            name="idx_golden_ratio"
        )
        _info("  ✓ idx_golden_ratio")
    except Exception as e:
        _warn(f"  ⚠ idx_golden_ratio: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # ANALYSIS HISTORY
    # ──────────────────────────────────────────────────────────────────────────

    history = db["analysis_history"]
    _hci = history.create_index

    _info("📍 Creating indexes for analysis_history...")

    # Compound index: user_id + created_at DESC (covers history queries)
    try:
        _hci(
            [("user_id", ASCENDING), ("created_at", DESCENDING)],
            name="idx_user_created"
        )
        _info("  ✓ idx_user_created")
    except Exception as e:
        _warn(f"  ⚠ idx_user_created: {e}")

    # Index on created_at for time-based queries
    try:
        _hci(
            [("created_at", DESCENDING)],
            name="idx_created_desc"
        )
        _info("  ✓ idx_created_desc")
    except Exception as e:
        _warn(f"  ⚠ idx_created_desc: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # AI CONVERSATIONS (chat history)
    # ──────────────────────────────────────────────────────────────────────────

    convs = db["ai_conversations"]

    _info("📍 Creating indexes for ai_conversations...")

    # Compound index: user_id + updated_at DESC (covers history endpoint)
    try:
        convs.create_index(
            [("user_id", ASCENDING), ("updated_at", DESCENDING)],
            name="idx_user_updated"
        )
        _info("  ✓ idx_user_updated")
    except Exception as e:
        _warn(f"  ⚠ idx_user_updated: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # COMPATIBILITY (user-to-user matching)
    # ──────────────────────────────────────────────────────────────────────────

    compat = db["compatibility"]
    _cai = compat.create_index

    _info("📍 Creating indexes for compatibility...")

    # Unique compound index on user pair
    try:
        _cai(
            [("user1_id", ASCENDING), ("user2_id", ASCENDING)],
            unique=True,
            name="idx_pair_unique"
        )
        _info("  ✓ idx_pair_unique")
    except Exception as e:
        _warn(f"  ⚠ idx_pair_unique: {e}")

    # Index on user1_id (for compatibility filtering)
    try:
        _cai(
            [("user1_id", ASCENDING)],
            name="idx_user1"
        )
        _info("  ✓ idx_user1")
    except Exception as e:
        _warn(f"  ⚠ idx_user1: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # COMMUNITY MEMBERS
    # ──────────────────────────────────────────────────────────────────────────

    members = db["community_members"]
    _midx = members.create_index

    _info("📍 Creating indexes for community_members...")

    # Compound unique index: community_id + user_id
    try:
        _midx(
            [("community_id", ASCENDING), ("user_id", ASCENDING)],
            unique=True,
            name="idx_community_user"
        )
        _info("  ✓ idx_community_user")
    except Exception as e:
        _warn(f"  ⚠ idx_community_user: {e}")

    # Index on user_id (for member lookups)
    try:
        _midx(
            [("user_id", ASCENDING)],
            name="idx_user"
        )
        _info("  ✓ idx_user")
    except Exception as e:
        _warn(f"  ⚠ idx_user: {e}")

    # Index on status (for membership filtering)
    try:
        _midx(
            [("status", ASCENDING)],
            name="idx_status"
        )
        _info("  ✓ idx_status")
    except Exception as e:
        _warn(f"  ⚠ idx_status: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # ASSESSMENT RESULTS
    # ──────────────────────────────────────────────────────────────────────────

    assessments = db["assessment_results"]

    _info("📍 Creating indexes for assessment_results...")

    # Compound index: user_id + created_at DESC
    try:
        assessments.create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)],
            name="idx_user_created"
        )
        _info("  ✓ idx_user_created")
    except Exception as e:
        _warn(f"  ⚠ idx_user_created: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # ADVISOR & MOTIVATE SENTENCES
    # Queried by { "sifat": sifat } on every face analysis — index is critical.
    # ──────────────────────────────────────────────────────────────────────────

    for col_name in ("appfaceapi_advisor", "appfaceapi_motivate"):
        col = db[col_name]
        _info(f"📍 Creating indexes for {col_name}...")
        try:
            col.create_index(
                [("sifat", ASCENDING)],
                name="idx_sifat"
            )
            _info(f"  ✓ idx_sifat")
        except Exception as e:
            _warn(f"  ⚠ idx_sifat: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # ADMIN USERS
    # ──────────────────────────────────────────────────────────────────────────

    admin_col = db["admin_users"]
    _info("📍 Creating indexes for admin_users...")
    for field, unique in (("id", True), ("email", True)):
        try:
            admin_col.create_index(
                [(field, ASCENDING)],
                unique=unique,
                sparse=True,
                name=f"idx_{field}_unique"
            )
            _info(f"  ✓ idx_{field}_unique")
        except Exception as e:
            _warn(f"  ⚠ idx_{field}_unique: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # ALERT RULES + HISTORY
    # ──────────────────────────────────────────────────────────────────────────

    alert_rules_col = db["alert_rules"]
    _info("📍 Creating indexes for alert_rules...")
    for field, unique in (("id", True), ("enabled", False)):
        try:
            alert_rules_col.create_index(
                [(field, ASCENDING)],
                unique=unique,
                sparse=(field == "id"),
                name=f"idx_{field}{'_unique' if unique else ''}"
            )
            _info(f"  ✓ idx_{field}")
        except Exception as e:
            _warn(f"  ⚠ idx_{field}: {e}")

    alert_history_col = db["alert_history"]
    _info("📍 Creating indexes for alert_history...")
    for index_spec, name in [
        ([("triggered_at", DESCENDING)], "idx_triggered_at_desc"),
        ([("rule_id", ASCENDING), ("triggered_at", DESCENDING)], "idx_rule_triggered"),
    ]:
        try:
            alert_history_col.create_index(index_spec, name=name)
            _info(f"  ✓ {name}")
        except Exception as e:
            _warn(f"  ⚠ {name}: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # ADMIN ACTIVITY LOG
    # ──────────────────────────────────────────────────────────────────────────

    activity_col = db["admin_activity_log"]
    _info("📍 Creating indexes for admin_activity_log...")
    for index_spec, name in [
        ([("timestamp", DESCENDING)], "idx_timestamp_desc"),
        ([("admin_id", ASCENDING), ("timestamp", DESCENDING)], "idx_admin_timestamp"),
        ([("action", ASCENDING)], "idx_action"),
    ]:
        try:
            activity_col.create_index(index_spec, name=name)
            _info(f"  ✓ {name}")
        except Exception as e:
            _warn(f"  ⚠ {name}: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # USER SUBSCRIPTIONS
    # ──────────────────────────────────────────────────────────────────────────

    subs_col = db["user_subscriptions"]
    _info("📍 Creating indexes for user_subscriptions...")
    for index_spec, name, unique in [
        ([("user_id", ASCENDING)], "idx_user_id_unique", True),
        ([("tier", ASCENDING), ("status", ASCENDING)], "idx_tier_status", False),
        ([("expires_date", ASCENDING)], "idx_expires_date", False),
        ([("renews_at", ASCENDING)], "idx_renews_at", False),
    ]:
        try:
            subs_col.create_index(index_spec, name=name, unique=unique, sparse=unique)
            _info(f"  ✓ {name}")
        except Exception as e:
            _warn(f"  ⚠ {name}: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # APP REGISTRY
    # ──────────────────────────────────────────────────────────────────────────

    registry_col = db["app_registry"]
    _info("📍 Creating indexes for app_registry...")
    try:
        registry_col.create_index(
            [("app_id", ASCENDING)],
            unique=True,
            sparse=True,
            name="idx_app_id_unique"
        )
        _info("  ✓ idx_app_id_unique")
    except Exception as e:
        _warn(f"  ⚠ idx_app_id_unique: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # RESULT SUMMARY
    # ──────────────────────────────────────────────────────────────────────────

    _info("\n" + "="*60)
    _info("INDEX CREATION COMPLETE")
    _info("="*60)

    # List all indexes
    collections_to_check = [
        "appfaceapi_myuser",
        "analysis_history",
        "ai_conversations",
        "compatibility",
        "community_members",
        "assessment_results",
        "appfaceapi_advisor",
        "appfaceapi_motivate",
        "admin_users",
        "alert_rules",
        "alert_history",
        "admin_activity_log",
        "user_subscriptions",
        "app_registry",
    ]

    for col_name in collections_to_check:
        col = db[col_name]
        indexes = list(col.list_indexes())
        _info(f"\n{col_name} ({len(indexes)} indexes):")
        for idx in indexes:
            _info(f"  • {idx['name']}")

    client.close()
    _info("\n✓ All indexes created successfully!")


if __name__ == "__main__":
    create_indexes()
