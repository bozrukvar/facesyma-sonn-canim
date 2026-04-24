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
    _append = points.append

    _append(eye[1])
    _append(eye[2])
    _append(eye[12])
    _append(eye[13])
    _append(eye[24])
    _append(eye[25])
    _append(eye[26])
    _append(eye[27])
    _append(eye[30])
    _append(eye[31])

    _append(eyebrow[18])
    _append(eyebrow[19])
    _append(eyebrow[20])
    _append(eyebrow[21])
    _append(eyebrow[22])
    _append(eyebrow[23])


    _append(lip[1])
    _append(lip[2])
    _append(lip[3])
    _append(lip[4])
    _append(lip[5])
    _append(lip[6])
    _append(lip[7])
    _append(lip[8])
    _append(lip[9])
    _append(lip[10])
    _append(lip[11])
    _append(lip[12])
    _append(lip[13])

    _append(nose[14])
    _append(nose[15])
    _append(nose[16])
    _append(nose[17])

    _append(face[34])
    _append(face[37])
    _append(face[10])

    return points
