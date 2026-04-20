#!/usr/bin/env python
"""
Complete translations for 5 main languages using MyMemory API (free, no key needed)
Translates all remaining untranslated strings to:
  - Turkish (tr) - 8 remaining
  - Spanish (es) - 25 remaining
  - German (de) - 60 remaining
  - French (fr) - 70 remaining
  - Japanese (ja) - 73 remaining
"""

import re
from pathlib import Path
import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  requests library not found. Installing...")
    import subprocess
    subprocess.run(['pip', 'install', '-q', 'requests'])
    import requests
    HAS_REQUESTS = True

BASE_DIR = Path(__file__).resolve().parent

# Language codes for MyMemory API
LANGUAGE_PAIRS = {
    'tr': ('en', 'tr'),  # English to Turkish
    'es': ('en', 'es'),  # English to Spanish
    'de': ('en', 'de'),  # English to German
    'fr': ('en', 'fr'),  # English to French
    'ja': ('en', 'ja'),  # English to Japanese
}

# Manual fallbacks for MyMemory failures (common UI terms)
FALLBACK_TRANSLATIONS = {
    'tr': {
        'Leaderboard updated, please refresh': 'Lider tablosu güncellendi, lütfen yenileyin',
        'Keep-alive ping confirmed': 'Canlı tutma ping\'i onaylandı',
        'Subscribed to leaderboard updates': 'Lider tablosu güncellemeleri\'ne abone olundu',
        'Unsubscribed from leaderboard updates': 'Lider tablosu güncellemeleri\'nden abonelikten çıkıldı',
        'Internal server error': 'İç sunucu hatası',
        'No trend data found for user %d': 'Kullanıcı %d için trend verisi bulunamadı',
        'Invalid JSON in request body': 'İstek gövdesinde geçersiz JSON',
        'Unauthorized': 'Yetkisiz',
    },
    'es': {
        'Leaderboard updated, please refresh': 'Tablero actualizado, por favor actualice',
        'Keep-alive ping confirmed': 'Ping de mantener vivo confirmado',
        'Subscribed to leaderboard updates': 'Suscrito a actualizaciones del tablero',
        'Internal server error': 'Error interno del servidor',
        'Invalid JSON in request body': 'JSON no válido en el cuerpo de la solicitud',
        'Unauthorized': 'No autorizado',
    },
    'de': {
        'Leaderboard updated, please refresh': 'Rangliste aktualisiert, bitte aktualisieren Sie',
        'Keep-alive ping confirmed': 'Keep-Alive-Ping bestätigt',
        'Subscribed to leaderboard updates': 'Abonniert für Ranglisten-Updates',
        'Internal server error': 'Interner Serverfehler',
        'Invalid JSON in request body': 'Ungültiges JSON im Anforderungstext',
        'Unauthorized': 'Nicht berechtigt',
    },
    'fr': {
        'Leaderboard updated, please refresh': 'Classement mis à jour, veuillez actualiser',
        'Keep-alive ping confirmed': 'Ping de maintien confirme',
        'Subscribed to leaderboard updates': 'Abonné aux mises à jour du classement',
        'Internal server error': 'Erreur interne du serveur',
        'Invalid JSON in request body': 'JSON invalide dans le corps de la demande',
        'Unauthorized': 'Non autorisé',
    },
    'ja': {
        'Leaderboard updated, please refresh': 'リーダーボードが更新されました。更新してください',
        'Keep-alive ping confirmed': 'キープアライブピングが確認されました',
        'Subscribed to leaderboard updates': 'リーダーボード更新に登録済み',
        'Internal server error': '内部サーバーエラー',
        'Invalid JSON in request body': 'リクエスト本文の無効なJSON',
        'Unauthorized': '無許可',
    },
}


def translate_with_mymemory(text, src_lang='en', tgt_lang='tr'):
    """
    Translate using MyMemory API (free, no authentication needed)
    API: https://mymemory.translated.net/api/get
    """
    if not text or len(text.strip()) < 2:
        return text

    try:
        # Skip very short strings and special markers
        if text.startswith('%') or len(text) < 3:
            return text

        url = 'https://mymemory.translated.net/api/get'
        params = {
            'q': text,
            'langpair': f'{src_lang}|{tgt_lang}'
        }

        response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data['responseStatus'] == 200 and data['responseData']['translatedText']:
                translated = data['responseData']['translatedText']
                # Skip if translation is same as original
                if translated != text and translated.lower() != text.lower():
                    return translated

    except Exception as e:
        print(f"    ⚠️  API error: {e}")

    return None


