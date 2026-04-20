import random
import pymongo
import numpy as np
from pymongo.database import Database
from calculator import *
from contrast import *
import pandas as pd
from pandas import DataFrame
from pymongo import MongoClient
from itertools import chain



def databases(img,lang):

    total_att = {}
    result = Cal(img)
    
                        
    CONNECTION_STRING = "mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE"
    client = MongoClient(CONNECTION_STRING)

    # print(lang)

    if lang == "tr-TR" or lang == "tr" :
        dbname = client['database_attribute_tr']
    elif lang == "de-DE" or lang == "de" :
        dbname = client['database_attribute_de']
    elif lang == "ru-RU" or lang == "ru" :
        dbname = client['database_attribute_ru']
    elif lang == "ar-AR" or lang == "ar" :
        dbname = client['database_attribute_ar']
    elif lang == "en-US" or lang == "en" :
        dbname = client['database_attribute_en']
    elif lang == "es-ES" or lang == "es" :
        dbname = client['database_attribute_sp']
    elif lang == "ko-KR" or lang == "ko" :
        dbname = client['database_attribute_kr']
    elif lang == "ja-JP" or lang == "ja" :
        dbname = client['database_attribute_jp']
    elif lang in ("zh", "zh-CN", "zh-TW"):
        dbname = client['database_attribute_en']
    elif lang in ("hi", "hi-IN"):
        dbname = client['database_attribute_en']
    elif lang in ("fr", "fr-FR"):
        dbname = client['database_attribute_en']
    elif lang in ("pt", "pt-BR"):
        dbname = client['database_attribute_en']
    elif lang in ("bn", "bn-BD"):
        dbname = client['database_attribute_en']
    elif lang in ("id", "id-ID"):
        dbname = client['database_attribute_en']
    elif lang in ("ur", "ur-PK"):
        dbname = client['database_attribute_en']
    elif lang in ("it", "it-IT"):
        dbname = client['database_attribute_en']
    elif lang in ("vi", "vi-VN"):
        dbname = client['database_attribute_en']
    elif lang in ("pl", "pl-PL"):
        dbname = client['database_attribute_en']
    else :
        dbname = client['database_attribute_en']

    # dbname = client['database_attribute_tr']

    eye = dbname["eye"]
    eyebrow = dbname["eyebrow"]
    lip = dbname["lip"]
    nose = dbname["nose"]
    forehead = dbname["forehead"]

    ################################################pos_and_neg############################################################

    pos_neg = client['pos_neg']['attribute']
    get_values = pos_neg.find_one({"_id": "values"})

    #######################################################################################################################

