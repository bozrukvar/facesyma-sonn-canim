import os
"""
setup_admin_phase1.py
=====================
Admin Panel Phase 1 - MongoDB Collections Setup

Creates all collections needed for:
  - Analytics Dashboard
  - Payment Integration
  - Health Monitoring
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
import logging

log = logging.getLogger(__name__)

MONGO_URI = os.environ.get('MONGO_URI', '')


def setup_collections():
    """MongoDB collections ve indexes'i oluştur"""

    _cidx = col.create_index
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['facesyma-backend']

    print("\n" + "=" * 70)
    print("🔧 Setting up Admin Panel Phase 1 Collections...")
    print("=" * 70)

    # ── Collection 1: payment_transactions ─────────────────────────────
    print("\n1️⃣  Creating payment_transactions collection...")
    try:
        col = db['payment_transactions']

        _cidx([('provider', ASCENDING)])
        _cidx([('status', ASCENDING)])
        _cidx([('created_at', ASCENDING)], expireAfterSeconds=7776000)  # 90 days
        _cidx([('user_id', ASCENDING)])
        _cidx([('payment_intent_id', ASCENDING), ('charge_id', ASCENDING)])

        print("   ✅ payment_transactions OK")
        print("   - Index 1: (provider)")
        print("   - Index 2: (status)")
        print("   - Index 3: TTL 90 days on created_at")
        print("   - Index 4: (user_id)")
        print("   - Index 5: (payment_intent_id, charge_id)")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # ── Collection 2: payment_refunds ──────────────────────────────────
    print("\n2️⃣  Creating payment_refunds collection...")
    try:
        col = db['payment_refunds']

        _cidx([('transaction_id', ASCENDING)])
        _cidx([('status', ASCENDING)])
        _cidx([('created_at', ASCENDING)], expireAfterSeconds=7776000)  # 90 days

        print("   ✅ payment_refunds OK")
        print("   - Index 1: (transaction_id)")
        print("   - Index 2: (status)")
        print("   - Index 3: TTL 90 days on created_at")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # ── Collection 3: uptime_logs ──────────────────────────────────────
    print("\n3️⃣  Creating uptime_logs collection...")
    try:
        col = db['uptime_logs']

        _cidx([('timestamp', DESCENDING)])
        _cidx([('status', ASCENDING)])
        _cidx([('timestamp', ASCENDING)], expireAfterSeconds=7776000)  # 90 days

        print("   ✅ uptime_logs OK")
        print("   - Index 1: (timestamp DESC)")
        print("   - Index 2: (status)")
        print("   - Index 3: TTL 90 days on timestamp")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # ── Collection 4: error_logs ───────────────────────────────────────
    print("\n4️⃣  Creating error_logs collection...")
    try:
        col = db['error_logs']

        _cidx([('timestamp', DESCENDING)])
        _cidx([('endpoint', ASCENDING)])
        _cidx([('error_type', ASCENDING)])
        _cidx([('timestamp', ASCENDING)], expireAfterSeconds=2592000)  # 30 days

        print("   ✅ error_logs OK")
        print("   - Index 1: (timestamp DESC)")
        print("   - Index 2: (endpoint)")
        print("   - Index 3: (error_type)")
        print("   - Index 4: TTL 30 days on timestamp")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # ── Collection 5: api_logs ────────────────────────────────────────
    print("\n5️⃣  Creating api_logs collection...")
    try:
        col = db['api_logs']

        _cidx([('timestamp', DESCENDING)])
        _cidx([('endpoint', ASCENDING)])
        _cidx([('response_time_ms', ASCENDING)])
        _cidx([('timestamp', ASCENDING)], expireAfterSeconds=2592000)  # 30 days

        print("   ✅ api_logs OK")
        print("   - Index 1: (timestamp DESC)")
        print("   - Index 2: (endpoint)")
        print("   - Index 3: (response_time_ms)")
        print("   - Index 4: TTL 30 days on timestamp")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # ── Collection 6: alerts ───────────────────────────────────────────
    print("\n6️⃣  Creating alerts collection...")
    try:
        col = db['alerts']

        _cidx([('status', ASCENDING)])
        _cidx([('created_at', DESCENDING)])
        _cidx([('type', ASCENDING)])

        print("   ✅ alerts OK")
        print("   - Index 1: (status)")
        print("   - Index 2: (created_at DESC)")
        print("   - Index 3: (type)")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # ── Collection 7: system_logs ──────────────────────────────────────
    print("\n7️⃣  Creating system_logs collection...")
    try:
        col = db['system_logs']

        _cidx([('timestamp', DESCENDING)])
        _cidx([('level', ASCENDING)])
        _cidx([('service', ASCENDING)])
        _cidx([('timestamp', ASCENDING)], expireAfterSeconds=1296000)  # 15 days

        print("   ✅ system_logs OK")
        print("   - Index 1: (timestamp DESC)")
        print("   - Index 2: (level)")
        print("   - Index 3: (service)")
        print("   - Index 4: TTL 15 days on timestamp")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # ── Statistics ─────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("✅ All Phase 1 collections created successfully!")
    print("=" * 70)

    print("\n📊 Collection Statistics:")
    for collection in ['payment_transactions', 'payment_refunds', 'uptime_logs',
                       'error_logs', 'api_logs', 'alerts', 'system_logs']:
        count = db[collection].count_documents({})
        print(f"   - {collection}: {count} documents")

    client.close()
    print("\n✨ Setup complete!")
    print("\nNote: Make sure these environment variables are set:")
    print("  - GOOGLE_PAY_MERCHANT_ID  (Google Pay merchant ID)")
    print("  - APPLE_PAY_MERCHANT_ID   (Apple Pay merchant ID)")
    print("  # Vakıfbank VPP: ileriki versiyon güncellemesi ile eklenecek")


if __name__ == '__main__':
    setup_collections()
