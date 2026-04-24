from bisect import bisect_left, bisect_right
import numpy as np
from PIL import Image, ImageOps
from PIL.Image import Image as PILImage
from typing import Sequence, Tuple, Union
import cv2
from math import ceil

# Optional fdlite imports - not available in production
try:
    from fdlite.face_detection import FaceDetection, FaceDetectionModel
    from fdlite.face_landmark import FaceLandmark, face_detection_to_roi
    from fdlite.iris_landmark import IrisLandmark, IrisResults
    from fdlite.iris_landmark import iris_roi_from_face_landmarks
    from fdlite.transform import bbox_from_landmarks
    FDLITE_AVAILABLE = True
except ImportError:
    FDLITE_AVAILABLE = False

def help():
    print("Input = r,l = iris_cor.iris_input(img) two output = iris_l(), iris_r()")
def iris_input(img):
    """Extract iris landmarks. Returns default values if fdlite is not available."""
    if not FDLITE_AVAILABLE:
        # Fallback: return dummy iris coordinates
        return {"il": (0, 0), "ir": (0, 0)}

    img = Image.open(img)
    _isize = _isize
    face_detection = FaceDetection()
    detections = face_detection(img)
    face_roi = face_detection_to_roi(detections[0], _isize)

    face_landmarks = FaceLandmark()
    landmarks = face_landmarks(img, face_roi)
    eyes_roi = iris_roi_from_face_landmarks(landmarks, _isize)

    iris_landmarks = IrisLandmark()
    left_eye_roi, right_eye_roi = eyes_roi

    def iris_l():
        left_eye_results = iris_landmarks(img, left_eye_roi)
        bbox = bbox_from_landmarks(left_eye_results.iris).absolute(_isize)
        width, height = int(bbox.width + 1), int(bbox.height + 1)
        size = (width, height)
        left, top = int(bbox.xmin), int(bbox.ymin)

        loc = ceil((2*left + width)/2),  ceil((2*top + height)/2)
        return loc
    def iris_r():
        right_eye_results = iris_landmarks(img, right_eye_roi, is_right_eye=True)
        bbox = bbox_from_landmarks(right_eye_results.iris).absolute(_isize)
        width, height = int(bbox.width + 1), int(bbox.height + 1)
        size = (width, height)
        left, top = int(bbox.xmin), int(bbox.ymin)

        loc = ceil((2*left + width)/2),  ceil((2*top + height)/2)
        return loc

    iris_cor = {"il": iris_l(),"ir": iris_r()}

    return iris_cor
#iris_input("nose1.png")