"""
goals/views.py
==============
Hedef Takip API — assessment tabanlı kişisel hedefler.

Koleksiyon: user_goals (MongoDB)
Doküman:
  {
    "_id": ObjectId,
    "user_id": int,
    "title": str,
    "test_type": str,
    "target_score": int (0-100),
    "current_score": int (0-100),
    "deadline": "YYYY-MM-DD",
    "weekly_tasks": [{"id": int, "week": int, "text": str, "done": bool}],
    "status": "active|completed|abandoned",
    "created_at": datetime,
    "updated_at": datetime
  }
"""
import json
import logging
from datetime import datetime, timezone
from bson import ObjectId

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

log = logging.getLogger(__name__)

_VALID_STATUSES = {'active', 'completed', 'abandoned'}

# Test types aligned with assessment system
_VALID_TEST_TYPES = {
    'personality', 'skills', 'hr', 'career', 'relationship', 'vocation',
    'attachment', 'grit', 'growth_mindset', 'life_satisfaction',
    'self_compassion', 'body_image', 'self_efficacy', 'stress',
    'finance', 'finance_anxiety',
}

# ── Micro-task templates by test_type ─────────────────────────────────────────
# Each entry: list of 4 weeks × 1 task (index 0-3 = week 1-4)
_TASK_TEMPLATES: dict[str, list[str]] = {
    'stress': [
        'Sabah 5 dakika derin nefes egzersizi yap',
        'Günde en az 20 dakika yürüyüş yap',
        'Akşam dijital detoks: yatmadan 1 saat önce ekran kapatma',
        '10 dakikalık mindfulness meditasyonu dene',
    ],
    'personality': [
        'Kişilik testindeki en düşük puanlı alan için 1 makale oku',
        'Sosyal konfor alanını genişletmek için yeni bir aktivite dene',
        'Haftada 1 derin konuşma: seni tanıyan biriyle güçlü yönlerini konuş',
        'Güçlü yönün olan bir alanda gönüllülük yap',
    ],
    'skills': [
        'Zayıf alanınla ilgili 30 dakika online kurs ya da video izle',
        'Öğrendiğin 1 beceriyi küçük bir projede uygula',
        'Mentor veya deneyimli biri ile 15 dakika sohbet et',
        'Haftalık öz-değerlendirme: 3 şey öğrendim, 1 şey geliştireceğim',
    ],
    'hr': [
        'Takım iletişimini geliştirmek için aktif dinleme egzersizi yap',
        'Geri bildirim ver ya da al: yapıcı bir değerlendirme paylaş',
        'Liderlik veya ekip yönetimi üzerine 1 bölüm podcast dinle',
        'Bir iş arkadaşına destek ol veya mentor ol',
    ],
    'career': [
        'Kariyer hedeflerini 3 sütuna yaz: güçlüler / zayıflar / fırsatlar',
        'Sektöründe 1 networking etkinliğine katıl ya da online grupla etkileş',
        'CV veya LinkedIn profilini güncelle',
        'Bir kariyer mentoruyla veya danışmanla görüş',
    ],
    'relationship': [
        'Güvendiğin biri için beklenmedik küçük bir jest yap',
        'Aktif dinleme pratiği: telefonsuz 20 dakika tam dikkatli sohbet',
        'Sınır koyma egzersizi: enerji düşüren bir durumda nazikçe hayır de',
        'İlişkideki minnettarlıklarını yaz, birini paylaş',
    ],
    'vocation': [
        'Değerlerinle örtüşen 3 mesleği araştır, 1 saatlik keşif yap',
        'Hobini veya tutkunu işe dönüştürmeye yönelik 1 küçük adım at',
        'Değer uyumu testi: işin sana neler vermesini istiyorsun?',
        'İlgi alanında çalışan biriyle bilgi mülakatı (informational interview) yap',
    ],
    'attachment': [
        'Bağlanma stilinle ilgili 1 makale oku; kendi kalıplarını listele',
        'İhtiyaçlarını açıkça ifade etme pratiği: 1 kişiyle dene',
        'Duygusal tetikleyicilerini fark etme günlüğü tut',
        'Terapist veya danışmanla 1 seans ya da kitap önerisi al',
    ],
    'grit': [
        'Zor bir görevi 25 dakika tek odaklanmayla tamamla (Pomodoro)',
        'Geçmişte zorluğu aştığın bir anıyı yaz; ne öğrendin?',
        'Uzun vadeli bir hedef için küçük günlük alışkanlık belirle',
        'Engel listesi: bu hedefe ulaşmayı zorlaştıran 3 şeyi ve çözümünü yaz',
    ],
    'growth_mindset': [
        '"Henüz yapamıyorum" → "henüz" diyerek bir zorlukla yeniden yüzleş',
        'Bu hafta başarısız olduğun bir şeyden öğrenilen dersleri yaz',
        'Yeni ve zor bir şey dene: sonuç değil süreç önemli',
        'Sabit zihin tepkilerini büyüme tepkisine dönüştür: 5 örnek listele',
    ],
    'life_satisfaction': [
        'Yaşam denge tekerleği çiz; en düşük alan için 1 eylem planla',
        'Her gün 3 şükredeceğin şeyi yaz (sabah ritüeli)',
        'Anlamlı bir aktiviteye zaman ayır: sanat, doğa, sosyal',
        'Bir olumsuz alışkanlığı pozitif alternatifle değiştir',
    ],
    'self_compassion': [
        'Kendine iyi bir arkadaşa yazdığın gibi nazik bir mektup yaz',
        'Öz-eleştiri anında dur ve "Bu konuşma yapıcı mı?" sor',
        'Güçlü yönler egzersizi: 5 güçlü yönün ve kanıtını listele',
        'Mindful self-compassion meditasyonu dene (10 dk)',
    ],
    'body_image': [
        'Bedenine teşekkür et: bugün sana hizmet eden 3 şeyi yaz',
        'Sosyal medyada beden imajını olumsuz etkileyen hesapları takipten çıkar',
        'Hareketi ceza değil enerji olarak gör: keyif aldığın 1 aktivite dene',
        'Beden nötr konuşma pratiği: değerlendirme yerine tanımlama',
    ],
    'self_efficacy': [
        'Geçmişte başardığın zorlu bir görevi hatırla ve nedenini analiz et',
        'Büyük hedefi küçük alt görevlere böl; ilk adımı bu hafta yap',
        'Başarı günlüğü tut: her gün 1 küçük kazanım kaydet',
        '"Yapabildiğimden emin değilim" → "nasıl yapabilirim?" diye yeniden çerçevele',
    ],
    'finance': [
        'Bu haftanın tüm harcamalarını kategorilere göre listele',
        'Aylık bütçe oluştur: gelir → zorunlu → birikm → isteğe bağlı',
        'Finansal hedefine yönelik otomatik tasarruf talimatı ver',
        'Kişisel finans üzerine 1 bölüm podcast veya kitap bölümü oku',
    ],
    'finance_anxiety': [
        'Mali durumu kağıda dök: borçlar, varlıklar, net değer — sadece görmek rahatlatır',
        'Finansal kaygı tetikleyicilerini listele; her biri için 1 küçük eylem planla',
        'Acil durum fonu için küçük bir başlangıç miktarı ayır',
        'Finansal danışman veya güvenilir biriyle durumunu konuş',
    ],
}

