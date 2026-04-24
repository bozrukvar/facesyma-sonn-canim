"""
cheekbone.py
============
Cheekbone prominence measurements using MediaPipe 468 landmarks.

Measures cheekbone height, width, and prominence relative to jaw.
Key landmarks: 234 (left cheekbone), 454 (right cheekbone), 172/397 (jaw)
"""

import cv2
import mediapipe as mp

cheekbone_landmarks = [234, 454, 172, 397]  # left cheek, right cheek, left jaw, right jaw


def cheekbone_input(img):
    """
    Extract cheekbone landmark coordinates from image.

    Returns dict with cheekbone measurements:
        {
            "234": (x, y),     # left cheekbone
            "454": (x, y),     # right cheekbone
            "172": (x, y),     # left jaw
            "397": (x, y)      # right jaw
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
            for j in range(0, len(cheekbone_landmarks)):
                pt1 = facial_landmarks.landmark[cheekbone_landmarks[j]]
                x = int(pt1.x * width)
                y = int(pt1.y * height)
                lis.append((x, y))
            return lis

    list = draw()
    cheekbone_cor = {
        "234": list[0],     # left cheekbone
        "454": list[1],     # right cheekbone
        "172": list[2],     # left jaw
        "397": list[3]      # right jaw
    }
    return cheekbone_cor


def measure_cheekbone(img):
    """
    Measure cheekbone characteristics from image.

    Returns dict with measurements:
        {
            "cheekbone_width": ratio,
            "cheekbone_prominence": ratio,
            "cheekbone_category": "low" | "golden" | "high"
        }
    """
    cheekbone = cheekbone_input(img)

    _c234 = cheekbone["234"]
    _c454 = cheekbone["454"]
    _c172 = cheekbone["172"]
    _c397 = cheekbone["397"]

    # Cheekbone width: distance between left and right cheekbones
    cheek_width = abs(_c234[0] - _c454[0])

    # Jaw width reference
    jaw_width = abs(_c172[0] - _c397[0])

    # Cheekbone to jaw ratio
    cheekbone_ratio = round(cheek_width / jaw_width, 2)

    # Categorize (higher cheekbone-to-jaw ratio = more prominent)
    if cheekbone_ratio < 0.9:
        cheekbone_category = "cheekbone_low"
    elif cheekbone_ratio > 1.1:
        cheekbone_category = "cheekbone_high"
    else:
        cheekbone_category = "cheekbone_golden"

    # Cheekbone prominence: vertical distance from cheekbone to jaw
    cheek_y = (_c234[1] + _c454[1]) / 2
    jaw_y = (_c172[1] + _c397[1]) / 2
    prominence = abs(cheek_y - jaw_y)

    return {
        "cheekbone_width": cheekbone_ratio,
        "cheekbone_width_rate": cheek_width,
        "cheekbone_category": cheekbone_category,
        "cheekbone_prominence": prominence,
        "cheekbone_prominence_category": "prominent" if prominence > 40 else "subtle"
    }


# Test
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = measure_cheekbone(sys.argv[1])
        print(f"Cheekbone measurements: {result}")
    else:
        print("Usage: python cheekbone.py <image_path>")
