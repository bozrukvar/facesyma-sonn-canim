"""
partnerships/views.py
=====================
Partner / Uyumluluk Modu API.

Endpoints:
  POST   /api/v1/partner/invite/         → davet kodu üret
  POST   /api/v1/partner/join/           → koda katıl
  GET    /api/v1/partner/compatibility/  → uyumluluk raporu hesapla / getir
  GET    /api/v1/partner/status/         → mevcut ortaklık durumu
  DELETE /api/v1/partner/disconnect/     → bağlantıyı kes

Koleksiyon: partnerships (MongoDB)
Doküman:
  {
    "_id": ObjectId,
    "invite_code": str (6 chars),
    "user_a_id": int,
    "user_b_id": int | null,
    "user_a_name": str,
    "user_b_name": str | null,
    "status": "pending" | "active" | "disconnected",
    "compatibility_score": int | null,
    "report": dict | null,
    "created_at": datetime,
    "updated_at": datetime
  }
"""
import json
import logging
import random
import string
from datetime import datetime, timezone

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from bson import ObjectId

log = logging.getLogger(__name__)

# ── Bağlanma stili ağırlık matrisi ───────────────────────────────────────────
# Satır/Sütun: secure, anxious, avoidant, disorganized
_ATTACHMENT_MATRIX = {
    ('secure',       'secure'):       95,
    ('secure',       'anxious'):      65,
    ('secure',       'avoidant'):     60,
    ('secure',       'disorganized'): 50,
    ('anxious',      'anxious'):      50,
    ('anxious',      'avoidant'):     60,
    ('anxious',      'disorganized'): 40,
    ('avoidant',     'avoidant'):     55,
    ('avoidant',     'disorganized'): 40,
    ('disorganized', 'disorganized'): 35,
}


def _attachment_compat(style_a: str, style_b: str) -> int:
    """Symmetric lookup."""
    key = tuple(sorted([style_a, style_b]))
    return _ATTACHMENT_MATRIX.get(key, 55)


def _classify_attachment(anxiety: float, avoidance: float) -> str:
    """0-100 anxiety/avoidance scores → attachment style label."""
    if anxiety >= 50 and avoidance >= 50:
        return 'disorganized'
    if anxiety >= 50:
        return 'anxious'
    if avoidance >= 50:
        return 'avoidant'
    return 'secure'


def _decode_token(request):
    from auth_api.views import _decode_token as _dt
    return _dt(request)


from admin_api.utils.mongo import get_db as _get_db


def _get_col():
    return _get_db()['partnerships']


def _gen_invite_code() -> str:
    """6-karakter büyük alfanümerik kod üret."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _serialize(doc: dict) -> dict:
    d = dict(doc)
    if '_id' in d:
        d['partnership_id'] = str(d.pop('_id'))
    for field in ('created_at', 'updated_at'):
        if hasattr(d.get(field), 'isoformat'):
            d[field] = d[field].isoformat()
    return d


def _get_latest_breakdown(db, user_id: int, test_type: str) -> dict:
    """En son assessment sonucunun breakdown'ını çek (0-100 normalize)."""
    doc = db['assessment_results'].find_one(
        {'user_id': user_id, 'test_type': test_type},
        sort=[('created_at', -1)],
        projection={'breakdown': 1, 'overall_score': 1},
    )
    if not doc:
        return {}
    return doc.get('breakdown') or {}


def _domain_compat(score_a: float, score_b: float) -> int:
    """İki 0-100 puan arasındaki benzerlik skoru. Yakın = yüksek."""
    return round(100 - abs(score_a - score_b))


