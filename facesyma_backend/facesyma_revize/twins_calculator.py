from one_face import *
from two_face import *

def Match(face1,face2):
    x = Cal1(face1)
    y = Cal2(face2)

    def Eye():
        if(x[0]['eyes_distance'] == y[0]['eyes_distance']):
            eyes_distance = x[0]["eyes_distance"]
        else:
            eyes_distance = "not_defined"

        if (x[0]['eyes_size'] == y[0]['eyes_size']):
            eyes_size = x[0]["eyes_size"]
        else:
            eyes_size = "not_defined"

        if (x[0]['eyes_compare'] == y[0]['eyes_compare']):
            eyes_compare = x[0]["eyes_compare"]
        else:
            eyes_compare = "not_defined"
        eyes_dict = {"eyes_distance": eyes_distance, "eyes_size":eyes_size, "eyes_compare":eyes_compare}
        return eyes_dict
    def Eyebrow():
        if (x[1]['eyebrows_eyes_distance'] == y[1]['eyebrows_eyes_distance']):
            eyebrows_eyes_distance = x[1]["eyebrows_eyes_distance"]
        else:
            eyebrows_eyes_distance = "not_defined"
        eyebrow_dict = {"eyebrows_eyes_distance": eyebrows_eyes_distance}
        return eyebrow_dict
    def Lip():
        if (x[2]['lips_width'] == y[2]['lips_width']):
            lips_width = x[2]["lips_width"]
        else:
            lips_width = "not_defined"

        if (x[2]['lips_thickness'] == y[2]['lips_thickness']):
            lips_thickness = x[2]["lips_thickness"]
        else:
            lips_thickness = "not_defined"

        if (x[2]['lips_height_compare'] == y[2]['lips_height_compare']):
            lips_height_compare = x[2]["lips_height_compare"]
        else:
            lips_height_compare = "not_defined"

        if (x[2]['lips_height_status_result'] == y[2]['lips_height_status_result']):
            lips_height_status_result = x[2]["lips_height_status_result"]
        else:
            lips_height_status_result = "not_defined"

        lip_dict = {"lips_width": lips_width, "lips_thickness": lips_thickness, "lips_height_compare":lips_height_compare,"lips_height_status_result":lips_height_status_result}
        return lip_dict
    def Nose():
        if (x[3]['nose_length'] == y[3]['nose_length']):
            nose_length = x[3]["nose_length"]
        else:
            nose_length = "not_defined"

        if (x[3]['nose_width'] == y[3]['nose_width']):
            nose_width = x[3]["nose_width"]
        else:
            nose_width = "not_defined"

        if (x[3]['nose_size'] == y[3]['nose_size']):
            nose_size = x[3]["nose_size"]
        else:
            nose_size = "not_defined"

        nose_dict = {"nose_length": nose_length, "nose_width":nose_width, "nose_size": nose_size}
        return nose_dict

    def Forehead():
        if (x[4]['forehead_distance'] == y[4]['forehead_distance']):
            forehead_distance = x[4]["forehead_distance"]
        else:
            forehead_distance = "not_defined"
        forehead_dict = {"forehead_distance":forehead_distance}
        return forehead_dict

    return Eye(), Eyebrow(), Lip(), Nose(), Forehead(), x, y
