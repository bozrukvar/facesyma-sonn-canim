import cv2
import mediapipe as mp


#forehead = ([10,151,55,285,8,356,127,152])

forehead = ([8,9,10,151,152])

def help():
    print("Input = x = face.face_input(img) one output = dic")

def forehead_input(img):
    lis = []  # Fixed: moved inside function to avoid global state persistence
    image = cv2.imread(img)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh()
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    result = face_mesh.process(rgb_image)
    height, width, _ = image.shape

    def draw():
        for facial_landmarks in result.multi_face_landmarks:
            for j in range(0, len(forehead)):
                pt1 = facial_landmarks.landmark[forehead[j]]
                x = int(pt1.x * width)
                y = int(pt1.y * height)

                #print(forehead[j])
                #cv2.circle(image, (x,y), 1, (0, 255, 0), 2)
                #cv2.imshow("da", image)
                #cv2.waitKey(0)

                lis.append((x,y))
            return lis
    list = draw()
    _l2 = list[2]
    _l2_1 = _l2[1]
    a = _l2[0]
    b = _l2_1 - list[3][1]
    c = _l2_1 + b
    f = (a,c)

    forehead_cor = {"f":f,"8":list[0],"9":list[1],"152":list[4]}

    return forehead_cor



#forehead_input("0.jpg")




