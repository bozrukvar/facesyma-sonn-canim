"""
assessment_views.py
===================
Assessment & Questionnaire API
Testleri serve et ve cevapları score'la

Endpoints:
  GET  /api/v1/assessment/questions/{test_type}/?lang=tr     → Soruları al
  POST /api/v1/assessment/submit/{test_type}/                → Cevapları gönder

Test Types (20 soru, 5-li Likert):
  - skills       → 5 domain: problem_solving, empathy, organization, learning_speed, decision_making
  - hr           → 5 domain: leadership, team_fit, communication, stress_tolerance, motivation
  - personality  → 5 domain (Big Five): openness, conscientiousness, extraversion, agreeableness, neuroticism
  - career       → 6 domain: analytical, creative, social, entrepreneurial, managerial, technical
  - relationship → 4 subscale: attachment_style, love_language, relationship_values, emotional_intelligence
  - vocation     → 6 domain (Holland RIASEC): realistic, investigative, artistic, social, enterprising, conventional
"""

import json
import logging
from pathlib import Path
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from .assessment_recommendations import generate_recommendations

log = logging.getLogger(__name__)

# Supported test types
VALID_TESTS = ['skills', 'hr', 'personality', 'career', 'relationship', 'vocation']


def _get_questions_path(test_type: str) -> Path:
    """Get path to questionnaire JSON file."""
    # Questions are in questions subdirectory within facesyma_backend
    base = Path(settings.BASE_DIR)
    return base / 'questions' / f'{test_type}_questions.json'


def _load_questions(test_type: str) -> dict | None:
    """Load questionnaire JSON file."""
    if test_type not in VALID_TESTS:
        return None

    path = _get_questions_path(test_type)
    if not path.exists():
        log.error(f'Questionnaire not found: {path}')
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log.error(f'Error loading questionnaire {test_type}: {e}')
        return None


def _get_domain_key(test_type: str) -> str:
    """Get the domain/subscale key name for each test type."""
    mapping = {
        'skills': 'domain',
        'hr': 'domain',
        'personality': 'domain',
        'career': 'domain',
        'relationship': 'subscale',
        'vocation': 'domain',
    }
    return mapping.get(test_type, 'domain')


def _score_test(test_data: dict, responses: list) -> dict:
    """
    Score test responses.

    Args:
        test_data: Loaded questionnaire data
        responses: List of { q_id, score } objects

    Returns:
        Scoring breakdown by domain
    """
    domain_key = _get_domain_key(test_data.get('test_type', 'skills'))
    scores = {}
    question_count = {}

    # Build question lookup
    questions_by_id = {}
    for q in test_data.get('questions', []):
        questions_by_id[q['q_id']] = q

    # Process responses
    for resp in responses:
        q_id = resp.get('q_id')
        score = resp.get('score', 0)

        # Validate score range (1-5)
        if not isinstance(score, int) or score < 1 or score > 5:
            continue

        # Find question
        if q_id not in questions_by_id:
            continue

        q = questions_by_id[q_id]
        domain = q.get(domain_key, 'unknown')

        # Handle reverse-scored items
        if q.get('reverse_scored', False):
            score = 6 - score  # Reverse: 1→5, 2→4, 3→3, 4→2, 5→1

        if domain not in scores:
            scores[domain] = 0
            question_count[domain] = 0

        scores[domain] += score
        question_count[domain] += 1

    # Calculate averages and interpretation
    breakdown = {}
    for domain in scores:
        count = question_count[domain]
        avg = scores[domain] / count if count > 0 else 0

        # Interpret score (1-5 scale)
        if avg >= 4.5:
            level = 'Very High'
            level_tr = 'Çok Yüksek'
        elif avg >= 3.5:
            level = 'High'
            level_tr = 'Yüksek'
        elif avg >= 2.5:
            level = 'Moderate'
            level_tr = 'Orta'
        elif avg >= 1.5:
            level = 'Low'
            level_tr = 'Düşük'
        else:
            level = 'Very Low'
            level_tr = 'Çok Düşük'

        breakdown[domain] = {
            'score': round(avg, 2),
            'level': level,
            'level_tr': level_tr,
            'questions_answered': count,
        }

    return breakdown


