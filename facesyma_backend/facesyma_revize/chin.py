"""
chin.py
=======
Chin shape and characteristics measurements using MediaPipe 468 landmarks.

Measures chin shape (pointed/round), width, and projection.
Key landmarks: 152 (chin tip), 172 (left jaw), 397 (right jaw), 166/391 (chin edges)
"""

import cv2
import mediapipe as mp

chin_landmarks = [152, 172, 397, 166, 391]  # chin tip, left jaw, right jaw, chin left, chin right


def chin_input(img):
    """
    Extract chin landmark coordinates from image.

    Returns dict with chin measurements:
        {
            "152": (x, y),     # chin tip
            "172": (x, y),     # left jaw
            "397": (x, y),     # right jaw
            "166": (x, y),     # left chin edge
            "391": (x, y)      # right chin edge
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
            for j in range(0, len(chin_landmarks)):
                pt1 = facial_landmarks.landmark[chin_landmarks[j]]
                x = int(pt1.x * width)
                y = int(pt1.y * height)
                lis.append((x, y))
            return lis

    list = draw()
    chin_cor = {
        "152": list[0],     # chin tip
        "172": list[1],     # left jaw
        "397": list[2],     # right jaw
        "166": list[3],     # left chin edge
        "391": list[4]      # right chin edge
    }
    return chin_cor


def measure_chin(img):
    """
    Measure chin characteristics from image.

    Returns dict with measurements:
        {
            "chin_shape": ratio,
            "chin_width": distance,
            "chin_projection": distance,
            "chin_category": "pointed" | "golden" | "round"
        }
    """
    chin = chin_input(img)

    # Chin width: distance between chin left and right edges
    chin_width = abs(chin["166"][0] - chin["391"][0])

    # Chin projection: vertical distance from jaw line to chin tip
    jaw_y = (chin["172"][1] + chin["397"][1]) / 2
    chin_y = chin["152"][1]
    chin_projection = abs(chin_y - jaw_y)

    # Chin shape ratio: width / height
    if chin_projection > 0:
        chin_shape = round(chin_width / chin_projection, 2)
    else:
        chin_shape = 1.0

    # Categorize
    if chin_shape < 1.5:
        chin_category = "chin_pointed"
    elif chin_shape > 2.0:
        chin_category = "chin_round"
    else:
        chin_category = "chin_balanced"

    return {
        "chin_shape": chin_shape,
        "chin_width": chin_width,
        "chin_projection": chin_projection,
        "chin_category": chin_category,
        "chin_projection_category": "strong" if chin_projection > 25 else "weak"
    }


# Test
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = measure_chin(sys.argv[1])
        print(f"Chin measurements: {result}")
    else:
        print("Usage: python chin.py <image_path>")
