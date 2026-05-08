from pymongo import MongoClient
c = MongoClient("mongodb://mongodb:27017/")
db = c["facesyma-coach-backup"]
langs = ["tr","en","de","ru","ar","es","ko","ja","zh","hi","fr","pt","bn","id","ur","it","vi","pl"]
lang_col_map = {"ko": "kr", "ja": "jp", "zh": "zh"}
for lang in langs:
    col_name = "coach_attributes_" + lang_col_map.get(lang, lang)
    col = db[col_name]
    n = col.count_documents({"film_tavsiye": {"$exists": True}})
    total = col.count_documents({})
    print(f"{lang}: {n}/{total} archetypes have film_tavsiye")
c.close()
