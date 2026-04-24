import cv2
import mediapipe as mp

face = ([10,151,55,285,8,356,127,152])

face_cor = {}
lis = []
def help():
    print("Input = x = face.face_input(img) one output = dic")

def face_input(img):
    image = cv2.imread(img)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh()
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    result = face_mesh.process(rgb_image)
    height, width, _ = image.shape

    def draw():
        for facial_landmarks in result.multi_face_landmarks:
            for j in range(0, len(face)):
                pt1 = facial_landmarks.landmark[face[j]]
                x = int(pt1.x * width)
                y = int(pt1.y * height)

                #print(face[j])
                #cv2.circle(image, (x,y), 1, (0, 255, 0), 2)
                #cv2.imshow("da", image)
                #cv2.waitKey(0)

                lis.append((x,y))
            return lis
    list = draw()
    _l0 = list[0]
    _l0_1 = _l0[1]
    a = _l0[0]
    b = _l0_1 - list[1][1]
    c = _l0_1 + b

    face_cor[34] = (a,c)
    face_cor[35] = list[2]
    face_cor[36] = list[3]
    face_cor[37] = list[4]
    face_cor[25] = list[5]
    face_cor[24] = list[6]
    face_cor[10] = list[7]

    return face_cor


#face_input(path)




