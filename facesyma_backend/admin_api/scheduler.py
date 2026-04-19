"""
admin_api/scheduler.py
======================
Background job scheduler for gamification tasks.

Uses APScheduler to schedule:
- Daily leaderboard snapshots (3 types: global, trait-based, community-specific)
- Old snapshot cleanup (90-day retention policy)
"""

import logging
from datetime import datetime, timedelta
import time
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from django.core.mail import send_mail
from django.conf import settings

log = logging.getLogger(__name__)

# Global scheduler instance
_scheduler = None


def _job_take_global_snapshot():
    """Take snapshot of global leaderboard"""
    try:
        from gamification.services.leaderboard_trend_service import (
            LeaderboardTrendService
        )
        snapshot_id = LeaderboardTrendService.take_snapshot(
            leaderboard_type="global",
            trait_id=None,
            community_id=None,
            time_period="all_time",
            sort_by="coins",
            top_n=100,
        )
        log.info(f"✓ Daily snapshot (global): {snapshot_id}")
    except Exception as e:
        log.error(f"✗ Failed to take global snapshot: {e}")


def _job_take_trait_snapshots():
    """Take snapshots of all trait-based leaderboards"""
    try:
        from admin_api.utils.mongo import _get_db
        from gamification.services.leaderboard_trend_service import (
            LeaderboardTrendService
        )

        # Get all unique sifats
        db = _get_db()
        users_col = db["appfaceapi_myuser"]
        sifats = users_col.distinct("top_sifats")

        if not sifats:
            log.warning("No sifats found to snapshot")
            return

        count = 0
        for sifat_id in sifats:
            try:
                LeaderboardTrendService.take_snapshot(
                    leaderboard_type="trait",
                    trait_id=sifat_id,
                    community_id=None,
                    time_period="all_time",
                    sort_by="coins",
                    top_n=100,
                )
                count += 1
            except Exception as e:
                log.warning(f"Failed to snapshot trait {sifat_id}: {e}")

        log.info(f"✓ Daily snapshots (trait): {count} traits")

    except Exception as e:
        log.error(f"✗ Failed to take trait snapshots: {e}")


def _job_take_community_snapshots():
    """Take snapshots of all community leaderboards"""
    try:
        from admin_api.utils.mongo import _get_db
        from gamification.services.leaderboard_trend_service import (
            LeaderboardTrendService
        )

        # Get all communities
        db = _get_db()
        communities_col = db["communities"]
        communities = communities_col.find({}, {"_id": 1})

        count = 0
        for community in communities:
            try:
                community_id = community["_id"]
                LeaderboardTrendService.take_snapshot(
                    leaderboard_type="community",
                    trait_id=None,
                    community_id=community_id,
                    time_period="all_time",
                    sort_by="coins",
                    top_n=100,
                )
                count += 1
            except Exception as e:
                log.warning(f"Failed to snapshot community {community_id}: {e}")

        log.info(f"✓ Daily snapshots (community): {count} communities")

    except Exception as e:
        log.error(f"✗ Failed to take community snapshots: {e}")


def _job_cleanup_old_snapshots():
    """Delete snapshots older than retention policy (90 days)"""
    try:
        from gamification.services.leaderboard_trend_service import (
            LeaderboardTrendService
        )
        deleted = LeaderboardTrendService.cleanup_old_snapshots()
        log.info(f"✓ Cleaned up old snapshots: {deleted} deleted")
    except Exception as e:
        log.error(f"✗ Failed to cleanup snapshots: {e}")


