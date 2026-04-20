"""
admin_api/utils/challenge_indexes.py
===================================
MongoDB index creation for social challenges system.

Run this once on deployment:
  python manage.py shell < admin_api/utils/challenge_indexes.py
"""

from admin_api.utils.mongo import _get_db

def create_challenge_indexes():
    """Create all required indexes for social challenges system"""
    db = _get_db()

    # ── Social Challenges collection indexes ────────────────────────────
    challenges_col = db['social_challenges']

    # Index 1: challenge_id for quick lookup
    challenges_col.create_index([("challenge_id", 1)], unique=True)
    print("✓ Index: social_challenges(challenge_id UNIQUE)")

    # Index 2: status for finding active/pending challenges
    challenges_col.create_index([("status", 1)])
    print("✓ Index: social_challenges(status)")

    # Index 3: creator_id for user's created challenges
    challenges_col.create_index([("creator_id", 1), ("created_at", -1)])
    print("✓ Index: social_challenges(creator_id, created_at DESC)")

    # Index 4: start_time + end_time for time-based queries
    challenges_col.create_index([("start_time", 1), ("end_time", 1)])
    print("✓ Index: social_challenges(start_time, end_time)")

    # Index 5: participants.user_id for finding user's challenges
    challenges_col.create_index([("participants.user_id", 1)])
    print("✓ Index: social_challenges(participants.user_id)")

    # Index 6: visibility for filtering public/friends-only
    challenges_col.create_index([("visibility", 1), ("status", 1)])
    print("✓ Index: social_challenges(visibility, status)")

    print("\n✅ All challenge indexes created successfully!")


if __name__ == "__main__":
    create_challenge_indexes()
