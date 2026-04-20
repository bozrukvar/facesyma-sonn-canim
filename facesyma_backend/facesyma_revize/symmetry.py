"""
symmetry.py
===========
Facial symmetry measurement using MediaPipe 468 landmarks.

Compares left/right landmark pairs to calculate overall facial symmetry score.
Symmetry score ranges 0-1, where 1.0 = perfect symmetry.
"""

import cv2
import mediapipe as mp
import math

# Key landmark pairs for symmetry check (left/right)
symmetry_pairs = [
    (33, 263),    # outer eye corners
    (159, 386),   # eye bottom
    (158, 385),   # eye inner bottom
    (161, 388),   # eye outer bottom
    (121, 350),   # cheekbone
    (118, 347),   # cheekbone upper
    (172, 397),   # jaw corners
    (166, 391),   # chin sides
    (80, 309),    # nostril
    (55, 285),    # mouth corners
]


def symmetry_input(img):
    """
    Extract all facial landmark coordinates for symmetry analysis.

    Returns dict with landmark IDs and their (x, y) coordinates.
    """
    image = cv2.imread(img)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh()
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    result = face_mesh.process(rgb_image)
    height, width, _ = image.shape

    landmarks_dict = {}

    for facial_landmarks in result.multi_face_landmarks:
        for idx, landmark in enumerate(facial_landmarks.landmark):
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            landmarks_dict[idx] = (x, y)

    return landmarks_dict


def measure_symmetry(img):
    """
    Measure facial symmetry by comparing left/right landmark pairs.

    Returns dict with measurements:
        {
            "overall_symmetry": 0-1,
            "symmetry_details": {
                "eyes": 0-1,
                "cheekbones": 0-1,
                "jaw": 0-1,
                "mouth": 0-1
            },
            "symmetry_category": "asymmetric" | "balanced" | "symmetric"
        }
    """
    landmarks = symmetry_input(img)

    if not landmarks:
        return {"overall_symmetry": 0.5, "symmetry_category": "unknown"}

    # Find face center (use landmark 0 as reference)
    if 0 not in landmarks:
        center_x = sum(x for x, y in landmarks.values()) / len(landmarks)
    else:
        center_x = landmarks[0][0]

    # Measure distances for each pair
    pair_scores = []

    for left_idx, right_idx in symmetry_pairs:
        if left_idx in landmarks and right_idx in landmarks:
            left_point = landmarks[left_idx]
            right_point = landmarks[right_idx]

            # Distance from center for left point
            left_distance = abs(left_point[0] - center_x)
            # Distance from center for right point
            right_distance = abs(right_point[0] - center_x)

            # Y-coordinate should be similar
            y_diff = abs(left_point[1] - right_point[1])

            # Calculate symmetry score for this pair
            # 1.0 = perfect symmetry, 0.0 = completely asymmetric
            if left_distance + right_distance > 0:
                distance_ratio = min(left_distance, right_distance) / max(left_distance, right_distance)
            else:
                distance_ratio = 1.0

            # Y-position penalty (should be at same height)
            y_penalty = max(0, 1.0 - (y_diff / 50.0))  # Normalize to 50px tolerance

            pair_score = (distance_ratio * 0.7) + (y_penalty * 0.3)
            pair_scores.append(pair_score)

    # Calculate averages by category
    eyes_score = pair_scores[0] if len(pair_scores) > 0 else 0.5
    cheekbones_score = (pair_scores[3] + pair_scores[4]) / 2 if len(pair_scores) > 4 else 0.5
    jaw_score = (pair_scores[5] + pair_scores[6]) / 2 if len(pair_scores) > 6 else 0.5
    mouth_score = pair_scores[-1] if len(pair_scores) > 0 else 0.5

    # Overall symmetry
    overall_symmetry = round(sum(pair_scores) / len(pair_scores) if pair_scores else 0.5, 3)

    # Categorize
    if overall_symmetry > 0.85:
        symmetry_category = "highly_symmetric"
    elif overall_symmetry > 0.75:
        symmetry_category = "balanced"
    elif overall_symmetry > 0.60:
        symmetry_category = "slightly_asymmetric"
    else:
        symmetry_category = "very_asymmetric"

    return {
        "overall_symmetry": overall_symmetry,
        "symmetry_details": {
            "eyes": round(eyes_score, 3),
            "cheekbones": round(cheekbones_score, 3),
            "jaw": round(jaw_score, 3),
            "mouth": round(mouth_score, 3)
        },
        "symmetry_category": symmetry_category
    }


# Test
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = measure_symmetry(sys.argv[1])
        print(f"Symmetry measurements: {result}")
    else:
        print("Usage: python symmetry.py <image_path>")
