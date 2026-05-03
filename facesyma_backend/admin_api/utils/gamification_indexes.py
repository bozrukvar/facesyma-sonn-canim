"""MongoDB index creation for new gamification collections."""

from admin_api.utils.mongo import _get_db


def create_gamification_indexes():
    db = _get_db()

    # ── leaderboard_snapshots ────────────────────────────────────────────
    snap = db['leaderboard_snapshots']
    snap.create_index([('snapshot_id', 1)], unique=True)
    snap.create_index([('leaderboard_type', 1), ('taken_at', -1)])
    snap.create_index([('trait_id', 1), ('taken_at', -1)], sparse=True)
    snap.create_index([('community_id', 1), ('taken_at', -1)], sparse=True)
    snap.create_index([('taken_at', 1)])  # TTL-style cleanup queries
    print('✓ Indexes: leaderboard_snapshots')

    # ── user_badges ──────────────────────────────────────────────────────
    badges = db['user_badges']
    badges.create_index([('user_id', 1), ('badge_id', 1)], unique=True)
    badges.create_index([('badge_id', 1), ('awarded_at', -1)])
    badges.create_index([('user_id', 1), ('awarded_at', -1)])
    print('✓ Indexes: user_badges')

    # ── discovery_game_sessions ──────────────────────────────────────────
    sessions = db['discovery_game_sessions']
    sessions.create_index([('session_id', 1)], unique=True)
    sessions.create_index([('user_id', 1), ('started_at', -1)])
    sessions.create_index([('state', 1), ('updated_at', -1)])
    print('✓ Indexes: discovery_game_sessions')

    # ── community_missions ───────────────────────────────────────────────
    missions = db['community_missions']
    missions.create_index([('mission_id', 1)], unique=True)
    missions.create_index([('status', 1), ('end_time', 1)])
    missions.create_index([('community_id', 1), ('status', 1)], sparse=True)
    missions.create_index([('participants.user_id', 1)], sparse=True)
    print('✓ Indexes: community_missions')

    print('\n✅ All new gamification indexes created!')


if __name__ == '__main__':
    create_gamification_indexes()
