"""
Management command to seed default alert rules.

Usage:
    python manage.py seed_alert_rules
"""

from django.core.management.base import BaseCommand
from admin_api.utils.mongo import _get_db, _next_id
from datetime import datetime


class Command(BaseCommand):
    help = 'Seed default alert rules into MongoDB'

    def handle(self, *args, **options):
        _write = self.stdout.write
        _style = self.style
        try:
            db = _get_db()
            rules_col = db['alert_rules']

            # Default alert rules
            default_rules = [
                {
                    'name': 'No New Users Today',
                    'description': 'Alert when no new users register in a day',
                    'metric': 'new_users_today',
                    'condition': 'less_than',
                    'threshold': 1,
                    'enabled': True,
                    'cooldown_minutes': 1440,  # Daily
                    'notify_email': 'admin@facesyma.com',
                },
                {
                    'name': 'Low Analysis Count Today',
                    'description': 'Alert when analyses today are below threshold',
                    'metric': 'analyses_today',
                    'condition': 'less_than',
                    'threshold': 5,
                    'enabled': True,
                    'cooldown_minutes': 720,  # 12 hours
                    'notify_email': 'admin@facesyma.com',
                },
                {
                    'name': 'High Error Rate',
                    'description': 'Alert when error rate (1 hour) exceeds threshold',
                    'metric': 'error_rate_1h',
                    'condition': 'greater_than',
                    'threshold': 10,
                    'enabled': True,
                    'cooldown_minutes': 60,
                    'notify_email': 'admin@facesyma.com',
                },
            ]

            seeded_count = 0
            _success = _style.SUCCESS

            for rule_data in default_rules:
                _rdname = rule_data['name']
                # Check if rule already exists by name
                existing = rules_col.find_one({'name': _rdname})
                if existing:
                    _write(
                        _style.WARNING(f'⊘ Skipped (exists): {_rdname}')
                    )
                    continue

                # Create new rule
                rule = {
                    'id': _next_id(rules_col),
                    'name': _rdname,
                    'description': rule_data['description'],
                    'metric': rule_data['metric'],
                    'condition': rule_data['condition'],
                    'threshold': rule_data['threshold'],
                    'enabled': rule_data['enabled'],
                    'cooldown_minutes': rule_data['cooldown_minutes'],
                    'notify_email': rule_data['notify_email'],
                    'last_triggered_at': None,
                    'created_at': (_ts := datetime.utcnow().isoformat()),
                    'updated_at': _ts,
                }

                rules_col.insert_one(rule)
                seeded_count += 1

                _write(
                    _success(f'✓ Seeded: {_rdname}')
                )

            _write(
                _success(f'\n✓ Total seeded: {seeded_count} alert rules')
            )

        except Exception as e:
            _write(
                _style.ERROR(f'✗ Error seeding alert rules: {e}')
            )
            raise
