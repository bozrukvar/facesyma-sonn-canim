"""Create MongoDB indexes for the 5 new game collections.
Run inside the backend container:
  python -m gamification.migrate_game_indexes
"""
import os
import pymongo

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/facesyma')
_client = pymongo.MongoClient(MONGO_URI)
_db = _client.get_default_database()


def run():
    results = []

    # ── wordle_attempts ──────────────────────────────────────────────────────
    col = _db['wordle_attempts']
    col.create_index(
        [('user_id', 1), ('date', 1)],
        unique=True,
        name='wordle_user_date_unique',
    )
    col.create_index([('date', 1), ('won', 1)], name='wordle_date_won')
    # TTL: drop records older than 90 days
    col.create_index(
        [('updated_at', 1)],
        expireAfterSeconds=60 * 60 * 24 * 90,
        name='wordle_ttl_90d',
        sparse=True,
    )
    results.append('wordle_attempts: 3 indexes')

    # ── speed_match_scores ───────────────────────────────────────────────────
    col = _db['speed_match_scores']
    col.create_index([('user_id', 1)], name='speed_user')
    col.create_index([('score', -1)], name='speed_score_desc')
    col.create_index([('user_id', 1), ('score', -1)], name='speed_user_score')
    results.append('speed_match_scores: 3 indexes')

    # ── poll_votes ───────────────────────────────────────────────────────────
    col = _db['poll_votes']
    col.create_index(
        [('user_id', 1), ('date', 1)],
        unique=True,
        name='poll_user_date_unique',
    )
    col.create_index([('date', 1)], name='poll_date')
    col.create_index(
        [('created_at', 1)],
        expireAfterSeconds=60 * 60 * 24 * 30,
        name='poll_ttl_30d',
        sparse=True,
    )
    results.append('poll_votes: 3 indexes')

    # ── memory_scores ────────────────────────────────────────────────────────
    col = _db['memory_scores']
    col.create_index([('user_id', 1)], name='memory_user')
    col.create_index([('moves', 1)], name='memory_moves_asc')
    col.create_index([('user_id', 1), ('moves', 1)], name='memory_user_moves')
    results.append('memory_scores: 3 indexes')

    # ── daily_spins ──────────────────────────────────────────────────────────
    col = _db['daily_spins']
    col.create_index(
        [('user_id', 1), ('date', 1)],
        unique=True,
        name='spin_user_date_unique',
    )
    col.create_index([('date', 1)], name='spin_date')
    col.create_index(
        [('spun_at', 1)],
        expireAfterSeconds=60 * 60 * 24 * 90,
        name='spin_ttl_90d',
        sparse=True,
    )
    results.append('daily_spins: 3 indexes')

    # ── discovery_game_sessions ──────────────────────────────────────────────
    col = _db['discovery_game_sessions']
    col.create_index([('user_id', 1), ('state', 1)], name='disc_user_state')
    col.create_index(
        [('started_at', 1)],
        expireAfterSeconds=60 * 60 * 24 * 30,
        name='disc_ttl_30d',
        sparse=True,
    )
    results.append('discovery_game_sessions: 2 indexes')

    # ── meal_game_sessions ───────────────────────────────────────────────────
    col = _db['meal_game_sessions']
    col.create_index([('user_id', 1), ('meal_id', 1)], unique=True, name='meal_session_user_meal')
    col.create_index([('user_id', 1), ('started_at', -1)], name='meal_session_user_time')
    col.create_index(
        [('started_at', 1)],
        expireAfterSeconds=60 * 60 * 24 * 30,
        name='meal_session_ttl_30d',
        sparse=True,
    )
    results.append('meal_game_sessions: 3 indexes')

    # ── meal_selections ──────────────────────────────────────────────────────
    col = _db['meal_selections']
    col.create_index([('user_id', 1)], name='meal_sel_user')
    col.create_index([('week', 1)], name='meal_sel_week')
    col.create_index([('user_id', 1), ('week', 1)], name='meal_sel_user_week')
    results.append('meal_selections: 3 indexes')

    # ── meal_leaderboard ─────────────────────────────────────────────────────
    col = _db['meal_leaderboard']
    col.create_index([('week', 1), ('score', -1)], name='meal_lb_week_score')
    col.create_index([('user_id', 1), ('week', 1)], unique=True, name='meal_lb_user_week')
    results.append('meal_leaderboard: 2 indexes')

    # ── existing game collections (ensure indexes) ───────────────────────────
    _db['wordle_attempts'].create_index([('date', 1)], name='wordle_date')
    _db['speed_match_scores'].create_index([('created_at', -1)], name='speed_created_desc')

    for r in results:
        print(f'  ✓ {r}')
    print(f'\nTamamlandı: {len(results)} koleksiyon indexlendi.')


if __name__ == '__main__':
    print('Facesyma game index migration başlıyor...\n')
    run()
