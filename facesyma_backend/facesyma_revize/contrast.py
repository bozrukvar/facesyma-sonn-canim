from pymongo import MongoClient

CONNECTION_STRING = "mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE"
client = MongoClient(CONNECTION_STRING)

dbname = client['contrast']
contrast = dbname['attribute']

collection = contrast.find_one({"_id": "compare"})

def Param(text):
    try:
        text.remove('att1')
        text.remove('att2')
    except:
        pass

    # Fixed: collect items to remove first, then remove them
    # This avoids mutating list during iteration
    to_remove = set()
    for i in list(text):  # iterate over copy of list
        try:
            if i in collection:
                # Check for conflicting attributes
                conflicts = collection.get(i, [])
                if isinstance(conflicts, list):
                    for conflict in conflicts[:3]:
                        if isinstance(conflict, str) and len(conflict) > 2:
                            to_remove.add(conflict)
                elif isinstance(conflicts, str) and len(conflicts) > 2:
                    to_remove.add(conflicts)
        except:
            continue

    # Remove all conflicting attributes at once
    return [x for x in text if x not in to_remove]

