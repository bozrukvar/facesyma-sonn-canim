"""
reports/views.py
================
Aylık Kişisel Rapor API.

GET /api/v1/reports/monthly/?month=2026-05
  → Kullanıcının o aya ait tüm verilerini toplar ve rapor döner.

Veri kaynakları (hepsi sadece okunur):
  - assessment_results  (analysis_api)
  - daily_checkins      (checkin app)
  - user_goals          (goals app)
"""
import logging
from datetime import datetime, timezone, timedelta
from calendar import monthrange

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

log = logging.getLogger(__name__)


def _decode_token(request):
    from auth_api.views import _decode_token as _dt
    return _dt(request)


from admin_api.utils.mongo import get_db as _get_db


# ── Percentile estimator (rough normal distribution mapping) ─────────────────
# Assumes population mean ≈ 50, std ≈ 18 for most psych tests.
# Returns 0-99 integer percentile.
def _score_to_percentile(score: float, mean: float = 50.0, std: float = 18.0) -> int:
    import math
    z = (score - mean) / std
    # Approximation of standard normal CDF
    p = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return max(1, min(99, int(p * 100)))


# ── Coach summary generator (template-based, no LLM needed) ──────────────────
def _gen_coach_summary(lang: str, tests_n: int, mood_avg: float,
                       goals_done: int, top_domain: str, growth_domain: str) -> str:
    mood_word = {
        'tr': {1: 'zor', 2: 'yorucu', 3: 'dengeli', 4: 'olumlu', 5: 'harika'}[round(max(1, min(5, mood_avg)))],
        'en': {1: 'tough', 2: 'tiring', 3: 'balanced', 4: 'positive', 5: 'great'}[round(max(1, min(5, mood_avg)))],
    }.get(lang, {1:'tough',2:'tiring',3:'balanced',4:'positive',5:'great'}[round(max(1,min(5,mood_avg)))])

    if lang == 'tr':
        parts = []
        if tests_n > 0:
            parts.append(f"Bu ay {tests_n} test tamamladın")
            if top_domain:
                parts.append(f"en güçlü alanın {top_domain} olarak öne çıktı")
        if mood_avg > 0:
            parts.append(f"genel ruh halin {mood_word} geçti")
        if goals_done > 0:
            parts.append(f"{goals_done} hedefe ulaştın")
        if growth_domain:
            parts.append(f"{growth_domain} alanında daha fazla çalışmaya değer")
        summary = '. '.join(p.capitalize() for p in parts) + '.'
        return summary or "Bu ay verilerini toplamaya devam et — koçun seni takip ediyor."
    else:
        parts = []
        if tests_n > 0:
            parts.append(f"You completed {tests_n} test{'s' if tests_n > 1 else ''} this month")
            if top_domain:
                parts.append(f"{top_domain} was your strongest domain")
        if mood_avg > 0:
            parts.append(f"your mood was generally {mood_word}")
        if goals_done > 0:
            parts.append(f"you achieved {goals_done} goal{'s' if goals_done > 1 else ''}")
        if growth_domain:
            parts.append(f"{growth_domain} is worth more focus going forward")
        summary = '. '.join(p.capitalize() for p in parts) + '.'
        return summary or "Keep tracking your data — your coach is watching your progress."


# ── Main view ─────────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class MonthlyReportView(View):

    def get(self, request):
        """
        Query param: month=YYYY-MM (default: current month)
        """
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        lang = request.GET.get('lang', 'en')

        # Parse month
        month_str = request.GET.get('month', '')
        try:
            month_dt = datetime.strptime(month_str, '%Y-%m')
        except ValueError:
            month_dt = datetime.now(timezone.utc).replace(day=1)
        month_label = month_dt.strftime('%Y-%m')

        # Date range for the month
        _, last_day = monthrange(month_dt.year, month_dt.month)
        start_date = month_dt.strftime('%Y-%m-01')
        end_date   = month_dt.strftime(f'%Y-%m-{last_day:02d}')

        try:
            db = _get_db()
            report = _build_report(db, uid, month_label, start_date, end_date, lang)
            return JsonResponse({'success': True, 'report': report})
        except Exception:
            log.exception(f'Monthly report error: user_id={uid} month={month_label}')
            return JsonResponse({'detail': 'Internal error.'}, status=500)


