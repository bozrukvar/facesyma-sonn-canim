"""Gamification views — all endpoints for the gamification sub-system."""
import json
import random
import string
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from admin_api.utils.mongo import _get_db
from gamification.models.badge import BADGE_DEFINITIONS
from gamification.models.discovery_game import DISCOVERY_GAME_TYPES
from gamification.services.badge_service import BadgeService, BadgeNotFoundError
from gamification.services.challenge_service import (
    ChallengeService, ChallengeNotFoundError, InvalidChallengeTypeError, UserAlreadyJoinedError,
)
from gamification.services.community_mission_service import (
    CommunityMissionService, MissionNotFoundError, MissionError,
)
from gamification.services.discovery_game_service import (
    DiscoveryGameService, GameTypeNotFoundError, SessionNotFoundError,
)
from gamification.services.hybrid_leaderboard_service import HybridLeaderboardService
from gamification.models.leaderboard import LeaderboardFilter
from gamification.services.leaderboard_trend_service import LeaderboardTrendService


_JWT_SECRET = settings.JWT_SECRET if hasattr(settings, 'JWT_SECRET') else settings.SECRET_KEY


def _get_user_id(request) -> int | None:
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = jwt.decode(auth.split(' ', 1)[1], _JWT_SECRET, algorithms=['HS256'])
        return payload.get('user_id')
    except Exception:
        return None


def _require_user(request):
    uid = _get_user_id(request)
    if not uid:
        return None, JsonResponse({'detail': 'Authentication required'}, status=401)
    return uid, None


def _get_username(user_id: int) -> str:
    try:
        db = _get_db()
        user = db['appfaceapi_myuser'].find_one({'id': user_id}, {'username': 1, '_id': 0})
        return user.get('username', f'user_{user_id}') if user else f'user_{user_id}'
    except Exception:
        return f'user_{user_id}'


def _add_xp(user_id: int, amount: int, reason: str) -> dict:
    """Add XP, record transaction. Returns level_progress dict."""
    from core.services.xp_service import XPService
    try:
        return XPService.add_xp(user_id, amount, reason)
    except Exception:
        return {'xp': 0, 'level': 1, 'xp_to_next': 100, 'level_progress': 0}


# backwards-compat alias used by game_views imports
def _add_coins(user_id: int, amount: int, reason: str) -> int:
    info = _add_xp(user_id, amount, reason)
    return info.get('xp', 0)


def _get_xp(user_id: int) -> dict:
    """Returns level_progress dict."""
    from core.services.xp_service import XPService, level_progress
    db = _get_db()
    user = db['appfaceapi_myuser'].find_one(
        {'id': user_id}, {'xp': 1, '_id': 0}
    )
    if not user:
        return level_progress(0)
    return level_progress(int(user.get('xp', 0)))


# ── XP & LEVEL ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def xp_balance(request):
    uid, err = _require_user(request)
    if err:
        return err
    from core.services.xp_service import XPService, XPReward
    try:
        stats = XPService.get_stats(uid)
    except Exception:
        from core.services.xp_service import level_progress
        stats = {**level_progress(0), 'streak_days': 0, 'last_daily_quest': None}
    db = _get_db()
    today = datetime.utcnow().strftime('%Y-%m-%d')
    quest_claimed = db['daily_quests'].find_one({'user_id': uid, 'date': today}) is not None
    return JsonResponse({
        'xp':              stats['xp'],
        'level':           stats['level'],
        'level_progress':  stats['level_progress'],
        'xp_to_next':      stats['xp_to_next'],
        'streak_days':     stats['streak_days'],
        'daily_quest_xp':  XPReward.DAILY_QUEST,
        'daily_quest_claimed': quest_claimed,
    })

# backwards-compat alias
coin_balance = xp_balance


@csrf_exempt
@require_http_methods(['GET'])
def xp_history(request):
    uid, err = _require_user(request)
    if err:
        return err
    limit  = min(int(request.GET.get('limit', 20)), 100)
    offset = int(request.GET.get('offset', 0))
    from core.services.xp_service import XPService
    try:
        docs, total = XPService.get_transaction_history(uid, limit=limit, offset=offset)
    except Exception:
        docs, total = [], 0
    return JsonResponse({'transactions': docs, 'total': total})

# backwards-compat alias
coin_history = xp_history


@csrf_exempt
@require_http_methods(['POST'])
def daily_quest(request):
    uid, err = _require_user(request)
    if err:
        return err
    from core.services.xp_service import XPService, XPReward
    db = _get_db()
    today = datetime.utcnow().strftime('%Y-%m-%d')
    existing = db['daily_quests'].find_one({'user_id': uid, 'date': today})
    if existing:
        try:
            info = XPService.get_stats(uid)
        except Exception:
            from core.services.xp_service import level_progress
            info = level_progress(0)
        return JsonResponse({'xp_earned': 0, 'message': 'already_claimed', 'xp': info['xp'], 'level': info['level']})
    xp_earned = XPReward.DAILY_QUEST
    db['daily_quests'].insert_one({'user_id': uid, 'date': today, 'claimed_at': datetime.utcnow().isoformat()})
    streak = XPService.update_daily_quest_streak(uid)
    info = _add_xp(uid, xp_earned, 'daily_quest')
    BadgeService.award_badge(uid, 'streak_keeper', 1)
    return JsonResponse({'xp_earned': xp_earned, 'message': 'claimed', 'xp': info['xp'], 'level': info['level'], 'streak_days': streak})

# backwards-compat alias
coin_daily_quest = daily_quest