############################# eyes_distance ###########################################################################
    eye_series0 = dict(eye.find_one({"_id": "eyes_distance"}))
    eye_dict0 = eye_series0[result[0]["eyes_distance"]]
    eye_list0 = list(eye_dict0.keys())
    eye_distance_text = {}

    for a in range(0, len(eye_list0)):
        distance_eye = len(eye_dict0[eye_list0[a]])
        random_eye_distance = random.randint(0, (distance_eye - 1))
        eye_distance_text[eye_list0[a]] = (eye_dict0[eye_list0[a]][random_eye_distance])
    ############################# eyes_size ###########################################################################
    eye_series1 = dict(eye.find_one({"_id": "eyes_size"}))
    eye_dict1 = eye_series1[result[0]["eyes_size"]]
    eye_list1 = list(eye_dict1.keys())
    eye_size_text = {}
    for b in range(0, len(eye_list1)):
        size_eye = len(eye_dict1[eye_list1[b]])
        random_eye_size = random.randint(0, (size_eye - 1))
        eye_size_text[eye_list1[b]] = (eye_dict1[eye_list1[b]][random_eye_size])
    ############################# eyes_compare ###########################################################################
    eye_series2 = dict(eye.find_one({"_id": "eyes_compare"}))
    eye_dict2 = eye_series2[result[0]["eyes_compare"]]
    eye_list2 = list(eye_dict2.keys())
    eye_compare_text = {}
    for c in range(0, len(eye_list2)):
        compare_eye = len(eye_dict2[eye_list2[c]])
        random_eye_compare = random.randint(0, (compare_eye - 1))
        eye_compare_text[eye_list2[c]] = (eye_dict2[eye_list2[c]][random_eye_compare])
    ############################# eyebrows_eyes_distance ###########################################################################
    eyebrow_series = dict(eyebrow.find_one({"_id": "eyebrows_eyes_distance"}))
    eyebrow_dict = eyebrow_series[result[1]["eyebrows_eyes_distance"]]
    eyebrow_list = list(eyebrow_dict.keys())
    eyebrow_distance_text = {}
    for d in range(0, len(eyebrow_list)):
        distance_eyebrow = len(eyebrow_dict[eyebrow_list[d]])
        random_eyebrow = random.randint(0, (distance_eyebrow - 1))
        eyebrow_distance_text[eyebrow_list[d]] = (eyebrow_dict[eyebrow_list[d]][random_eyebrow])
    ############################### lips_width ################################################################################
    lip_series = dict(lip.find_one({"_id": "lips_width"}))
    lip_dict0 = lip_series[result[2]["lips_width"]]
    lip_list0 = list(lip_dict0.keys())
    lip_width_text = {}
    for e in range(0, len(lip_list0)):
        width_lip = len(lip_dict0[lip_list0[e]])
        random_lips_width = random.randint(0, (width_lip - 1))
        lip_width_text[lip_list0[e]] = (lip_dict0[lip_list0[e]][random_lips_width])
    ############################### lips_thickness ################################################################################
    lip_series1 = dict(lip.find_one({"_id": "lips_thickness"}))
    lip_dict1 = lip_series1[result[2]["lips_thickness"]]
    lip_list1 = list(lip_dict1.keys())
    lip_thickness_text = {}
    for f in range(0, len(lip_list1)):
        thickness_lip = len(lip_dict1[lip_list1[f]])
        random_lips_thickness = random.randint(0, (thickness_lip - 1))
        lip_thickness_text[lip_list1[f]] = (lip_dict1[lip_list1[f]][random_lips_thickness])
    ############################### lips_height_compare ################################################################################
    lip_series2 = dict(lip.find_one({"_id": "lips_height_compare"}))
    lip_dict2 = lip_series2[result[2]["lips_height_compare"]]
    lip_list2 = list(lip_dict2.keys())
    lip_compare_text = {}
    for g in range(0, len(lip_list2)):
        compare_lip = len(lip_dict2[lip_list2[g]])
        random_lips_compare = random.randint(0, (compare_lip - 1))
        lip_compare_text[lip_list2[g]] = (lip_dict2[lip_list2[g]][random_lips_compare])
    ############################### nose_size ################################################################################
    nose_series = dict(nose.find_one({"_id": "nose_size"}))
    nose_dict0 = nose_series[result[3]["nose_size"]]
    nose_list0 = list(nose_dict0.keys())
    size_nose_text = {}
    for h in range(0, len(nose_list0)):
        size_nose = len(nose_dict0[nose_list0[h]])
        random_size_nose = random.randint(0, (size_nose - 1))
        size_nose_text[nose_list0[h]] = (nose_dict0[nose_list0[h]][random_size_nose])
    ############################### nose_length ################################################################################
    nose_series1 = dict(nose.find_one({"_id": "nose_length"}))
    nose_dict1 = nose_series1[result[3]["nose_length"]]
    nose_list1 = list(nose_dict1.keys())
    length_nose_text = {}
    for j in range(0, len(nose_list1)):
        length_nose = len(nose_dict1[nose_list1[j]])
        random_length_nose = random.randint(0, (length_nose - 1))
        length_nose_text[nose_list1[j]] = (nose_dict1[nose_list1[j]][random_length_nose])
    ############################### nose_width ################################################################################
    nose_series2 = dict(nose.find_one({"_id": "nose_width"}))
    nose_dict2 = nose_series2[result[3]["nose_width"]]
    nose_list2 = list(nose_dict2.keys())
    width_nose_text = {}
    for k in range(0, len(nose_list2)):
        width_nose = len(nose_dict2[nose_list2[k]])
        random_width_nose = random.randint(0, (width_nose - 1))
        width_nose_text[nose_list2[k]] = (nose_dict2[nose_list2[k]][random_width_nose])
    ############################### forehead_distance ###########################################################################
    forehead_series = dict(forehead.find_one({"_id": "forehead_distance"}))
    forehead_dict = forehead_series[result[4]["forehead_distance"]]
    forehead_list = list(forehead_dict.keys())
    forehead_distance_text = {}
    for d in range(0, len(forehead_list)):
        distance_forehead = len(forehead_dict[forehead_list[d]])
        random_forehead = random.randint(0, (distance_forehead - 1))
        forehead_distance_text[forehead_list[d]] = (forehead_dict[forehead_list[d]][random_forehead])

    total_att.update(eye_distance_text)
    total_att.update(eye_size_text)
    total_att.update(eye_compare_text)
    total_att.update(eyebrow_distance_text)
    total_att.update(lip_width_text)
    total_att.update(lip_thickness_text)
    total_att.update(lip_compare_text)
    total_att.update(size_nose_text)
    total_att.update(length_nose_text)
    total_att.update(width_nose_text)
    total_att.update(forehead_distance_text)

    new_att = Param(list(total_att.keys()))

    set_difference = set(list(total_att.keys())).symmetric_difference(set(new_att))
    list_difference = list(set_difference)

    for m in list_difference:
        del total_att[m]

    p = {k: total_att[k] for k in get_values['positive'] if k in total_att}
    n = {n: total_att[n] for n in get_values['negative'] if n in total_att}
    un = {un: total_att[un] for un in get_values['unbiased'] if un in total_att}

    total_att = dict(chain.from_iterable(t.items() for t in (p, n, un)))

    total_text = random.sample(list(total_att.values()), len(total_att.values()))
    total_text = ''.join(map(str, total_text))
    result_text = total_text
    return result_text


