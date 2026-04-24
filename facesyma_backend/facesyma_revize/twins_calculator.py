from one_face import *
from two_face import *

def Match(face1,face2):
    x = Cal1(face1)
    y = Cal2(face2)

    _x1 = x[1]; _x4 = x[4]

    def Eye():
        _x0 = x[0]; _y0 = y[0]
        _ed = _x0['eyes_distance']
        _es = _x0['eyes_size']
        _ec = _x0['eyes_compare']
        if(_ed == _y0['eyes_distance']):
            eyes_distance = _ed
        else:
            eyes_distance = "not_defined"

        if (_es == _y0['eyes_size']):
            eyes_size = _es
        else:
            eyes_size = "not_defined"

        if (_ec == _y0['eyes_compare']):
            eyes_compare = _ec
        else:
            eyes_compare = "not_defined"
        eyes_dict = {"eyes_distance": eyes_distance, "eyes_size":eyes_size, "eyes_compare":eyes_compare}
        return eyes_dict
    def Eyebrow():
        _x1eed = _x1['eyebrows_eyes_distance']
        if (_x1eed == y[1]['eyebrows_eyes_distance']):
            eyebrows_eyes_distance = _x1eed
        else:
            eyebrows_eyes_distance = "not_defined"
        eyebrow_dict = {"eyebrows_eyes_distance": eyebrows_eyes_distance}
        return eyebrow_dict
    def Lip():
        _x2 = x[2]; _y2 = y[2]
        _lw = _x2['lips_width']
        _lt = _x2['lips_thickness']
        _lhc = _x2['lips_height_compare']
        _lhs = _x2['lips_height_status_result']
        if (_lw == _y2['lips_width']):
            lips_width = _lw
        else:
            lips_width = "not_defined"

        if (_lt == _y2['lips_thickness']):
            lips_thickness = _lt
        else:
            lips_thickness = "not_defined"

        if (_lhc == _y2['lips_height_compare']):
            lips_height_compare = _lhc
        else:
            lips_height_compare = "not_defined"

        if (_lhs == _y2['lips_height_status_result']):
            lips_height_status_result = _lhs
        else:
            lips_height_status_result = "not_defined"

        lip_dict = {"lips_width": lips_width, "lips_thickness": lips_thickness, "lips_height_compare":lips_height_compare,"lips_height_status_result":lips_height_status_result}
        return lip_dict
    def Nose():
        _x3 = x[3]; _y3 = y[3]
        _nl = _x3['nose_length']
        _nw = _x3['nose_width']
        _ns = _x3['nose_size']
        if (_nl == _y3['nose_length']):
            nose_length = _nl
        else:
            nose_length = "not_defined"

        if (_nw == _y3['nose_width']):
            nose_width = _nw
        else:
            nose_width = "not_defined"

        if (_ns == _y3['nose_size']):
            nose_size = _ns
        else:
            nose_size = "not_defined"

        nose_dict = {"nose_length": nose_length, "nose_width":nose_width, "nose_size": nose_size}
        return nose_dict

    def Forehead():
        _x4fd = _x4['forehead_distance']
        if (_x4fd == y[4]['forehead_distance']):
            forehead_distance = _x4fd
        else:
            forehead_distance = "not_defined"
        forehead_dict = {"forehead_distance":forehead_distance}
        return forehead_dict

    return Eye(), Eyebrow(), Lip(), Nose(), Forehead(), x, y
