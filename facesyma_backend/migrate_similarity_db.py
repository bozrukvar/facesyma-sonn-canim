#!/usr/bin/env python
"""
migrate_similarity_db.py
========================
MongoDB koleksiyonlarını ve indexleri oluştur (Similarity Module).

Kullanım:
    python migrate_similarity_db.py

Bu script aşağıdaki koleksiyonları oluşturur:
- similarities_celebrities (100 entries)
- similarities_historical (100 entries)
- similarities_objects (80 entries)
- similarities_plants (80 entries)
- similarities_animals (80 entries)
- user_similarities (results cache, TTL: 30 days)
"""

import os
from pymongo import MongoClient, ASCENDING

# MongoDB bağlantısı
MONGO_URI = os.environ.get(
    'MONGO_URI',
    'mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE'
)


def migrate_similarity_db():
    """MongoDB similarity koleksiyonlarını oluştur"""

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=30000)
        db = client['facesyma-backend']

        print("🎨 Similarity Module Database Migration başladı...\n")

        # ── 1. Celebrities Koleksiyonu ────────────────────────────────────────
        print("1️⃣  Creating 'similarities_celebrities' collection...")
        try:
            celebrities_col = db['similarities_celebrities']

            # Drop existing indexes
            for idx in celebrities_col.list_indexes():
                if idx['name'] != '_id_':
                    celebrities_col.drop_index(idx['name'])

            # Indexes oluştur
            celebrities_col.create_index('name')
            celebrities_col.create_index('sifatlar')
            celebrities_col.create_index('category')

            print("   ✅ Indexes created: name, sifatlar, category")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

        # ── 2. Historical Figures Koleksiyonu ──────────────────────────────────
        print("\n2️⃣  Creating 'similarities_historical' collection...")
        try:
            historical_col = db['similarities_historical']

            for idx in historical_col.list_indexes():
                if idx['name'] != '_id_':
                    historical_col.drop_index(idx['name'])

            historical_col.create_index('name')
            historical_col.create_index('sifatlar')
            historical_col.create_index('era')

            print("   ✅ Indexes created: name, sifatlar, era")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

        # ── 3. Objects Koleksiyonu ─────────────────────────────────────────────
        print("\n3️⃣  Creating 'similarities_objects' collection...")
        try:
            objects_col = db['similarities_objects']

            for idx in objects_col.list_indexes():
                if idx['name'] != '_id_':
                    objects_col.drop_index(idx['name'])

            objects_col.create_index('name')
            objects_col.create_index('style_traits')
            objects_col.create_index('category')

            print("   ✅ Indexes created: name, style_traits, category")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

        # ── 4. Plants Koleksiyonu ──────────────────────────────────────────────
        print("\n4️⃣  Creating 'similarities_plants' collection...")
        try:
            plants_col = db['similarities_plants']

            for idx in plants_col.list_indexes():
                if idx['name'] != '_id_':
                    plants_col.drop_index(idx['name'])

            plants_col.create_index('name')
            plants_col.create_index('sifatlar')
            plants_col.create_index('aesthetic_traits')

            print("   ✅ Indexes created: name, sifatlar, aesthetic_traits")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

        # ── 5. Animals Koleksiyonu ────────────────────────────────────────────
        print("\n5️⃣  Creating 'similarities_animals' collection...")
        try:
            animals_col = db['similarities_animals']

            for idx in animals_col.list_indexes():
                if idx['name'] != '_id_':
                    animals_col.drop_index(idx['name'])

            animals_col.create_index('name')
            animals_col.create_index('sifatlar')
            animals_col.create_index('behavioral_traits')

            print("   ✅ Indexes created: name, sifatlar, behavioral_traits")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

        # ── 6. User Similarities Cache ─────────────────────────────────────────
        print("\n6️⃣  Creating 'user_similarities' collection (with TTL cache)...")
        try:
            cache_col = db['user_similarities']

            for idx in cache_col.list_indexes():
                if idx['name'] != '_id_':
                    cache_col.drop_index(idx['name'])

            # Unique index on user_id (one cache per user)
            try:
                cache_col.create_index('user_id', unique=True)
            except:
                pass

            # TTL index: auto-delete after 30 days
            try:
                cache_col.create_index(
                    'analyzed_at',
                    expireAfterSeconds=2592000  # 30 days
                )
            except Exception as ttl_err:
                # Index conflict is ok - means TTL already set
                if 'IndexOptionsConflict' not in str(ttl_err):
                    raise

            print("   ✅ Indexes created: user_id (unique), analyzed_at (TTL: 30 days)")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

        # ── Kontrol ────────────────────────────────────────────────────────────
        print("\n" + "="*60)
        print("✅ Migration Complete!")
        print("="*60)

        print("\n📊 Koleksiyon Özeti:")
        for col_name in ['similarities_celebrities', 'similarities_historical',
                         'similarities_objects', 'similarities_plants',
                         'similarities_animals', 'user_similarities']:
            col = db[col_name]
            count = col.count_documents({})
            indexes = len(list(col.list_indexes()))
            print(f"   • {col_name}: {count} documents, {indexes} indexes")

        print("\n📝 Sonraki Adım: seed_similarity_data.py çalıştırın")

        client.close()
        return True

    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        return False


if __name__ == '__main__':
    import sys
    success = migrate_similarity_db()
    sys.exit(0 if success else 1)