def _job_check_expired_subscriptions():
    """Proactively downgrade expired premium subscriptions"""
    try:
        from admin_api.utils.mongo import _get_db

        db = _get_db()
        subs_col = db["user_subscriptions"]
        users_col = db["appfaceapi_myuser"]
        events_col = db["subscription_events"]
        now = datetime.utcnow()
        now_ts = time.time()

        expired_count = 0

        # Check path 1: expires_date (ISO string, RevenueCat)
        expired_docs = list(
            subs_col.find(
                {
                    "expires_date": {"$lt": now.isoformat()},
                    "plan": "premium",
                }
            )
        )

        for doc in expired_docs:
            user_id = doc.get("user_id")
            if not user_id:
                continue

            # Update subscription doc
            subs_col.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "plan": "free",
                        "status": "expired",
                        "expired_at": now.isoformat(),
                    }
                },
            )

            # Update user doc — CRITICAL FIX
            user = users_col.find_one({"id": user_id})
            if user:
                users_col.update_one({"id": user_id}, {"$set": {"plan": "free"}})

            # Log event
            events_col.insert_one(
                {
                    "type": "expired",
                    "user_id": user_id,
                    "user_email": user.get("email") if user else "",
                    "expired_at": now.isoformat(),
                    "detail": f"Subscription expired. expires_date was {doc.get('expires_date')}",
                }
            )

            expired_count += 1

        # Check path 2: renews_at (Unix timestamp, freemium)
        expired_docs_2 = list(
            subs_col.find(
                {
                    "renews_at": {"$lt": now_ts},
                    "tier": "premium",
                }
            )
        )

        for doc in expired_docs_2:
            user_id = doc.get("user_id")
            if not user_id:
                continue

            # Update subscription doc
            subs_col.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "tier": "free",
                        "status": "expired",
                        "expired_at": now.isoformat(),
                    }
                },
            )

            # Update user doc
            user = users_col.find_one({"id": user_id})
            if user:
                users_col.update_one({"id": user_id}, {"$set": {"plan": "free"}})

            # Log event
            events_col.insert_one(
                {
                    "type": "expired",
                    "user_id": user_id,
                    "user_email": user.get("email") if user else "",
                    "expired_at": now.isoformat(),
                    "detail": f"Subscription expired. renews_at was {doc.get('renews_at')}",
                }
            )

            expired_count += 1

        log.info(f"✓ Checked subscriptions: {expired_count} expired and downgraded")

    except Exception as e:
        log.error(f"✗ Failed to check expired subscriptions: {e}")


def _job_send_renewal_reminders():
    """Send renewal reminder notifications for subscriptions expiring soon"""
    try:
        from admin_api.utils.mongo import _get_db

        db = _get_db()
        subs_col = db["user_subscriptions"]
        users_col = db["appfaceapi_myuser"]
        notif_col = db["subscription_notifications"]
        now = datetime.utcnow()
        now_ts = time.time()

        reminder_count = 0

        # Find subscriptions expiring in 3-8 days
        future_3d = now + timedelta(days=3)
        future_8d = now + timedelta(days=8)

        # Path 1: expires_date (ISO string)
        expiring_soon = list(
            subs_col.find(
                {
                    "expires_date": {
                        "$gte": future_3d.isoformat(),
                        "$lt": future_8d.isoformat(),
                    },
                    "plan": "premium",
                }
            )
        )

        for doc in expiring_soon:
            user_id = doc.get("user_id")
            if not user_id:
                continue

            user = users_col.find_one({"id": user_id})
            if not user:
                continue

            expires_date = doc.get("expires_date")
            try:
                exp_dt = datetime.fromisoformat(expires_date.replace("Z", "+00:00"))
                expires_in_days = (exp_dt - now).days
            except Exception:
                expires_in_days = 5

            # Create notification
            notif_col.insert_one(
                {
                    "type": "reminder",
                    "user_id": user_id,
                    "user_email": user.get("email"),
                    "expires_in_days": expires_in_days,
                    "expires_at": expires_date,
                    "created_at": now.isoformat(),
                    "email_sent": False,
                }
            )

            reminder_count += 1

        # Path 2: renews_at (Unix timestamp)
        future_3d_ts = now_ts + (3 * 86400)
        future_8d_ts = now_ts + (8 * 86400)

        expiring_soon_2 = list(
            subs_col.find(
                {
                    "renews_at": {
                        "$gte": future_3d_ts,
                        "$lt": future_8d_ts,
                    },
                    "tier": "premium",
                }
            )
        )

        for doc in expiring_soon_2:
            user_id = doc.get("user_id")
            if not user_id:
                continue

            user = users_col.find_one({"id": user_id})
            if not user:
                continue

            renews_at = doc.get("renews_at")
            expires_in_days = int((renews_at - now_ts) / 86400)

            # Create notification
            notif_col.insert_one(
                {
                    "type": "reminder",
                    "user_id": user_id,
                    "user_email": user.get("email"),
                    "expires_in_days": expires_in_days,
                    "expires_at": datetime.fromtimestamp(renews_at).isoformat(),
                    "created_at": now.isoformat(),
                    "email_sent": False,
                }
            )

            reminder_count += 1

        log.info(f"✓ Sent renewal reminders: {reminder_count} notifications created")

    except Exception as e:
        log.error(f"✗ Failed to send renewal reminders: {e}")


