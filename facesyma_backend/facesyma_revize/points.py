from eye import *
from eyebrow import *
from lip import *
from nose import *
from face import *

points = []
def point(img):
    eye = eye_input(img)
    eyebrow = eyebrow_input(img)
    lip = lip_input(img)
    nose = nose_input(img)
    face = face_input(img)

    points.append(eye[1])
    points.append(eye[2])
    points.append(eye[12])
    points.append(eye[13])
    points.append(eye[24])
    points.append(eye[25])
    points.append(eye[26])
    points.append(eye[27])
    points.append(eye[30])
    points.append(eye[31])

    points.append(eyebrow[18])
    points.append(eyebrow[19])
    points.append(eyebrow[20])
    points.append(eyebrow[21])
    points.append(eyebrow[22])
    points.append(eyebrow[23])


    points.append(lip[1])
    points.append(lip[2])
    points.append(lip[3])
    points.append(lip[4])
    points.append(lip[5])
    points.append(lip[6])
    points.append(lip[7])
    points.append(lip[8])
    points.append(lip[9])
    points.append(lip[10])
    points.append(lip[11])
    points.append(lip[12])
    points.append(lip[13])

    points.append(nose[14])
    points.append(nose[15])
    points.append(nose[16])
    points.append(nose[17])

    points.append(face[34])
    points.append(face[37])
    points.append(face[10])

    return points