_DEFAULT_TASKS = [
    'Hedefinle ilgili 1 kitap veya makale oku',
    'Haftada 3 kez 20 dakika bu alana odaklı çalış',
    'İlerlemeyi bir günlükte takip et',
    'Gelişimin için bir uzman veya mentor bul',
]


def _generate_micro_tasks(test_type: str, current_score: int, target_score: int) -> list[dict]:
    templates = _TASK_TEMPLATES.get(test_type, _DEFAULT_TASKS)
    gap = target_score - current_score

    # If gap is large (>30), use all 4 tasks in sequence; if small, pick most relevant
    tasks = []
    for week_idx, text in enumerate(templates[:4]):
        tasks.append({
            'id': week_idx + 1,
            'week': week_idx + 1,
            'text': text,
            'done': False,
        })

    # If gap is small, mark week 1-2 tasks as more urgent
    if gap <= 10 and tasks:
        tasks = tasks[2:]  # Focus on refinement tasks (weeks 3-4)
        for i, task in enumerate(tasks):
            task['week'] = i + 1

    return tasks


def _decode_token(request):
    from auth_api.views import _decode_token as _dt
    return _dt(request)


def _get_col():
    from admin_api.utils.mongo import get_db
    return get_db()['user_goals']


def _serialize_goal(doc: dict) -> dict:
    d = dict(doc)
    if '_id' in d:
        d['goal_id'] = str(d.pop('_id'))
    for field in ('created_at', 'updated_at'):
        if hasattr(d.get(field), 'isoformat'):
            d[field] = d[field].isoformat()
    return d


