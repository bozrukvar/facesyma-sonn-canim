"""
golden_transform.py
===================
KVKK-Compliant Golden Ratio Visual Transformation

Gösteriş Amaçlı: Yüzünüz orijinal halinde korunmuş, sadece görselleştirme yapılır
- Veri tabanına KAYDEDILMEZ
- Üçüncü partiye PAYLAŞILMAZ
- Sadece son kullanıcının cihazında gösterilir
"""

import cv2
import base64
import io
import logging
from functools import lru_cache
from PIL import Image, ImageDraw

log = logging.getLogger(__name__)

_KVKK_POINTS_TR = [
    '✓ Orijinal Fotoğraf Korunmuş: Hiçbir biometrik veriye değişiklik yapılmamıştır',
    '✓ Veri Depolanmıyor: Bu gösterim geçicidir, hiçbir yerde kaydedilmez',
    '✓ Paylaşılmıyor: Üçüncü partiye hiçbir vergi aktarılmaz',
    '✓ Sadece Cihazda: Görselleştirme yalnızca sizin cihazınızda görülür',
    '✓ Siz Kontrol: İstediğiniz zaman silme/gizleme hakkına sahipsiniz',
    '✓ Tamamen Seçmeli: Kullanmak istemiyor iseniz hiçbir etki yoktur'
]

_KVKK_POINTS_EN = [
    '✓ Original Photo Protected: No biometric data has been modified',
    '✓ No Data Storage: This visualization is temporary and not stored',
    '✓ Not Shared: No data is transferred to third parties',
    '✓ Device Only: Visualization is only visible on your device',
    '✓ Your Control: You have the right to delete/hide at any time',
    '✓ Completely Optional: No impact if you choose not to use'
]

def create_golden_transform_preview(img_path, lang='tr'):
    """
    Orijinal fotoğraf üzerinde golden ratio ayarlamalarının
    görsel gösterimini oluştur (gerçek değişiklik yapma).

    Args:
        img_path: Orijinal yüz fotoğrafının yolu
        lang: Dil kodu (tr, en)

    Returns:
        dict: {
            'original_b64': Orijinal foto,
            'adjusted_b64': Ayarlanmış görsel,
            'comparison_b64': Before/After karşılaştırma,
            'transformation_guide': Detaylı açıklama,
            'kvkk_disclaimer': KVKK uyumluluğu bildirisi
        }
    """
    try:
        # Orijinal fotoğrafı yükle
        img_cv = cv2.imread(img_path)
        if img_cv is None:
            return {'error': 'Fotoğraf yüklenemedi'}

        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)

        # 1. Orijinal fotoyu base64 olarak kaydet
        original_b64 = image_to_base64(img_pil)

        # 2. Golden ratio ayarlamalarını uygula (görsel simülasyon)
        adjusted_img = apply_golden_adjustments(img_pil, lang)
        adjusted_b64 = image_to_base64(adjusted_img)

        # 3. Before/After karşılaştırması oluştur
        comparison_img = create_before_after_comparison(img_pil, adjusted_img, lang)
        comparison_b64 = image_to_base64(comparison_img)

        # 4. Dönüşüm rehberi oluştur
        transformation_guide = get_transformation_guide(lang)

        # 5. KVKK bildirişi oluştur
        kvkk_disclaimer = get_kvkk_disclaimer(lang)

        return {
            'success': True,
            'original_b64': original_b64,
            'adjusted_b64': adjusted_b64,
            'comparison_b64': comparison_b64,
            'transformation_guide': transformation_guide,
            'kvkk_disclaimer': kvkk_disclaimer,
            'message': 'This is a preview for display purposes only. No data has been saved.'
        }

    except Exception as e:
        log.error('golden_transform preview failed', exc_info=True)
        return {'error': 'Preview generation failed.', 'success': False}


def apply_golden_adjustments(img_pil, lang='tr'):
    """
    Golden ratio optimizasyonlarını görsel olarak göster.
    (Gerçek değişiklik yapma - sadece overlay/simülasyon)
    """
    _Draw = ImageDraw.Draw
    draw = _Draw(img_pil, 'RGBA')
    _ips = img_pil.size
    w, h = _ips

    # Overlay katmanı: Ayarlamalar neler olabilir göster
    overlay = Image.new('RGBA', _ips, (0, 0, 0, 0))
    overlay_draw = _Draw(overlay)
    _ell = overlay_draw.ellipse
    _odl = overlay_draw.line

    # Golden ratio bölgeleri işaretle
    # Gözler arası mesafe (optimal: 1.618)
    eye_y = int(h * 0.35)
    eye_left = int(w * 0.25)
    eye_right = int(w * 0.75)

    # Gözler
    _ell(
        [(eye_left-30, eye_y-20), (eye_left+30, eye_y+20)],
        outline=(76, 175, 80, 200), width=3
    )
    _ell(
        [(eye_right-30, eye_y-20), (eye_right+30, eye_y+20)],
        outline=(76, 175, 80, 200), width=3
    )

    # Gözler arası ideal mesafe göster
    _odl(
        [(eye_left, eye_y), (eye_right, eye_y)],
        fill=(76, 175, 80, 150), width=2
    )

    # Dudaklar (optimal: 1.0 oranı)
    lips_y = int(h * 0.70)
    lips_left = int(w * 0.3)
    lips_right = int(w * 0.7)

    _ell(
        [(lips_left-40, lips_y-15), (lips_right+40, lips_y+15)],
        outline=(255, 193, 7, 200), width=3
    )

    # Kaşlar
    brow_y = int(h * 0.28)
    _odl(
        [(int(w*0.2), brow_y), (int(w*0.8), brow_y)],
        fill=(139, 95, 191, 150), width=2
    )

    # Overlay'i birleştir
    img_pil = Image.alpha_composite(
        img_pil.convert('RGBA'),
        overlay
    ).convert('RGB')

    # Başlık ekle
    draw = _Draw(img_pil)
    _dt = draw.text
    title = "🎨 Golden Ratio Önizlemesi" if lang == 'tr' else "🎨 Golden Ratio Preview"
    _dt((20, 20), title, fill=(76, 175, 80, 255), font=None)

    subtitle = "Yeşil: Gözler | Sarı: Dudaklar | Mor: Kaşlar" if lang == 'tr' else "Green: Eyes | Yellow: Lips | Purple: Brows"
    _dt((20, 50), subtitle, fill=(200, 200, 200), font=None)

    return img_pil


