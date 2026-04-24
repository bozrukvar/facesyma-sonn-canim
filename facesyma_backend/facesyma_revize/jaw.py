"""
jaw.py
======
Jaw/chin line measurements using MediaPipe 468 landmarks.

Measures jaw width, definition, and contour quality.
Key landmarks: 172 (left jaw), 397 (right jaw), 152 (chin tip), 10 (crown)
"""

import cv2
import mediapipe as mp

jaw_landmarks = [10, 152, 172, 397]  # crown, chin, left jaw, right jaw


def jaw_input(img):
    """
    Extract jaw landmark coordinates from image.

    Returns dict with jaw measurements:
        {
            "10": (x, y),      # crown/forehead top
            "152": (x, y),     # chin tip
            "172": (x, y),     # left jaw corner
            "397": (x, y)      # right jaw corner
        }
    """
    lis = []
    image = cv2.imread(img)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh()
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    result = face_mesh.process(rgb_image)
    height, width, _ = image.shape

    def draw():
        for facial_landmarks in result.multi_face_landmarks:
            for j in range(0, len(jaw_landmarks)):
                pt1 = facial_landmarks.landmark[jaw_landmarks[j]]
                x = int(pt1.x * width)
                y = int(pt1.y * height)
                lis.append((x, y))
            return lis

    list = draw()
    jaw_cor = {
        "10": list[0],      # crown
        "152": list[1],     # chin
        "172": list[2],     # left jaw
        "397": list[3]      # right jaw
    }
    return jaw_cor


def measure_jaw(img):
    """
    Measure jaw characteristics from image.

    Returns dict with measurements:
        {
            "jaw_width": ratio,
            "jaw_definition": ratio,
            "jaw_category": "narrow" | "golden" | "wide"
        }
    """
    jaw = jaw_input(img)
    _j172 = jaw["172"]; _j397 = jaw["397"]

    # Jaw width: distance between left and right jaw corners
    jaw_width = abs(_j172[0] - _j397[0])

    # Face width reference: use landmarks from wider part of face
    # Approximate face width using standard proportions
    avg_face_width = jaw_width * 1.1  # Jaw is typically narrower than face

    # Calculate ratio
    jaw_ratio = round(jaw_width / avg_face_width, 2)

    # Categorize
    if jaw_ratio < 1.5371:
        jaw_category = "jaw_narrow"
    elif jaw_ratio > 1.6989:
        jaw_category = "jaw_wide"
    else:
        jaw_category = "jaw_width_golden"

    # Jaw definition: vertical distance from chin to jaw corners
    chin_y = jaw["152"][1]
    jaw_y = (_j172[1] + _j397[1]) / 2
    jaw_definition = abs(chin_y - jaw_y)

    return {
        "jaw_width": jaw_ratio,
        "jaw_width_rate": jaw_width,
        "jaw_width_category": jaw_category,
        "jaw_definition": jaw_definition,
        "jaw_definition_category": "defined" if jaw_definition > 30 else "soft"
    }


# Test
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = measure_jaw(sys.argv[1])
        print(f"Jaw measurements: {result}")
    else:
        print("Usage: python jaw.py <image_path>")
