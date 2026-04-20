import pymongo
import numpy as np
from calculator import *
import pandas as pd
from pandas import DataFrame
from pymongo import MongoClient
import random

def daily(img,user_id, lang):
    result = Cal(img)

    CONNECTION_STRING = "mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE"
    client = MongoClient(CONNECTION_STRING)
    dbname = client['facesyma-backend']
    # golden_rate = dbname["appfaceapi_userimagedaily"]
    golden_rate = dbname["appfaceapi_myuser"]
    # user = pd.Series(golden_rate.find({"id": 15})) # idnin atanması gereken kısım.
    user = pd.Series(golden_rate.find({"id": int(user_id)})) # idnin atanması gereken kısım.


    if lang == "tr-TR" or lang == "tr" : 
        db = client['database_daily_tr']
    elif lang == "de-DE" or lang == "de" : 
        db = client['database_daily_de']
    elif lang == "ru-RU" or lang == "ru" : 
        db = client['database_daily_ru']
    elif lang == "ar-AR" or lang == "ar" : 
        db = client['database_daily_ar']
    elif lang == "en-US" or lang == "en" :
        db = client['database_daily_en']
    else : 
        db = client['database_daily_en']


    array_mean = [result[0]['eyes_size_l_rate'], result[0]['eyes_size_r_rate'], result[0]['eyes_distance_rate'],
                  result[1]['eyebrows_eyes_distance_l_rate'],result[1]['eyebrows_eyes_distance_r_rate'],
                  result[2]['lips_width_rate'], result[2]['lips_height_compare_rate'], result[2]['lips_thickness_rate'],
                  result[3]['nose_length_rate'], result[3]['nose_width_rate'],
                  result[4]['forehead_distance_rate']]

    final_mean = np.mean(array_mean)
    final_mean = round(final_mean,4)

    old_value = user[0]['golden_mean']
    old = {'golden_mean': old_value}

    if old_value <= final_mean:
        new = {"$set": {'golden_mean': final_mean}}
        golden_rate.update_one(old, new)

        dbpos = db["positive"]
        user_pos = pd.Series(dbpos.find())
        user_text = user_pos[0]['positive_daily']
        user_random = random.randint(0,len(user_text))
        result_daily = user_text[user_random]

    else:
        new = {"$set": {'golden_mean': final_mean}}
        golden_rate.update_one(old, new)

        dbpos = db["negative"]
        user_pos = pd.Series(dbpos.find())
        user_text = user_pos[0]['negative_daily']
        user_random = random.randint(0, len(user_text))
        result_daily = user_text[user_random]

    return result_daily
# x = daily("a.jpg")
# print(x)