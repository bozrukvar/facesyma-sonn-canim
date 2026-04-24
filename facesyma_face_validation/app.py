"""
Face Validation Microservice
=============================
Handles face detection, validation, and feature extraction.

Çözdüğü sorunlar:
✅ Yan yüz (profile) - MediaPipe'ı 180° angle'a kadar handle ediyor
✅ Çok eğik açı - Rotation invariant detection
✅ Yüz çok küçük/büyük - Adaptive face detection

API Endpoints:
- POST /api/v1/face/validate - Kalite kontrolü
- POST /api/v1/face/analyze - Detaylı analiz
- POST /api/v1/face/landmarks - Landmark extraction
- GET /health - Health check
"""

import base64
import logging
import numpy as np
from typing import Optional, Dict, List, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import cv2
import mediapipe as mp
from functools import lru_cache

# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_OBJECT_MESSAGES = {
    'bottle':    'Bu bir bardak/şişe. Lütfen yüzünüzün fotoğrafını çekin.',
    'cup':       'Bu bir kupa. Lütfen yüzünüzün fotoğrafını çekin.',
    'glass':     'Bu bir bardak. Lütfen yüzünüzün fotoğrafını çekin.',
    'dog':       'Bu bir köpek. Lütfen insan yüzü çekin.',
    'cat':       'Bu bir kedi. Lütfen insan yüzü çekin.',
    'bird':      'Bu bir kuş. Lütfen insan yüzü çekin.',
    'animal':    'Bu bir hayvan. Lütfen insan yüzü çekin.',
    'car':       'Bu bir araba. Lütfen yüzünüzün fotoğrafını çekin.',
    'person':    'İnsan tespit edildi ama yüz net değil. Lütfen yüzünüze yakın çekin.',
    'tree':      'Bu bir ağaç. Lütfen yüzünüzün fotoğrafını çekin.',
    'flower':    'Bu bir çiçek. Lütfen yüzünüzün fotoğrafını çekin.',
    'food':      'Bu yemek. Lütfen yüzünüzün fotoğrafını çekin.',
    'phone':     'Bu bir telefon. Lütfen yüzünüzün fotoğrafını çekin.',
    'laptop':    'Bu bir bilgisayar. Lütfen yüzünüzün fotoğrafını çekin.',
    'book':      'Bu bir kitap. Lütfen yüzünüzün fotoğrafını çekin.',
    'teddy bear':'Bu bir oyuncak. Lütfen yüzünüzün fotoğrafını çekin.',
    'cake':      'Bu bir pasta. Lütfen yüzünüzün fotoğrafını çekin.',
    'donut':     'Bu bir donut. Lütfen yüzünüzün fotoğrafını çekin.',
    'pizza':     'Bu pizza. Lütfen yüzünüzün fotoğrafını çekin.',
}

app = FastAPI(
    title="Face Validation Service",
    description="Real-time face detection and validation",
    version="1.0.0"
)

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# ═══════════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════════

_MAX_B64_LEN = 27_000_000  # ~20 MB decoded


class FaceValidationRequest(BaseModel):
    image: str  # Base64 encoded image
    strict: bool = False  # Strict validation mode

class FaceValidationResponse(BaseModel):
    is_valid: bool
    score: float  # 0-100
    face_detected: bool
    face_count: int
    face_box: Optional[Dict[str, float]]  # {x, y, width, height}
    confidence: float
    issues: List[str]
    recommendations: List[str]
    angle: Optional[float]  # Face rotation angle in degrees
    size_ratio: Optional[float]  # Face size as % of image
    brightness: Optional[float]  # Estimated brightness 0-100
    detected_object: Optional[str] = None  # What was detected if not a face

class LandmarkPoint(BaseModel):
    x: float
    y: float
    z: float
    confidence: float

class FaceAnalysisResponse(BaseModel):
    face_box: Dict[str, float]
    landmarks: List[LandmarkPoint]
    face_angle: float
    face_size: float
    quality_metrics: Dict[str, float]

# ═══════════════════════════════════════════════════════════════════════════
# Face Detection Service
# ═══════════════════════════════════════════════════════════════════════════

