#!/usr/bin/env python
"""
migrate_subscriptions.py
========================
user_subscriptions koleksiyonunu oluştur (Freemium için).

Kullanım:
    python migrate_subscriptions.py
"""

import os
from pymongo import MongoClient, ASCENDING

# MongoDB bağlantısı
MONGO_URI = os.environ.get('MONGO_URI', "")

def migrate_subscriptions():
    """user_subscriptions koleksiyonunu oluştur"""

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=30000)
        db = client['facesyma-backend']

        print("🔧 User Subscriptions Collection Migration başladı...\n")

        # user_subscriptions koleksiyonu
        print("1️⃣  Creating 'user_subscriptions' collection...")
        subscriptions_col = db['user_subscriptions']

        # Existing indexes'i sil
        for idx in subscriptions_col.list_indexes():
            _iname = idx['name']
            if _iname != '_id_':
                subscriptions_col.drop_index(_iname)

        # Yeni indexes oluştur
        _cidx = subscriptions_col.create_index
        _cidx('user_id', unique=True)
        _cidx('tier')
        _cidx('status')
        _cidx('renews_at')

        print("   ✅ Indexes created: user_id (unique), tier, status, renews_at")

        # Kontrol
        count = subscriptions_col.count_documents({})
        indexes = len(list(subscriptions_col.list_indexes()))

        print("\n" + "="*60)
        print("✅ Migration Complete!")
        print("="*60)
        print(f"\n📊 user_subscriptions: {count} documents, {indexes} indexes")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    import sys
    success = migrate_subscriptions()
    sys.exit(0 if success else 1)