def _compute_compatibility(db, user_a_id: int, user_b_id: int, lang: str = 'tr') -> dict:
    """
    Uyumluluk algoritması:
      - Kişilik (Big Five, %35)
      - Bağlanma stili (%25)
      - İlişki dinamikleri (%40)
    """
    # ── Kişilik ──────────────────────────────────────────────────────────────
    pers_a = _get_latest_breakdown(db, user_a_id, 'personality')
    pers_b = _get_latest_breakdown(db, user_b_id, 'personality')

    big5_domains = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
    personality_breakdown: dict[str, int] = {}
    personality_scores: list[int] = []

    for domain in big5_domains:
        sa = pers_a.get(domain, {}).get('score', 50) if pers_a else 50
        sb = pers_b.get(domain, {}).get('score', 50) if pers_b else 50
        c = _domain_compat(sa, sb)
        personality_breakdown[domain] = c
        personality_scores.append(c)

    personality_compat = round(sum(personality_scores) / len(personality_scores)) if personality_scores else 50
    has_personality = bool(pers_a and pers_b)

    # ── Bağlanma stili ───────────────────────────────────────────────────────
    attach_a = _get_latest_breakdown(db, user_a_id, 'attachment')
    attach_b = _get_latest_breakdown(db, user_b_id, 'attachment')

    anx_a  = attach_a.get('anxiety', {}).get('score', 50)   if attach_a else 50
    avd_a  = attach_a.get('avoidance', {}).get('score', 50) if attach_a else 50
    anx_b  = attach_b.get('anxiety', {}).get('score', 50)   if attach_b else 50
    avd_b  = attach_b.get('avoidance', {}).get('score', 50) if attach_b else 50

    style_a = _classify_attachment(anx_a, avd_a)
    style_b = _classify_attachment(anx_b, avd_b)
    attachment_compat = _attachment_compat(style_a, style_b)
    has_attachment = bool(attach_a and attach_b)

    # ── İlişki dinamikleri ───────────────────────────────────────────────────
    rel_a = _get_latest_breakdown(db, user_a_id, 'relationship')
    rel_b = _get_latest_breakdown(db, user_b_id, 'relationship')

    rel_domains = ['love_language', 'conflict_style', 'intimacy_needs', 'relationship_values']
    # love_language: aynı olmak önemli → daha katı benzerlik
    rel_weights  = {'love_language': 0.40, 'conflict_style': 0.20, 'intimacy_needs': 0.20, 'relationship_values': 0.20}

    relationship_breakdown: dict[str, int] = {}
    rel_weighted_sum = 0.0

    for rd in rel_domains:
        sa = rel_a.get(rd, {}).get('score', 50) if rel_a else 50
        sb = rel_b.get(rd, {}).get('score', 50) if rel_b else 50
        c = _domain_compat(sa, sb)
        relationship_breakdown[rd] = c
        rel_weighted_sum += c * rel_weights[rd]

    relationship_compat = round(rel_weighted_sum)
    has_relationship = bool(rel_a and rel_b)

    # ── Genel skor ───────────────────────────────────────────────────────────
    overall_score = round(
        personality_compat  * 0.35 +
        attachment_compat   * 0.25 +
        relationship_compat * 0.40
    )

    # ── Güçlü yönler ve dikkat alanları ─────────────────────────────────────
    domain_scores = {
        'personality':  personality_compat,
        'attachment':   attachment_compat,
        'relationship': relationship_compat,
    }

    DOMAIN_LABELS = {
        'tr': {
            'personality': 'Kişilik Uyumu',
            'attachment': 'Bağlanma Uyumu',
            'relationship': 'İlişki Dinamikleri',
            'openness': 'Açıklık',
            'conscientiousness': 'Sorumluluk',
            'extraversion': 'Dışadönüklük',
            'agreeableness': 'Uyumluluk',
            'neuroticism': 'Duygusal Denge',
            'love_language': 'Sevgi Dili',
            'conflict_style': 'Çatışma Tarzı',
            'intimacy_needs': 'Yakınlık İhtiyacı',
            'relationship_values': 'İlişki Değerleri',
        },
        'en': {
            'personality': 'Personality Match',
            'attachment': 'Attachment Match',
            'relationship': 'Relationship Dynamics',
            'openness': 'Openness',
            'conscientiousness': 'Conscientiousness',
            'extraversion': 'Extraversion',
            'agreeableness': 'Agreeableness',
            'neuroticism': 'Emotional Stability',
            'love_language': 'Love Language',
            'conflict_style': 'Conflict Style',
            'intimacy_needs': 'Intimacy Needs',
            'relationship_values': 'Relationship Values',
        },
    }
    labels = DOMAIN_LABELS.get(lang, DOMAIN_LABELS['en'])

    all_scores = {**personality_breakdown, **relationship_breakdown, 'attachment': attachment_compat}
    strengths  = [labels.get(k, k) for k, v in all_scores.items() if v >= 75]
    watchouts  = [labels.get(k, k) for k, v in all_scores.items() if v < 50]

    # ── Narratif ─────────────────────────────────────────────────────────────
    narrative = _gen_narrative(lang, overall_score, style_a, style_b,
                               personality_compat, attachment_compat, relationship_compat)

    return {
        'overall_score':          overall_score,
        'domain_scores':          domain_scores,
        'personality_breakdown':  personality_breakdown,
        'relationship_breakdown': relationship_breakdown,
        'attachment_styles': {
            'user_a': style_a,
            'user_b': style_b,
        },
        'strengths':  strengths[:5],
        'watchouts':  watchouts[:4],
        'narrative':  narrative,
        'data_quality': {
            'has_personality':  has_personality,
            'has_attachment':   has_attachment,
            'has_relationship': has_relationship,
        },
    }