def _build_report(db, uid: int, month_label: str,
                  start_date: str, end_date: str, lang: str) -> dict:
    # ── 1. Assessment results this month ─────────────────────────────────────
    assessments = list(db['assessment_results'].find(
        {
            'user_id': uid,
            'created_at': {
                '$gte': datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc),
                '$lte': (datetime.strptime(end_date, '%Y-%m-%d')
                         .replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)),
            },
        },
        {'_id': 0, 'test_type': 1, 'overall_score': 1, 'breakdown': 1, 'created_at': 1},
        sort=[('created_at', 1)],
    ))

    # Fetch previous month's last result per test_type for delta
    prev_month = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=1))
    prev_end   = prev_month.strftime('%Y-%m-%d')
    prev_start = prev_month.replace(day=1).strftime('%Y-%m-%d')
    prev_results_raw = list(db['assessment_results'].find(
        {
            'user_id': uid,
            'created_at': {
                '$gte': datetime.strptime(prev_start, '%Y-%m-%d').replace(tzinfo=timezone.utc),
                '$lte': datetime.strptime(prev_end, '%Y-%m-%d').replace(hour=23, minute=59, tzinfo=timezone.utc),
            },
        },
        {'_id': 0, 'test_type': 1, 'overall_score': 1},
        sort=[('created_at', -1)],
    ))
    prev_scores: dict[str, float] = {}
    for r in prev_results_raw:
        tt = r.get('test_type', '')
        if tt not in prev_scores:
            prev_scores[tt] = r.get('overall_score', 0)

    # Aggregate per test_type: latest score of the month
    latest_by_type: dict[str, dict] = {}
    for a in assessments:
        tt = a.get('test_type', '')
        if tt:
            latest_by_type[tt] = a  # sorted asc → last overwrites = latest

    test_scores = []
    all_domain_scores: list[tuple[str, str, float]] = []  # (test_type, domain, score)
    for tt, a in latest_by_type.items():
        score = float(a.get('overall_score', 0))
        prev  = prev_scores.get(tt)
        entry: dict = {
            'test_type': tt,
            'score': round(score),
            'percentile': _score_to_percentile(score),
        }
        if prev is not None:
            entry['change'] = round(score - prev)
        created = a.get('created_at')
        if hasattr(created, 'strftime'):
            entry['date'] = created.strftime('%Y-%m-%d')
        test_scores.append(entry)

        # Collect domain scores
        breakdown = a.get('breakdown', {})
        for domain, info in (breakdown.items() if isinstance(breakdown, dict) else []):
            ds = info.get('score', 0) if isinstance(info, dict) else 0
            if isinstance(ds, (int, float)):
                all_domain_scores.append((tt, domain, float(ds)))

    # Strongest + growth area
    strongest = max(all_domain_scores, key=lambda x: x[2], default=None)
    growth    = min(all_domain_scores, key=lambda x: x[2], default=None)
    strongest_domain = f"{strongest[0]}/{strongest[1]}" if strongest else ''
    growth_domain    = f"{growth[0]}/{growth[1]}"    if growth    else ''
    strongest_label  = strongest[1].replace('_', ' ').title() if strongest else ''
    growth_label     = growth[1].replace('_', ' ').title()    if growth    else ''

    # ── 2. Mood check-ins this month ─────────────────────────────────────────
    checkins = list(db['daily_checkins'].find(
        {'user_id': uid, 'date': {'$gte': start_date, '$lte': end_date}},
        {'_id': 0, 'mood_score': 1, 'date': 1},
        sort=[('date', 1)],
    ))
    checkin_days  = len(checkins)
    mood_scores   = [c.get('mood_score', 3) for c in checkins if c.get('mood_score')]
    mood_avg      = round(sum(mood_scores) / len(mood_scores), 1) if mood_scores else 0.0
    mood_trend    = 'stable'
    if len(mood_scores) >= 4:
        first_half  = sum(mood_scores[:len(mood_scores)//2]) / (len(mood_scores)//2)
        second_half = sum(mood_scores[len(mood_scores)//2:]) / (len(mood_scores) - len(mood_scores)//2)
        if second_half - first_half > 0.3:
            mood_trend = 'improving'
        elif first_half - second_half > 0.3:
            mood_trend = 'declining'
    # Mood histogram (count per score)
    mood_hist = {str(i): 0 for i in range(1, 6)}
    for s in mood_scores:
        key = str(int(s))
        if key in mood_hist:
            mood_hist[key] += 1

    # ── 3. Goals this month ───────────────────────────────────────────────────
    # All goals (active or completed) — use updated_at within month OR created_at within month
    goals_all = list(db['user_goals'].find(
        {'user_id': uid},
        {'_id': 0, 'title': 1, 'test_type': 1, 'target_score': 1,
         'current_score': 1, 'status': 1, 'weekly_tasks': 1, 'created_at': 1},
    ))
    goals_active    = sum(1 for g in goals_all if g.get('status') == 'active')
    goals_completed = sum(1 for g in goals_all if g.get('status') == 'completed')
    goals_progress  = []
    for g in goals_all[:5]:  # max 5
        target = g.get('target_score', 1) or 1
        current = g.get('current_score', 0)
        pct = min(100, round(current / target * 100))
        tasks      = g.get('weekly_tasks', [])
        tasks_done = sum(1 for t in tasks if t.get('done'))
        goals_progress.append({
            'title':      g.get('title', '')[:60],
            'test_type':  g.get('test_type', ''),
            'pct':        pct,
            'status':     g.get('status', 'active'),
            'tasks_done': tasks_done,
            'tasks_total': len(tasks),
        })

    # ── 4. Percentile hints (top 3 tests) ────────────────────────────────────
    percentile_hints = []
    for entry in sorted(test_scores, key=lambda x: x.get('percentile', 0), reverse=True)[:3]:
        percentile_hints.append({
            'test_type':  entry['test_type'],
            'score':      entry['score'],
            'percentile': entry['percentile'],
        })

    # ── 5. Coach summary ─────────────────────────────────────────────────────
    coach_summary = _gen_coach_summary(
        lang         = lang,
        tests_n      = len(test_scores),
        mood_avg     = mood_avg,
        goals_done   = goals_completed,
        top_domain   = strongest_label,
        growth_domain= growth_label,
    )

    return {
        'month':            month_label,
        'tests_completed':  len(test_scores),
        'test_scores':      test_scores,
        'strongest_domain': {
            'label': strongest_label,
            'key':   strongest_domain,
            'score': round(strongest[2]) if strongest else 0,
        },
        'growth_area': {
            'label': growth_label,
            'key':   growth_domain,
            'score': round(growth[2]) if growth else 0,
        },
        'mood_avg':         mood_avg,
        'mood_trend':       mood_trend,
        'checkin_days':     checkin_days,
        'mood_histogram':   mood_hist,
        'goals_active':     goals_active,
        'goals_completed':  goals_completed,
        'goals_progress':   goals_progress,
        'percentile_hints': percentile_hints,
        'coach_summary':    coach_summary,
        'generated_at':     datetime.now(timezone.utc).isoformat(),
    }
