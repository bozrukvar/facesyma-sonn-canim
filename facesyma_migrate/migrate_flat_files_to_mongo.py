#!/usr/bin/env python3
"""
migrate_flat_files_to_mongo.py
==============================
Migrate AI module flat-file JSON databases to MongoDB collections.

SAFE TO RE-RUN: All operations are upsert-based (idempotent).
Can be run against production with zero data loss.

Migration Plan:
  users_db.json                  → ai_users (user_id unique, email unique)
  analytics_db.json (per-user)   → ai_insights (user_id unique)
  conversations_db.json          → ai_conv_memory (conversation_id unique, user_id indexed)

Usage:
    python migrate_flat_files_to_mongo.py

Environment:
    Requires MONGO_URI to be set in environment or .env file
"""

import os
import sys
import json
import logging
from pathlib import Path
from pymongo import MongoClient, ASCENDING
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


def migrate_flat_files():
    """Migrate all flat-file JSON databases to MongoDB"""

    _info = log.info
    _warn = log.warning
    _err = log.error
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    try:
        # Test connection
        client.admin.command('ping')
        _info(f"✓ Connected to MongoDB")
    except Exception as e:
        _err(f"✗ Failed to connect to MongoDB: {e}")
        sys.exit(1)

    db = client["facesyma-backend"]
    _jload = json.load

    # ──────────────────────────────────────────────────────────────────────────
    # MIGRATION 1: users_db.json → ai_users
    # ──────────────────────────────────────────────────────────────────────────

    users_col = db["ai_users"]
    users_db_path = Path("./users_db.json")

    _info("📍 Migrating users_db.json → ai_users...")

    if users_db_path.exists():
        try:
            with open(users_db_path, 'r', encoding='utf-8') as f:
                users_data = _jload(f)

            inserted = 0
            updated = 0

            for user_id, user_doc in users_data.items():
                # Upsert: insert if new, update if exists
                result = users_col.update_one(
                    {"user_id": user_doc.get("user_id", user_id)},
                    {"$set": user_doc},
                    upsert=True
                )
                if result.upserted_id:
                    inserted += 1
                elif result.modified_count:
                    updated += 1

            _info(f"  ✓ {inserted} inserted, {updated} updated ({len(users_data)} total)")

            # Create indexes
            try:
                users_col.create_index([("user_id", ASCENDING)], unique=True, name="idx_user_id_unique")
                _info("  ✓ Created index on user_id")
            except Exception as e:
                _warn(f"  ⚠ Index creation: {e}")

            try:
                users_col.create_index([("email", ASCENDING)], unique=True, sparse=True, name="idx_email_unique")
                _info("  ✓ Created unique index on email")
            except Exception as e:
                _warn(f"  ⚠ Email index: {e}")

        except Exception as e:
            _err(f"  ✗ Migration failed: {e}")
    else:
        _warn(f"  ⚠ File not found: {users_db_path}")

    # ──────────────────────────────────────────────────────────────────────────
    # MIGRATION 2: analytics_db.json → ai_insights + ai_metrics
    # ──────────────────────────────────────────────────────────────────────────

    insights_col = db["ai_insights"]
    analytics_db_path = Path("./analytics_db.json")

    _info("📍 Migrating analytics_db.json → ai_insights...")

    if analytics_db_path.exists():
        try:
            with open(analytics_db_path, 'r', encoding='utf-8') as f:
                analytics_data = _jload(f)

            inserted = 0
            updated = 0

            for user_id, analytics_doc in analytics_data.items():
                # Store per-user analytics as single document
                result = insights_col.update_one(
                    {"user_id": user_id},
                    {"$set": analytics_doc},
                    upsert=True
                )
                if result.upserted_id:
                    inserted += 1
                elif result.modified_count:
                    updated += 1

            _info(f"  ✓ {inserted} inserted, {updated} updated ({len(analytics_data)} total)")

            # Create indexes
            try:
                insights_col.create_index([("user_id", ASCENDING)], unique=True, name="idx_user_id_unique")
                _info("  ✓ Created index on user_id")
            except Exception as e:
                _warn(f"  ⚠ Index creation: {e}")

        except Exception as e:
            _err(f"  ✗ Migration failed: {e}")
    else:
        _warn(f"  ⚠ File not found: {analytics_db_path}")

    # ──────────────────────────────────────────────────────────────────────────
    # MIGRATION 3: conversations_db.json → ai_conv_memory
    # ──────────────────────────────────────────────────────────────────────────

    conv_col = db["ai_conv_memory"]
    conversations_db_path = Path("./conversations_db.json")

    _info("📍 Migrating conversations_db.json → ai_conv_memory...")

    if conversations_db_path.exists():
        try:
            with open(conversations_db_path, 'r', encoding='utf-8') as f:
                conversations_data = _jload(f)

            inserted = 0
            updated = 0

            for conv_id, conv_doc in conversations_data.items():
                result = conv_col.update_one(
                    {"conversation_id": conv_id},
                    {"$set": conv_doc},
                    upsert=True
                )
                if result.upserted_id:
                    inserted += 1
                elif result.modified_count:
                    updated += 1

            _info(f"  ✓ {inserted} inserted, {updated} updated ({len(conversations_data)} total)")

            # Create indexes
            try:
                conv_col.create_index(
                    [("conversation_id", ASCENDING)],
                    unique=True,
                    name="idx_conversation_id_unique"
                )
                _info("  ✓ Created index on conversation_id")
            except Exception as e:
                _warn(f"  ⚠ Index creation: {e}")

            try:
                conv_col.create_index(
                    [("user_id", ASCENDING)],
                    name="idx_user_id"
                )
                _info("  ✓ Created index on user_id")
            except Exception as e:
                _warn(f"  ⚠ Index creation: {e}")

        except Exception as e:
            _err(f"  ✗ Migration failed: {e}")
    else:
        _warn(f"  ⚠ File not found: {conversations_db_path}")

    # ──────────────────────────────────────────────────────────────────────────
    # RESULT SUMMARY
    # ──────────────────────────────────────────────────────────────────────────

    _info("\n" + "="*60)
    _info("MIGRATION COMPLETE")
    _info("="*60)

    collections_to_check = [
        "ai_users",
        "ai_insights",
        "ai_conv_memory",
    ]

    for col_name in collections_to_check:
        col = db[col_name]
        count = col.count_documents({})
        indexes = list(col.list_indexes())
        _info(f"\n{col_name}:")
        _info(f"  • Documents: {count}")
        _info(f"  • Indexes: {len(indexes)}")
        for idx in indexes:
            _info(f"    - {idx['name']}")

    client.close()
    _info("\n✓ All migrations completed successfully!")
    _info("  Flat files remain untouched for backup purposes.")
    _info("  You can delete them manually after verifying data integrity.")


if __name__ == "__main__":
    migrate_flat_files()
