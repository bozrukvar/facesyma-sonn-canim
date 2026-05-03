"""
analysis_api/management/commands/seed_communities.py
------------------------------------------------------
47 seed topluluğunu idempotent olarak oluşturur.

Kullanım:
    python manage.py seed_communities
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Seed 47 predefined communities (idempotent)'

    def handle(self, *args, **options):
        from analysis_api.community_seed import run
        run()
        self.stdout.write(self.style.SUCCESS('Community seed complete.'))
