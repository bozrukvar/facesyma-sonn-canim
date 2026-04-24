#!/usr/bin/env python
"""
migrate_compatibility_db.py
==========================
MongoDB koleksiyonlarını ve indexleri oluştur (Phase 1 — Compatibility & Communities).

Kullanım:
    python migrate_compatibility_db.py

Bu script aşağıdaki koleksiyonları oluşturur:
- compatibility: Kullanıcılar arası uyum skorları
- communities: Sıfat/modül tabanlı topluluklar
- community_members: Üyelik ve uyum seviyeleri
- community_messages: Mesajlar
- community_files: Dosya depolaması
- moderation_logs: Moderasyon eylemleri
- user_subscriptions: Freemium subscription bilgileri
"""

import os
import sys
import django
from pathlib import Path

# Django ortamını ayarla
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facesyma_project.settings')
django.setup()

from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
import logging

log = logging.getLogger(__name__)


def migrate_compatibility_db():
    """MongoDB koleksiyonlarını ve indexleri oluştur"""

    # MongoDB bağlantısı
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=30000)
    db = client['facesyma-backend']

    print("📋 Compatibility & Communities DB Migration başladı...\n")

    # ── 1. Compatibility Koleksiyonu ───────────────────────────────────────────
    print("1️⃣  Creating 'compatibility' collection...")
    try:
        compatibility_col = db['compatibility']

        # Drop existing indexes except _id
        for idx in compatibility_col.list_indexes():
            _iname = idx['name']
            if _iname != '_id_':
                compatibility_col.drop_index(_iname)

        # Indexes oluştur
        _cidx = compatibility_col.create_index
        _cidx([('user1_id', ASCENDING), ('user2_id', ASCENDING)], unique=True, name='idx_user_pair')
        _cidx('user1_id')
        _cidx('user2_id')
        _cidx('category')
        _cidx('calculated_at', expireAfterSeconds=2592000)  # 30 gün

        print("   ✅ Indexes created: user_pair, user1_id, user2_id, category, calculated_at (TTL)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # ── 2. Communities Koleksiyonu ────────────────────────────────────────────
    print("\n2️⃣  Creating 'communities' collection...")
    try:
        communities_col = db['communities']

        for idx in communities_col.list_indexes():
            _iname = idx['name']
            if _iname != '_id_':
                communities_col.drop_index(_iname)

        _cidx = communities_col.create_index
        _cidx('name')
        _cidx('type')
        _cidx('trait_name')
        _cidx('created_at')

        print("   ✅ Indexes created: name, type, trait_name, created_at")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # ── 3. Community Members Koleksiyonu ──────────────────────────────────────
    print("\n3️⃣  Creating 'community_members' collection...")
    try:
        members_col = db['community_members']

        for idx in members_col.list_indexes():
            _iname = idx['name']
            if _iname != '_id_':
                members_col.drop_index(_iname)

        _cidx = members_col.create_index
        _cidx([('community_id', ASCENDING), ('user_id', ASCENDING)], unique=True, name='idx_community_user')
        _cidx('user_id')
        _cidx('community_id')
        _cidx('joined_at')

        print("   ✅ Indexes created: community_user (unique), user_id, community_id, joined_at")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # ── 4. Community Messages Koleksiyonu ─────────────────────────────────────
    print("\n4️⃣  Creating 'community_messages' collection...")
    try:
        messages_col = db['community_messages']

        for idx in messages_col.list_indexes():
            _iname = idx['name']
            if _iname != '_id_':
                messages_col.drop_index(_iname)

        _cidx = messages_col.create_index
        _cidx('from_user_id')
        _cidx('to_user_id')
        _cidx('community_id')
        _cidx('created_at', expireAfterSeconds=7776000)  # 90 gün auto-delete

        print("   ✅ Indexes created: from_user_id, to_user_id, community_id, created_at (TTL: 90 days)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # ── 5. Community Files Koleksiyonu ────────────────────────────────────────
    print("\n5️⃣  Creating 'community_files' collection...")
    try:
        files_col = db['community_files']

        for idx in files_col.list_indexes():
            _iname = idx['name']
            if _iname != '_id_':
                files_col.drop_index(_iname)

        _cidx = files_col.create_index
        _cidx('owner_id')
        _cidx('community_id')
        _cidx('uploaded_at')
        _cidx('expires_at', expireAfterSeconds=0)  # TTL enabled

        print("   ✅ Indexes created: owner_id, community_id, uploaded_at, expires_at (TTL)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # ── 6. Moderation Logs Koleksiyonu ────────────────────────────────────────
    print("\n6️⃣  Creating 'moderation_logs' collection...")
    try:
        moderation_col = db['moderation_logs']

        for idx in moderation_col.list_indexes():
            _iname = idx['name']
            if _iname != '_id_':
                moderation_col.drop_index(_iname)

        _cidx = moderation_col.create_index
        _cidx('community_id')
        _cidx('target_user_id')
        _cidx('created_at')
        _cidx('status')

        print("   ✅ Indexes created: community_id, target_user_id, created_at, status")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # ── 7. User Subscriptions Koleksiyonu ──────────────────────────────────────
    print("\n7️⃣  Creating 'user_subscriptions' collection...")
    try:
        subscriptions_col = db['user_subscriptions']

        for idx in subscriptions_col.list_indexes():
            _iname = idx['name']
            if _iname != '_id_':
                subscriptions_col.drop_index(_iname)

        _cidx = subscriptions_col.create_index
        _cidx('user_id', unique=True)
        _cidx('tier')
        _cidx('status')
        _cidx('renews_at')

        print("   ✅ Indexes created: user_id (unique), tier, status, renews_at")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # ── Kontrol ────────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("✅ Migration Complete!")
    print("="*60)

    print("\n📊 Koleksiyon Özeti:")
    for col_name in ['compatibility', 'communities', 'community_members', 'community_messages', 'community_files', 'moderation_logs', 'user_subscriptions']:
        col = db[col_name]
        count = col.count_documents({})
        indexes = len(list(col.list_indexes()))
        print(f"   • {col_name}: {count} documents, {indexes} indexes")

    client.close()
    return True


if __name__ == '__main__':
    success = migrate_compatibility_db()
    sys.exit(0 if success else 1)
