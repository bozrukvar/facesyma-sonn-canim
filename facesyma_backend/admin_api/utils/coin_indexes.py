"""
admin_api/utils/coin_indexes.py
==============================
MongoDB index creation for coin system.

Run this once on deployment:
  python manage.py shell < admin_api/utils/coin_indexes.py
"""

from admin_api.utils.mongo import _get_db

def create_coin_indexes():
    """Create all required indexes for coin system"""
    db = _get_db()

    # ── Transaction collection indexes ────────────────────────────────
    trans_col = db['coin_transactions']

    # Index 1: user_id + created_at (main query for history)
    trans_col.create_index([("user_id", -1), ("created_at", -1)])
    print("✓ Index: coin_transactions(user_id DESC, created_at DESC)")

    # Index 2: user_id + type (for filtering by type)
    trans_col.create_index([("user_id", 1), ("type", 1)])
    print("✓ Index: coin_transactions(user_id, type)")

    # Index 3: created_at (for admin reporting)
    trans_col.create_index([("created_at", -1)])
    print("✓ Index: coin_transactions(created_at DESC)")

    # Index 4: TTL - delete old transactions after 2 years (optional)
    # Uncomment if you want automatic cleanup
    # trans_col.create_index([("created_at", 1)], expireAfterSeconds=63072000)
    # print("✓ Index: coin_transactions TTL (2 years)")

    # ── User collection indexes (extend existing) ────────────────────
    users_col = db['appfaceapi_myuser']

    # Index 1: coins (for leaderboard filtering)
    users_col.create_index([("coins", -1)])
    print("✓ Index: appfaceapi_myuser(coins DESC)")

    # Index 2: total_earned (for stats)
    users_col.create_index([("total_earned", -1)])
    print("✓ Index: appfaceapi_myuser(total_earned DESC)")

    # Index 3: streak_count (for leaderboard)
    users_col.create_index([("streak_count", -1)])
    print("✓ Index: appfaceapi_myuser(streak_count DESC)")

    # Index 4: last_daily_quest (for checking completion)
    users_col.create_index([("last_daily_quest", 1)])
    print("✓ Index: appfaceapi_myuser(last_daily_quest)")

    print("\n✅ All coin indexes created successfully!")


if __name__ == "__main__":
    create_coin_indexes()
