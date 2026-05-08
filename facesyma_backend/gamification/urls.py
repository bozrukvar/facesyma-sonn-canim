"""Gamification URL routing."""
from django.urls import path
from gamification import views, game_views

urlpatterns = [
    # Coins
    path('coins/balance/',      views.coin_balance,      name='gam-coin-balance'),
    path('coins/history/',      views.coin_history,      name='gam-coin-history'),
    path('coins/daily-quest/',  views.coin_daily_quest,  name='gam-daily-quest'),

    # Leaderboard
    path('leaderboard/',          views.leaderboard,           name='gam-leaderboard'),
    path('leaderboard/trending/', views.leaderboard_trending,  name='gam-leaderboard-trending'),
    path('leaderboard/trend/',    views.leaderboard_trend,     name='gam-leaderboard-trend'),

    # Badges
    path('badges/',                             views.badges_list,       name='gam-badges'),
    path('badges/user/',                        views.badges_user,       name='gam-badges-user'),
    path('badges/<str:badge_id>/leaderboard/',  views.badge_leaderboard, name='gam-badge-leaderboard'),

    # Challenges
    path('challenges/',                               views.challenges_list,     name='gam-challenges'),
    path('challenges/create/',                        views.challenges_create,   name='gam-challenges-create'),
    path('challenges/<str:challenge_id>/join/',       views.challenge_join,      name='gam-challenge-join'),
    path('challenges/<str:challenge_id>/score/',      views.challenge_score,     name='gam-challenge-score'),
    path('challenges/<str:challenge_id>/leaderboard/', views.challenge_leaderboard, name='gam-challenge-lb'),
    path('challenges/<str:challenge_id>/abandon/',    views.challenge_abandon,   name='gam-challenge-abandon'),

    # Missions
    path('missions/',                                  views.missions_list,       name='gam-missions'),
    path('missions/<str:mission_id>/join/',            views.mission_join,        name='gam-mission-join'),
    path('missions/<str:mission_id>/contribute/',      views.mission_contribute,  name='gam-mission-contribute'),
    path('missions/<str:mission_id>/leaderboard/',     views.mission_leaderboard, name='gam-mission-lb'),

    # Meal Game
    path('meal-game/weekly/',      views.meal_game_weekly,      name='gam-meal-weekly'),
    path('meal-game/select/',      views.meal_game_select,      name='gam-meal-select'),
    path('meal-game/guess-sifat/', views.meal_game_guess_sifat, name='gam-meal-guess'),
    path('meal-game/leaderboard/', views.meal_game_leaderboard, name='gam-meal-lb'),

    # Discovery Game
    path('discovery/types/',   views.discovery_types,  name='gam-discovery-types'),
    path('discovery/start/',   views.discovery_start,  name='gam-discovery-start'),
    path('discovery/answer/',  views.discovery_answer, name='gam-discovery-answer'),
    path('discovery/abandon/', views.discovery_abandon, name='gam-discovery-abandon'),

    # Sıfat Bul (Wordle)
    path('wordle/daily/',       game_views.wordle_daily,       name='gam-wordle-daily'),
    path('wordle/guess/',       game_views.wordle_guess,       name='gam-wordle-guess'),
    path('wordle/leaderboard/', game_views.wordle_leaderboard, name='gam-wordle-lb'),

    # Hızlı Eşleştir (Speed Match)
    path('speed-match/start/',       game_views.speed_match_start,       name='gam-speed-start'),
    path('speed-match/submit/',      game_views.speed_match_submit,      name='gam-speed-submit'),
    path('speed-match/leaderboard/', game_views.speed_match_leaderboard, name='gam-speed-lb'),

    # Topluluk Oyu (Daily Poll)
    path('poll/daily/', game_views.poll_daily, name='gam-poll-daily'),
    path('poll/vote/',  game_views.poll_vote,  name='gam-poll-vote'),

    # Hafıza Kartları (Memory Cards)
    path('memory/cards/',       game_views.memory_cards,       name='gam-memory-cards'),
    path('memory/complete/',    game_views.memory_complete,    name='gam-memory-complete'),
    path('memory/leaderboard/', game_views.memory_leaderboard, name='gam-memory-lb'),

    # Günlük Çark (Spin Wheel)
    path('spin/status/', game_views.spin_status, name='gam-spin-status'),
    path('spin/',        game_views.spin_wheel,  name='gam-spin'),
]
