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

            for rule_data in default_rules:
                # Check if rule already exists by name
                existing = rules_col.find_one({'name': rule_data['name']})
                if existing:
                    self.stdout.write(
                        self.style.WARNING(f'⊘ Skipped (exists): {rule_data["name"]}')
                    )
                    continue

                # Create new rule
                rule = {
                    'id': _next_id(rules_col),
                    'name': rule_data['name'],
                    'description': rule_data['description'],
                    'metric': rule_data['metric'],
                    'condition': rule_data['condition'],
                    'threshold': rule_data['threshold'],
                    'enabled': rule_data['enabled'],
                    'cooldown_minutes': rule_data['cooldown_minutes'],
                    'notify_email': rule_data['notify_email'],
                    'last_triggered_at': None,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat(),
                }

                rules_col.insert_one(rule)
                seeded_count += 1

                self.stdout.write(
                    self.style.SUCCESS(f'✓ Seeded: {rule_data["name"]}')
                )

            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Total seeded: {seeded_count} alert rules')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error seeding alert rules: {e}')
            )
            raise
