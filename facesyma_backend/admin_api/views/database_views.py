"""
admin_api/views/database_views.py
==================================
Sıfat veritabanı JSON yönetimi (CRUD + dil ekleme + otomatik çeviri).
"""

import json
import os
import re
import threading
from pathlib import Path
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

from admin_api.utils.auth import _require_admin


def _json(request):
    """Request body JSON'ı parse et"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


# ──── Atomik JSON yazma (thread-safe) ──────────────────────────────────────────
_file_lock = threading.Lock()


def _load_sifat_db() -> dict:
    """Sıfat veritabanını diskten oku"""
    try:
        with open(settings.SIFAT_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'metadata': {'total_sifatlar': 0}, 'sifatlar': {}}
    except json.JSONDecodeError:
        return {'metadata': {'total_sifatlar': 0}, 'sifatlar': {}}


def _save_sifat_db(data: dict) -> bool:
    """
    Sıfat veritabanını diskten kaydet (atomik).
    Önce .tmp dosyasına yaz, sonra os.replace() ile taşı.

    Returns: True başarılı, False başarısız
    """
    with _file_lock:
        try:
            db_path = Path(settings.SIFAT_DB_PATH)
            tmp_path = db_path.parent / f"{db_path.name}.tmp"

            # Tmp dosyasına yaz
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomik taşı
            os.replace(tmp_path, db_path)
            return True
        except Exception as e:
            # Tmp dosyasını temizle
            try:
                os.remove(tmp_path)
            except:
                pass
            return False


def _translate_with_google(text: str, target_lang: str) -> str:
    """
    Google Translate API ile çevir (opsiyonel).

    target_lang: 'en', 'de', vb.
    Returns: çevirilen metin veya orijinal metin (API key yoksa)
    """
    api_key = settings.GOOGLE_TRANSLATE_API_KEY
    if not api_key:
        return text  # Anahtarı yoksa, orijinali döner

    try:
        from google.cloud import translate_v2
        client = translate_v2.Client(api_key=api_key)
        result = client.translate_text(text, target_language=target_lang)
        return result['translatedText']
    except Exception as e:
        # Hata varsa orijinali döner, API hatası fırlatmaz
        return text


# ═══════════════════════════════════════════════════════════════════════════════
# ── Sıfat Listesi ──────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class SifatListView(View):
    """
    Tüm sıfatları listele (sayfalanmış, filtreleme, arama).

    GET /api/v1/admin/database/sifatlar/?page=1&limit=10&tur=Orijinal&search=güzel
    Query params:
        - page: int (default 1)
        - limit: int (default 10, max 50)
        - tur: str ("Orijinal" vb)
        - search: str (sıfat adı'nda arama)
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        # Query params
        page = max(1, int(request.GET.get('page', 1)))
        limit = min(int(request.GET.get('limit', 10)), 50)
        tur_filter = request.GET.get('tur', '').strip()
        search = request.GET.get('search', '').strip().lower()

        db = _load_sifat_db()
        sifatlar = db.get('sifatlar', {})

        # Filter ve arama
        filtered = []
        for key, sifat in sifatlar.items():
            # Tür filtresi
            if tur_filter and sifat.get('tur') != tur_filter:
                continue

            # Arama
            if search and search not in sifat.get('ad', '').lower():
                continue

            filtered.append({
                'no': sifat.get('no'),
                'ad': sifat.get('ad'),
                'tur': sifat.get('tur'),
                'cumle_count': len(sifat.get('cumleler', [])),
            })

        # Sayfalama
        total = len(filtered)
        start = (page - 1) * limit
        end = start + limit
        paginated = filtered[start:end]

        return JsonResponse({
            'sifatlar': paginated,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,
            }
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Sıfat Detayı ───────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class SifatDetailView(View):
    """
    Tek sıfatın detayı.

    GET /api/v1/admin/database/sifatlar/<no>/
    """

    def get(self, request, no):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        db = _load_sifat_db()
        sifatlar = db.get('sifatlar', {})
        sifat = sifatlar.get(str(no))

        if not sifat:
            return JsonResponse(
                {'detail': f'Sıfat #{no} bulunamadı.'},
                status=404
            )

        return JsonResponse(sifat)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Sıfat Oluştur ──────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class SifatCreateView(View):
    """
    Yeni sıfat ekle.

    POST /api/v1/admin/database/sifatlar/
    Body: {
        ad: str,
        tur: str ("Orijinal", vb),
        grup_no: int,
        cumleler: [{no: int, metin: str}, ...]
    }
    """

    def post(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        data = _json(request)

        # Doğrulama
        if not data.get('ad'):
            return JsonResponse({'detail': 'Sıfat adı zorunlu.'}, status=400)
        if not data.get('tur'):
            return JsonResponse({'detail': 'Sıfat türü zorunlu.'}, status=400)

        db = _load_sifat_db()
        sifatlar = db.get('sifatlar', {})

        # Sonraki ID
        next_id = max([int(k) for k in sifatlar.keys()], default=0) + 1

        # Yeni sıfat
        new_sifat = {
            'no': next_id,
            'grup_no': data.get('grup_no', 1),
            'tur': data.get('tur'),
            'ad': data.get('ad'),
            'cumleler': data.get('cumleler', []),
        }

        sifatlar[str(next_id)] = new_sifat

        # Metadata güncelle
        db['metadata']['total_sifatlar'] = len(sifatlar)

        # Kaydet
        if not _save_sifat_db(db):
            return JsonResponse(
                {'detail': 'Dosya kaydedilemedi.'},
                status=500
            )

        return JsonResponse({
            'message': f'Sıfat oluşturuldu: #{next_id}',
            'sifat': new_sifat
        }, status=201)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Sıfat Güncelle ────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class SifatUpdateView(View):
    """
    Sıfat güncelle.

    PATCH /api/v1/admin/database/sifatlar/<no>/
    Body: {ad?, tur?, grup_no?, cumleler?}
    """

    def patch(self, request, no):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        data = _json(request)
        db = _load_sifat_db()
        sifatlar = db.get('sifatlar', {})

        sifat = sifatlar.get(str(no))
        if not sifat:
            return JsonResponse(
                {'detail': f'Sıfat #{no} bulunamadı.'},
                status=404
            )

        # Güncellenebilir alanlar
        if 'ad' in data:
            sifat['ad'] = data['ad']
        if 'tur' in data:
            sifat['tur'] = data['tur']
        if 'grup_no' in data:
            sifat['grup_no'] = data['grup_no']
        if 'cumleler' in data:
            sifat['cumleler'] = data['cumleler']

        # Kaydet
        if not _save_sifat_db(db):
            return JsonResponse(
                {'detail': 'Dosya kaydedilemedi.'},
                status=500
            )

        return JsonResponse({
            'message': f'Sıfat güncellendi: #{no}',
            'sifat': sifat
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Sıfat Sil ──────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class SifatDeleteView(View):
    """
    Sıfat sil.

    DELETE /api/v1/admin/database/sifatlar/<no>/
    """

    def delete(self, request, no):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        db = _load_sifat_db()
        sifatlar = db.get('sifatlar', {})

        if str(no) not in sifatlar:
            return JsonResponse(
                {'detail': f'Sıfat #{no} bulunamadı.'},
                status=404
            )

        deleted = sifatlar.pop(str(no))
        db['metadata']['total_sifatlar'] = len(sifatlar)

        # Kaydet
        if not _save_sifat_db(db):
            return JsonResponse(
                {'detail': 'Dosya kaydedilemedi.'},
                status=500
            )

        return JsonResponse({
            'message': f'Sıfat silindi: {deleted.get("ad")} (#{no})'
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Sıfata Cümle Ekle (Dil Ekleme) ──────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class SifatAddCumleView(View):
    """
    Sıfata yeni dilde cümleler ekle.

    POST /api/v1/admin/database/sifatlar/<no>/cumle/
    Body: {
        lang: str ("en", "de", vb. — "cumleler_" + lang olarak kaydedilir),
        cumleler: [{no: int, metin: str}, ...]
    }
    """

    def post(self, request, no):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        data = _json(request)
        lang = data.get('lang', '').strip().lower()
        cumleler = data.get('cumleler', [])

        if not lang:
            return JsonResponse({'detail': 'Dil kodu zorunlu (lang).'}, status=400)
        if not cumleler:
            return JsonResponse({'detail': 'Cümleler zorunlu.'}, status=400)

        db = _load_sifat_db()
        sifatlar = db.get('sifatlar', {})

        sifat = sifatlar.get(str(no))
        if not sifat:
            return JsonResponse(
                {'detail': f'Sıfat #{no} bulunamadı.'},
                status=404
            )

        # Alan adı: cumleler (Türkçe) veya cumleler_en, cumleler_de, vb.
        field_name = 'cumleler' if lang == 'tr' else f'cumleler_{lang}'

        # Cümleleri ekle
        sifat[field_name] = cumleler

        # Kaydet
        if not _save_sifat_db(db):
            return JsonResponse(
                {'detail': 'Dosya kaydedilemedi.'},
                status=500
            )

        return JsonResponse({
            'message': f'Sıfat #{no} için {lang.upper()} cümleleri eklendi.',
            'field': field_name,
            'cumle_count': len(cumleler),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Otomatik Çeviri (Google Translate) ───────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class SifatAutoTranslateView(View):
    """
    Google Translate ile otomatik çeviri (GOOGLE_TRANSLATE_API_KEY gerekli).

    POST /api/v1/admin/database/sifatlar/<no>/translate/
    Body: {
        source_lang: str ("tr"),
        target_lang: str ("en", "de", vb.),
        field: str ("cumleler" — kaynak alan adı)
    }

    Eğer API key yoksa 501 (Not Implemented) döner.
    """

    def post(self, request, no):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        # API key kontrol
        if not settings.GOOGLE_TRANSLATE_API_KEY:
            return JsonResponse(
                {'detail': 'Google Translate API key yapılandırılmamış.'},
                status=501
            )

        data = _json(request)
        target_lang = data.get('target_lang', '').strip().lower()
        source_field = data.get('field', 'cumleler')

        if not target_lang:
            return JsonResponse(
                {'detail': 'Hedef dil (target_lang) zorunlu.'},
                status=400
            )

        db = _load_sifat_db()
        sifatlar = db.get('sifatlar', {})

        sifat = sifatlar.get(str(no))
        if not sifat:
            return JsonResponse(
                {'detail': f'Sıfat #{no} bulunamadı.'},
                status=404
            )

        # Kaynak cümleleri al
        source_cumleler = sifat.get(source_field, [])
        if not source_cumleler:
            return JsonResponse(
                {'detail': f'Kaynak cümleleri bulunamadı ({source_field}).'},
                status=400
            )

        # Çevir
        translated = []
        for cumle_obj in source_cumleler:
            metin = cumle_obj.get('metin', '')
            translated_metin = _translate_with_google(metin, target_lang)

            translated.append({
                'no': cumle_obj.get('no'),
                'metin': translated_metin
            })

        # Hedef alan adı
        target_field = 'cumleler' if target_lang == 'tr' else f'cumleler_{target_lang}'

        # Ekle
        sifat[target_field] = translated

        # Kaydet
        if not _save_sifat_db(db):
            return JsonResponse(
                {'detail': 'Dosya kaydedilemedi.'},
                status=500
            )

        return JsonResponse({
            'message': f'Sıfat #{no} otomatik olarak {target_lang.upper()} diline çevrildi.',
            'field': target_field,
            'translated_count': len(translated),
        })


# ──── Dil Senkronizasyonu ───────────────────────────────────────────────────────

SUPPORTED_LANGUAGES = ['tr', 'en', 'de', 'fr', 'es', 'it', 'pt', 'ru', 'ar', 'zh', 'ja', 'ko', 'hi', 'bn', 'id', 'vi', 'pl', 'ur']


@method_decorator(csrf_exempt, name='dispatch')
class SifatSyncStatusView(View):
    """Dil çeviri durumunu kontrol et"""

    def get(self, request):
        try:
            db = _load_sifat_db()
            sifatlar = db.get('sifatlar', {})

            if not sifatlar:
                return JsonResponse({
                    'success': True,
                    'total_sifatlar': 0,
                    'languages': {}
                })

            total = len(sifatlar)
            language_status = {}

            for lang in SUPPORTED_LANGUAGES:
                field = 'cumleler' if lang == 'tr' else f'cumleler_{lang}'
                translated_count = sum(1 for s in sifatlar.values() if field in s and s[field])
                missing = total - translated_count

                language_status[lang] = {
                    'total': total,
                    'translated': translated_count,
                    'missing': missing,
                    'percentage': round((translated_count / max(total, 1)) * 100, 1)
                }

            return JsonResponse({
                'success': True,
                'total_sifatlar': total,
                'languages': language_status
            })

        except Exception as e:
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SifatBatchSyncView(View):
    """Toplu dil çevirisi tetikle"""

    def post(self, request):
        try:
            data = _json(request)
            target_lang = data.get('lang', 'en')

            if target_lang not in SUPPORTED_LANGUAGES:
                return JsonResponse(
                    {'detail': f'Desteklenmeyen dil: {target_lang}'},
                    status=400
                )

            if target_lang == 'tr':
                return JsonResponse(
                    {'detail': 'Türkçe çevirisi zaten mevcut (kaynak dil)'},
                    status=400
                )

            db = _load_sifat_db()
            sifatlar = db.get('sifatlar', {})

            if not sifatlar:
                return JsonResponse({'detail': 'Sıfat veritabanı boş'}, status=400)

            target_field = f'cumleler_{target_lang}'
            translated_count = 0
            skipped_count = 0
            error_count = 0

            for no_str, sifat in sifatlar.items():
                # Eğer zaten çevrilmişse atla
                if target_field in sifat and sifat[target_field]:
                    skipped_count += 1
                    continue

                # Kaynağı al (Türkçe)
                source_cumleler = sifat.get('cumleler', [])
                if not source_cumleler:
                    error_count += 1
                    continue

                try:
                    # Çevir
                    translated = []
                    for cumle_obj in source_cumleler:
                        metin = cumle_obj.get('metin', '')
                        translated_metin = _translate_with_google(metin, target_lang)

                        translated.append({
                            'no': cumle_obj.get('no'),
                            'metin': translated_metin
                        })

                    # Güncelle
                    sifat[target_field] = translated
                    translated_count += 1

                except Exception as e:
                    error_count += 1

            # Kaydet
            if not _save_sifat_db(db):
                return JsonResponse(
                    {'detail': 'Dosya kaydedilemedi'},
                    status=500
                )

            return JsonResponse({
                'success': True,
                'lang': target_lang,
                'translated_count': translated_count,
                'skipped_count': skipped_count,
                'error_count': error_count,
                'total': len(sifatlar)
            })

        except Exception as e:
            return JsonResponse({'detail': str(e)}, status=500)
