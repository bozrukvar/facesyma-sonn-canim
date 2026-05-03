"""
python manage.py seed_archetypes

Translates TR+EN archetype seed data into all 18 languages and upserts
each entry into the MongoDB `archetype_pool` collection.
Idempotent: safe to re-run.
"""
import time
import sys

from django.core.management.base import BaseCommand

LANGS = ['tr', 'en', 'de', 'ru', 'ar', 'es', 'ko', 'ja', 'zh',
         'hi', 'fr', 'pt', 'bn', 'id', 'ur', 'it', 'vi', 'pl']
SOURCE_LANG = 'tr'
TRANSLATE_LANGS = [l for l in LANGS if l not in ('tr', 'en')]


def _translate(text: str, src: str, dest: str) -> str:
    """Translate with googletrans, retrying once on failure."""
    try:
        from googletrans import Translator
        t = Translator()
        result = t.translate(text, src=src, dest=dest)
        return result.text
    except Exception:
        try:
            time.sleep(1)
            from googletrans import Translator
            t = Translator()
            result = t.translate(text, src=src, dest=dest)
            return result.text
        except Exception:
            return text  # fallback: keep original


class Command(BaseCommand):
    help = 'Seed 205 archetypes (18 languages) into MongoDB archetype_pool'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-translate',
            action='store_true',
            default=False,
            help='Skip Google Translate; only store TR+EN and leave other langs empty',
        )

    def handle(self, *args, **options):
        skip_translate = options['skip_translate']

        try:
            from admin_api.utils.mongo import _get_db
            db = _get_db()
        except Exception as e:
            self.stderr.write(f'MongoDB connection error: {e}')
            sys.exit(1)

        try:
            from facesyma_revize.archetype_pool_data import ARCHETYPE_POOL
        except ImportError as e:
            self.stderr.write(f'Cannot import ARCHETYPE_POOL: {e}')
            sys.exit(1)

        collection = db['archetype_pool']
        total = len(ARCHETYPE_POOL)
        done = 0

        for entry in ARCHETYPE_POOL:
            aid        = entry['id']
            name_tr    = entry.get('name_tr', '')
            name_en    = entry.get('name_en', name_tr)
            reason_tr  = entry.get('reason_tr', '')
            reason_en  = entry.get('reason_en', reason_tr)

            name_dict   = {'tr': name_tr,   'en': name_en}
            reason_dict = {'tr': reason_tr, 'en': reason_en}

            if skip_translate:
                for l in TRANSLATE_LANGS:
                    name_dict[l]   = name_en
                    reason_dict[l] = reason_en
            else:
                for l in TRANSLATE_LANGS:
                    name_dict[l]   = _translate(name_tr,   SOURCE_LANG, l)
                    reason_dict[l] = _translate(reason_tr, SOURCE_LANG, l)
                    time.sleep(0.15)  # rate-limit courtesy delay

            doc = {
                'id':       aid,
                'type':     entry['type'],
                'emoji':    entry.get('emoji', ''),
                'clusters': entry.get('clusters', {}),
                'name':     name_dict,
                'reason':   reason_dict,
            }

            collection.update_one({'id': aid}, {'$set': doc}, upsert=True)
            done += 1
            if done % 20 == 0 or done == total:
                self.stdout.write(f'  {done}/{total} seeded...')

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ {done} archetypes seeded into archetype_pool'
        ))

        # ensure indexes
        from pymongo import ASCENDING
        collection.create_index([('type', ASCENDING)], background=True)
        collection.create_index([('id', ASCENDING)], unique=True, background=True)
        db['user_archetype_history'].create_index(
            [('user_id', ASCENDING)], unique=True, background=True
        )
        self.stdout.write('✓ Indexes ensured')
