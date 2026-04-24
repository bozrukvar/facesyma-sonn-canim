from eye import *
from eyebrow import *
from lip import *
from nose import *
from forehead import *
from scorer import score_ratio, get_sifat_score

def help():
    return "Dic Type İndex = {Eye} , {Eyeborn} , {Lip} , {Nose} , {Forehead} \n"


def Cal(img):
    eye = eye_input(img)
    eyebrow = eyebrow_input(img)
    lip = lip_input(img)
    nose = nose_input(img)
    forehead = forehead_input(img)
    _lip2  = lip['2']
    _lip17c = lip['17']
    _lip2_1 = _lip2[1]

    def Eye():
        _e398x = eye['398'][0]; _e157x = eye['157'][0]
        eyes_distance = round(abs(eye['ir'][0] - eye['il'][0]) / abs(_e398x - _e157x), 2)

        if eyes_distance < 1.5371:
            eyes_distance_result = "eyes_near"
        elif eyes_distance > 1.6989:
            eyes_distance_result = "eyes_far"
        else:
            eyes_distance_result = "eyes_distance_golden"

        eyes_size_r = round(abs(_e157x - _e398x) / abs(eye['33'][0] - _e157x), 2)

        if eyes_size_r < 1.5371:
            eyes_size_r_result = "eyes_size_r_big"
        elif eyes_size_r > 1.6989:
            eyes_size_r_result = "eyes_size_r_small"
        else:
            eyes_size_r_result = "eyes_distance_r_golden"

        eyes_size_l = round(abs(_e157x - _e398x) / abs(_e398x - eye['263'][0]), 2)

        if eyes_size_l < 1.5371:
            eyes_size_l_result = "eyes_size_l_big"
        elif eyes_size_l < 1.6989:
            eyes_size_l_result = "eyes_size_l_small"
        else:
            eyes_size_l_result = "eyes_distance_l_golden"

        if eyes_size_r_result == "eyes_size_r_small" and eyes_size_l_result == "eyes_size_l_small":
            eyes_size_result = "eyes_size_small"
        elif eyes_size_r_result == "eyes_size_r_big" and eyes_size_l_result == "eyes_size_l_big":
            eyes_size_result = "eyes_size_big"
        elif eyes_size_r_result == "eyes_size_r_golden" and eyes_size_l_result == "eyes_size_l_golden":
            eyes_size_result = "eyes_size_golden"
        else:
            eyes_size_result = "not_defined"

        if eyes_size_r > eyes_size_l * 1.05:
            eyes_compare = "right_eye_bigger_than_left_eye"
        elif eyes_size_r < eyes_size_l * 0.95:
            eyes_compare = "left_eye_bigger_than_right_eye"
        else:
            eyes_compare = "left_and_right_eyes_equal"

        # Enhanced: Add scores for each measurement
        eyes_dic = {
            "eyes_distance_rate": eyes_distance,
            "eyes_distance": eyes_distance_result,
            "eyes_distance_score": get_sifat_score(eyes_distance_result, eyes_distance),
            "eyes_size_r_rate": eyes_size_r,
            "eyes_size_r_result": eyes_size_r_result,
            "eyes_size_r_score": get_sifat_score(eyes_size_r_result, eyes_size_r),
            "eyes_size_l_rate": eyes_size_l,
            "eyes_size_l_result": eyes_size_l_result,
            "eyes_size_l_score": get_sifat_score(eyes_size_l_result, eyes_size_l),
            "eyes_size": eyes_size_result,
            "eyes_compare": eyes_compare
        }
        return eyes_dic

    def Eyebrow():
        _e159_1 = eyebrow['159'][1]
        oL = abs(eyebrow['105'][1] - _e159_1)
        pL = abs(eyebrow['145'][1] - _e159_1)
        eyebrows_eyes_distance_l = round(oL/pL,2)

        _e386_1 = eyebrow['386'][1]
        oR = abs(eyebrow['334'][1] - _e386_1)
        pR = abs(eyebrow['374'][1] - _e386_1)
        eyebrows_eyes_distance_r = round(oR / pR, 2)

        if eyebrows_eyes_distance_l > 1.6989 and eyebrows_eyes_distance_r > 1.6989:
            eyebrows_eyes_distance_result = "eyebrows_eyes_distance_far"
        elif eyebrows_eyes_distance_l < 1.5371 and eyebrows_eyes_distance_r < 1.5371:
            eyebrows_eyes_distance_result = "eyebrows_eyes_distance_near"
        else:
            eyebrows_eyes_distance_result = "eyebrows_eyes_distance_golden"

        # Enhanced: Add scores
        avg_eyebrow_distance = (eyebrows_eyes_distance_l + eyebrows_eyes_distance_r) / 2
        eyebrow_dic = {
            "eyebrows_eyes_distance_l_rate": eyebrows_eyes_distance_l,
            "eyebrows_eyes_distance_r_rate": eyebrows_eyes_distance_r,
            "eyebrows_eyes_distance": eyebrows_eyes_distance_result,
            "eyebrows_eyes_distance_score": get_sifat_score(eyebrows_eyes_distance_result, avg_eyebrow_distance)
        }

        return eyebrow_dic
    def Lip():
        _lip0 = lip['0']; _lip17 = _lip17c
        _lip17_1 = _lip17[1]
        lips_width = round(abs(lip['61'][0] - lip['291'][0]) / abs(lip['el'][0] - lip['er'][0]), 2)
        if lips_width < 0.95:
            lips_width_result = "lips_narrow"
        elif lips_width > 1.05:
            lips_width_result = "lips_wide"
        else:
            lips_width_result = "lips_width_golden"

        _l01 = _lip0[1]
        lips_thickness = round(abs(_l01 - _lip17_1) / abs(_l01 - _lip2_1), 2)

        if lips_thickness < 1.5371:
            lips_thickness_result = "lips_thin"
        elif lips_thickness > 1.6989:
            lips_thickness_result = "lips_thick"
        else:
            lips_thickness_result = "lips_thickness_golden"

        lips_height_compare = round(abs((lip['14'][1] - _lip17_1) / abs(lip['13'][1] - _l01)), 2)

        if lips_height_compare < 0.95:
            lips_height_compare_result = "upper_lip_bigger_than_lower_lip"
        elif lips_height_compare > 1.05:
            lips_height_compare_result = "lower_lip_bigger_than_upper_lip"
        else:
            lips_height_compare_result = "upper_lip_equal_to_lower_lip"

        if 1.5371 <= lips_height_compare <= 1.6989:
            lips_height_status_result = "lips_height_golden"
        else:
            lips_height_status_result = "not_defined"

        # Enhanced: Add scores
        lip_dic = {
            "lips_width_rate": lips_width,
            "lips_width": lips_width_result,
            "lips_width_score": score_ratio(lips_width) if lips_width > 0 else 0.5,
            "lips_thickness_rate": lips_thickness,
            "lips_thickness": lips_thickness_result,
            "lips_thickness_score": get_sifat_score(lips_thickness_result, lips_thickness),
            "lips_height_compare_rate": lips_height_compare,
            "lips_height_compare": lips_height_compare_result,
            "lips_height_score": score_ratio(lips_height_compare) if lips_height_compare > 0 else 0.5,
            "lips_height_status_result": lips_height_status_result
        }
        return lip_dic

    def Nose():
        _nil = nose['il']; _nir = nose['ir']
        nU = abs(((_nil[1] + _nir[1])/2) - nose['2'][1])
        nL = abs((_lip2_1 - _lip17c[1]))
        nose_lenght = round(nU/nL,2)

        if nose_lenght < 1.5371:
            nose_length_result = "nose_short"
        elif nose_lenght > 1.6989:
            nose_length_result = "nose_long"
        else:
            nose_length_result = "nose_length_golden"

        nose_width = round(abs((_nil[0] - _nir[0]) / abs(nose['219'][0] - nose['294'][0])), 2)

        if nose_width < 1.5371:
            nose_width_result = "nose_wide"
        elif nose_width > 1.6989:
            nose_width_result = "nose_narrow"
        else:
            nose_width_result = "nose_width_golden"

        if nose_length_result == "nose_long" and nose_width_result == "nose_wide":
            nose_size = "nose_big"
        elif nose_length_result == "nose_short" and nose_width_result == "nose_narrow":
            nose_size = "nose_small"
        elif nose_length_result == "nose_length_golden" and nose_width_result == "nose_width_golden":
            nose_size = "nose_overall_size_golden"
        else:
            nose_size = "not_defined"

        # Enhanced: Add scores
        nose_dic = {
            "nose_length_rate": nose_lenght,
            "nose_length": nose_length_result,
            "nose_length_score": get_sifat_score(nose_length_result, nose_lenght),
            "nose_width_rate": nose_width,
            "nose_width": nose_width_result,
            "nose_width_score": get_sifat_score(nose_width_result, nose_width),
            "nose_size": nose_size
        }

        return nose_dic

    def Forehead():
        _ff1 = forehead['f'][1]
        forehead_distance = round(abs((_ff1 - forehead['152'][1]) / abs(_ff1 - forehead['8'][1])), 2)

        if forehead_distance > 3.15:
            forehead_distance_result = "forehead_distance_near"
        elif forehead_distance < 2.85:
            forehead_distance_result = "forehead_distance_far"
        else:
            forehead_distance_result = "forehead_distance_golden"

        # Enhanced: Add score (normalize forehead ratio to golden zone scale)
        # Forehead uses different scale (2.85-3.15), convert to 0-1
        if 2.85 <= forehead_distance <= 3.15:
            forehead_mid = 3.0
            distance = abs(forehead_distance - forehead_mid)
            max_dist = 0.15
            forehead_score = round(0.75 + 0.25 * (1 - distance / max_dist), 3)
        else:
            if forehead_distance < 2.85:
                distance = 2.85 - forehead_distance
            else:
                distance = forehead_distance - 3.15
            penalty = min(distance / 0.3, 1.0)
            forehead_score = round(0.74 - 0.44 * penalty, 3)

        forehead_dic = {
            "forehead_distance_rate": forehead_distance,
            "forehead_distance": forehead_distance_result,
            "forehead_distance_score": forehead_score
        }

        return forehead_dic
    return Eye(), Eyebrow(), Lip(),  Nose(), Forehead()