# ── Alert Rules Checking (Feature 3 - Automated Alerts) ───────────────────

def _fetch_metric(metric: str) -> float:
    """Fetch metric value for alert evaluation."""
    try:
        from admin_api.utils.mongo import get_users_col, get_history_col, _get_db

        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        today_start_ts = today_start.timestamp()
        one_hour_ago_ts = (now - timedelta(hours=1)).timestamp()

        users_col = get_users_col()
        history_col = get_history_col()

        if metric == 'new_users_today':
            return float(users_col.count_documents({
                'date_joined': {'$gte': today_start.isoformat()}
            }))
        elif metric == 'analyses_today':
            return float(history_col.count_documents({
                'created_at': {'$gte': today_start_ts}
            }))
        elif metric == 'active_users_5min':
            return float(users_col.count_documents({
                'last_active': {'$gte': now.timestamp() - 300}
            }))
        elif metric == 'error_rate_1h':
            db = _get_db()
            audit_col = db['admin_activity_log']
            total = audit_col.count_documents({
                'timestamp': {'$gte': (now - timedelta(hours=1)).isoformat()}
            })
            if total == 0:
                return 0.0
            errors = audit_col.count_documents({
                'timestamp': {'$gte': (now - timedelta(hours=1)).isoformat()},
                'action': {'$regex': 'delete|error', '$options': 'i'}
            })
            return (errors / total) * 100.0

        return 0.0
    except Exception as e:
        log.error(f"Error fetching metric {metric}: {e}")
        return 0.0


def _evaluate_condition(value: float, condition: str, threshold: float) -> bool:
    """Evaluate if condition is met."""
    if condition == 'less_than':
        return value < threshold
    elif condition == 'greater_than':
        return value > threshold
    return False


