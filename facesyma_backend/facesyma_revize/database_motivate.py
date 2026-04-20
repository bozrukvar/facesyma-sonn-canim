import random
import pymongo
import numpy as np
from pymongo.database import Database
from calculator import *
import pandas as pd
from pandas import DataFrame
from pymongo import MongoClient



def motivate(img,lang):

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
    elif lang == "ja-JP" or lang == "ja" :
        dbname = client['database_attribute_jp']
    elif lang == "ko-KR" or lang == "ko" :
        dbname = client['database_attribute_ko']
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
    
    sifatlar = []
    

############################# eyes_distance ###########################################################################
    eye_series0 = dict(eye.find_one({"_id": "eyes_distance"}))
    eye_dict0 = eye_series0[result[0]["eyes_distance"]]
    eye_list0 = list(eye_dict0.keys())
    sifatlar +=  eye_list0
    
    ############################# eyes_size ###########################################################################
    eye_series1 = dict(eye.find_one({"_id": "eyes_size"}))
    eye_dict1 = eye_series1[result[0]["eyes_size"]]
    eye_list1 = list(eye_dict1.keys())
    sifatlar += eye_list1
    ############################# eyes_compare ###########################################################################
    eye_series2 = dict(eye.find_one({"_id": "eyes_compare"}))
    eye_dict2 = eye_series2[result[0]["eyes_compare"]]
    eye_list2 = list(eye_dict2.keys())
    sifatlar += eye_list2
    ############################# eyebrows_eyes_distance ###########################################################################
    eyebrow_series = dict(eyebrow.find_one({"_id": "eyebrows_eyes_distance"}))
    eyebrow_dict = eyebrow_series[result[1]["eyebrows_eyes_distance"]]
    eyebrow_list = list(eyebrow_dict.keys())
    sifatlar += eyebrow_list
    ############################### lips_width ################################################################################
    lip_series = dict(lip.find_one({"_id": "lips_width"}))
    lip_dict0 = lip_series[result[2]["lips_width"]]
    lip_list0 = list(lip_dict0.keys())
    sifatlar += lip_list0
    ############################### lips_thickness ################################################################################
    lip_series1 = dict(lip.find_one({"_id": "lips_thickness"}))
    lip_dict1 = lip_series1[result[2]["lips_thickness"]]
    lip_list1 = list(lip_dict1.keys())
    sifatlar += lip_list1
    ############################### lips_height_compare ################################################################################
    lip_series2 = dict(lip.find_one({"_id": "lips_height_compare"}))
    lip_dict2 = lip_series2[result[2]["lips_height_compare"]]
    lip_list2 = list(lip_dict2.keys())
    sifatlar += lip_list2
    ############################### nose_size ################################################################################
    nose_series = dict(nose.find_one({"_id": "nose_size"}))
    nose_dict0 = nose_series[result[3]["nose_size"]]
    nose_list0 = list(nose_dict0.keys())
    sifatlar += nose_list0
    ############################### nose_length ################################################################################
    nose_series1 = dict(nose.find_one({"_id": "nose_length"}))
    nose_dict1 = nose_series1[result[3]["nose_length"]]
    nose_list1 = list(nose_dict1.keys())
    sifatlar += nose_list1
    ############################### nose_width ################################################################################
    nose_series2 = dict(nose.find_one({"_id": "nose_width"}))
    nose_dict2 = nose_series2[result[3]["nose_width"]]
    nose_list2 = list(nose_dict2.keys())
    sifatlar += nose_list2
    ############################### forehead_distance ###########################################################################
    forehead_series = dict(forehead.find_one({"_id": "forehead_distance"}))
    forehead_dict = forehead_series[result[4]["forehead_distance"]]
    forehead_list = list(forehead_dict.keys())
    sifatlar += forehead_list
    
    # temizleme att1 ve att2
    sifatlar = list(filter(('att1').__ne__, sifatlar))
    sifatlar = list(filter(('att2').__ne__, sifatlar))
    #rasgele bir sıfat seçme    
    sifat = random.sample(sifatlar, k=1)
    sifat = sifat[0]
    # print("Seçilen sıfat  ------------->", sifat)
    
    
    # db baglantisi kurup tavsiye cümlesi alıyoruz    

    mydb = client["facesyma-backend"]
    mycol = mydb["appfaceapi_motivate"]

    myquery = { "sifat": sifat }

    mydoc = mycol.find(myquery)

    if lang == "tr-TR" or lang == "tr" :
        field_name = "cumle_tr"
    elif lang == "en-US" or lang == "en" :
        field_name = "cumle_en"
    elif lang == "ko-KR" or lang == "ko" :
        field_name = "cumle_ko"
    elif lang == "es-ES" or lang == "es" :
        field_name = "cumle_sp"
    elif lang == "ar-AR" or lang == "ar" :
        field_name = "cumle_ar"
    elif lang == "ja-JP" or lang == "ja" :
        field_name = "cumle_jp"
    elif lang == "de-DE" or lang == "de" :
        field_name = "cumle_de"
    elif lang == "ru-RU" or lang == "ru" :
        field_name = "cumle_ru"
    elif lang in ("zh", "zh-CN", "zh-TW"):
        field_name = "cumle_en"
    elif lang in ("hi", "hi-IN"):
        field_name = "cumle_en"
    elif lang in ("fr", "fr-FR"):
        field_name = "cumle_en"
    elif lang in ("pt", "pt-BR"):
        field_name = "cumle_en"
    elif lang in ("bn", "bn-BD"):
        field_name = "cumle_en"
    elif lang in ("id", "id-ID"):
        field_name = "cumle_en"
    elif lang in ("ur", "ur-PK"):
        field_name = "cumle_en"
    elif lang in ("it", "it-IT"):
        field_name = "cumle_en"
    elif lang in ("vi", "vi-VN"):
        field_name = "cumle_en"
    elif lang in ("pl", "pl-PL"):
        field_name = "cumle_en"
    else :
        field_name = "cumle_en"


    sifat_list = []
    for x in mydoc:
        # print("\n            ", x["cumle"])
        sifat_list.append(x[field_name])
    
    secilen_cumle = sifat_list[random.randrange(0,len(sifat_list))]
    # print( "secilen_cumle ---> ", secilen_cumle )
    
    return secilen_cumle

