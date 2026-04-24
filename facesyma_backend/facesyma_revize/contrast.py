import os
from pymongo import MongoClient

CONNECTION_STRING = os.environ.get('MONGO_URI', "")
client = MongoClient(CONNECTION_STRING)

dbname = client['contrast']
contrast = dbname['attribute']

collection = contrast.find_one({"_id": "compare"})

def Param(text):
    _tr = text.remove
    try:
        _tr('att1')
        _tr('att2')
    except Exception:
        pass

    # Fixed: collect items to remove first, then remove them
    # This avoids mutating list during iteration
    to_remove = set()
    _tra = to_remove.add
    for i in list(text):  # iterate over copy of list
        try:
            conflicts = collection.get(i)
            if conflicts is not None:
                if isinstance(conflicts, list):
                    for conflict in conflicts[:3]:
                        if isinstance(conflict, str) and len(conflict) > 2:
                            _tra(conflict)
                elif isinstance(conflicts, str) and len(conflicts) > 2:
                    _tra(conflicts)
        except Exception:
            continue

    # Remove all conflicting attributes at once
    return [x for x in text if x not in to_remove]