# ── Assessment Questions View ─────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class AssessmentQuestionsView(View):
    """
    GET /api/v1/assessment/questions/{test_type}/?lang=tr

    Fetch questionnaire questions for a specific test type.
    """

    def get(self, request, test_type):
        try:
            # Validate test type
            if test_type not in VALID_TESTS:
                return JsonResponse({
                    'detail': f'Invalid test type. Valid: {", ".join(VALID_TESTS)}'
                }, status=400)

            # Get language
            lang = request.GET.get('lang', 'tr')

            # Load questionnaire
            test_data = _load_questions(test_type)
            if not test_data:
                return JsonResponse({
                    'detail': f'Questionnaire not found: {test_type}'
                }, status=404)

            # Extract questions and translate to requested language
            domain_key = _get_domain_key(test_data.get('test_type', 'skills'))
            questions = []
            for q in test_data.get('questions', []):
                translations = q.get('translations', {})
                text = translations.get(lang, translations.get('tr', ''))

                questions.append({
                    'q_id': q['q_id'],
                    'order': q['order'],
                    'text': text,
                    'domain': q.get(domain_key, 'unknown'),
                    'reverse_scored': q.get('reverse_scored', False),
                })

            # Get scale labels
            scale_labels = test_data.get('scale_labels', {}).get(lang,
                                        test_data.get('scale_labels', {}).get('tr', {}))

            return JsonResponse({
                'success': True,
                'data': {
                    'test_type': test_type,
                    'version': test_data.get('version', '1.0'),
                    'description': test_data.get('description', ''),
                    'domains': test_data.get('domains') or test_data.get('subscales', []),
                    'questions': questions,
                    'scale': {
                        '1': scale_labels.get('1', 'Strongly Disagree'),
                        '2': scale_labels.get('2', 'Disagree'),
                        '3': scale_labels.get('3', 'Neutral'),
                        '4': scale_labels.get('4', 'Agree'),
                        '5': scale_labels.get('5', 'Strongly Agree'),
                    },
                    'total_questions': len(questions),
                }
            })

        except Exception as e:
            log.exception(f'Error fetching questions: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


# ── Assessment Submit View ─────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class AssessmentSubmitView(View):
    """
    POST /api/v1/assessment/submit/{test_type}/

    Submit test responses and get scoring breakdown.

    Body:
    {
        "lang": "tr",
        "responses": [
            { "q_id": "S001", "score": 4 },
            { "q_id": "S002", "score": 5 },
            ...
        ]
    }
    """

    def post(self, request, test_type):
        try:
            # Validate test type
            if test_type not in VALID_TESTS:
                return JsonResponse({
                    'detail': f'Invalid test type. Valid: {", ".join(VALID_TESTS)}'
                }, status=400)

            # Parse request body
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'detail': 'Invalid JSON'}, status=400)

            lang = body.get('lang', 'tr')
            responses = body.get('responses', [])

            # Validate responses
            if not isinstance(responses, list) or len(responses) == 0:
                return JsonResponse({
                    'detail': 'responses array required'
                }, status=400)

            # Load questionnaire
            test_data = _load_questions(test_type)
            if not test_data:
                return JsonResponse({
                    'detail': f'Questionnaire not found: {test_type}'
                }, status=404)

            # Score test
            breakdown = _score_test(test_data, responses)

            # Calculate overall score
            all_scores = [v['score'] for v in breakdown.values()]
            overall_score = sum(all_scores) / len(all_scores) if all_scores else 0

            # Interpret overall
            if overall_score >= 4.5:
                overall_level = 'Very High'
                overall_level_tr = 'Çok Yüksek'
            elif overall_score >= 3.5:
                overall_level = 'High'
                overall_level_tr = 'Yüksek'
            elif overall_score >= 2.5:
                overall_level = 'Moderate'
                overall_level_tr = 'Orta'
            elif overall_score >= 1.5:
                overall_level = 'Low'
                overall_level_tr = 'Düşük'
            else:
                overall_level = 'Very Low'
                overall_level_tr = 'Çok Düşük'

            # Generate personalized recommendations using Ollama
            recommendations_result = generate_recommendations(
                test_type=test_type,
                breakdown=breakdown,
                overall_score=overall_score,
                lang=lang
            )

            return JsonResponse({
                'success': True,
                'data': {
                    'test_type': test_type,
                    'completed_at': __import__('time').time(),
                    'overall_score': round(overall_score, 2),
                    'overall_level': overall_level,
                    'overall_level_tr': overall_level_tr,
                    'breakdown': breakdown,
                    'responses_counted': len([r for r in responses if r.get('q_id')]),
                    'recommendations': recommendations_result.get('recommendations', []),
                    'recommendations_status': recommendations_result.get('status', 'unknown'),
                }
            })

        except Exception as e:
            log.exception(f'Error submitting test: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


# ── Assessment Results Storage (MongoDB) ──────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class SaveAssessmentResultView(View):
    """
    POST /api/v1/assessment/results/{test_type}/

    Save assessment result to MongoDB.

    Body:
    {
        "overall_score": 3.5,
        "overall_level_tr": "Yüksek",
        "breakdown": {...},
        "recommendations": [...],
        "responses_counted": 20
    }
    """

    def post(self, request, test_type):
        try:
            # Validate test type
            if test_type not in VALID_TESTS:
                return JsonResponse({
                    'detail': f'Invalid test type. Valid: {", ".join(VALID_TESTS)}'
                }, status=400)

            # Parse request body
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'detail': 'Invalid JSON'}, status=400)

            # Get user (if authenticated)
            user_id = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_id = str(request.user.id)

            # Save to MongoDB
            from admin_api.utils.mongo import get_assessment_results_col
            from datetime import datetime
            from bson import ObjectId

            col = get_assessment_results_col()
            result_doc = {
                '_id': ObjectId(),
                'user_id': user_id,
                'test_type': test_type,
                'overall_score': body.get('overall_score'),
                'overall_level_tr': body.get('overall_level_tr'),
                'breakdown': body.get('breakdown', {}),
                'recommendations': body.get('recommendations', []),
                'responses_counted': body.get('responses_counted'),
                'created_at': datetime.utcnow(),
            }

            inserted = col.insert_one(result_doc)

            return JsonResponse({
                'success': True,
                'data': {
                    'result_id': str(inserted.inserted_id),
                    'test_type': test_type,
                    'saved_at': result_doc['created_at'].isoformat(),
                }
            })

        except Exception as e:
            log.exception(f'Error saving assessment result: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class GetAssessmentHistoryView(View):
    """
    GET /api/v1/assessment/history/?limit=10

    Get user's assessment history from MongoDB.
    """

    def get(self, request):
        try:
            # Get user (if authenticated)
            user_id = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_id = str(request.user.id)
            else:
                return JsonResponse({
                    'detail': 'Authentication required'
                }, status=401)

            # Get limit from query params
            limit = int(request.GET.get('limit', 10))
            if limit > 100:
                limit = 100

            # Query MongoDB
            from admin_api.utils.mongo import get_assessment_results_col

            col = get_assessment_results_col()
            results = list(col.find(
                {'user_id': user_id},
                sort=[('created_at', -1)],
            ).limit(limit))

            # Format results
            formatted = []
            for r in results:
                formatted.append({
                    'id': str(r['_id']),
                    'test_type': r.get('test_type'),
                    'overall_score': r.get('overall_score'),
                    'overall_level_tr': r.get('overall_level_tr'),
                    'created_at': r.get('created_at').isoformat() if r.get('created_at') else None,
                    'responses_counted': r.get('responses_counted'),
                })

            return JsonResponse({
                'success': True,
                'data': {
                    'results': formatted,
                    'count': len(formatted),
                }
            })

        except Exception as e:
            log.exception(f'Error fetching assessment history: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