def _gen_narrative(lang: str, score: int, style_a: str, style_b: str,
                   pers: int, attach: int, rel: int) -> str:
    """Puana göre template narratif üret."""
    if lang == 'tr':
        if score >= 80:
            intro = 'Mükemmel bir uyum! İkinizin değerleri, bağlanma biçimleri ve ilişki beklentileri birbiriyle güçlü şekilde örtüşüyor.'
        elif score >= 65:
            intro = 'Güçlü bir uyum var. Bazı farklılıklar ilişkinizi zenginleştirebilir; önemli alanlarda ise derin bir anlayış paylaşıyorsunuz.'
        elif score >= 50:
            intro = 'Orta düzeyde bir uyum. Temel farklılıklarınız büyüme fırsatı sunarken iletişim becerileri bu ilişkiyi besleyebilir.'
        else:
            intro = 'Farklı perspektiflerden geliyor olabilirsiniz. Açık iletişim ve karşılıklı sabır bu ilişkiyi güçlendirmenin anahtarı.'

        attach_part = ''
        if style_a == 'secure' and style_b == 'secure':
            attach_part = ' İkiniz de güvenli bağlanma stiline sahipsiniz — bu ilişki için harika bir temel.'
        elif 'secure' in (style_a, style_b):
            attach_part = ' Güvenli bağlanan taraf, ilişkide dengeleyici bir rol üstlenebilir.'
        elif style_a == 'anxious' and style_b == 'avoidant':
            attach_part = ' Kaygılı-kaçıngan dinamiği farkındalık gerektirir; açık sınır konuşmaları önemli.'
        elif style_a == 'avoidant' and style_b == 'anxious':
            attach_part = ' Kaygılı-kaçıngan dinamiği farkındalık gerektirir; açık sınır konuşmaları önemli.'

        return intro + attach_part
    else:
        if score >= 80:
            intro = 'Excellent compatibility! Your values, attachment styles, and relationship expectations align strongly.'
        elif score >= 65:
            intro = 'Strong compatibility. Some differences can enrich your relationship while you share deep understanding in key areas.'
        elif score >= 50:
            intro = 'Moderate compatibility. Core differences offer growth opportunities while communication skills can nurture this relationship.'
        else:
            intro = 'You may come from different perspectives. Open communication and mutual patience are key to strengthening this connection.'

        attach_part = ''
        if style_a == 'secure' and style_b == 'secure':
            attach_part = ' Both of you have secure attachment styles — a wonderful foundation for this relationship.'
        elif 'secure' in (style_a, style_b):
            attach_part = ' The securely attached partner can play a balancing role in the relationship.'
        elif set([style_a, style_b]) == {'anxious', 'avoidant'}:
            attach_part = ' The anxious-avoidant dynamic requires awareness; open boundary conversations matter.'

        return intro + attach_part


# ── POST /api/v1/partner/invite/ ──────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class InviteView(View):
    """Yeni davet kodu üret."""

    def post(self, request):
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        col = _get_col()
        db  = _get_db()

        # Mevcut aktif/bekleyen ortaklık var mı?
        existing = col.find_one({'$or': [{'user_a_id': uid}, {'user_b_id': uid}],
                                  'status': {'$in': ['pending', 'active']}})
        if existing:
            return JsonResponse({
                'detail': 'You already have an active or pending partnership.',
                'invite_code': existing.get('invite_code'),
                'status': existing.get('status'),
            }, status=409)

        # Kullanıcı adını al
        user_doc = db['users'].find_one({'id': uid}, {'name': 1})
        user_name = (user_doc or {}).get('name', f'User#{uid}')

        # Benzersiz kod üret
        code = _gen_invite_code()
        for _ in range(10):
            if not col.find_one({'invite_code': code, 'status': 'pending'}):
                break
            code = _gen_invite_code()

        now = datetime.now(timezone.utc)
        doc = {
            'invite_code':    code,
            'user_a_id':      uid,
            'user_a_name':    user_name,
            'user_b_id':      None,
            'user_b_name':    None,
            'status':         'pending',
            'compatibility_score': None,
            'report':         None,
            'created_at':     now,
            'updated_at':     now,
        }
        col.insert_one(doc)

        return JsonResponse({'success': True, 'invite_code': code, 'status': 'pending'})