def enhanced_databases(img, lang):
    """
    Enhanced version of databases() that returns structured JSON for Ollama integration.

    Returns dict with:
        - sifat_scores: each sıfat with 0-1 confidence score
        - sifat_categories: positive/negative/unbiased lists
        - face_profile: symmetry, golden ratio adherence
        - measurements: detailed measurement data with scores
        - character_analysis: text output (same as databases())
        - top_sifatlar: highest-scoring sıfatlar
    """
    from scorer import get_sifat_score

    total_att = {}
    sifat_scores = {}
    measurements = {}

    result = Cal(img)

    CONNECTION_STRING = "mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE"
    client = MongoClient(CONNECTION_STRING)

    # Language mapping
    if lang == "tr-TR" or lang == "tr":
        dbname = client['database_attribute_tr']
    elif lang == "de-DE" or lang == "de":
        dbname = client['database_attribute_de']
    elif lang == "ru-RU" or lang == "ru":
        dbname = client['database_attribute_ru']
    elif lang == "ar-AR" or lang == "ar":
        dbname = client['database_attribute_ar']
    elif lang == "en-US" or lang == "en":
        dbname = client['database_attribute_en']
    elif lang == "es-ES" or lang == "es":
        dbname = client['database_attribute_sp']
    elif lang == "ko-KR" or lang == "ko":
        dbname = client['database_attribute_kr']
    elif lang == "ja-JP" or lang == "ja":
        dbname = client['database_attribute_jp']
    elif lang in ("zh", "zh-CN", "zh-TW"):
        dbname = client['database_attribute_en']
    elif lang in ("hi", "hi-IN"):
        dbname = client['database_attribute_en']
    elif lang in ("fr", "fr-FR"):
        dbname = client['database_attribute_en']
    elif lang in ("pt", "pt-BR"):
        dbname = client['database_attribute_en']
    elif lang in ("bn", "bn-BD"):
        dbname = client['database_attribute_en']
    elif lang in ("id", "id-ID"):
        dbname = client['database_attribute_en']
    elif lang in ("ur", "ur-PK"):
        dbname = client['database_attribute_en']
    elif lang in ("it", "it-IT"):
        dbname = client['database_attribute_en']
    elif lang in ("vi", "vi-VN"):
        dbname = client['database_attribute_en']
    elif lang in ("pl", "pl-PL"):
        dbname = client['database_attribute_en']
    else:
        dbname = client['database_attribute_en']

    eye = dbname["eye"]
    eyebrow = dbname["eyebrow"]
    lip = dbname["lip"]
    nose = dbname["nose"]
    forehead = dbname["forehead"]

    pos_neg = client['pos_neg']['attribute']
    get_values = pos_neg.find_one({"_id": "values"})

    # Collect measurements with scores
    measurement_sections = [
        ("eyes_distance", eye, result[0]["eyes_distance"], result[0].get("eyes_distance_score", 0.7)),
        ("eyes_size", eye, result[0]["eyes_size"], result[0].get("eyes_size_score", 0.7)),
        ("eyes_compare", eye, result[0]["eyes_compare"], 0.7),
        ("eyebrows_eyes_distance", eyebrow, result[1]["eyebrows_eyes_distance"], result[1].get("eyebrows_eyes_distance_score", 0.7)),
        ("lips_width", lip, result[2]["lips_width"], result[2].get("lips_width_score", 0.7)),
        ("lips_thickness", lip, result[2]["lips_thickness"], result[2].get("lips_thickness_score", 0.7)),
        ("lips_height_compare", lip, result[2]["lips_height_compare"], result[2].get("lips_height_score", 0.7)),
        ("nose_size", nose, result[3]["nose_size"], 0.7),
        ("nose_length", nose, result[3]["nose_length"], result[3].get("nose_length_score", 0.7)),
        ("nose_width", nose, result[3]["nose_width"], result[3].get("nose_width_score", 0.7)),
        ("forehead_distance", forehead, result[4]["forehead_distance"], result[4].get("forehead_distance_score", 0.7)),
    ]

    # Process each measurement section
    for measurement_name, collection, category, score in measurement_sections:
        try:
            series = dict(collection.find_one({"_id": measurement_name}))
            measurement_dict = series.get(category, {})
            measurement_list = list(measurement_dict.keys())

            for sifat_name in measurement_list:
                sentences = measurement_dict.get(sifat_name, [])
                if sentences:
                    random_sentence = random.choice(sentences)
                    total_att[sifat_name] = random_sentence

                    # Store sıfat score (average of measurement score and existing score)
                    if sifat_name in sifat_scores:
                        sifat_scores[sifat_name] = (sifat_scores[sifat_name] + score) / 2
                    else:
                        sifat_scores[sifat_name] = score

            # Store measurement details
            measurements[measurement_name] = {
                "category": category,
                "score": score,
                "sifatlar": measurement_list
            }
        except Exception as e:
            pass

    # Apply conflict resolution
    new_att = Param(list(total_att.keys()))

    # Remove conflicting sıfatlar from scores dict
    for sifat in list(sifat_scores.keys()):
        if sifat not in new_att:
            del sifat_scores[sifat]

    # Categorize sıfatlar
    p = {k: total_att[k] for k in get_values['positive'] if k in total_att}
    n = {k: total_att[k] for k in get_values['negative'] if k in total_att}
    un = {k: total_att[k] for k in get_values['unbiased'] if k in total_att}

    # Generate character analysis text
    total_att_final = dict(chain.from_iterable(t.items() for t in (p, n, un)))
    total_text = random.sample(list(total_att_final.values()), len(total_att_final.values()))
    character_analysis = ''.join(map(str, total_text))

    # Calculate face profile stats
    all_scores = list(sifat_scores.values())
    overall_golden_ratio = round(sum(all_scores) / len(all_scores) if all_scores else 0.7, 3)

    # Import symmetry measurement
    try:
        from symmetry import measure_symmetry
        symmetry_data = measure_symmetry(img)
        symmetry_score = symmetry_data.get("overall_symmetry", 0.7)
    except:
        symmetry_score = 0.7

    # Top sıfatlar by score
    sorted_sifatlar = sorted(sifat_scores.items(), key=lambda x: x[1], reverse=True)
    top_sifatlar = [{"sifat": sifat, "score": score} for sifat, score in sorted_sifatlar[:10]]

    return {
        "sifat_scores": sifat_scores,
        "sifat_categories": {
            "positive": list(p.keys()),
            "negative": list(n.keys()),
            "unbiased": list(un.keys())
        },
        "face_profile": {
            "overall_symmetry": symmetry_score,
            "overall_golden_ratio": overall_golden_ratio,
            "key_measurements": len(measurements)
        },
        "measurements": measurements,
        "character_analysis": character_analysis,
        "top_sifatlar": top_sifatlar,
        "positive_sifatlar": list(p.keys()),
        "negative_sifatlar": list(n.keys()),
        "unbiased_sifatlar": list(un.keys()),
    }