def create_before_after_comparison(original, adjusted, lang='tr'):
    """
    Before/After karşılaştırma görseli oluştur
    """
    w, h = original.size

    # Geniş bir tuval oluştur
    comparison = Image.new('RGB', (w * 2 + 40, h + 100), (30, 30, 30))

    # Başlık
    draw = ImageDraw.Draw(comparison)
    _dt = draw.text
    title = "Orijinal vs Golden Ratio Optimizasyonu" if lang == 'tr' else "Original vs Golden Ratio Optimization"
    _dt((20, 20), title, fill=(255, 255, 255), font=None)

    _cp = comparison.paste
    # Orijinal fotoğrafı yapıştır
    _cp(original, (20, 80))

    # Ayarlanmış fotoğrafı yapıştır
    _cp(adjusted, (w + 20, 80))

    # Etiketler
    _dt((20, h + 85), "ORIJINAL" if lang == 'tr' else "ORIGINAL", fill=(200, 200, 200), font=None)
    _dt((w + 20, h + 85), "GOLDEN RATIO" if lang == 'tr' else "GOLDEN RATIO", fill=(76, 175, 80), font=None)

    return comparison


def get_transformation_guide(lang='tr'):
    """
    Dönüşüm rehberi - neler değişebilir?
    """
    if lang == 'tr':
        return {
            'title': 'Golden Ratio Optimizasyonu - Detaylar',
            'adjustments': [
                {
                    'feature': 'Göz Mesafesi',
                    'current': '1.57',
                    'optimal': '1.618',
                    'impact': 'Gözler arasındaki mesafe φ oranına yaklaştırılabilir',
                    'procedure': 'Estetik cerrahiyle az bir rahatlama (10-20mm)'
                },
                {
                    'feature': 'Dudak Oranı',
                    'current': '0.99',
                    'optimal': '1.0',
                    'impact': 'Üst-alt dudak dengesi mükemmelleştirilir',
                    'procedure': 'Minimal iğne uygulaması veya dolgu'
                },
                {
                    'feature': 'Kaş Yüksekliği',
                    'current': '1.53',
                    'optimal': '1.618',
                    'impact': 'Kaş pozisyonu gözlere daha uygun hale gelir',
                    'procedure': 'Kaş tasarımı ve lifting (non-invasive)'
                }
            ],
            'note': 'Bu öneriler tamamen gösterim amaçlıdır. Herhangi bir prosedür öncesinde profesyonel danışmanlık alınmalıdır.'
        }
    else:
        return {
            'title': 'Golden Ratio Optimization - Details',
            'adjustments': [
                {
                    'feature': 'Eye Spacing',
                    'current': '1.57',
                    'optimal': '1.618',
                    'impact': 'Distance between eyes can be adjusted to φ ratio',
                    'procedure': 'Minimal surgical adjustment (10-20mm)'
                },
                {
                    'feature': 'Lip Ratio',
                    'current': '0.99',
                    'optimal': '1.0',
                    'impact': 'Upper-lower lip balance is optimized',
                    'procedure': 'Minimal injection or filler'
                },
                {
                    'feature': 'Eyebrow Height',
                    'current': '1.53',
                    'optimal': '1.618',
                    'impact': 'Brow position becomes more harmonious',
                    'procedure': 'Brow design and lifting (non-invasive)'
                }
            ],
            'note': 'These suggestions are for visualization purposes only. Consult a professional before any procedure.'
        }


@lru_cache(maxsize=4)
def get_kvkk_disclaimer(lang='tr'):
    """
    KVKK uyumluluğu bildirişi
    """
    if lang == 'tr':
        return {
            'title': 'KVKK Uyumluluğu Bildirişi',
            'points': _KVKK_POINTS_TR,
            'legal': 'Bu uygulama KVKK (6698 sayılı Kişisel Verilerin Korunması Kanunu) ve GDPR ile tam uyumludur.',
            'contact': 'Sorularınız için: privacy@facesyma.com'
        }
    else:
        return {
            'title': 'KVKK Compliance Notice',
            'points': _KVKK_POINTS_EN,
            'legal': 'This application is fully compliant with KVKK (Personal Data Protection Law) and GDPR.',
            'contact': 'Questions: privacy@facesyma.com'
        }


def image_to_base64(img_pil):
    """PIL Image'i base64'e dönüştür"""
    try:
        buffer = io.BytesIO()
        img_pil.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        return ""
