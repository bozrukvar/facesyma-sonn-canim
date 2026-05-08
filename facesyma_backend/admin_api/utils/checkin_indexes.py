"""
admin_api/utils/checkin_indexes.py
===================================
MongoDB indexes for daily_checkins collection.

Run once on deployment:
  python manage.py shell < admin_api/utils/checkin_indexes.py
"""

from admin_api.utils.mongo import get_db


def create_checkin_indexes():
    db  = get_db()
    col = db['daily_checkins']

    # Primary lookup: user_id + date (upsert key — must be unique)
    col.create_index([("user_id", 1), ("date", 1)], unique=True)
    print("✓ Index: daily_checkins(user_id, date) UNIQUE")

    # Streak calc + history: user_id + date DESC
    col.create_index([("user_id", 1), ("date", -1)])
    print("✓ Index: daily_checkins(user_id, date DESC)")

    # Admin reporting: created_at DESC
    col.create_index([("created_at", -1)])
    print("✓ Index: daily_checkins(created_at DESC)")

    print("\n✅ Checkin indexes created.")


if __name__ == "__main__":
    create_checkin_indexes()