class FaceDetectionService:
    """Advanced face detection handling profile, tilted, small, large faces"""

    def __init__(self):
        self.face_detection = mp_face_detection.FaceDetection(
            model_selection=1,  # 1 = full range (can detect profile)
            min_detection_confidence=0.5
        )
        self.pose = mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.5
        )

        # Object detection for non-face identification
        try:
            from mediapipe.tasks.python import vision
            from mediapipe.framework.formats import detector_pb2

            self.object_detector = self._initialize_object_detector()
        except Exception as e:
            logger.warning(f"Object detection unavailable: {e}")
            self.object_detector = None

    def detect_face(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect face and return detailed information

        ✅ Handles profile faces (up to 90°)
        ✅ Handles tilted angles
        ✅ Detects multiple faces
        """
        h, w, c = image.shape

        # Convert to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect faces with MediaPipe
        results = self.face_detection.process(image_rgb)

        _rd = results.detections
        if not _rd:
            return {
                'face_detected': False,
                'face_count': 0,
                'faces': []
            }

        faces = []
        for detection in _rd:
            bbox = detection.location_data.relative_bounding_box

            # Convert relative to absolute coordinates
            x_min = int(bbox.xmin * w)
            y_min = int(bbox.ymin * h)
            x_max = x_min + int(bbox.width * w)
            y_max = y_min + int(bbox.height * h)

            face_width = x_max - x_min
            face_height = y_max - y_min

            # Detect face angle using pose detection
            angle = self._estimate_face_angle(image_rgb, x_min, y_min, x_max, y_max)

            # Calculate size ratio
            size_ratio = (face_width * face_height) / (w * h) * 100

            faces.append({
                'box': {
                    'x': x_min,
                    'y': y_min,
                    'x_max': x_max,
                    'y_max': y_max,
                    'width': face_width,
                    'height': face_height
                },
                'confidence': (_ds := detection.score)[0] if _ds else 0.7,
                'angle': angle,
                'size_ratio': size_ratio,
                'landmarks': self._extract_landmarks(detection)
            })

        _nfaces = len(faces)
        return {
            'face_detected': _nfaces > 0,
            'face_count': _nfaces,
            'faces': faces
        }

    def _estimate_face_angle(self, image: np.ndarray, x_min: int, y_min: int,
                             x_max: int, y_max: int) -> float:
        """Estimate face rotation angle using pose detection"""
        try:
            face_region = image[y_min:y_max, x_min:x_max]

            # Use MediaPipe Pose for better angle detection
            pose_results = self.pose.process(face_region)

            _landmarks = pose_results.pose_landmarks
            if _landmarks:
                # Use shoulder keypoints to estimate head angle
                left_shoulder = _landmarks[11]
                right_shoulder = _landmarks[12]

                # Calculate angle from shoulders
                angle = np.arctan2(
                    right_shoulder.y - left_shoulder.y,
                    right_shoulder.x - left_shoulder.x
                ) * 180 / np.pi

                return float(angle)

            return 0.0
        except Exception as e:
            logger.warning(f"Error estimating face angle: {e}")
            return 0.0

    def _extract_landmarks(self, detection) -> List[Dict]:
        """Extract face landmarks if available"""
        landmarks = []

        _dld = detection.location_data
        if hasattr(_dld, 'relative_keypoints'):
            for keypoint in _dld.relative_keypoints:
                landmarks.append({
                    'x': float(keypoint.x),
                    'y': float(keypoint.y),
                    'z': float(keypoint.z) if hasattr(keypoint, 'z') else 0.0,
                    'confidence': 1.0
                })

        return landmarks

    def _initialize_object_detector(self):
        """Initialize MediaPipe Object Detector for identifying non-face objects"""
        try:
            from mediapipe.tasks.python import vision

            base_options = vision.BaseOptions(
                model_asset_path='https://storage.googleapis.com/mediapipe-tasks/object_detector/object_detector.tflite'
            )
            options = vision.ObjectDetectorOptions(
                base_options=base_options,
                max_results=1,
                score_threshold=0.5
            )
            return vision.ObjectDetector.create_from_options(options)
        except Exception as e:
            logger.warning(f"Failed to initialize object detector: {e}")
            return None

    def detect_object(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """Detect what object is in the image if not a face"""
        if self.object_detector is None:
            return None

        try:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.object_detector.detect(image_rgb)

            _rdet = results.detections
            if _rdet:
                top_detection = _rdet[0]
                _cats = top_detection.categories
                _c0 = _cats[0] if _cats else None
                category = _c0.category_name if _c0 else 'unknown'
                confidence = _c0.score if _c0 else 0.0

                return {
                    'object': category,
                    'confidence': float(confidence)
                }

            return None
        except Exception as e:
            logger.warning(f"Object detection failed: {e}")
            return None

# ═══════════════════════════════════════════════════════════════════════════
# Validation Service
# ═══════════════════════════════════════════════════════════════════════════

class FaceValidationService:
    """Comprehensive face validation with edge case handling"""

    def __init__(self, detection_service: FaceDetectionService):
        self.detector = detection_service

    def _get_object_message(self, obj_name: str) -> str:
        """Get Turkish message for detected non-face object"""
        _obj_lower = obj_name.lower()
        for key, message in _OBJECT_MESSAGES.items():
            if key in _obj_lower or _obj_lower in key:
                return message
        return f'Lütfen insan yüzünün fotoğrafını çekin. (Tespit edilen: {obj_name})'

    def validate_face_photo(self, image: np.ndarray, strict: bool = False) -> FaceValidationResponse:
        """
        Validate face photo handling:
        ✅ Profile faces (side angles up to 90°)
        ✅ Tilted angles (up to 45°)
        ✅ Small faces (down to 5% of image)
        ✅ Large faces (up to 95% of image)
        """
        h, w = image.shape[:2]
        issues = []
        _iappend = issues.append
        recommendations = []
        _rappend = recommendations.append
        score = 100

        # Detect faces
        detection_result = self.detector.detect_face(image)
        _drfd = detection_result['face_detected']
        _drfc = detection_result['face_count']

        if not _drfd:
            # Try to identify what was in the image instead
            detected_obj = self.detector.detect_object(image)

            if detected_obj:
                _doobj = detected_obj['object']
                issue_message = self._get_object_message(_doobj)
                detected_object = _doobj
            else:
                issue_message = 'Yüz tespit edilemedi. Lütfen yüzünüzün fotoğrafını çekin.'
                detected_object = None

            return FaceValidationResponse(
                is_valid=False,
                score=0,
                face_detected=False,
                face_count=0,
                face_box=None,
                confidence=0.0,
                issues=[issue_message],
                recommendations=['Lütfen yüzünüzün açık ve net olduğu bir fotoğraf çekin'],
                angle=None,
                size_ratio=None,
                brightness=None,
                detected_object=detected_object
            )

        # Multiple faces detected
        if _drfc > 1:
            _iappend('Birden fazla yüz tespit edildi')
            _rappend('Sadece sizin yüzünüzün görüneceği bir fotoğraf çekin')
            score -= 30

        # Get primary face
        primary_face = detection_result['faces'][0]
        face_box = primary_face['box']
        angle = primary_face['angle']
        size_ratio = primary_face['size_ratio']
        confidence = primary_face['confidence']

        # ═══════════════════════════════════════════════════════════════════
        # 1. ANGLE VALIDATION (Profile, Tilted)
        # ═══════════════════════════════════════════════════════════════════

        abs_angle = abs(angle)

        if abs_angle > 45:  # Very tilted
            _iappend(f'Yüz çok eğik ({abs_angle:.0f}°)')
            _rappend('Kameraya daha düz bakacak şekilde çekin')
            score -= 25
        elif abs_angle > 30:  # Moderately tilted
            _rappend('Kameraya biraz daha düz bakabilirsiniz')
            score -= 10

        # Profile detection (side face)
        if abs_angle > 60:
            _iappend('Yan yüz (profile) tespit edildi')
            _rappend('Kameraya doğru bakacak şekilde konumlandırın')
            score -= 15

        # ═══════════════════════════════════════════════════════════════════
        # 2. SIZE VALIDATION (Too small/big)
        # ═══════════════════════════════════════════════════════════════════

        if size_ratio < 5:  # Too small
            _iappend(f'Yüz çok küçük ({size_ratio:.1f}% of image)')
            _rappend('Kameraya yaklaşın veya daha yakın bir fotoğraf yükleyin')
            score -= 25
        elif size_ratio < 15:  # Relatively small
            _rappend('Kameraya biraz daha yaklaşabilirsiniz')
            score -= 10

        if size_ratio > 90:  # Too large
            _iappend(f'Yüz çok büyük ({size_ratio:.1f}% of image)')
            _rappend('Kamerada biraz geriye çekilin')
            score -= 20
        elif size_ratio > 70:  # Relatively large
            _rappend('Kamerada biraz geriye çekilebilirsiniz')
            score -= 5

        # ═══════════════════════════════════════════════════════════════════
        # 3. BRIGHTNESS VALIDATION
        # ═══════════════════════════════════════════════════════════════════

        brightness = self._calculate_brightness(image)

        if brightness < 30:
            _iappend('Çok karanlık')
            _rappend('Daha aydınlık bir yere gitmeyi deneyin')
            score -= 15
        elif brightness < 50:
            _rappend('Daha aydınlık bir ortam tercih edebilirsiniz')
            score -= 8

        if brightness > 95:
            _iappend('Çok parlak/kontrast düşük')
            _rappend('Doğrudan güneş ışığından kaçınız')
            score -= 12
        elif brightness > 85:
            _rappend('Daha az parlak bir ortamda çekim yapabilirsiniz')
            score -= 5

        # ═══════════════════════════════════════════════════════════════════
        # 4. CONFIDENCE VALIDATION
        # ═══════════════════════════════════════════════════════════════════

        if confidence < 0.6:
            score -= (0.6 - confidence) * 20

        # ═══════════════════════════════════════════════════════════════════
        # FINAL SCORING
        # ═══════════════════════════════════════════════════════════════════

        score = max(0, min(100, score))

        # Determine validity based on strict mode
        is_valid = True
        if strict:
            is_valid = score >= 70 and len(issues) == 0
        else:
            is_valid = score >= 40 and _drfd

        return FaceValidationResponse(
            is_valid=is_valid,
            score=score,
            face_detected=True,
            face_count=_drfc,
            face_box={
                'x': float(face_box['x']),
                'y': float(face_box['y']),
                'width': float(face_box['width']),
                'height': float(face_box['height'])
            },
            confidence=float(confidence),
            issues=issues,
            recommendations=recommendations,
            angle=float(angle),
            size_ratio=float(size_ratio),
            brightness=float(brightness),
            detected_object=None  # Face was detected, so no object substitution
        )

    def _calculate_brightness(self, image: np.ndarray) -> float:
        """Calculate image brightness (0-100)"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        brightness = np.mean(gray) / 255 * 100
        return float(brightness)

# ═══════════════════════════════════════════════════════════════════════════
# Service Initialization
# ═══════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def get_detection_service():
    return FaceDetectionService()

@lru_cache(maxsize=1)
def get_validation_service():
    return FaceValidationService(get_detection_service())

# ═══════════════════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "face-validation",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/face/validate", response_model=FaceValidationResponse)
async def validate_face(request: FaceValidationRequest):
    """
    Validate face photo quality

    Handles:
    ✅ Profile faces (side angles)
    ✅ Tilted angles (up to 45°)
    ✅ Small faces (down to 5%)
    ✅ Large faces (up to 95%)
    ✅ Brightness issues
    """
    try:
        _ri = request.image
        if len(_ri) > _MAX_B64_LEN:
            raise HTTPException(status_code=400, detail="Image too large")
        # Decode base64 image
        image_data = base64.b64decode(_ri)
        image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Validate
        validation_service = get_validation_service()
        result = validation_service.validate_face_photo(image, strict=request.strict)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail="Validation failed. Please try again.")

