// MongoDB initialization script — runs once on first container start.
// Creates all indexes for the facesyma database.
// Applied automatically when MongoDB starts with an empty data volume.

db = db.getSiblingDB('facesyma');

// ── Users ────────────────────────────────────────────────────────────────────
db.appfaceapi_myuser.createIndex({ id: 1 }, { unique: true, name: 'user_id_unique' });
db.appfaceapi_myuser.createIndex({ email: 1 }, { unique: true, sparse: true, name: 'user_email_unique' });

// ── XP transactions ───────────────────────────────────────────────────────────
db.xp_transactions.createIndex({ user_id: 1 }, { name: 'xp_user' });
db.xp_transactions.createIndex({ user_id: 1, created_at: -1 }, { name: 'xp_user_time' });
db.xp_transactions.createIndex({ transaction_id: 1 }, { unique: true, sparse: true, name: 'xp_tx_unique' });

// ── Coin transactions (legacy, keep for migration period) ─────────────────────
db.coin_transactions.createIndex({ user_id: 1 }, { name: 'coins_user' });
db.coin_transactions.createIndex({ user_id: 1, created_at: -1 }, { name: 'coins_user_time' });

// ── Gamification — leaderboard ───────────────────────────────────────────────
db.gamification_scores.createIndex({ user_id: 1 }, { unique: true, name: 'gam_score_user' });
db.gamification_scores.createIndex({ total_score: -1 }, { name: 'gam_score_desc' });

// ── Social challenges ─────────────────────────────────────────────────────────
db.social_challenges.createIndex({ challenge_id: 1 }, { unique: true, name: 'challenge_id_unique' });
db.social_challenges.createIndex({ status: 1, end_time: 1 }, { name: 'challenge_status_end' });
db.social_challenges.createIndex({ type_id: 1, is_system: 1, status: 1 }, { name: 'challenge_type_system' });

// ── Game: Wordle ─────────────────────────────────────────────────────────────
db.wordle_attempts.createIndex(
  { user_id: 1, date: 1 },
  { unique: true, name: 'wordle_user_date_unique' }
);
db.wordle_attempts.createIndex({ date: 1, won: 1 }, { name: 'wordle_date_won' });
db.wordle_attempts.createIndex(
  { updated_at: 1 },
  { expireAfterSeconds: 7776000, sparse: true, name: 'wordle_ttl_90d' }  // 90 days
);

// ── Game: Speed Match ─────────────────────────────────────────────────────────
db.speed_match_scores.createIndex({ user_id: 1 }, { name: 'speed_user' });
db.speed_match_scores.createIndex({ score: -1 }, { name: 'speed_score_desc' });
db.speed_match_scores.createIndex({ user_id: 1, score: -1 }, { name: 'speed_user_score' });

// ── Game: Daily Poll ──────────────────────────────────────────────────────────
db.poll_votes.createIndex(
  { user_id: 1, date: 1 },
  { unique: true, name: 'poll_user_date_unique' }
);
db.poll_votes.createIndex({ date: 1 }, { name: 'poll_date' });
db.poll_votes.createIndex(
  { created_at: 1 },
  { expireAfterSeconds: 2592000, sparse: true, name: 'poll_ttl_30d' }  // 30 days
);

// ── Game: Memory Cards ────────────────────────────────────────────────────────
db.memory_scores.createIndex({ user_id: 1 }, { name: 'memory_user' });
db.memory_scores.createIndex({ moves: 1 }, { name: 'memory_moves_asc' });
db.memory_scores.createIndex({ user_id: 1, moves: 1 }, { name: 'memory_user_moves' });

// ── Game: Daily Spin ──────────────────────────────────────────────────────────
db.daily_spins.createIndex(
  { user_id: 1, date: 1 },
  { unique: true, name: 'spin_user_date_unique' }
);
db.daily_spins.createIndex({ date: 1 }, { name: 'spin_date' });
db.daily_spins.createIndex(
  { spun_at: 1 },
  { expireAfterSeconds: 7776000, sparse: true, name: 'spin_ttl_90d' }  // 90 days
);

// ── Discovery game sessions ───────────────────────────────────────────────────
db.discovery_game_sessions.createIndex({ session_id: 1 }, { unique: true, name: 'disc_session_unique' });
db.discovery_game_sessions.createIndex({ user_id: 1, started_at: -1 }, { name: 'disc_user_started' });
db.discovery_game_sessions.createIndex({ state: 1, updated_at: -1 }, { name: 'disc_state_updated' });
db.discovery_game_sessions.createIndex({ user_id: 1, state: 1 }, { name: 'disc_user_state' });
db.discovery_game_sessions.createIndex(
  { started_at: 1 },
  { expireAfterSeconds: 2592000, sparse: true, name: 'disc_ttl_30d' }  // 30 days
);

// ── Meal game sessions ────────────────────────────────────────────────────────
db.meal_game_sessions.createIndex(
  { user_id: 1, meal_id: 1 },
  { unique: true, name: 'meal_session_user_meal' }
);
db.meal_game_sessions.createIndex({ user_id: 1, started_at: -1 }, { name: 'meal_session_user_time' });
db.meal_game_sessions.createIndex(
  { started_at: 1 },
  { expireAfterSeconds: 2592000, sparse: true, name: 'meal_session_ttl_30d' }  // 30 days
);

// ── Meal selections ───────────────────────────────────────────────────────────
db.meal_selections.createIndex({ user_id: 1 }, { name: 'meal_user' });
db.meal_selections.createIndex({ week: 1 }, { name: 'meal_week' });
db.meal_selections.createIndex({ user_id: 1, week: 1 }, { name: 'meal_sel_user_week' });

// ── Meal leaderboard ──────────────────────────────────────────────────────────
db.meal_leaderboard.createIndex({ week: 1, score: -1 }, { name: 'meal_lb_week_score' });
db.meal_leaderboard.createIndex(
  { user_id: 1, week: 1 },
  { unique: true, name: 'meal_lb_user_week' }
);

// ── Discovery game ────────────────────────────────────────────────────────────
db.discovery_sessions.createIndex({ user_id: 1, status: 1 }, { name: 'discovery_user_status' });

// ── Assessment results ────────────────────────────────────────────────────────
db.assessment_results.createIndex({ user_id: 1, created_at: -1 }, { name: 'asr_user_time' });
db.assessment_results.createIndex({ user_id: 1, test_type: 1 },   { name: 'asr_user_type' });
db.assessment_results.createIndex({ user_id: 1, face_enriched: 1, test_type: 1 }, { name: 'asr_reenrich' });

// ── Diet coaching ─────────────────────────────────────────────────────────────
db.diet_recommendations.createIndex(
  { user_id: 1, date: 1 },
  { unique: true, name: 'diet_rec_user_date' }
);
db.diet_recommendations.createIndex({ user_id: 1, date: -1 }, { name: 'diet_rec_user_recent' });
db.diet_recommendations.createIndex(
  { updated_at: 1 },
  { expireAfterSeconds: 7776000, sparse: true, name: 'diet_rec_ttl_90d' }  // 90 days
);
db.diet_feedback.createIndex(
  { user_id: 1, meal_id: 1, date: 1 },
  { unique: true, name: 'diet_fb_user_meal_date' }
);
db.diet_feedback.createIndex({ user_id: 1, date: -1 }, { name: 'diet_fb_user_recent' });

print('✓ All indexes created successfully.');
