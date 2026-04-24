import cv2
import mediapipe as mp
from eye import eye_input

#lip = ([61,291,87,317,37,267,17,152,2,38,268])
lip = ([0,2,13,14,17,37,61,219,267,291,439])

def help():
    print("Input = x = lip.lip_input(img) one output = dic")

def lip_input(img):
    lis = []  # Fixed: moved inside function to avoid global state persistence
    eye = eye_input(img)
    image = cv2.imread(img)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh()
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    result = face_mesh.process(rgb_image)
    height, width, _ = image.shape

    def draw():
        for facial_landmarks in result.multi_face_landmarks:
            for j in range(0, len(lip)):
                pt1 = facial_landmarks.landmark[lip[j]]
                x = int(pt1.x * width)
                y = int(pt1.y * height)
                #print(lip[j])
                #cv2.circle(image, (x,y),2,(0,255,0),-2,1)
                #cv2.imshow("image",image)
                #cv2.waitKey(0)
                lis.append((x, y))
            return lis

    list = draw()
    #print(eye["il"][0])
    _eil = eye["il"]; _e157 = eye["157"]
    onex = int((_eil[0] + _e157[0]) / 2)
    oney = int((_eil[1] + _e157[1]) / 2)
    el = (onex,oney)

    _eir = eye["ir"]; _e398 = eye["398"]
    twox = int((_eir[0] + _e398[0]) / 2)
    twoy = int((_eir[1] + _e398[1]) / 2)
    er = (twox,twoy)

    lip_cor = {"el": el, "er": er, "0":list[0], "2":list[1], "13":list[2], "14":list[3], "17":list[4], "37":list[5],
               "61":list[6],"219":list[7], "267":list[8], "291":list[9], "439":list[10] }

    #print(lip_cor)
    return lip_cor



#lip_input("3.jpg")







