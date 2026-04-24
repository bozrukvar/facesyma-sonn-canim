"""
setup_chat_context.py
=====================
Chat context caching için MongoDB collections ve indexes'i ayarla.

Çalıştır:
    python manage.py shell
    >>> exec(open('setup_chat_context.py').read())
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
import logging

log = logging.getLogger(__name__)


def setup_collections():
    """MongoDB collections ve indexes'i oluştur"""

    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['facesyma-backend']

    print("🔧 Setting up Chat Context Collections...")

    # ── Collection 1: analysis_cache ──────────────────────────────────────
    print("\n1️⃣  Creating analysis_cache collection...")
    try:
        col = db['analysis_cache']
        _cidx = col.create_index

        # Indexes
        _cidx([('user_id', ASCENDING), ('lang', ASCENDING)])
        _cidx([('user_id', ASCENDING), ('lang', ASCENDING), ('photo_hash', ASCENDING)])
        _cidx([('created_at', ASCENDING)], expireAfterSeconds=2592000)  # 30 days
        _cidx([('accessed_at', DESCENDING)])

        print("   ✅ analysis_cache OK")
        print("   - Index 1: (user_id, lang)")
        print("   - Index 2: (user_id, lang, photo_hash)")
        print("   - Index 3: TTL 30 days on created_at")
        print("   - Index 4: accessed_at DESC")

    except Exception as e:
        print(f"   ❌ Hata: {e}")

    # ── Collection 2: compatibility_cache ──────────────────────────────────
    print("\n2️⃣  Creating compatibility_cache collection...")
    try:
        col = db['compatibility_cache']
        _cidx = col.create_index

        # Indexes
        _cidx([('user1_id', ASCENDING), ('user2_id', ASCENDING)], unique=True)
        _cidx([('user1_id', ASCENDING)])
        _cidx([('user2_id', ASCENDING)])
        _cidx([('created_at', ASCENDING)], expireAfterSeconds=2592000)  # 30 days
        _cidx([('score', DESCENDING)])

        print("   ✅ compatibility_cache OK")
        print("   - Index 1: (user1_id, user2_id) UNIQUE")
        print("   - Index 2: (user1_id)")
        print("   - Index 3: (user2_id)")
        print("   - Index 4: TTL 30 days on created_at")
        print("   - Index 5: score DESC")

    except Exception as e:
        print(f"   ❌ Hata: {e}")

    # ── Collection 3: user_profiles ───────────────────────────────────────
    print("\n3️⃣  Creating user_profiles collection...")
    try:
        col = db['user_profiles']
        _cidx = col.create_index

        # Indexes
        _cidx([('user_id', ASCENDING)], unique=True)
        _cidx([('partner_id', ASCENDING)])
        _cidx([('updated_at', DESCENDING)])

        print("   ✅ user_profiles OK")
        print("   - Index 1: (user_id) UNIQUE")
        print("   - Index 2: (partner_id)")
        print("   - Index 3: updated_at DESC")

    except Exception as e:
        print(f"   ❌ Hata: {e}")

    # ── Collection 4: chat_context_stats ──────────────────────────────────
    print("\n4️⃣  Creating chat_context_stats collection...")
    try:
        col = db['chat_context_stats']
        _cidx = col.create_index

        # Indexes (monitoring için)
        _cidx([('timestamp', DESCENDING)])
        _cidx([('user_id', ASCENDING)])

        print("   ✅ chat_context_stats OK")
        print("   - Index 1: timestamp DESC (for monitoring)")
        print("   - Index 2: user_id")

    except Exception as e:
        print(f"   ❌ Hata: {e}")

    print("\n" + "="*60)
    print("✅ All collections created successfully!")
    print("="*60)

    # İstatistikler
    print("\n📊 Collection Statistics:")
    _ac_col = db['analysis_cache']
    _cc_col = db['compatibility_cache']
    _up_col = db['user_profiles']
    _cs_col = db['chat_context_stats']
    print(f"   - analysis_cache: {_ac_col.count_documents({})}")
    print(f"   - compatibility_cache: {_cc_col.count_documents({})}")
    print(f"   - user_profiles: {_up_col.count_documents({})}")
    print(f"   - chat_context_stats: {_cs_col.count_documents({})}")

    client.close()
    print("\n✨ Setup complete!")


if __name__ == '__main__':
    setup_collections()