def _send_slack_notification(rule: dict, value: float) -> bool:
    """
    Send alert notification to Slack.

    Supports both global webhook (settings.SLACK_WEBHOOK_URL) and per-rule webhook.
    """
    from django.conf import settings
    webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', '') or rule.get('slack_webhook_url', '')
    if not webhook_url:
        return False

    try:
        payload = {
            "text": f"⚠️ *[Facesyma Alert]* {rule['name']}",
            "attachments": [{
                "color": "#ff0000",
                "fields": [
                    {"title": "Metrik", "value": rule['metric'], "short": True},
                    {"title": "Mevcut Değer", "value": str(value), "short": True},
                    {"title": "Eşik", "value": str(rule['threshold']), "short": True},
                    {"title": "Açıklama", "value": rule.get('description', ''), "short": False},
                ]
            }]
        }
        resp = requests.post(webhook_url, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        log.warning(f"Failed to send Slack notification: {e}")
        return False


def _job_check_alert_rules():
    """Check all enabled alert rules every 15 minutes."""
    try:
        from admin_api.utils.mongo import _get_db, _next_id

        db = _get_db()
        rules_col = db['alert_rules']
        history_col = db['alert_history']

        rules = list(rules_col.find({'enabled': True}))
        now = datetime.utcnow()

        triggered_count = 0

        for rule in rules:
            try:
                # Check cooldown
                if rule.get('last_triggered_at'):
                    last = datetime.fromisoformat(rule['last_triggered_at'])
                    cooldown_seconds = rule.get('cooldown_minutes', 60) * 60
                    if (now - last).total_seconds() < cooldown_seconds:
                        continue

                # Get metric value
                value = _fetch_metric(rule['metric'])

                # Evaluate condition
                if _evaluate_condition(value, rule['condition'], rule['threshold']):
                    # Trigger alert
                    email_sent = False
                    slack_sent = False

                    # Send email notification
                    if rule.get('notify_email'):
                        try:
                            send_mail(
                                subject=f"[Facesyma Alert] {rule['name']}",
                                message=f"{rule['description']}\n\nMevcut değer: {value}\nEşik: {rule['threshold']}",
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[rule['notify_email']],
                                fail_silently=True
                            )
                            email_sent = True
                        except Exception as e:
                            log.warning(f"Failed to send alert email for rule {rule['id']}: {e}")

                    # Send Slack notification
                    slack_sent = _send_slack_notification(rule, value)

                    # Record trigger
                    history_col.insert_one({
                        'id': _next_id(history_col),
                        'rule_id': rule['id'],
                        'rule_name': rule['name'],
                        'metric_value': value,
                        'threshold': rule['threshold'],
                        'triggered_at': now.isoformat(),
                        'email_sent': email_sent,
                        'slack_sent': slack_sent,  # YENİ
                    })

                    # Update last trigger time
                    rules_col.update_one(
                        {'id': rule['id']},
                        {'$set': {'last_triggered_at': now.isoformat()}}
                    )

                    # Broadcast alert triggered event to admin panel (WS)
                    try:
                        from admin_api.consumers import send_admin_event
                        send_admin_event('alert_triggered', {
                            'rule_name': rule['name'],
                            'metric': rule['metric'],
                            'value': value,
                            'threshold': rule['threshold'],
                            'time': now.isoformat()
                        })
                    except Exception:
                        pass  # WS broadcast failure shouldn't break alert checking

                    triggered_count += 1

            except Exception as e:
                log.error(f"Error checking rule {rule.get('id')}: {e}")

        if triggered_count > 0:
            log.info(f"✓ Alert rules checked: {triggered_count} alerts triggered")

    except Exception as e:
        log.error(f"✗ Failed to check alert rules: {e}")


def start_scheduler():
    """
    Start the background scheduler with gamification and subscription tasks.

    Schedule:
      - 00:05 UTC: Check and downgrade expired subscriptions
      - 02:00 UTC: Take global snapshot
      - 02:15 UTC: Take trait snapshots
      - 02:30 UTC: Take community snapshots
      - 03:00 UTC: Cleanup old snapshots
      - 09:00 UTC: Send renewal reminder notifications
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        log.warning("Scheduler already running")
        return

    try:
        _scheduler = BackgroundScheduler()

        # Global leaderboard snapshot (daily at 2:00 AM UTC)
        _scheduler.add_job(
            _job_take_global_snapshot,
            CronTrigger(hour=2, minute=0),
            id="job_global_snapshot",
            name="Daily global leaderboard snapshot",
            replace_existing=True,
        )

        # Trait leaderboard snapshots (daily at 2:15 AM UTC)
        _scheduler.add_job(
            _job_take_trait_snapshots,
            CronTrigger(hour=2, minute=15),
            id="job_trait_snapshots",
            name="Daily trait leaderboard snapshots",
            replace_existing=True,
        )

        # Community leaderboard snapshots (daily at 2:30 AM UTC)
        _scheduler.add_job(
            _job_take_community_snapshots,
            CronTrigger(hour=2, minute=30),
            id="job_community_snapshots",
            name="Daily community leaderboard snapshots",
            replace_existing=True,
        )

        # Old snapshot cleanup (daily at 3:00 AM UTC)
        _scheduler.add_job(
            _job_cleanup_old_snapshots,
            CronTrigger(hour=3, minute=0),
            id="job_cleanup",
            name="Cleanup old leaderboard snapshots",
            replace_existing=True,
        )

        # Check expired subscriptions (daily at 0:05 AM UTC)
        _scheduler.add_job(
            _job_check_expired_subscriptions,
            CronTrigger(hour=0, minute=5),
            id="job_check_expired_subs",
            name="Check and downgrade expired subscriptions",
            replace_existing=True,
        )

        # Send renewal reminders (daily at 9:00 AM UTC)
        _scheduler.add_job(
            _job_send_renewal_reminders,
            CronTrigger(hour=9, minute=0),
            id="job_renewal_reminders",
            name="Send subscription renewal reminders",
            replace_existing=True,
        )

        # Check alert rules (every 15 minutes)
        _scheduler.add_job(
            _job_check_alert_rules,
            IntervalTrigger(minutes=15),
            id="job_check_alert_rules",
            name="Check alert rules",
            replace_existing=True,
        )

        _scheduler.start()
        log.info("✓ Scheduler started with 7 jobs (4 gamification + 2 subscription + 1 alerts)")

    except Exception as e:
        log.error(f"✗ Failed to start scheduler: {e}")
        _scheduler = None


def stop_scheduler():
    """Stop the background scheduler"""
    global _scheduler

    if _scheduler is None or not _scheduler.running:
        return

    try:
        _scheduler.shutdown()
        _scheduler = None
        log.info("✓ Scheduler stopped")
    except Exception as e:
        log.error(f"✗ Failed to stop scheduler: {e}")


def get_scheduler_status():
    """Get scheduler status and job list"""
    global _scheduler

    if _scheduler is None:
        return {
            "running": False,
            "jobs": [],
        }

    return {
        "running": _scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in _scheduler.get_jobs()
        ],
    }