# ── POST /api/v1/partner/join/ ────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class JoinView(View):
    """Davet koduna katıl."""

    def post(self, request):
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        code = (body.get('invite_code') or '').strip().upper()
        if len(code) != 6:
            return JsonResponse({'detail': 'Invite code must be 6 characters.'}, status=400)

        col = _get_col()
        db  = _get_db()

        # Mevcut ortaklık kontrolü
        existing = col.find_one({'$or': [{'user_a_id': uid}, {'user_b_id': uid}],
                                  'status': {'$in': ['pending', 'active']}})
        if existing:
            return JsonResponse({'detail': 'You already have an active or pending partnership.'}, status=409)

        # Kodu bul
        partnership = col.find_one({'invite_code': code, 'status': 'pending'})
        if not partnership:
            return JsonResponse({'detail': 'Invalid or expired invite code.'}, status=404)

        if partnership['user_a_id'] == uid:
            return JsonResponse({'detail': 'You cannot join your own invite.'}, status=400)

        # Kullanıcı adını al
        user_doc = db['users'].find_one({'id': uid}, {'name': 1})
        user_name = (user_doc or {}).get('name', f'User#{uid}')

        now = datetime.now(timezone.utc)

        # Uyumluluk hesapla
        try:
            lang = body.get('lang', 'tr')
            report = _compute_compatibility(db, partnership['user_a_id'], uid, lang)
            overall = report['overall_score']
        except Exception:
            log.exception('Compatibility computation failed')
            report = None
            overall = None

        col.update_one(
            {'_id': partnership['_id']},
            {'$set': {
                'user_b_id':   uid,
                'user_b_name': user_name,
                'status':      'active',
                'compatibility_score': overall,
                'report':      report,
                'updated_at':  now,
            }},
        )

        return JsonResponse({
            'success': True,
            'status': 'active',
            'partner_name': partnership['user_a_name'],
            'compatibility_score': overall,
        })


# ── GET /api/v1/partner/compatibility/ ───────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class CompatibilityView(View):
    """Uyumluluk raporunu getir (veya yeniden hesapla)."""

    def get(self, request):
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        col = _get_col()
        db  = _get_db()
        lang = request.GET.get('lang', 'tr')

        partnership = col.find_one(
            {'$or': [{'user_a_id': uid}, {'user_b_id': uid}], 'status': 'active'}
        )
        if not partnership:
            return JsonResponse({'detail': 'No active partnership found.'}, status=404)

        # Rapor yoksa hesapla
        report = partnership.get('report')
        if not report:
            try:
                report = _compute_compatibility(db, partnership['user_a_id'],
                                                partnership['user_b_id'], lang)
                overall = report['overall_score']
                col.update_one(
                    {'_id': partnership['_id']},
                    {'$set': {'report': report, 'compatibility_score': overall,
                              'updated_at': datetime.now(timezone.utc)}},
                )
            except Exception:
                log.exception('Compatibility computation failed')
                return JsonResponse({'detail': 'Could not compute compatibility.'}, status=500)

        partner_id   = partnership['user_b_id'] if partnership['user_a_id'] == uid else partnership['user_a_id']
        partner_name = partnership['user_b_name'] if partnership['user_a_id'] == uid else partnership['user_a_name']

        return JsonResponse({
            'success': True,
            'partner_id':   partner_id,
            'partner_name': partner_name,
            'report': report,
        })


# ── GET /api/v1/partner/status/ ──────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class PartnerStatusView(View):
    """Mevcut ortaklık durumunu getir."""

    def get(self, request):
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        col = _get_col()

        partnership = col.find_one(
            {'$or': [{'user_a_id': uid}, {'user_b_id': uid}],
             'status': {'$in': ['pending', 'active']}},
            projection={'_id': 1, 'invite_code': 1, 'user_a_id': 1, 'user_a_name': 1,
                        'user_b_id': 1, 'user_b_name': 1, 'status': 1,
                        'compatibility_score': 1, 'created_at': 1},
        )

        if not partnership:
            return JsonResponse({'success': True, 'status': 'none'})

        d = _serialize(partnership)

        # Karşı tarafın adını "partner_name" olarak döndür
        if partnership['user_a_id'] == uid:
            d['partner_name'] = partnership.get('user_b_name')
            d['partner_id']   = partnership.get('user_b_id')
            d['is_inviter']   = True
        else:
            d['partner_name'] = partnership.get('user_a_name')
            d['partner_id']   = partnership.get('user_a_id')
            d['is_inviter']   = False

        return JsonResponse({'success': True, **d})


# ── DELETE /api/v1/partner/disconnect/ ────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class DisconnectView(View):
    """Ortaklığı kes."""

    def delete(self, request):
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        col = _get_col()

        partnership = col.find_one(
            {'$or': [{'user_a_id': uid}, {'user_b_id': uid}],
             'status': {'$in': ['pending', 'active']}}
        )
        if not partnership:
            return JsonResponse({'detail': 'No active partnership found.'}, status=404)

        col.update_one(
            {'_id': partnership['_id']},
            {'$set': {'status': 'disconnected', 'updated_at': datetime.now(timezone.utc)}},
        )

        return JsonResponse({'success': True, 'message': 'Partnership disconnected.'})
