"""
community_hooks.py
==================
Community auto-creation hooks — triggered when users complete analysis.

Functions:
- auto_add_to_communities() — Auto-add user to trait/module-based communities
- find_and_notify_compatible_users() — Find compatible users and notify
"""
import time
import logging
from pymongo import MongoClient
from django.conf import settings

log = logging.getLogger(__name__)


def _get_db():
    """MongoDB'ye bağlan"""
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=30000)
    return client['facesyma-backend']


def _get_communities_col():
    return _get_db()['communities']


def _get_community_members_col():
    return _get_db()['community_members']


def _get_users_col():
    return _get_db()['appfaceapi_myuser']


def auto_add_to_communities(user_id: int, analysis_result: dict):
    """
    Kullanıcıya sıfat/modül tabanlı topluluk davetiyesi gönder.

    NOT: Otomatik üyelik değil, PENDING (onay bekleme) durumuyla davet gönderilir.
    Kullanıcı talep ettikten sonra STATUS: 'active' olur.

    Args:
        user_id: Kullanıcı ID
        analysis_result: Analiz sonucu {
            'top_sifats': ['Lider', 'Disiplinli', ...],
            'modules': ['Liderlik', 'Duygusal Zeka', ...],
            'sifat_scores': {...}
        }

    Returns:
        {
            'success': bool,
            'invitations_sent': int,
            'message': str,
            'pending_approvals': int
        }
    """

    try:
        communities_col = _get_communities_col()
        members_col = _get_community_members_col()

        top_sifats = analysis_result.get('top_sifats', [])
        modules = analysis_result.get('modules', [])

        invitations_count = 0

        # 1. Sıfat tabanlı topluluklara davet gönder
        for sifat in top_sifats:
            try:
                # Sıfat için topluluk var mı?
                community = communities_col.find_one({
                    'type': 'TRAIT',
                    'trait_name': sifat
                })

                if not community:
                    # Eğer yok, oluştur
                    community = {
                        'name': f'{sifat} Topluluğu',
                        'type': 'TRAIT',
                        'trait_name': sifat,
                        'description': f'{sifat} özelliklerine sahip kişilerin toplandığı topluluk.',
                        'founder_id': 0,  # System
                        'member_count': 0,
                        'is_active': True,
                        'created_at': time.time(),
                        'updated_at': time.time(),
                        'rules': '',
                        'moderation_policy': 'automated'
                    }
                    result = communities_col.insert_one(community)
                    community['_id'] = result.inserted_id
                    log.info(f'Yeni topluluk oluşturuldu: {sifat}')

                # Üyelik var mı kontrol et
                existing = members_col.find_one({
                    'community_id': str(community['_id']),
                    'user_id': user_id
                })

                if not existing:
                    # ✅ PENDING durumunda davet gönder (onay bekleme)
                    members_col.insert_one({
                        'community_id': str(community['_id']),
                        'user_id': user_id,
                        'status': 'pending',  # 🔐 Onay bekleme durumu
                        'joined_at': None,  # Henüz katılmadı
                        'approved_at': None,  # Onay tarihi boş
                        'harmony_level': 75,  # Default uyum seviyesi
                        'is_mod': False,
                        'invited_at': time.time()  # Davet tarihi
                    })

                    invitations_count += 1
                    log.info(f'Kullanıcı {user_id} "{sifat}" topluluğuna DAVET gönderildi (onay bekleme).')

            except Exception as e:
                log.warning(f'Sıfat topluluğu davetiyle hata ({sifat}): {e}')

        # 2. Modül tabanlı topluluklara davet gönder
        for module in modules:
            try:
                # Modül için topluluk var mı?
                community = communities_col.find_one({
                    'type': 'MODULE',
                    'trait_name': module
                })

                if not community:
                    # Eğer yok, oluştur
                    community = {
                        'name': f'{module} Modülü',
                        'type': 'MODULE',
                        'trait_name': module,
                        'description': f'{module} modülüne abone olan kişilerin toplandığı topluluk.',
                        'founder_id': 0,  # System
                        'member_count': 0,
                        'is_active': True,
                        'created_at': time.time(),
                        'updated_at': time.time(),
                        'rules': '',
                        'moderation_policy': 'automated'
                    }
                    result = communities_col.insert_one(community)
                    community['_id'] = result.inserted_id
                    log.info(f'Yeni modül topluluğu oluşturuldu: {module}')

                # Üyelik var mı kontrol et
                existing = members_col.find_one({
                    'community_id': str(community['_id']),
                    'user_id': user_id
                })

                if not existing:
                    # ✅ PENDING durumunda davet gönder (onay bekleme)
                    members_col.insert_one({
                        'community_id': str(community['_id']),
                        'user_id': user_id,
                        'status': 'pending',  # 🔐 Onay bekleme durumu
                        'joined_at': None,
                        'approved_at': None,
                        'harmony_level': 75,
                        'is_mod': False,
                        'invited_at': time.time()
                    })

                    invitations_count += 1
                    log.info(f'Kullanıcı {user_id} "{module}" modül topluluğuna DAVET gönderildi (onay bekleme).')

            except Exception as e:
                log.warning(f'Modül topluluğu davetiyle hata ({module}): {e}')

        return {
            'success': True,
            'invitations_sent': invitations_count,
            'pending_approvals': invitations_count,
            'message': f'Kullanıcıya {invitations_count} topluluk davetiyeleri gönderildi. Lütfen onayı beklemektedir.'
        }

    except Exception as e:
        log.exception(f'auto_add_to_communities hatası: {e}')
        return {
            'success': False,
            'invitations_sent': 0,
            'pending_approvals': 0,
            'message': f'Hata: {str(e)}'
        }


def find_and_notify_compatible_users(user_id: int, limit: int = 10):
    """
    Kullanıcıya uyumlu kullanıcıları bul ve (future: notify).

    Args:
        user_id: Kullanıcı ID
        limit: Döndürülecek kaç uyumlu kullanıcı

    Returns:
        {
            'success': bool,
            'compatible_users': int,
            'message': str
        }
    """

    try:
        from compatibility_views import _get_user_profile, _load_compatibility_module

        user = _get_user_profile(user_id)
        if not user:
            return {
                'success': False,
                'compatible_users': 0,
                'message': 'Kullanıcı bulunamadı.'
            }

        _, find_compat = _load_compatibility_module()
        if not find_compat:
            return {
                'success': False,
                'compatible_users': 0,
                'message': 'Compatibility modülü yüklenemedı.'
            }

        users_col = _get_users_col()
        all_users = list(users_col.find({'id': {'$ne': user_id}}, {
            '_id': 0, 'id': 1, 'username': 1, 'golden_ratio': 1,
            'top_sifats': 1, 'modules': 1
        }).limit(100))

        # Uyumlu kullanıcıları bul
        compatible_users = find_compat(user_id, [user] + all_users, 'UYUMLU', limit)

        log.info(f'Kullanıcı {user_id} için {len(compatible_users)} uyumlu kullanıcı bulundu.')

        # TODO: Notification gönder (future phase)

        return {
            'success': True,
            'compatible_users': len(compatible_users),
            'message': f'{len(compatible_users)} uyumlu kullanıcı bulundu.'
        }

    except Exception as e:
        log.exception(f'find_and_notify_compatible_users hatası: {e}')
        return {
            'success': False,
            'compatible_users': 0,
            'message': f'Hata: {str(e)}'
        }
