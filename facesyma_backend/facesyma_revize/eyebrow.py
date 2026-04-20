import cv2
import mediapipe as mp
import numpy as np

#eyebrow = [63, 293,159,386,145, 374]
eyebrow = [105,145,159,334,374,386]

def help():
    print("Input = x = eyebrow.eyebrow_input(img) one output = dic")

def eyebrow_input(img):
    lis = []  # Fixed: moved inside function to avoid global state persistence
    image = cv2.imread(img)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh()
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    result = face_mesh.process(rgb_image)
    height, width, _ = image.shape

    def draw():
        for facial_landmarks in result.multi_face_landmarks:
            for j in range(0, len(eyebrow)):
                pt1 = facial_landmarks.landmark[eyebrow[j]]
                x = int(pt1.x * width)
                y = int(pt1.y * height)

                #print(eyebrow[j])
                #cv2.circle(image, (x,y), 1, (0, 255, 0), 2)
                #cv2.imshow("da", image)
                #cv2.waitKey(0)
                lis.append((x,y))

            return lis

    list = draw()
    eyebrow_cor = {"105": list[0], "145":list[1] , "159":list[2] , "334":list[3] , "374":list[4] , "386":list[5] }
    return eyebrow_cor

#eyebrow_input("3.jpg")










