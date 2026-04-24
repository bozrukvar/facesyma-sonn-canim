#!/usr/bin/env python
"""
seed_app_registry.py
====================
App registry (app_registry koleksiyonu) başlangıç verilerini MongoDB'ye ekler.
Tek seferlik script — Idempotent ($setOnInsert + upsert=True ile).

Kullanım:
    cd facesyma_backend
    python ../seed_app_registry.py
"""

import os
import sys
from datetime import datetime

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facesyma_project.settings')

import django
django.setup()

from django.conf import settings
from pymongo import MongoClient


def seed_app_registry():
    """Seed app_registry collection with mobile ve web apps."""

    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=30000)
    db = client['facesyma-backend']
    col = db['app_registry']

    now = datetime.now().isoformat()

    # Mobile app — aktif, tüm feature flags açık
    mobile_app = {
        'app_id': 'mobile',
        'name': 'Facesyma Mobile',
        'status': 'active',
        'config': {
            'maintenance_mode': False,
            'maintenance_message': '',
            'min_version': '1.0.0',
            'feature_flags': {
                'golden_ratio': True,
                'ai_chat': True,
                'community': True,
                'leaderboard': True,
            }
        },
        'created_at': now,
        'updated_at': now,
    }

    # Web app — başlangıçta pasif
    web_app = {
        'app_id': 'web',
        'name': 'Facesyma Web',
        'status': 'inactive',
        'config': {
            'maintenance_mode': False,
            'maintenance_message': 'Web app coming soon',
            'min_version': '0.0.0',
            'feature_flags': {
                'golden_ratio': True,
                'ai_chat': False,
                'community': False,
                'leaderboard': False,
            }
        },
        'created_at': now,
        'updated_at': now,
    }

    apps = [mobile_app, web_app]

    for app in apps:
        _aid = app['app_id']
        result = col.update_one(
            {'app_id': _aid},
            {
                '$setOnInsert': app
            },
            upsert=True
        )

        if result.upserted_id:
            print(f"✓ Seeded: {_aid}")
        else:
            print(f"⊘ Already exists, skipped: {_aid}")

    client.close()
    print("\n✓ App registry seeding complete")


if __name__ == '__main__':
    try:
        seed_app_registry()
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
