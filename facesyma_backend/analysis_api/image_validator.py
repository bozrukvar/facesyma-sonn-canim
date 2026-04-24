"""
image_validator.py
==================
Server-side image quality validation.

Backend'de de kontrol yaparak mobile'dan gelen
kalitesiz fotoğrafları reddet.

Fonksiyonlar:
  - validate_image_quality(): Tüm kontrolleri yap
  - calculate_brightness(): Parlaklık hesapla
  - calculate_contrast(): Kontrast hesapla
  - check_face_position(): Yüz konumunu kontrol et
"""

import cv2
import numpy as np
import logging

log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# IMAGE QUALITY VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

class ImageQualityValidator:
    """Fotoğraf kalitesini kontrol et"""

    # Thresholds
    MIN_BRIGHTNESS = 30        # Minimum brightness (0-255)
    MAX_BRIGHTNESS = 240       # Maximum brightness
    MIN_CONTRAST = 20          # Minimum contrast score
    MAX_FACE_OFFSET = 25       # Maximum face offset from center (%)
    MIN_IMAGE_SIZE = 200       # Minimum image dimension

    @staticmethod
    def validate_image_quality(image_path: str) -> dict:
        """
        Tüm kalite kontrolleri yap

        Returns:
        {
            'overall_score': 0-100,
            'brightness': {'value': 0-255, 'score': 0-100},
            'contrast': {'value': 0-100, 'score': 0-100},
            'face_position': {'offset': 0-100, 'score': 0-100},
            'recommendation': 'str',
            'can_upload': True/False,
            'errors': []
        }
        """
        errors = []
        _eappend = errors.append
        scores = {}

        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return {
                    'overall_score': 0,
                    'brightness': {'value': 0, 'score': 0},
                    'contrast': {'value': 0, 'score': 0},
                    'face_position': {'offset': 0, 'score': 0},
                    'recommendation': 'Fotoğraf okunamadı',
                    'can_upload': False,
                    'errors': ['Image file corrupted']
                }

            # Check image size
            _msize = ImageQualityValidator.MIN_IMAGE_SIZE
            height, width = image.shape[:2]
            if width < _msize or height < _msize:
                _eappend(f'Image too small: {width}x{height}')

            # ── Brightness ────────────────────────────────────────────────────
            brightness = ImageQualityValidator.calculate_brightness(image)
            brightness_score = ImageQualityValidator.score_brightness(brightness)
            _brightness_int = int(brightness)
            scores['brightness'] = {
                'value': _brightness_int,
                'score': brightness_score,
                'status': 'good' if brightness_score >= 70 else 'poor'
            }
            _sb = scores['brightness']

            if brightness < ImageQualityValidator.MIN_BRIGHTNESS:
                _eappend(f'Image too dark: {_brightness_int}/255')
            if brightness > ImageQualityValidator.MAX_BRIGHTNESS:
                _eappend(f'Image too bright: {_brightness_int}/255')

            # ── Contrast ───────────────────────────────────────────────────────
            contrast = ImageQualityValidator.calculate_contrast(image)
            contrast_score = ImageQualityValidator.score_contrast(contrast)
            _contrast_int = int(contrast)
            scores['contrast'] = {
                'value': _contrast_int,
                'score': contrast_score,
                'status': 'good' if contrast_score >= 60 else 'poor'
            }
            _sc = scores['contrast']

            if contrast < ImageQualityValidator.MIN_CONTRAST:
                _eappend(f'Low contrast: {_contrast_int}/100')

            # ── Face Detection & Position ──────────────────────────────────────
            face_offset, face_score = ImageQualityValidator.check_face_position(image)
            scores['face_position'] = {
                'offset': face_offset,
                'score': face_score,
                'status': 'centered' if face_score >= 80 else 'off_center'
            }
            _sfp = scores['face_position']

            if face_offset > ImageQualityValidator.MAX_FACE_OFFSET:
                _eappend(f'Face off-center: {face_offset}% offset')

            # ── Calculate Overall Score ────────────────────────────────────────
            overall_score = int(
                brightness_score * 0.25 +
                contrast_score * 0.25 +
                face_score * 0.5
            )

            # ── Recommendation ─────────────────────────────────────────────────
            recommendation = ''
            can_upload = overall_score >= 60 and len(errors) == 0

            if overall_score >= 80:
                recommendation = 'Mükemmel kalite!'
            elif overall_score >= 60:
                recommendation = 'İyi kalite, devam edilebilir'
            elif overall_score >= 40:
                recommendation = 'Kalitesi düşük, uyarı ver'
            else:
                recommendation = 'Kalitesi çok düşük, reddet'

            return {
                'overall_score': overall_score,
                'brightness': _sb,
                'contrast': _sc,
                'face_position': _sfp,
                'recommendation': recommendation,
                'can_upload': can_upload,
                'errors': errors
            }

        except Exception as e:
            log.error(f'Image quality validation failed: {e}')
            return {
                'overall_score': 0,
                'brightness': {'value': 0, 'score': 0},
                'contrast': {'value': 0, 'score': 0},
                'face_position': {'offset': 0, 'score': 0},
                'recommendation': 'Image validation failed. Please try a different photo.',
                'can_upload': False,
                'errors': ['Validation error.']
            }

    @staticmethod
    def calculate_brightness(image) -> float:
        """
        Ortalama parlaklığı hesapla (0-255)

        Yöntem: Gri resme dönüştür, ortalaması al
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            return brightness
        except Exception as e:
            log.warning(f'Brightness calculation failed: {e}')
            return 128  # Default

    @staticmethod
    def score_brightness(brightness: float) -> int:
        """
        Parlaklık değerini 0-100 puanına dönüştür

        Ranges:
        - 0-40: Dark (0-50 points)
        - 40-200: Good (100 points)
        - 200-255: Bright (100-0 points)
        """
        if brightness < 40:
            return int((brightness / 40) * 50)
        if brightness <= 200:
            return 100
        if brightness <= 240:
            return 100 - int(((brightness - 200) / 40) * 25)
        return max(0, 100 - int(((brightness - 240) / 15) * 50))

    @staticmethod
    def calculate_contrast(image) -> float:
        """
        Kontrast seviyesini hesapla (0-100)

        Kontrast = (Max - Min) / (Max + Min) * 100
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            min_val = np.min(gray)
            max_val = np.max(gray)

            if (max_val + min_val) == 0:
                return 0

            contrast = ((max_val - min_val) / (max_val + min_val)) * 100
            return np.clip(contrast, 0, 100)
        except Exception as e:
            log.warning(f'Contrast calculation failed: {e}')
            return 50  # Default

    @staticmethod
    def score_contrast(contrast: float) -> int:
        """
        Kontrast değerini 0-100 puanına dönüştür

        Ranges:
        - 0-30: Low (0-50 points)
        - 30-70: Good (100 points)
        - 70-100: High (100 points)
        """
        if contrast < 30:
            return int((contrast / 30) * 50)
        return 100

    @staticmethod
    def check_face_position(image) -> tuple:
        """
        Yüzün konumunu kontrol et

        Returns: (offset_percent, score)
        - offset_percent: Max offset from center (0-50)
        - score: Quality score (0-100)
        """
        _warn = log.warning
        try:
            # Import face detector from mediapipe
            import mediapipe as mp
            mp_face = mp.solutions.face_detection

            face_detector = mp_face.FaceDetection(
                model_selection=0,
                min_detection_confidence=0.5
            )

            # Detect faces
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_detector.process(image_rgb)
            _rdet = results.detections

            height, width = image.shape[:2]
            image_area = width * height

            if not _rdet:
                # No face detected
                _warn('No face detected in image')
                return (50, 0)  # Worst score

            # Get first face (largest)
            detection = _rdet[0]
            bbox = detection.location_data.relative_bounding_box

            # Calculate face center
            face_center_x = bbox.xmin + bbox.width / 2
            face_center_y = bbox.ymin + bbox.height / 2

            # Calculate offset from image center
            image_center_x = 0.5
            image_center_y = 0.5

            offset_x = abs(face_center_x - image_center_x) * 100
            offset_y = abs(face_center_y - image_center_y) * 100
            max_offset = max(offset_x, offset_y)

            # Score: 100 if centered, 0 if at edge
            if max_offset <= 15:
                score = 100
            elif max_offset <= 25:
                score = 70
            else:
                score = max(0, 100 - (max_offset - 25) * 5)

            return (max_offset, int(score))

        except ImportError:
            _warn('MediaPipe not available for face position check')
            return (0, 100)  # Assume centered
        except Exception as e:
            _warn(f'Face position check failed: {e}')
            return (0, 100)  # Assume centered


# ══════════════════════════════════════════════════════════════════════════════
# USAGE IN VIEWS
# ══════════════════════════════════════════════════════════════════════════════

"""
Example usage in views.py:

from analysis_api.image_validator import ImageQualityValidator

def _run_analysis(img_path: str, mode: str, lang: str = 'tr', **kwargs):
    '''Validate image quality first'''

    # Validate image
    quality = ImageQualityValidator.validate_image_quality(img_path)

    if not quality['can_upload']:
        # Log for monitoring
        log.warning(f'Low quality image rejected: {quality["errors"]}')

        # Optionally raise error
        if len(quality['errors']) > 0:
            raise ValueError(f"Image quality too low: {quality['recommendation']}")

    # Continue with analysis
    from database import databases
    return databases(img_path, lang)
"""
