#!/usr/bin/env python
"""
facesyma_backend/migrate_coin_system.py
======================================
Initialize coin system for existing users.

This script:
1. Creates MongoDB indexes
2. Adds coin fields to existing users (if missing)
3. Sets up coin system for new users

Run once on deployment:
  python manage.py shell < migrate_coin_system.py
OR
  python migrate_coin_system.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facesyma_project.settings')
django.setup()

from admin_api.utils.mongo import get_users_col, _get_db
from admin_api.utils.coin_indexes import create_coin_indexes
from admin_api.utils.meal_indexes import create_meal_indexes
from admin_api.utils.challenge_indexes import create_challenge_indexes
from core.models.transaction import USER_COIN_FIELDS
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def migrate_coin_fields():
    """Add coin fields to existing users (idempotent)"""
    col = get_users_col()

    # Count users missing coin fields
    missing_count = col.count_documents({"coins": {"$exists": False}})
    print(f"\n📊 Users missing coin fields: {missing_count}")

    if missing_count == 0:
        print("✓ All users already have coin fields")
        return

    # Bulk update: add default coin fields to users without them
    result = col.update_many(
        {"coins": {"$exists": False}},
        {"$set": USER_COIN_FIELDS},
    )
    print(f"✓ Updated {result.modified_count} users with coin fields")


def create_transaction_collection():
    """Ensure transaction collection exists"""
    db = _get_db()
    if "coin_transactions" not in db.list_collection_names():
        db.create_collection("coin_transactions")
        print("✓ Created coin_transactions collection")
    else:
        print("✓ coin_transactions collection already exists")


def create_meal_selections_collection():
    """Ensure meal_selections collection exists"""
    db = _get_db()
    if "meal_selections" not in db.list_collection_names():
        db.create_collection("meal_selections")
        print("✓ Created meal_selections collection")
    else:
        print("✓ meal_selections collection already exists")


def create_challenges_collection():
    """Ensure social_challenges collection exists"""
    db = _get_db()
    if "social_challenges" not in db.list_collection_names():
        db.create_collection("social_challenges")
        print("✓ Created social_challenges collection")
    else:
        print("✓ social_challenges collection already exists")


def main():
    print("\n" + "="*60)
    print("GAMIFICATION SYSTEM MIGRATION")
    print("="*60)

    # ── COIN SYSTEM ────────────────────────────────────────────────────
    print("\n[COIN SYSTEM]")
    print("\n[1/7] Ensuring coin_transactions collection exists...")
    create_transaction_collection()

    print("\n[2/7] Adding coin fields to existing users...")
    migrate_coin_fields()

    print("\n[3/7] Creating coin system indexes...")
    create_coin_indexes()

    # ── MEAL GAME SYSTEM ────────────────────────────────────────────────
    print("\n[MEAL GAME SYSTEM]")
    print("\n[4/7] Ensuring meal_selections collection exists...")
    create_meal_selections_collection()

    print("\n[5/7] Creating meal game indexes...")
    create_meal_indexes()

    # ── SOCIAL CHALLENGES SYSTEM ───────────────────────────────────────
    print("\n[SOCIAL CHALLENGES SYSTEM]")
    print("\n[6/7] Ensuring social_challenges collection exists...")
    create_challenges_collection()

    print("\n[7/7] Creating social challenges indexes...")
    create_challenge_indexes()

    print("\n" + "="*60)
    print("✅ GAMIFICATION SYSTEM MIGRATION COMPLETE")
    print("="*60)
    print("\nTesting Coin System:")
    print("  POST /api/v1/coins/daily-quest/complete")
    print("  GET  /api/v1/coins/balance")
    print("  GET  /api/v1/coins/history")
    print("\nTesting Meal Game:")
    print("  GET  /api/v1/meals/daily")
    print("  POST /api/v1/meals/select")
    print("  POST /api/v1/meals/guess-sifat")
    print("  GET  /api/v1/meals/leaderboard")
    print("  GET  /api/v1/meals/history")
    print("\nTesting Social Challenges:")
    print("  GET  /api/v1/challenges/types")
    print("  POST /api/v1/challenges/create")
    print("  POST /api/v1/challenges/join")
    print("  POST /api/v1/challenges/update-score")
    print("  GET  /api/v1/challenges/leaderboard")
    print("  POST /api/v1/challenges/cancel")
    print("  GET  /api/v1/challenges/active")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
