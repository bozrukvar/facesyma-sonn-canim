"""
python manage.py translate_questions
python manage.py translate_questions --test personality
python manage.py translate_questions --dry-run

Tüm (ya da belirtilen) soru JSON dosyalarını okur, eksik dil çevirilerini
Google Translate ile doldurur ve dosyaya geri yazar.
İdempotent: zaten dolu çeviriler atlanır.
"""
import json
import time
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

LANGS = ['tr', 'en', 'de', 'ru', 'ar', 'es', 'ko', 'ja', 'zh',
         'hi', 'fr', 'pt', 'bn', 'id', 'ur', 'it', 'vi', 'pl']
SOURCE_LANG = 'en'
TRANSLATE_LANGS = [l for l in LANGS if l not in ('tr', 'en')]

QUESTIONS_DIR = Path(settings.BASE_DIR) / 'questions'

ALL_TESTS = [
    'attachment', 'body_image', 'career', 'grit', 'growth_mindset',
    'hr', 'life_satisfaction', 'personality', 'relationship',
    'self_compassion', 'self_efficacy', 'skills', 'stress', 'vocation',
]


def _translate(text: str, src: str, dest: str) -> str:
    try:
        from googletrans import Translator
        t = Translator()
        result = t.translate(text, src=src, dest=dest)
        return result.text
    except Exception:
        try:
            time.sleep(1.5)
            from googletrans import Translator
            t = Translator()
            result = t.translate(text, src=src, dest=dest)
            return result.text
        except Exception:
            return text


class Command(BaseCommand):
    help = 'Fill missing language translations in question JSON files using Google Translate'

    def add_arguments(self, parser):
        parser.add_argument('--test', type=str, default=None,
                            help='Sadece belirtilen testi çevir (örn: personality)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Çeviriyi göster ama dosyaya yazma')

    def handle(self, *args, **options):
        test_filter = options.get('test')
        dry_run = options.get('dry_run', False)
        tests = [test_filter] if test_filter else ALL_TESTS

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — dosyalar değiştirilmeyecek'))

        for test_type in tests:
            path = QUESTIONS_DIR / f'{test_type}_questions.json'
            if not path.exists():
                self.stdout.write(self.style.ERROR(f'  {test_type}: dosya yok, atlandı'))
                continue

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            questions = data.get('questions', [])
            total = len(questions)
            changed = 0

            for i, q in enumerate(questions):
                translations = q.get('translations', {})
                source_text = translations.get(SOURCE_LANG) or translations.get('tr', '')
                if not source_text:
                    continue

                for lang in TRANSLATE_LANGS:
                    if translations.get(lang):
                        continue  # zaten var, atla

                    translated = _translate(source_text, src=SOURCE_LANG, dest=lang)
                    translations[lang] = translated
                    changed += 1

                    if dry_run:
                        self.stdout.write(f'  [{test_type}] Q{i+1} → {lang}: {translated[:60]}')

                    time.sleep(0.15)  # rate limit

                q['translations'] = translations

            if not dry_run and changed > 0:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            status = self.style.SUCCESS('✓') if changed > 0 else '–'
            self.stdout.write(f'  {status} {test_type}: {total} soru, {changed} yeni çeviri eklendi')

        self.stdout.write(self.style.SUCCESS('\nÇeviri tamamlandı.'))
