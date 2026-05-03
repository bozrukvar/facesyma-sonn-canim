"""
facesyma_revize/push_service.py
================================
Firebase Cloud Messaging (FCM) push notification service.

Configure via .env:
  FCM_PROJECT_ID           — Firebase project ID (e.g. "facesyma-app")
  FCM_SERVICE_ACCOUNT_JSON — absolute path to service-account JSON file
                             OR the JSON content as a string (for Docker secrets)

If either var is missing the service silently skips sending — no crash.
"""
import os
import json
import logging

log = logging.getLogger(__name__)

_app = None
_init_done = False


def _get_app():
    global _app, _init_done
    if _init_done:
        return _app
    _init_done = True
    try:
        import firebase_admin
        from firebase_admin import credentials

        cred_val = os.environ.get('FCM_SERVICE_ACCOUNT_JSON', '').strip()
        project  = os.environ.get('FCM_PROJECT_ID', '').strip()

        if not cred_val or not project:
            log.warning('FCM not configured (FCM_PROJECT_ID / FCM_SERVICE_ACCOUNT_JSON missing)')
            return None

        if cred_val.startswith('{'):
            cred = credentials.Certificate(json.loads(cred_val))
        else:
            cred = credentials.Certificate(cred_val)

        _app = firebase_admin.initialize_app(cred, {'projectId': project})
        log.info('Firebase Admin SDK initialised for project: %s', project)
    except Exception as exc:
        log.error('Firebase Admin init failed: %s', exc)
    return _app


def send_push(token: str, title: str, body: str, data: dict | None = None) -> bool:
    """Send push to a single device token. Returns True on success."""
    if not token:
        return False
    try:
        from firebase_admin import messaging
        if _get_app() is None:
            return False
        msg = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={str(k): str(v) for k, v in (data or {}).items()},
            token=token,
        )
        messaging.send(msg)
        return True
    except Exception as exc:
        log.error('FCM send_push failed: %s', exc)
        return False


def send_multicast(tokens: list, title: str, body: str, data: dict | None = None) -> dict:
    """Send to up to 500 tokens. Returns {success: int, failure: int}.
    Caller must chunk larger lists.
    """
    tokens = [t for t in (tokens or []) if t]
    if not tokens:
        return {'success': 0, 'failure': 0}
    try:
        from firebase_admin import messaging
        if _get_app() is None:
            return {'success': 0, 'failure': len(tokens)}
        msg = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={str(k): str(v) for k, v in (data or {}).items()},
            tokens=tokens[:500],
        )
        resp = messaging.send_each_for_multicast(msg)
        return {'success': resp.success_count, 'failure': resp.failure_count}
    except Exception as exc:
        log.error('FCM send_multicast failed: %s', exc)
        return {'success': 0, 'failure': len(tokens)}


def send_multicast_chunked(tokens: list, title: str, body: str, data: dict | None = None) -> dict:
    """Send to any number of tokens, auto-chunking at 500."""
    tokens = [t for t in (tokens or []) if t]
    total_success = total_failure = 0
    for i in range(0, len(tokens), 500):
        result = send_multicast(tokens[i:i + 500], title, body, data)
        total_success += result['success']
        total_failure  += result['failure']
    return {'success': total_success, 'failure': total_failure}