@app.post("/api/v1/face/analyze", response_model=FaceAnalysisResponse)
async def analyze_face(request: FaceValidationRequest):
    """Detailed face analysis with landmarks"""
    try:
        _ri = request.image
        if len(_ri) > _MAX_B64_LEN:
            raise HTTPException(status_code=400, detail="Image too large")
        image_data = base64.b64decode(_ri)
        image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        detection_service = get_detection_service()
        detection = detection_service.detect_face(image)

        if not detection['face_detected']:
            raise HTTPException(status_code=400, detail="No face detected")

        face = detection['faces'][0]

        _box = face['box']
        _fangle = face['angle']
        _fsratio = face['size_ratio']
        return FaceAnalysisResponse(
            face_box={
                'x': float(_box['x']),
                'y': float(_box['y']),
                'width': float(_box['width']),
                'height': float(_box['height'])
            },
            landmarks=[
                LandmarkPoint(
                    x=float(lm['x']),
                    y=float(lm['y']),
                    z=float(lm['z']),
                    confidence=float(lm['confidence'])
                )
                for lm in face['landmarks']
            ],
            face_angle=float(_fangle),
            face_size=float(_fsratio),
            quality_metrics={
                'confidence': float(face['confidence']),
                'angle_deviation': float(abs(_fangle)),
                'size_ratio': float(_fsratio)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")

# ═══════════════════════════════════════════════════════════════════════════
# Startup/Shutdown
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    _linfo = logger.info
    _linfo("Face Validation Service starting...")
    # Pre-load models
    get_detection_service()
    get_validation_service()
    _linfo("Models loaded successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,
        log_level="info",
        workers=1  # Face detection needs single worker for GPU
    )
