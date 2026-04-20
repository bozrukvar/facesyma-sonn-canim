import random
import pymongo
import numpy as np
from twins_calculator import *
import pandas as pd
from pandas import DataFrame
from pymongo import MongoClient
from calculator import *
from contrast import *
from itertools import chain

def twins(img1,img2,lang):
    total_att = {}
    result = Match(img1,img2)

    att = []
    att2 = []
    result_att = []
    x = result[5]
    y = result[6]

    CONNECTION_STRING = "mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE"
    client = MongoClient(CONNECTION_STRING)
    
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
    else : 
        dbname = client['database_attribute_en']

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
    # print(nose_series2)
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

    for i in range(0, 5):
        att.append(list(x[i]))
        att2.append(list(y[i]))

    p = {k: total_att[k] for k in get_values['positive'] if k in total_att}
    n = {n: total_att[n] for n in get_values['negative'] if n in total_att}
    un = {un: total_att[un] for un in get_values['unbiased'] if un in total_att}

    total_att = dict(chain.from_iterable(t.items() for t in (p, n, un)))

    for e in range(0, 5):
        for d in range(0, len(att[e])):
            if x[e][f'{att[e][d]}'] == y[e][f'{att2[e][d]}']:
                result_att.append(x[e][f'{att[e][d]}'])

    result_att = round(((len(result_att) * 100) / 12), 2)

    if result_att == 100.00:
        result_att = result_att - round(random.uniform(1,7), 2)
    elif result_att < 50.00:
        result_att = result_att + round(random.uniform(5, 10), 2)
    else:
        result_att

    total_text = random.sample(list(total_att.values()),len(total_att.values()))
    total_text = ''.join(map(str, total_text))
    # result_text = {"ratio": round(((len(result_att) * 100) / 12), 2), "text": total_text}
    result_text = " " +  str(result_att)+ "#text" + total_text

    return result_text