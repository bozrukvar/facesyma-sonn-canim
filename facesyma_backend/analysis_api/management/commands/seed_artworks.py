"""
python manage.py seed_artworks

Translates TR+EN artwork seed data into all 18 languages and upserts
each entry into the MongoDB `art_pool` collection.
Idempotent: safe to re-run.
"""
import time
import sys

from django.core.management.base import BaseCommand

LANGS = ['tr', 'en', 'de', 'ru', 'ar', 'es', 'ko', 'ja', 'zh',
         'hi', 'fr', 'pt', 'bn', 'id', 'ur', 'it', 'vi', 'pl']
SOURCE_LANG = 'tr'
TRANSLATE_LANGS = [l for l in LANGS if l not in ('tr', 'en')]

# Text fields to translate (field_tr / field_en pairs)
_TEXT_FIELDS = ['title', 'artist', 'museum', 'style', 'reason']


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
    help = 'Seed 52 artworks (18 languages) into MongoDB art_pool'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-translate',
            action='store_true',
            default=False,
            help='Skip Google Translate; only store TR+EN and copy EN to other langs',
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
            from facesyma_revize.art_pool_data import ART_POOL
        except ImportError as e:
            self.stderr.write(f'Cannot import ART_POOL: {e}')
            sys.exit(1)

        collection = db['art_pool']
        total = len(ART_POOL)
        done = 0

        for entry in ART_POOL:
            aid = entry['id']

            # Build per-language dicts for each text field
            field_dicts: dict[str, dict] = {f: {'tr': entry.get(f'{f}_tr', ''),
                                                  'en': entry.get(f'{f}_en', entry.get(f'{f}_tr', ''))}
                                              for f in _TEXT_FIELDS}

            if skip_translate:
                for f in _TEXT_FIELDS:
                    for l in TRANSLATE_LANGS:
                        field_dicts[f][l] = field_dicts[f]['en']
            else:
                for l in TRANSLATE_LANGS:
                    for f in _TEXT_FIELDS:
                        src_text = field_dicts[f]['tr']
                        if src_text:
                            field_dicts[f][l] = _translate(src_text, SOURCE_LANG, l)
                        else:
                            field_dicts[f][l] = field_dicts[f]['en']
                    time.sleep(0.15)  # rate-limit courtesy delay

            doc = {
                'id':          aid,
                'has_portrait': entry.get('has_portrait', False),
                'emoji':       entry.get('emoji', '🖼'),
                'geo':         entry.get('geo', {}),
                'clusters':    entry.get('clusters', {}),
                'image_url':   entry.get('image_url', ''),
                'year':        entry.get('year', ''),
            }
            # flatten language dicts as field_<lang> keys
            for f in _TEXT_FIELDS:
                for l in LANGS:
                    doc[f'{f}_{l}'] = field_dicts[f].get(l, '')

            collection.update_one({'id': aid}, {'$set': doc}, upsert=True)
            done += 1
            if done % 10 == 0 or done == total:
                self.stdout.write(f'  {done}/{total} seeded...')

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ {done} artworks seeded into art_pool'
        ))

        # ensure indexes
        from pymongo import ASCENDING
        collection.create_index([('id', ASCENDING)], unique=True, background=True)
        collection.create_index([('has_portrait', ASCENDING)], background=True)
        db['user_art_history'].create_index(
            [('user_id', ASCENDING)], unique=True, background=True
        )
        self.stdout.write('✓ Indexes ensured')
