import cv2
import mediapipe as mp
from iris import iris_input

nose = ([0,2,17,219,294])

def nose_input(img):
    nosee = []  # Fixed: moved inside function to avoid global state persistence
    iris = iris_input(img)
    image = cv2.imread(img)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh()
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    result = face_mesh.process(rgb_image)
    height, width, _ = image.shape

    def draw_nose():
        for facial_landmarks in result.multi_face_landmarks:

            for j in range(0, len(nose)):
                pt1 = facial_landmarks.landmark[nose[j]]
                x = int(pt1.x * width)
                y = int(pt1.y * height)
                nosee.append((x,y))
                #print(nose[j])
                #cv2.circle(image, (x,y), 1, (0, 255, 0), 2)
                #cv2.imshow("da", image)
                #cv2.waitKey(0)

        return nosee

    list = draw_nose()
    nose_cor = {"il": iris["il"], "ir": iris["ir"],"0":list[0] ,"2":list[1] ,"17":list[2] ,"219":list[3] ,"294":list[4] }
    return nose_cor
    #print(nose_cor)
#nose_input("nose1.png")