# ── POST + GET /api/v1/goals/ ─────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class GoalsView(View):

    def post(self, request):
        """Yeni hedef oluştur."""
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        try:
            data = json.loads(request.body or b'{}')
        except Exception:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        title        = str(data.get('title', '')).strip()[:200]
        test_type    = data.get('test_type', '')
        target_score = data.get('target_score')
        current_score = data.get('current_score', 0)
        deadline     = data.get('deadline', '')

        if not title:
            return JsonResponse({'detail': 'title required.'}, status=400)
        if test_type not in _VALID_TEST_TYPES:
            return JsonResponse({'detail': f'Invalid test_type.'}, status=400)
        if not isinstance(target_score, (int, float)) or not (1 <= target_score <= 100):
            return JsonResponse({'detail': 'target_score must be 1-100.'}, status=400)
        if not isinstance(current_score, (int, float)):
            current_score = 0
        current_score = max(0, min(100, int(current_score)))
        target_score  = int(target_score)

        # Validate deadline
        try:
            datetime.strptime(deadline, '%Y-%m-%d')
        except (ValueError, TypeError):
            deadline = ''

        now = datetime.now(timezone.utc)
        weekly_tasks = _generate_micro_tasks(test_type, current_score, target_score)

        try:
            col = _get_col()
            result = col.insert_one({
                'user_id':      uid,
                'title':        title,
                'test_type':    test_type,
                'target_score': target_score,
                'current_score': current_score,
                'deadline':     deadline,
                'weekly_tasks': weekly_tasks,
                'status':       'active',
                'created_at':   now,
                'updated_at':   now,
            })
            return JsonResponse({
                'success': True,
                'goal_id': str(result.inserted_id),
                'weekly_tasks': weekly_tasks,
            }, status=201)
        except Exception:
            log.exception(f'Goal create error: user_id={uid}')
            return JsonResponse({'detail': 'Save failed.'}, status=500)

    def get(self, request):
        """Kullanıcının hedeflerini listele (status filtresi opsiyonel)."""
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        status_filter = request.GET.get('status', 'active')
        query: dict = {'user_id': uid}
        if status_filter and status_filter in _VALID_STATUSES:
            query['status'] = status_filter
        elif status_filter == 'all':
            pass  # no status filter

        try:
            col  = _get_col()
            docs = list(col.find(query, sort=[('created_at', -1)]).limit(50))
            return JsonResponse({
                'success': True,
                'goals':   [_serialize_goal(d) for d in docs],
            })
        except Exception:
            log.exception(f'Goals list error: user_id={uid}')
            return JsonResponse({'detail': 'Internal error.'}, status=500)


# ── GET + PATCH /api/v1/goals/<goal_id>/ ─────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class GoalDetailView(View):

    def get(self, request, goal_id: str):
        """Tek hedef detayı."""
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        try:
            oid = ObjectId(goal_id)
        except Exception:
            return JsonResponse({'detail': 'Invalid goal_id.'}, status=400)

        try:
            col = _get_col()
            doc = col.find_one({'_id': oid, 'user_id': uid})
            if not doc:
                return JsonResponse({'detail': 'Not found.'}, status=404)
            return JsonResponse({'success': True, 'goal': _serialize_goal(doc)})
        except Exception:
            log.exception(f'Goal get error: user_id={uid} goal_id={goal_id}')
            return JsonResponse({'detail': 'Internal error.'}, status=500)

    def patch(self, request, goal_id: str):
        """Hedef güncelle: status, current_score, task done toggle."""
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        try:
            oid = ObjectId(goal_id)
        except Exception:
            return JsonResponse({'detail': 'Invalid goal_id.'}, status=400)

        try:
            data = json.loads(request.body or b'{}')
        except Exception:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        updates: dict = {'updated_at': datetime.now(timezone.utc)}

        if 'status' in data and data['status'] in _VALID_STATUSES:
            updates['status'] = data['status']

        if 'current_score' in data:
            cs = data['current_score']
            if isinstance(cs, (int, float)):
                updates['current_score'] = max(0, min(100, int(cs)))

        try:
            col = _get_col()
            # Task toggle: {"task_id": 2, "done": true}
            if 'task_id' in data:
                task_id  = int(data['task_id'])
                done_val = bool(data.get('done', True))
                result = col.update_one(
                    {'_id': oid, 'user_id': uid, 'weekly_tasks.id': task_id},
                    {'$set': {
                        'weekly_tasks.$.done': done_val,
                        'updated_at': updates['updated_at'],
                    }},
                )
                if result.matched_count == 0:
                    return JsonResponse({'detail': 'Not found.'}, status=404)
                doc = col.find_one({'_id': oid})
                return JsonResponse({'success': True, 'goal': _serialize_goal(doc)})

            result = col.update_one(
                {'_id': oid, 'user_id': uid},
                {'$set': updates},
            )
            if result.matched_count == 0:
                return JsonResponse({'detail': 'Not found.'}, status=404)
            doc = col.find_one({'_id': oid})
            return JsonResponse({'success': True, 'goal': _serialize_goal(doc)})
        except Exception:
            log.exception(f'Goal patch error: user_id={uid} goal_id={goal_id}')
            return JsonResponse({'detail': 'Internal error.'}, status=500)
