"""
admin_api/utils/audit.py
========================
Admin activity logging — silent failures to prevent breaking main operations.
"""

import logging
from datetime import datetime
from admin_api.utils.mongo import _get_db, _next_id

log = logging.getLogger(__name__)


def log_admin_action(admin_payload: dict, action: str, target_type: str,
                     target_id=None, old_value=None, new_value=None,
                     ip_address: str = None, detail: str = None):
    """
    Log an admin action to MongoDB admin_activity_log collection.

    If logging fails, the failure is silently caught — logging errors
    should never break the main operation.

    Args:
        admin_payload: Dict from _require_admin(request) — contains user_id, email, etc.
        action: Action type (e.g., 'update_user', 'delete_user', 'bulk_delete', 'update_app_config')
        target_type: Type of target (e.g., 'user', 'app_config', 'sifat')
        target_id: ID of the specific target being modified
        old_value: Previous state (optional)
        new_value: New state (optional)
        ip_address: Client IP (extracted from request.META)
        detail: Additional context (optional)
    """
    try:
        col = _get_db()['admin_activity_log']

        col.insert_one({
            'id': _next_id(col),
            'admin_id': admin_payload.get('user_id'),
            'admin_email': admin_payload.get('email'),
            'action': action,
            'target_type': target_type,
            'target_id': target_id,
            'old_value': old_value,
            'new_value': new_value,
            'ip_address': ip_address,
            'timestamp': datetime.utcnow().isoformat(),
            'detail': detail,
        })
    except Exception as e:
        # Silently log the error — never raise
        log.exception(f'Audit log failed: {e}')
        pass


def extract_ip(request) -> str:
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip
