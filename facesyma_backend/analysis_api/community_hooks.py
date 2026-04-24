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
from admin_api.utils.mongo import (
    get_communities_col       as _get_communities_col,
    get_community_members_col as _get_community_members_col,
    get_users_col             as _get_users_col,
)

log = logging.getLogger(__name__)

_COMPAT_USER_PROJ = {'_id': 0, 'id': 1, 'username': 1, 'golden_ratio': 1, 'top_sifats': 1, 'modules': 1}


def auto_add_to_communities(user_id: int, analysis_result: dict):
    """
    Kullanıcıya sıfat/modül tabanlı topluluk davetiyesi gönder.

    NOT: Otomatik üyelik değil, PENDING (onay bekleme) durumuyla davet gönderilir.
    Kullanıcı talep ettikten sonra STATUS: 'active' olur.

    Args:
        user_id: Kullanıcı ID
        analysis_result: Analiz sonucu {
            'top_sifats': ['Lider', 'Disiplinli', ...],
            'modules': ['Leaderboard', 'Duygusal Zeka', ...],
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

        _arget = analysis_result.get
        top_sifats = _arget('top_sifats', [])
        modules = _arget('modules', [])

        invitations_count = 0

        def _process_communities(items, type_label, name_fn, desc_fn):
            """Batch-fetch existing communities, create missing ones, then invite."""
            nonlocal invitations_count
            if not items:
                return

            # Batch fetch all existing communities in one query
            existing_map = {
                doc['trait_name']: doc
                for doc in communities_col.find(
                    {'type': type_label, 'trait_name': {'$in': list(items)}},
                    {'_id': 1, 'trait_name': 1},
                )
            }

            # Build list of (item, community) pairs — create missing ones in bulk
            resolved = []
            _rappend = resolved.append
            _linfo = log.info
            now_ts = time.time()
            new_docs = []
            new_items = []
            for item in items:
                community = existing_map.get(item)
                if not community:
                    doc = {
                        'name': name_fn(item),
                        'type': type_label,
                        'trait_name': item,
                        'description': desc_fn(item),
                        'founder_id': 0,
                        'member_count': 0,
                        'is_active': True,
                        'created_at': now_ts,
                        'updated_at': now_ts,
                        'rules': '',
                        'moderation_policy': 'automated'
                    }
                    new_docs.append(doc)
                    new_items.append(item)
                else:
                    _rappend((item, community))
            if new_docs:
                result = communities_col.insert_many(new_docs, ordered=True)
                for doc, oid, item in zip(new_docs, result.inserted_ids, new_items):
                    doc['_id'] = oid
                    _rappend((item, doc))
                    _linfo(f'New {type_label} community created: {item}')
            # Re-sort resolved to preserve original items order
            item_order = {item: idx for idx, item in enumerate(items)}
            resolved.sort(key=lambda x: item_order.get(x[0], 0))

            # Batch fetch existing memberships in one query
            community_ids = [str(c['_id']) for _, c in resolved]
            already_member = {
                doc['community_id']
                for doc in members_col.find(
                    {'community_id': {'$in': community_ids}, 'user_id': user_id},
                    {'community_id': 1},
                )
            }

            # Batch insert missing memberships
            new_memberships = []
            invited_items = []
            for item, community in resolved:
                cid = str(community['_id'])
                if cid not in already_member:
                    new_memberships.append({
                        'community_id': cid,
                        'user_id': user_id,
                        'status': 'pending',
                        'joined_at': None,
                        'approved_at': None,
                        'harmony_level': 75,
                        'is_mod': False,
                        'invited_at': now_ts,
                    })
                    invited_items.append(item)
            if new_memberships:
                try:
                    members_col.insert_many(new_memberships, ordered=False)
                    invitations_count += len(new_memberships)
                    for item in invited_items:
                        _linfo(f'User {user_id} INVITED to "{item}" {type_label} community (awaiting approval).')
                except Exception as e:
                    log.warning(f'{type_label} community batch invite error: {e}')

        # 1. Sıfat tabanlı topluluklara davet gönder
        _process_communities(
            top_sifats, 'TRAIT',
            lambda s: f'{s} Topluluğu',
            lambda s: f'{s} özelliklerine sahip kişilerin toplandığı topluluk.',
        )

        # 2. Modül tabanlı topluluklara davet gönder
        _process_communities(
            modules, 'MODULE',
            lambda m: f'{m} Modülü',
            lambda m: f'{m} modülüne abone olan kişilerin toplandığı topluluk.',
        )

        return {
            'success': True,
            'invitations_sent': invitations_count,
            'pending_approvals': invitations_count,
            'message': f'{invitations_count} community invitations sent. Awaiting approval.'
        }

    except Exception as e:
        log.exception(f'auto_add_to_communities error: {e}')
        return {
            'success': False,
            'invitations_sent': 0,
            'pending_approvals': 0,
            'message': 'Community assignment failed.'
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
                'message': 'User not found.'
            }

        _, find_compat = _load_compatibility_module()
        if not find_compat:
            return {
                'success': False,
                'compatible_users': 0,
                'message': 'Compatibility module could not be loaded.'
            }

        users_col = _get_users_col()
        all_users = list(users_col.find({'id': {'$ne': user_id}}, _COMPAT_USER_PROJ).limit(100))

        # Uyumlu kullanıcıları bul
        compatible_users = find_compat(user_id, [user] + all_users, 'UYUMLU', limit)

        n_compat = len(compatible_users)
        log.info(f'Found {n_compat} compatible users for user {user_id}.')

        # TODO: Notification gönder (future phase)

        return {
            'success': True,
            'compatible_users': n_compat,
            'message': f'{n_compat} compatible users found.',
        }

    except Exception as e:
        log.exception(f'find_and_notify_compatible_users error: {e}')
        return {
            'success': False,
            'compatible_users': 0,
            'message': 'Compatible user search failed.'
        }
