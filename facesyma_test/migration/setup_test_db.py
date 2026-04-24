#!/usr/bin/env python3
"""
Facesyma Test Module — MongoDB Setup Script
=============================================
Creates indexes and initializes the test database.

Run once during deployment:
  python setup_test_db.py
"""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING

MONGO_URI = os.environ.get("MONGO_URI", "")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable must be set.")

def setup_database():
    """Create indexes and collections"""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["facesyma-test-backup"]

    print("=" * 70)
    print("SETTING UP FACESYMA TEST DATABASE")
    print("=" * 70)

    # ── test_sessions collection ──────────────────────────────────────────
    print("\n[1/3] Setting up test_sessions collection...")
    sessions = db["test_sessions"]
    _sidx = sessions.create_index
    _sidx([("user_id", ASCENDING)])
    _sidx([("test_type", ASCENDING)])
    _sidx([("created_at", DESCENDING)])
    _sidx([("status", ASCENDING)])
    print("      ✓ Indexes created")

    # ── test_results collection ───────────────────────────────────────────
    print("\n[2/3] Setting up test_results collection...")
    results = db["test_results"]
    _ridx = results.create_index
    _ridx([("user_id", ASCENDING)])
    _ridx([("test_type", ASCENDING)])
    _ridx([("created_at", DESCENDING)])
    _ridx([("session_id", ASCENDING)])
    print("      ✓ Indexes created")

    # ── Verify ──────────────────────────────────────────────────────────
    print("\n[3/3] Verifying setup...")
    collections = db.list_collection_names()
    print(f"      Collections: {', '.join(collections)}")
    print(f"      test_sessions indexes: {list(sessions.list_indexes())}")
    print(f"      test_results indexes: {list(results.list_indexes())}")

    print("\n" + "=" * 70)
    print("✅ Database setup complete!")
    print("=" * 70)

if __name__ == "__main__":
    setup_database()
