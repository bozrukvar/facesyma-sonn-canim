"""
admin_api/utils/goals_indexes.py
===================================
MongoDB indexes for user_goals collection.

Run once on deployment:
  python manage.py shell < admin_api/utils/goals_indexes.py
"""

from admin_api.utils.mongo import get_db


def create_goals_indexes():
    db  = get_db()
    col = db['user_goals']

    # Primary list query: user_id + status + created_at
    col.create_index([("user_id", 1), ("status", 1), ("created_at", -1)])
    print("✓ Index: user_goals(user_id, status, created_at DESC)")

    # Single goal lookup: user_id + _id (default _id index covers _id, but add user_id filter)
    col.create_index([("user_id", 1), ("_id", 1)])
    print("✓ Index: user_goals(user_id, _id)")

    # Test type analytics
    col.create_index([("test_type", 1), ("status", 1)])
    print("✓ Index: user_goals(test_type, status)")

    print("\n✅ Goals indexes created.")


if __name__ == "__main__":
    create_goals_indexes()