# ── LEADERBOARD ────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def leaderboard(request):
    uid, err = _require_user(request)
    if err:
        return err
    lb_type = request.GET.get('type', 'global')
    limit = min(int(request.GET.get('limit', 50)), 200)
    offset = int(request.GET.get('offset', 0))
    sort_by = request.GET.get('sort_by', 'coins')
    time_period = request.GET.get('time_period', 'all_time')
    trait_id = request.GET.get('trait_id')
    community_id = request.GET.get('community_id')

    lb_filter = LeaderboardFilter(
        leaderboard_type=lb_type,
        trait_id=trait_id,
        community_id=community_id,
        time_period=time_period,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )
    result = HybridLeaderboardService.get_hybrid_leaderboard(lb_filter, uid)
    entries = [
        {
            'rank': e.rank,
            'user_id': e.user_id,
            'username': e.username,
            'xp': e.coins_balance,
            'total_xp': e.total_coins_earned,
            'platinum_badges': e.platinum_badges,
            'challenges_won': e.challenges_won,
            'meals_completed': e.meals_completed,
            'avg_accuracy': e.avg_accuracy,
        }
        for e in result.entries
    ]
    return JsonResponse({
        'entries': entries,
        'total': result.total_entries,
        'user_rank': result.user_rank,
        'leaderboard_type': result.leaderboard_type,
    })


@csrf_exempt
@require_http_methods(['GET'])
def leaderboard_trending(request):
    uid, err = _require_user(request)
    if err:
        return err
    days = int(request.GET.get('days', 7))
    limit = min(int(request.GET.get('limit', 20)), 100)
    trending = LeaderboardTrendService.get_trending_users(days=days, limit=limit)
    return JsonResponse({'trending': trending})


@csrf_exempt
@require_http_methods(['GET'])
def leaderboard_trend(request):
    uid, err = _require_user(request)
    if err:
        return err
    days = int(request.GET.get('days', 30))
    try:
        resp = LeaderboardTrendService.get_user_trend(uid, days=days)
        return JsonResponse({
            'rank_change':  resp.rank_change,
            'xp_gained':    resp.coins_gained,
            'current_rank': resp.current_rank,
            'current_xp':   resp.current_coins,
        })
    except Exception:
        info = _get_xp(uid)
        return JsonResponse({'rank_change': 0, 'xp_gained': 0, 'current_rank': None, 'current_xp': info.get('xp', 0)})


# ── BADGES ─────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def badges_list(request):
    uid, err = _require_user(request)
    if err:
        return err
    badges = BadgeService.list_all_badges()
    data = [
        {
            'badge_id': b.badge_id,
            'name': b.name_en,
            'name_tr': b.name_tr,
            'description': b.description_en,
            'description_tr': b.description_tr,
            'icon_emoji': '🏅',
            'game_type': b.game_type,
            'category': b.category,
            'tiers': [{'tier': t.tier, 'level': t.level, 'threshold': t.threshold} for t in (b.tiers or [])],
            'xp_reward_per_tier': b.coin_reward_per_tier,
        }
        for b in badges
    ]
    return JsonResponse({'badges': data})


@csrf_exempt
@require_http_methods(['GET'])
def badges_user(request):
    uid, err = _require_user(request)
    if err:
        return err
    user_badges = BadgeService.get_user_badges(uid)
    return JsonResponse({'badges': user_badges})


@csrf_exempt
@require_http_methods(['GET'])
def badge_leaderboard(request, badge_id: str):
    uid, err = _require_user(request)
    if err:
        return err
    limit = min(int(request.GET.get('limit', 50)), 200)
    try:
        entries = BadgeService.get_badge_leaderboard(badge_id, limit=limit)
        data = [
            {
                'rank': e.rank,
                'user_id': e.user_id,
                'username': e.username,
                'current_tier': e.current_tier,
                'current_progress': e.current_progress,
            }
            for e in entries
        ]
        return JsonResponse({'entries': data})
    except BadgeNotFoundError:
        return JsonResponse({'detail': 'Badge not found'}, status=404)


# ── CHALLENGES ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def challenges_list(request):
    uid, err = _require_user(request)
    if err:
        return err
    limit = min(int(request.GET.get('limit', 20)), 100)
    docs, total = ChallengeService.get_active_challenges(uid, limit=limit)
    for d in docs:
        d.setdefault('participants', [])
    return JsonResponse({'challenges': docs, 'total': total})


@csrf_exempt
@require_http_methods(['POST'])
def challenges_create(request):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    username = _get_username(uid)

    class Req:
        type_id = body.get('type_id', 'accuracy_duel')
        title = body.get('title', 'New Challenge')
        description = body.get('description', '')
        visibility = body.get('visibility', 'public')
        leaderboard_mode = body.get('leaderboard_mode', 'score')
        is_handicapped = body.get('is_handicapped', False)
        duration_minutes = body.get('duration_minutes') or body.get('duration_hours', 24) * 60

    try:
        challenge_id, start, end = ChallengeService.create_challenge(uid, username, None, Req())
        db = _get_db()
        ch = db['social_challenges'].find_one({'challenge_id': challenge_id}, {'_id': 0})
        return JsonResponse({'challenge_id': challenge_id, 'challenge': ch or {}}, status=201)
    except InvalidChallengeTypeError as e:
        return JsonResponse({'detail': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['POST'])
def challenge_join(request, challenge_id: str):
    uid, err = _require_user(request)
    if err:
        return err
    username = _get_username(uid)
    try:
        ChallengeService.join_challenge(challenge_id, uid, username, None, None)
        db = _get_db()
        ch = db['social_challenges'].find_one({'challenge_id': challenge_id}, {'_id': 0})
        return JsonResponse({'success': True, 'challenge': ch or {}})
    except ChallengeNotFoundError:
        return JsonResponse({'detail': 'Challenge not found'}, status=404)
    except UserAlreadyJoinedError:
        return JsonResponse({'detail': 'already_joined'}, status=409)


@csrf_exempt
@require_http_methods(['POST'])
def challenge_score(request, challenge_id: str):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    score_delta = int(body.get('score', 0))
    try:
        new_score, rank = ChallengeService.update_score(challenge_id, uid, score_delta)
        return JsonResponse({'success': True, 'new_score': new_score, 'current_rank': rank})
    except ChallengeNotFoundError:
        return JsonResponse({'detail': 'Challenge not found'}, status=404)
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['GET'])
def challenge_leaderboard(request, challenge_id: str):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        entries = ChallengeService.get_leaderboard(challenge_id)
        data = [
            {'rank': e.rank, 'user_id': e.user_id, 'username': e.username, 'score': e.score}
            for e in entries
        ]
        return JsonResponse({'entries': data})
    except ChallengeNotFoundError:
        return JsonResponse({'detail': 'Challenge not found'}, status=404)


