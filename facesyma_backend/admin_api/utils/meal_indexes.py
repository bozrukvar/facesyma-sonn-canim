"""
admin_api/utils/meal_indexes.py
==============================
MongoDB index creation for meal game system.

Run this once on deployment:
  python manage.py shell < admin_api/utils/meal_indexes.py
"""

from admin_api.utils.mongo import _get_db

def create_meal_indexes():
    """Create all required indexes for meal game system"""
    db = _get_db()

    # ── Meal Selections collection indexes ──────────────────────────────
    sel_col = db['meal_selections']
    _cidx = sel_col.create_index

    # Index 1: (user_id, week_key) for weekly leaderboard
    _cidx([("user_id", 1), ("week_key", 1)])
    print("✓ Index: meal_selections(user_id, week_key)")

    # Index 2: (country, week_key) for leaderboard aggregation
    _cidx([("country", 1), ("week_key", 1)])
    print("✓ Index: meal_selections(country, week_key)")

    # Index 3: (user_id, selected_at) for user history
    _cidx([("user_id", 1), ("selected_at", -1)])
    print("✓ Index: meal_selections(user_id, selected_at DESC)")

    # Index 4: selected_at for admin reporting
    _cidx([("selected_at", -1)])
    print("✓ Index: meal_selections(selected_at DESC)")

    # Index 5: meal_id for quick meal lookup
    _cidx([("meal_id", 1)])
    print("✓ Index: meal_selections(meal_id)")

    print("\n✅ All meal game indexes created successfully!")


if __name__ == "__main__":
    create_meal_indexes()