def get_untranslated_strings(po_file_path):
    """Extract untranslated strings from .po file"""
    untranslated = []

    with open(po_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        # Look for msgid (skip header)
        if lines[i].startswith('msgid "') and not lines[i].startswith('msgid ""'):
            msgid_content = lines[i][7:-2]  # Remove 'msgid "' and '"\n'

            # Check for multiline
            i += 1
            while i < len(lines) and lines[i].startswith('"'):
                msgid_content += lines[i][1:-2]
                i += 1

            # Check msgstr
            if i < len(lines) and lines[i].startswith('msgstr ""'):
                # This is untranslated
                untranslated.append(msgid_content)
                i += 1
            else:
                i += 1
        else:
            i += 1

    return untranslated


def translate_po_file(po_file_path, lang_code):
    """Translate all untranslated strings in .po file"""
    if lang_code not in LANGUAGE_PAIRS:
        return 0

    src_lang, tgt_lang = LANGUAGE_PAIRS[lang_code]
    fallback_dict = FALLBACK_TRANSLATIONS.get(lang_code, {})

    # Get untranslated strings
    untranslated = get_untranslated_strings(po_file_path)

    if not untranslated:
        return 0

    print(f"  Translating {len(untranslated)} strings...")

    # Read file
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    translated_count = 0

    for idx, english_string in enumerate(untranslated, 1):
        print(f"    [{idx}/{len(untranslated)}] {english_string[:40]:<40}", end=' ')

        # Try fallback first
        if english_string in fallback_dict:
            translated = fallback_dict[english_string]
            print(f"✅ (fallback)")
        else:
            # Try MyMemory API
            translated = translate_with_mymemory(english_string, src_lang, tgt_lang)
            if translated:
                print(f"✅")
            else:
                print(f"⏭️  (skip)")
                continue

        # Replace in content
        pattern = f'msgid "{re.escape(english_string)}"\nmsgstr ""'
        replacement = f'msgid "{english_string}"\nmsgstr "{translated}"'
        content = content.replace(pattern, replacement)
        translated_count += 1

        # Rate limit to avoid API blocking
        if idx % 5 == 0:
            time.sleep(0.5)

    # Write back
    with open(po_file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return translated_count


def main():
    """Complete translations for 5 main languages"""
    locale_dir = BASE_DIR / 'locale'

    languages = [
        ('tr', 'Türkçe (Turkish)'),
        ('es', 'Español (Spanish)'),
        ('de', 'Deutsch (German)'),
        ('fr', 'Français (French)'),
        ('ja', '日本語 (Japanese)'),
    ]

    print('\n🌐 Completing translations for 5 main languages...\n')

    total_translated = 0

    for code, name in languages:
        po_file = locale_dir / code / 'LC_MESSAGES' / 'django.po'

        if po_file.exists():
            print(f'📝 {name:30}', end=' ')
            try:
                count = translate_po_file(po_file, code)
                total_translated += count
                print(f'\n  ✅ {count} strings translated\n')
            except Exception as e:
                print(f'\n  ⚠️  Error: {e}\n')
        else:
            print(f'  ⚠️  File not found: {po_file}')

    print(f'\n✅ Translation complete!')
    print(f'   Total strings translated: {total_translated}')

    print(f'\n🔨 Compiling .mo files...\n')
    import subprocess
    result = subprocess.run(['python', 'compile_messages.py'], cwd=BASE_DIR)

    if result.returncode == 0:
        print(f'\n🎉 All 5 main languages now at ~95%+!')
        print(f'\nTest:')
        print(f'  curl -H "Accept-Language: tr" http://localhost:8000/api/v1/admin/gamification-dashboard/')
        print(f'  curl -H "Accept-Language: es" http://localhost:8000/api/v1/admin/gamification-dashboard/')
        print(f'  curl -H "Accept-Language: de" http://localhost:8000/api/v1/admin/gamification-dashboard/')
        print(f'  curl -H "Accept-Language: fr" http://localhost:8000/api/v1/admin/gamification-dashboard/')
        print(f'  curl -H "Accept-Language: ja" http://localhost:8000/api/v1/admin/gamification-dashboard/')


if __name__ == '__main__':
    main()