@csrf_exempt
@require_http_methods(['POST'])
def challenge_abandon(request, challenge_id: str):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        penalty = ChallengeService.cancel_challenge(challenge_id, uid)
        return JsonResponse({'success': True, 'penalty': penalty})
    except ChallengeNotFoundError:
        return JsonResponse({'detail': 'Challenge not found'}, status=404)


# ── MISSIONS ───────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def missions_list(request):
    uid, err = _require_user(request)
    if err:
        return err
    limit = min(int(request.GET.get('limit', 10)), 50)
    community_id = request.GET.get('community_id')
    missions = CommunityMissionService.get_active_missions(community_id=community_id, limit=limit)
    return JsonResponse({'missions': missions})


@csrf_exempt
@require_http_methods(['POST'])
def mission_join(request, mission_id: str):
    uid, err = _require_user(request)
    if err:
        return err
    username = _get_username(uid)
    try:
        mission = CommunityMissionService.join_mission(uid, mission_id, username)
        return JsonResponse({'success': True, 'mission': mission})
    except MissionNotFoundError:
        return JsonResponse({'detail': 'Mission not found'}, status=404)
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['POST'])
def mission_contribute(request, mission_id: str):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    contribution = int(body.get('contribution', 1))
    try:
        new_progress, progress_percent = CommunityMissionService.contribute(mission_id, uid, contribution)
        db = _get_db()
        mission = db['community_missions'].find_one({'mission_id': mission_id}, {'target_value': 1, 'status': 1, '_id': 0})
        is_complete = (mission or {}).get('status') == 'completed'
        xp_earned = 0
        if is_complete:
            from core.services.xp_service import XPReward
            info = _add_xp(uid, XPReward.MISSION_CONTRIB, f'mission_complete_{mission_id}')
            xp_earned = XPReward.MISSION_CONTRIB
            BadgeService.award_badge(uid, 'mission_hero', 1)
        return JsonResponse({
            'new_progress':    new_progress,
            'progress_percent': progress_percent,
            'is_complete':     is_complete,
            'xp_earned':       xp_earned,
        })
    except MissionNotFoundError:
        return JsonResponse({'detail': 'Mission not found'}, status=404)
    except MissionError as e:
        return JsonResponse({'detail': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['GET'])
def mission_leaderboard(request, mission_id: str):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        entries = CommunityMissionService.get_mission_leaderboard(mission_id)
        return JsonResponse({'entries': entries})
    except MissionNotFoundError:
        return JsonResponse({'detail': 'Mission not found'}, status=404)


# ── MEAL GAME ──────────────────────────────────────────────────────────────────

_MEAL_DATA = {
    'TR': {
        'name': 'Türkiye',
        'meals': [
            {'id': 'tr_kebap',    'name': 'Adana Kebap',      'description': 'Acılı kıyma kebabı',        'sifat': 'Baskın',     'coin_cost': 5, 'reason': 'Keskin baharat ve güçlü lezzet — sofrada söz hakkını alan baskın karakterlerin yemeği.'},
            {'id': 'tr_lahmacun', 'name': 'Lahmacun',         'description': 'Kıymalı ince hamur',        'sifat': 'Enerjik',    'coin_cost': 3, 'reason': 'İnce, hızlı ve dolu dolu — durmaksızın hareket eden enerjik ruhları çağrıştırır.'},
            {'id': 'tr_baklava',  'name': 'Baklava',          'description': 'Fıstıklı kat kat tatlı',    'sifat': 'Yaratıcı',   'coin_cost': 4, 'reason': 'Kırk kat yufka ve hassas tat dengesi, yaratıcı zekanın mutfaktaki yansımasıdır.'},
            {'id': 'tr_meze',     'name': 'Meze Tabağı',      'description': 'Paylaşımlık karışık mezeler','sifat': 'Sosyal',     'coin_cost': 3, 'reason': 'Paylaşmak için var olan, sofrayı bir araya getiren Türk sosyal ritüelinin özüdür.'},
            {'id': 'tr_corba',    'name': 'Mercimek Çorbası', 'description': 'Kırmızı mercimek çorbası',  'sifat': 'Nazik',      'coin_cost': 2, 'reason': 'Sıcak ve besleyici yapısıyla şefkatin ve özenli ilginin simgesidir.'},
            {'id': 'tr_iskender', 'name': 'İskender Kebap',   'description': 'Yoğurtlu et ve tereyağ',   'sifat': 'Karizmatik', 'coin_cost': 6, 'reason': 'Efsanevi sunumu ve çok katmanlı lezzetiyle girdiği her ortamda fark yaratan bir yemek.'},
            {'id': 'tr_manti',    'name': 'Mantı',            'description': 'Minik et dolu hamur',       'sifat': 'Analitik',   'coin_cost': 4, 'reason': 'Her küçük parçanın özenle katlanması, sabır ve detay odaklı analitik zihni simgeler.'},
            {'id': 'tr_simit',    'name': 'Simit',            'description': 'Susamlı halka ekmek',       'sifat': 'Empatik',    'coin_cost': 2, 'reason': 'Herkese açık, sade ve paylaşımcı — tam anlamıyla empatik bir yaklaşımın simgesidir.'},
        ],
    },
    'JP': {
        'name': 'Japonya',
        'meals': [
            {'id': 'jp_sushi',    'name': 'Sushi',         'description': 'Pirincli balık dilimleri',  'sifat': 'Analitik',   'coin_cost': 6, 'reason': 'Her parçanın milimetrik dengesi ve minimalist sunumu analitik mükemmeliyetçiliği yansıtır.'},
            {'id': 'jp_ramen',    'name': 'Ramen',         'description': 'Derin et sulu noodle',      'sifat': 'İçe dönük',  'coin_cost': 4, 'reason': 'Saatlerce süren derin et suyu hazırlığı, içe kapanık düşünce derinliğini temsil eder.'},
            {'id': 'jp_tempura',  'name': 'Tempura',       'description': 'Çıtır kızarmış deniz ürünleri', 'sifat': 'Yaratıcı', 'coin_cost': 5, 'reason': 'Sıradan malzemeleri altın çıtırlığa dönüştürmek — yaratıcı dönüşümün mutfaktaki halidir.'},
            {'id': 'jp_onigiri',  'name': 'Onigiri',       'description': 'Sevgiyle sarılmış pirinç topu', 'sifat': 'Nazik',   'coin_cost': 2, 'reason': 'Basit, besleyici ve elle sarılmış — saf nezaketi ve özenli ilgiyi yansıtır.'},
            {'id': 'jp_miso',     'name': 'Miso Çorbası',  'description': 'Geleneksel fermente çorba', 'sifat': 'Empatik',    'coin_cost': 3, 'reason': 'Sabah ritüeli olarak aile ile paylaşılan bu çorba, duygusal bağı ve sıcaklığı güçlendirir.'},
            {'id': 'jp_takoyaki', 'name': 'Takoyaki',      'description': 'Ahtapotlu hamur topları',   'sifat': 'Sosyal',     'coin_cost': 3, 'reason': 'Açık mutfaklarda birlikte yapılan bu sokak lezzeti sosyal enerjinin ve paylaşımın simgesidir.'},
            {'id': 'jp_wagyu',    'name': 'Wagyu Biftek',  'description': 'Mermer etli premium biftek', 'sifat': 'Baskın',    'coin_cost': 8, 'reason': 'En yüksek kalite standardı ve derin güç — baskın ve iddialı kişiliği temsil eder.'},
        ],
    },
    'IT': {
        'name': 'İtalya',
        'meals': [
            {'id': 'it_pizza',     'name': 'Pizza Margherita', 'description': 'Domates ve mozzarella',   'sifat': 'Sosyal',     'coin_cost': 4, 'reason': 'Herkesin etrafında toplandığı, paylaşım ve birliktelik kültürünün simgesidir.'},
            {'id': 'it_pasta',     'name': 'Pasta Carbonara',  'description': 'Kremalı yumurtalı makarna','sifat': 'Empatik',   'coin_cost': 4, 'reason': 'Sıcak ve sarıcı dokusu, insan bağlarının sıcaklığını ve derinliğini simgeler.'},
            {'id': 'it_gelato',    'name': 'Gelato',           'description': 'Kadifemsi İtalyan dondurması','sifat': 'Yaratıcı','coin_cost': 3, 'reason': 'Sonsuz renk ve aroma kombinasyonları, özgür ve renkli yaratıcılığı çağrıştırır.'},
            {'id': 'it_risotto',   'name': 'Risotto',          'description': 'Kremsi pirinç yemeği',    'sifat': 'Analitik',   'coin_cost': 5, 'reason': 'Her taneyi ayrı ayrı pişirme sabrı ve hassasiyeti, analitik ve metodolojik zihni simgeler.'},
            {'id': 'it_ossobuco',  'name': 'Osso Buco',        'description': 'Uzun pişirilmiş dana incik','sifat': 'Nazik',    'coin_cost': 6, 'reason': 'Saatlerce kısık ateşte pişmesi, sabır ve şefkatle ilgilenen nazik karakterleri yansıtır.'},
            {'id': 'it_tiramisu',  'name': 'Tiramisù',         'description': 'Kahve ve maskarpone tatlı', 'sifat': 'Romantik',  'coin_cost': 5, 'reason': 'Kahve, krem ve kakao katmanları — romantik karmaşıklığın ve derinliğin özeti.'},
            {'id': 'it_focaccia',  'name': 'Focaccia',         'description': 'Zeytinyağlı aromatik ekmek','sifat': 'Karizmatik','coin_cost': 3, 'reason': 'Gösterişli görünüşü ve dayanılmaz aromasıyla ortama hakim olan karizmatik bir varlık.'},
        ],
    },
    'MX': {
        'name': 'Meksika',
        'meals': [
            {'id': 'mx_taco',       'name': 'Taco',       'description': 'Tortilla ile baharatlı et',  'sifat': 'Enerjik',  'coin_cost': 3, 'reason': 'Hızlı, renkli ve canlı — durmak bilmeyen enerjik ruhu tam olarak yansıtır.'},
            {'id': 'mx_guacamole',  'name': 'Guacamole',  'description': 'Taze avokado sosu',          'sifat': 'Sosyal',   'coin_cost': 2, 'reason': 'Herkesin paylaştığı, sohbet başlatan ve masayı bir araya getiren sosyal bir dip sosu.'},
            {'id': 'mx_enchilada',  'name': 'Enchilada',  'description': 'Acı soslu fırın tortilla',   'sifat': 'Baskın',   'coin_cost': 4, 'reason': 'Keskin sos ve dominant lezzet profiliyle masada söz sahibi olan güçlü bir yemek.'},
            {'id': 'mx_churro',     'name': 'Churro',     'description': 'Tarçınlı kızarmış hamur',    'sifat': 'Yaratıcı', 'coin_cost': 2, 'reason': 'Sade hamuru altın ve neşeli bir lezzete dönüştürmek — yaratıcı oyunculuğun simgesi.'},
            {'id': 'mx_pozole',     'name': 'Pozole',     'description': 'Mısır taneli et çorbası',    'sifat': 'Empatik',  'coin_cost': 4, 'reason': 'Aile ve arkadaş toplantılarında paylaşılan bu çorba, derin duygusal bağı simgeler.'},
            {'id': 'mx_mole',       'name': 'Mole Negro', 'description': '30+ baharatlı karmaşık sos', 'sifat': 'Analitik', 'coin_cost': 6, 'reason': 'Otuzdan fazla malzemenin hassas dengesiyle hazırlanan bu sos, analitik ustalığın simgesidir.'},
        ],
    },
    'IN': {
        'name': 'Hindistan',
        'meals': [
            {'id': 'in_curry',   'name': 'Butter Chicken',  'description': 'Kadifemsi tavuk köri',      'sifat': 'Empatik',    'coin_cost': 5, 'reason': 'Kadifemsi sos ve sarıcı sıcaklığı, kucaklayıcı ve duygusal sıcaklığı temsil eder.'},
            {'id': 'in_biryani', 'name': 'Biryani',         'description': 'Onlarca baharat pirinç',    'sifat': 'Yaratıcı',   'coin_cost': 5, 'reason': 'Onlarca baharatın uyumlu dansı ve katmanlı karmaşıklığı yaratıcı zekayı simgeler.'},
            {'id': 'in_samosa',  'name': 'Samosa',          'description': 'Üçgen kızarmış börek',      'sifat': 'Analitik',   'coin_cost': 2, 'reason': 'Geometrik form içine hassasiyetle yerleştirilmiş iç harç — analitik düzeni yansıtır.'},
            {'id': 'in_naan',    'name': 'Naan',            'description': 'Tandırda pişmiş ekmek',     'sifat': 'Nazik',      'coin_cost': 2, 'reason': 'Her sofrada sıcacık sunulan bu ekmek, karşılama kültürünü ve nazik ilgiyi temsil eder.'},
            {'id': 'in_dal',     'name': 'Dal Tadka',       'description': 'Sarı mercimek körisi',      'sifat': 'İçe dönük',  'coin_cost': 3, 'reason': 'Sade görünüşünün ardında derin ve zengin lezzetiyle içe dönük ruhun yemeğidir.'},
            {'id': 'in_chai',    'name': 'Masala Çayı',     'description': 'Baharatlı süt çayı',        'sifat': 'Sosyal',     'coin_cost': 2, 'reason': 'Hint evlerinde misafir ağırlama ritüeli — sosyal bağın ve sıcak karşılamanın simgesi.'},
            {'id': 'in_gulab',   'name': 'Gulab Jamun',     'description': 'Şurupta yüzen tatlı toplar','sifat': 'Romantik',   'coin_cost': 3, 'reason': 'Şurupta yüzen yumuşak toplar, romantik yumuşaklığı ve tatlı duygusallığı simgeler.'},
        ],
    },
    'FR': {
        'name': 'Fransa',
        'meals': [
            {'id': 'fr_croissant',    'name': 'Croissant',         'description': 'Kat kat tereyağlı börek',     'sifat': 'Yaratıcı',   'coin_cost': 4, 'reason': 'Yüzlerce kat yufkanın hassas büküm tekniği, yaratıcı ustalığın ve özgünlüğün simgesidir.'},
            {'id': 'fr_coqauvin',     'name': 'Coq au Vin',        'description': 'Şarapta pişen tavuk',         'sifat': 'Romantik',   'coin_cost': 6, 'reason': 'Saatlerce şarapta demlenen bu yemek, Fransız romantizminin mutfaktaki zarif yansımasıdır.'},
            {'id': 'fr_souffle',      'name': 'Soufflé',           'description': 'Hassas fırın tatlısı',        'sifat': 'Analitik',   'coin_cost': 7, 'reason': 'Milimetrik sıcaklık ve zamanlama hassasiyeti gerektiren bu tatlı, analitik mükemmeliyetçiliği temsil eder.'},
            {'id': 'fr_ratatouille',  'name': 'Ratatouille',       'description': 'Sebze güveç',                 'sifat': 'Empatik',    'coin_cost': 4, 'reason': 'Her sebzenin uyumlu birlikteliği, farklılıkları anlayan ve kucaklayan empatiyi simgeler.'},
            {'id': 'fr_macaron',      'name': 'Macaron',           'description': 'Rengarenk badem kurabiyesi',  'sifat': 'Karizmatik', 'coin_cost': 5, 'reason': 'Canlı renkleri ve çekici görünüşüyle girdiği her ortamda dikkati üzerine çeken karizmatik bir tatlı.'},
            {'id': 'fr_bouillabaisse','name': 'Bouillabaisse',     'description': 'Deniz ürünlü balıkçı çorbası','sifat': 'Sosyal',    'coin_cost': 6, 'reason': 'Balıkçı ailelerinin birlikte paylaştığı bu çorba, topluluk ve dayanışma ruhunu simgeler.'},
        ],
    },
    'KR': {
        'name': 'Kore',
        'meals': [
            {'id': 'kr_kimchi',     'name': 'Kimchi',          'description': 'Fermente baharatlı lahana',    'sifat': 'Baskın',     'coin_cost': 3, 'reason': 'Güçlü fermente aroma ve keskin acılık — cesaretli ve baskın karakterlerin simgesidir.'},
            {'id': 'kr_bibimbap',   'name': 'Bibimbap',        'description': 'Renkli karışık pirinç kasesi', 'sifat': 'Yaratıcı',   'coin_cost': 4, 'reason': 'Onlarca rengi ve tadı tek kapta özgürce harmanlayan yaratıcı ifade özgürlüğünün simgesi.'},
            {'id': 'kr_tteokbokki','name': 'Tteokbokki',      'description': 'Acı soslu pirinç keki',        'sifat': 'Enerjik',    'coin_cost': 3, 'reason': 'Kırmızı ateşli sos ve çiğnenebilir doku — patlamaya hazır enerjiyi ve tutkuyu simgeler.'},
            {'id': 'kr_bulgogi',    'name': 'Bulgogi',         'description': 'Marine edilmiş ızgara et',    'sifat': 'Empatik',    'coin_cost': 5, 'reason': 'Sofra etrafında birlikte pişirme ritüeli, Kore\'nin misafirperver ve sıcak ruhunu simgeler.'},
            {'id': 'kr_japchae',    'name': 'Japchae',         'description': 'Cam şehriyeli sebze yemeği',  'sifat': 'Analitik',   'coin_cost': 4, 'reason': 'Her malzemenin ayrı ayrı pişirilip hassas bir araya getirilmesi analitik düşünceyi yansıtır.'},
            {'id': 'kr_sundubu',    'name': 'Sundubu Jjigae',  'description': 'Yumuşak tofulu güveç',        'sifat': 'Nazik',      'coin_cost': 3, 'reason': 'İpek gibi yumuşak tofu ve hafif dokusu, şefkati ve nazik ilgiyi simgeler.'},
        ],
    },
    'CN': {
        'name': 'Çin',
        'meals': [
            {'id': 'cn_peking',   'name': 'Pekin Ördeği',    'description': 'Törensel fırın ördeği',        'sifat': 'Karizmatik', 'coin_cost': 8, 'reason': 'Törensel sunumu ve görkemli lezzetiyle masada tartışmasız karizmatik bir varlık oluşturur.'},
            {'id': 'cn_dimsum',   'name': 'Dim Sum',         'description': 'Paylaşımlık küçük porsiyonlar','sifat': 'Sosyal',    'coin_cost': 4, 'reason': 'Birlikte sipariş edilen küçük porsiyonlar, sosyal bağı ve paylaşım kültürünü güçlendirir.'},
            {'id': 'cn_kungpao',  'name': 'Kung Pao Tavuk',  'description': 'Fıstıklı acılı wok yemeği',   'sifat': 'Enerjik',   'coin_cost': 4, 'reason': 'Fıstık ve ateşli baharatın patlaması — yüksek enerjili ve dinamik kişiliği simgeler.'},
            {'id': 'cn_mapo',     'name': 'Mapo Tofu',       'description': 'Uyuşturucu acılı tofu',       'sifat': 'Baskın',    'coin_cost': 4, 'reason': 'Sichuan biberi ve dominant lezzet profiliyle sofrada kolayca hakim olan güçlü bir yemek.'},
            {'id': 'cn_wonton',   'name': 'Wonton Çorbası',  'description': 'Etli hamur mantısı çorbası',  'sifat': 'Nazik',     'coin_cost': 3, 'reason': 'Hassasiyetle katlanmış küçük paketler, nazik ilgiyi ve özenli düşünceyi simgeler.'},
            {'id': 'cn_zhajiang', 'name': 'Zhajiang Mian',   'description': 'Soya soslu koyun eti ile noodle','sifat': 'İçe dönük','coin_cost': 3, 'reason': 'Sade dış görünüşü altında derin umami katmanları — içe dönük zenginliği ve derinliği temsil eder.'},
        ],
    },
    'GR': {
        'name': 'Yunanistan',
        'meals': [
            {'id': 'gr_moussaka',     'name': 'Moussaka',       'description': 'Patlıcanlı et güveci',         'sifat': 'Empatik',    'coin_cost': 5, 'reason': 'Katmanlar halinde sevgiyle pişirilen bu yemek, derinden hissettirme ve özen sanatını temsil eder.'},
            {'id': 'gr_souvlaki',     'name': 'Souvlaki',       'description': 'Sokak şiş eti',                'sifat': 'Sosyal',     'coin_cost': 3, 'reason': 'Sokaklarda paylaşılan ve sohbet açan bu şiş et, Yunan sosyal ruhunun simgesidir.'},
            {'id': 'gr_spanakopita',  'name': 'Spanakopita',    'description': 'Ispanaklı peynirli börek',     'sifat': 'Analitik',   'coin_cost': 4, 'reason': 'Katman katman yufkanın hassas dengesi ve iç harcın titiz hazırlanması analitik düşünceyi yansıtır.'},
            {'id': 'gr_tzatziki',     'name': 'Tzatziki',       'description': 'Yoğurtlu salatalık sosu',      'sifat': 'Nazik',      'coin_cost': 2, 'reason': 'Serinletici ve yumuşatıcı yapısıyla sertliği gidiren nazik karakteri simgeler.'},
            {'id': 'gr_loukoumades',  'name': 'Loukoumades',    'description': 'Ballı çıtır hamur topları',    'sifat': 'Yaratıcı',   'coin_cost': 3, 'reason': 'Bal, tarçın ve çeşitli toppinglerle özgürce süslenen bu tatlı, oyuncu yaratıcılığı simgeler.'},
        ],
    },
    'TH': {
        'name': 'Tayland',
        'meals': [
            {'id': 'th_padthai',  'name': 'Pad Thai',          'description': 'Wok\'ta karideslı noodle',     'sifat': 'Sosyal',     'coin_cost': 4, 'reason': 'Tayland sokaklarında herkesin omuz omuza paylaştığı bu wok yemeği sosyal enerjinin simgesidir.'},
            {'id': 'th_tomyum',   'name': 'Tom Yum',           'description': 'Ekşi acı limon otlu çorba',    'sifat': 'Enerjik',    'coin_cost': 4, 'reason': 'Limon otu ve acının keskin dansı, diri, enerjik ve canlı bir ruhu temsil eder.'},
            {'id': 'th_greencurry','name': 'Green Curry',      'description': 'Yeşil biber ve Hindistan cevizi','sifat': 'Yaratıcı', 'coin_cost': 5, 'reason': 'Otuzdan fazla aromanın renk ve tat senfonisi — yaratıcı uyumun mutfaktaki göstergesidir.'},
            {'id': 'th_mango',    'name': 'Mango Sticky Rice', 'description': 'Tatlı mango ve yapışkan pirinç','sifat': 'Romantik',  'coin_cost': 3, 'reason': 'Tatlı mango ve kremsi pirinç birlikteliği, romantik uyumu ve yumuşaklığı simgeler.'},
            {'id': 'th_somtum',   'name': 'Som Tum',           'description': 'Ezilmiş yeşil papaya salatası','sifat': 'Baskın',    'coin_cost': 3, 'reason': 'Papayayı ezdiren güçlü el ve dominant tat profili — baskın ve iddialı kişiliğin simgesidir.'},
        ],
    },
    'ES': {
        'name': 'İspanya',
        'meals': [
            {'id': 'es_paella',   'name': 'Paella',            'description': 'Deniz ürünlü safran pirinci',  'sifat': 'Sosyal',     'coin_cost': 6, 'reason': 'Büyük tavada herkes için hazırlanan bu yemek, İspanyol \'fiesta\' ruhunu ve birlikteliği simgeler.'},
            {'id': 'es_gazpacho', 'name': 'Gazpacho',          'description': 'Soğuk domates çorbası',       'sifat': 'Analitik',   'coin_cost': 3, 'reason': 'Sıcak havada soğuk düşünme — sezgisel olmak yerine metodolojik çözüm üretmeyi simgeler.'},
            {'id': 'es_churros',  'name': 'Churros',           'description': 'Çikolata soslu kızarmış hamur','sifat': 'Enerjik',   'coin_cost': 3, 'reason': 'Çıtır çıtır, neşeli ve renkli — enerjik sabah ruhunun ve coşkunun simgesidir.'},
            {'id': 'es_jamon',    'name': 'Jamón Ibérico',     'description': 'Yıllarca olgunlaşmış ham',    'sifat': 'Karizmatik', 'coin_cost': 8, 'reason': 'Yıllarca olgunlaşarak güçlenen bu eşsiz jambon, zamanla derinleşen karizmayı simgeler.'},
            {'id': 'es_tortilla', 'name': 'Tortilla Española', 'description': 'Patatesli İspanyol omleti',   'sifat': 'Nazik',      'coin_cost': 3, 'reason': 'Sade, besleyici ve ev sıcaklığını taşıyan bu omlet nazik ve samimi karakterleri simgeler.'},
        ],
    },
}

_COUNTRY_ROTATION = ['TR', 'JP', 'IT', 'MX', 'IN', 'FR', 'KR', 'CN', 'GR', 'TH', 'ES']


def _get_weekly_country(country_code=None):
    if country_code and country_code.upper() in _MEAL_DATA:
        code = country_code.upper()
    else:
        week_num = datetime.utcnow().isocalendar()[1]
        code = _COUNTRY_ROTATION[week_num % len(_COUNTRY_ROTATION)]
    week_key = datetime.utcnow().strftime('%Y-W%V')
    data = _MEAL_DATA[code]
    meals = [
        {'id': m['id'], 'name': m['name'], 'description': m['description'], 'xp_reward': m.get('coin_cost', 3) * 10}
        for m in data['meals']
    ]
    return code, data['name'], week_key, meals


@csrf_exempt
@require_http_methods(['GET'])
def meal_game_weekly(request):
    uid, err = _require_user(request)
    if err:
        return err
    country_code = request.GET.get('country')
    code, country_name, week_key, meals = _get_weekly_country(country_code)
    return JsonResponse({'country': country_name, 'country_code': code, 'meals': meals, 'week_key': week_key})


@csrf_exempt
@require_http_methods(['POST'])
def meal_game_select(request):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    meal_id = body.get('meal_id', '')
    country_code = body.get('country', '')
    code, _, _, meals = _get_weekly_country(country_code)
    meal = next((m for m in _MEAL_DATA.get(code, {}).get('meals', []) if m['id'] == meal_id), None)
    if not meal:
        return JsonResponse({'error': 'Meal not found'}, status=404)
    db = _get_db()
    db['meal_game_sessions'].update_one(
        {'user_id': uid, 'meal_id': meal_id},
        {'$set': {'user_id': uid, 'meal_id': meal_id, 'country': code, 'started_at': datetime.utcnow().isoformat(), 'guessed': False}},
        upsert=True,
    )
    return JsonResponse({'success': True, 'xp_reward': meal.get('coin_cost', 3) * 10})


@csrf_exempt
@require_http_methods(['POST'])
def meal_game_guess_sifat(request):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    meal_id = body.get('meal_id', '')
    country_code = body.get('country', '')
    guess = body.get('guess', '')
    code, _, _, _ = _get_weekly_country(country_code)
    meal = next((m for m in _MEAL_DATA.get(code, {}).get('meals', []) if m['id'] == meal_id), None)
    if not meal:
        return JsonResponse({'error': 'Meal not found'}, status=404)
    correct_sifat = meal.get('sifat', '')
    correct = guess.strip() == correct_sifat.strip()
    xp_earned = 0
    xp_info = {}
    if correct:
        from core.services.xp_service import XPReward
        xp_earned = XPReward.MEAL_CORRECT
        xp_info = _add_xp(uid, xp_earned, f'meal_guess_correct_{meal_id}')
        BadgeService.award_badge(uid, 'meal_adventurous_eater', 1)
    else:
        from core.services.xp_service import XPReward
        xp_earned = XPReward.MEAL_WRONG
        xp_info = _add_xp(uid, xp_earned, f'meal_guess_wrong_{meal_id}')
    db = _get_db()
    db['meal_game_sessions'].update_one(
        {'user_id': uid, 'meal_id': meal_id},
        {'$set': {'guessed': True, 'guess': guess, 'correct': correct, 'guessed_at': datetime.utcnow().isoformat()}},
    )
    db['appfaceapi_myuser'].update_one(
        {'id': uid},
        {'$inc': {'meals_completed': 1}},
    )
    return JsonResponse({
        'correct':       correct,
        'xp_earned':     xp_earned,
        'correct_sifat': correct_sifat,
        'reason':        meal.get('reason', ''),
        'xp':            xp_info.get('xp', 0),
        'level':         xp_info.get('level', 1),
    })


@csrf_exempt
@require_http_methods(['GET'])
def meal_game_leaderboard(request):
    uid, err = _require_user(request)
    if err:
        return err
    limit = min(int(request.GET.get('limit', 20)), 100)
    db = _get_db()
    pipeline = [
        {'$match': {'correct': True}},
        {'$group': {'_id': '$user_id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': limit},
    ]
    docs = list(db['meal_game_sessions'].aggregate(pipeline))
    user_ids = [d['_id'] for d in docs]
    users = {
        u['id']: u['username']
        for u in db['appfaceapi_myuser'].find({'id': {'$in': user_ids}}, {'id': 1, 'username': 1, '_id': 0})
    }
    entries = [
        {
            'rank': i + 1,
            'user_id': d['_id'],
            'username': users.get(d['_id'], f"user_{d['_id']}"),
            'xp_earned': d['count'] * 50,
            'accuracy_percent': 100.0,
        }
        for i, d in enumerate(docs)
    ]
    return JsonResponse({'entries': entries})


# ── DISCOVERY GAME ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def discovery_types(request):
    uid, err = _require_user(request)
    if err:
        return err
    game_types = [
        {
            'game_type_id': gt.game_type_id,
            'name': gt.name_en,
            'name_tr': gt.name_tr,
            'description': gt.description_en,
            'description_tr': gt.description_tr,
            'xp_reward_play': gt.coin_reward_play,
            'xp_reward_win':  gt.coin_reward_win,
        }
        for gt in DISCOVERY_GAME_TYPES.values()
    ]
    return JsonResponse({'game_types': game_types})


@csrf_exempt
@require_http_methods(['POST'])
def discovery_start(request):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    game_type = body.get('game_type', 'trait_discovery')
    difficulty = body.get('difficulty', 'normal')
    language = body.get('language', 'en')
    try:
        result = DiscoveryGameService.start_session(uid, game_type)
        return JsonResponse({
            'session_id': result['session_id'],
            'game_type_id': result['game_type_id'],
            'current_question': result.get('current_question'),
            'total_questions': result['total_questions'],
        })
    except GameTypeNotFoundError:
        return JsonResponse({'detail': f'Unknown game type: {game_type}'}, status=400)


@csrf_exempt
@require_http_methods(['POST'])
def discovery_answer(request):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    session_id = body.get('session_id', '')
    question_id = body.get('question_id', '')
    answer = body.get('answer', 0)
    try:
        is_correct, result = DiscoveryGameService.submit_answer(session_id, uid, question_id, answer)
        if isinstance(result, dict) and 'accuracy_percent' in result:
            xp_val = result.get('coins_earned', result.get('xp_earned', 0))
            xp_info = {}
            if xp_val > 0:
                xp_info = _add_xp(uid, xp_val, f'discovery_game_win_{session_id}')
            BadgeService.award_badge(uid, 'discovery_master', 1)
            return JsonResponse({
                'correct':          is_correct,
                'completed':        True,
                'accuracy_percent': result.get('accuracy_percent'),
                'xp_earned':        xp_val,
                'insights':         result.get('insights', ''),
                'level':            xp_info.get('level', 1),
                'next_question':    None,
            })
        return JsonResponse({
            'correct':      is_correct,
            'completed':    False,
            'next_question': result if result else None,
            'xp_earned':    0,
        })
    except SessionNotFoundError:
        return JsonResponse({'detail': 'Session not found'}, status=404)


@csrf_exempt
@require_http_methods(['POST'])
def discovery_abandon(request):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    session_id = body.get('session_id', '')
    try:
        DiscoveryGameService.abandon_session(session_id, uid)
        return JsonResponse({'success': True})
    except SessionNotFoundError:
        return JsonResponse({'detail': 'Session not found'}, status=404)
