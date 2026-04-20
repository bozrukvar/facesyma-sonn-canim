import cv2
import mediapipe as mp
import numpy as np
from iris import iris_input

eye = ([7,157,398,249])

def help():
    print("Input = x = eye.eye_input(img) one output = dic")

def eye_input(img):
    lis = []  # Fixed: moved inside function to avoid global state persistence
    iris = iris_input(img)
    image = cv2.imread(img)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh()
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    result = face_mesh.process(rgb_image)
    height, width, _ = image.shape

    def draw():
        for facial_landmarks in result.multi_face_landmarks:
            for j in range(0, len(eye)):
                pt1 = facial_landmarks.landmark[eye[j]]
                x = int(pt1.x * width)
                y = int(pt1.y * height)

                #print(eye[j])
                #cv2.circle(image, (x,y), 1, (0, 255, 0), 2)
                #cv2.imshow("da", image)
                #cv2.waitKey(0)

                lis.append((x,y))
            return lis
    list = draw()

    eye_cor = {"il": iris["il"],"ir":iris["ir"],"33":list[0],"157":list[1] ,"398": list[2],"263":list[3]}
    #print(eye_cor)
    return eye_cor
#eye_input("3.jpg")





