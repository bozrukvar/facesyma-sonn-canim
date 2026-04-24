#!/usr/bin/env python
"""
Auto-translate all .po files using Google Translate
Populates msgstr fields for all 17 languages
"""

import re
from pathlib import Path
from urllib.parse import quote
import json

try:
    from google.cloud import translate_v2
    HAS_GOOGLE_SDK = True
except ImportError:
    HAS_GOOGLE_SDK = False

# Fallback to free online translation if no Google SDK
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# Dictionary-based fallback translations (minimal but better than nothing)
FALLBACK_TRANSLATIONS = {
    'tr': {  # Turkish
        'Cache Performance': 'Hiş Performansı',
        'Hit Rate': 'Hit Oranı',
        'Total Queries': 'Toplam Sorgular',
        'Memory Used': 'Kullanılan Bellek',
        'Leaderboard Performance': 'Lider Tablosu Performansı',
        'Average Query Time': 'Ortalama Sorgu Süresi',
        'P95 Latency': 'P95 Gecikmesi',
        'WebSocket Connections': 'WebSocket Bağlantıları',
        'Current Connections': 'Mevcut Bağlantılar',
        'Peak Today': 'Bugünün Zirvesi',
        'Trend Analysis': 'Trend Analizi',
        'Total Snapshots': 'Toplam Anlık Görüntüler',
        'Latest Snapshot Age': 'En Son Anlık Görüntü Yaşı',
        'System Health': 'Sistem Sağlığı',
        'Status': 'Durum',
        'Components': 'Bileşenler',
        'Healthy': 'Sağlıklı',
        'Degraded': 'Bozulmuş',
        'Error': 'Hata',
        'Unavailable': 'Kullanılamaz',
        'Coins': 'Madeni Paralar',
        'Badges': 'Rozetler',
        'Rank': 'Sıra',
        'Username': 'Kullanıcı Adı',
        'Most Improved': 'En İyileşen',
        'Most Active': 'En Aktif',
    },
    'es': {  # Spanish
        'Cache Performance': 'Rendimiento de Caché',
        'Hit Rate': 'Tasa de Acierto',
        'Total Queries': 'Consultas Totales',
        'Memory Used': 'Memoria Utilizada',
        'Leaderboard Performance': 'Rendimiento del Tablero de Clasificación',
        'Average Query Time': 'Tiempo Medio de Consulta',
        'Current Connections': 'Conexiones Actuales',
        'System Health': 'Salud del Sistema',
        'Status': 'Estado',
        'Healthy': 'Saludable',
        'Error': 'Error',
        'Coins': 'Monedas',
        'Rank': 'Rango',
        'Username': 'Nombre de Usuario',
    },
    'de': {  # German
        'Cache Performance': 'Cache-Leistung',
        'Hit Rate': 'Treffer Quote',
        'Total Queries': 'Gesamtabfragen',
        'Memory Used': 'Verwendeter Speicher',
        'Leaderboard Performance': 'Ranglisten-Leistung',
        'Average Query Time': 'Durchschnittliche Abfragezeit',
        'Current Connections': 'Aktuelle Verbindungen',
        'System Health': 'Systemgesundheit',
        'Status': 'Status',
        'Healthy': 'Gesund',
        'Error': 'Fehler',
        'Coins': 'Münzen',
        'Rank': 'Rang',
    },
    'fr': {  # French
        'Cache Performance': 'Performance du Cache',
        'Hit Rate': 'Taux de Réussite',
        'Total Queries': 'Requêtes Totales',
        'Memory Used': 'Mémoire Utilisée',
        'Leaderboard Performance': 'Performance du Classement',
        'Average Query Time': 'Temps Moyen de Requête',
        'Current Connections': 'Connexions Actuelles',
        'System Health': 'Santé du Système',
        'Status': 'Statut',
        'Healthy': 'Sain',
        'Error': 'Erreur',
        'Coins': 'Pièces',
        'Rank': 'Rang',
    },
}


def translate_with_google_api(text, target_lang):
    """Translate using Google Translate API (requires setup)"""
    if not HAS_GOOGLE_SDK:
        return None

    try:
        client = translate_v2.Client()
        result = client.translate_text(text, target_language=target_lang)
        return result['translatedText']
    except Exception as e:
        print(f"  ⚠️  Google API error: {e}")
        return None


def translate_with_google_free(text, target_lang):
    """Translate using free Google Translate (via requests)"""
    if not HAS_REQUESTS:
        return None

    try:
        url = "https://translate.googleapis.com/translate_a/element.js?cb=googleTranslateElementInit"
        # Use a simpler approach - direct translation URL
        from urllib.parse import urlencode

        # Using Google's free translate endpoint
        params = {
            'client': 'gtx',
            'sl': 'en',
            'tl': target_lang,
            'dt': 't',
            'q': text
        }

        response = requests.get('https://translate.google.com/translate_a/single',
                               params=params,
                               headers={'User-Agent': 'Mozilla/5.0'})

        if response.status_code == 200:
            result = response.json()
            if result and result[0]:
                return result[0][0][0]
    except Exception as e:
        pass

    return None


def translate_text(text, target_lang):
    """Translate text with fallback strategy"""
    # Skip untranslatable content
    if not text or text.startswith('%'):
        return text

    # Try fallback dictionary first (reliable)
    if target_lang in FALLBACK_TRANSLATIONS:
        if text in FALLBACK_TRANSLATIONS[target_lang]:
            return FALLBACK_TRANSLATIONS[target_lang][text]

    # Try Google Translate API
    translated = translate_with_google_api(text, target_lang)
    if translated and translated != text:
        return translated

    # Try free Google Translate
    translated = translate_with_google_free(text, target_lang)
    if translated and translated != text:
        return translated

    # Return original if no translation available
    return text


def populate_po_file(po_file_path, target_lang):
    """Fill .po file with translations"""
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all msgid/msgstr pairs
    lines = content.split('\n')
    _n_lines = len(lines)
    result_lines = []
    _rla = result_lines.append
    i = 0
    translation_count = 0

    while i < _n_lines:
        line = lines[i]
        _lsw = line.startswith
        _rla(line)

        # Look for msgid lines (not header)
        if _lsw('msgid "') and not _lsw('msgid ""'):
            # Extract the English string
            msgid_match = line[7:-1]  # Remove 'msgid "' and closing '"'

            # Handle multiline msgid
            msgid_content = msgid_match
            i += 1
            while i < _n_lines:
                _li = lines[i]
                if not _li.startswith('"'):
                    break
                msgid_content += _li[1:-1]  # Remove quotes
                _rla(_li)
                i += 1

            # Now handle msgstr
            if i < _n_lines:
                _li = lines[i]
                if _li.startswith('msgstr'):
                    translated = translate_text(msgid_content, target_lang)

                    # Build translated msgstr line
                    if translated and translated != msgid_content:
                        translated_line = f'msgstr "{translated}"'
                        _rla(translated_line)
                        translation_count += 1
                    else:
                        # Keep empty or original
                        _rla(_li)

                    i += 1

            continue

        i += 1

    # Write updated content
    new_content = '\n'.join(result_lines)
    with open(po_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return translation_count


def main():
    """Translate all .po files"""
    BASE_DIR = Path(__file__).resolve().parent
    locale_dir = BASE_DIR / 'locale'

    languages = [
        ('tr', 'Türkçe'),
        ('de', 'Deutsch'),
        ('fr', 'Français'),
        ('es', 'Español'),
        ('it', 'Italiano'),
        ('pt', 'Português'),
        ('pl', 'Polski'),
        ('ru', 'Русский'),
        ('ja', '日本語'),
        ('zh-hans', '简体中文'),
        ('zh-hant', '繁體中文'),
        ('ko', '한국어'),
        ('ar', 'العربية'),
        ('he', 'עברית'),
        ('hi', 'हिन्दी'),
        ('vi', 'Tiếng Việt'),
        ('th', 'ไทย'),
    ]

    print('\n🌍 Translating to 17 languages...\n')

    translated_langs = 0
    total_strings = 0

    for code, name in languages:
        po_file = locale_dir / code / 'LC_MESSAGES' / 'django.po'

        if po_file.exists():
            print(f'📝 {name:15} ({code:8})', end=' ... ')
            try:
                count = populate_po_file(po_file, code)
                translated_langs += 1
                total_strings += count
                print(f'✅ {count} translations')
            except Exception as e:
                print(f'⚠️  Error: {e}')
        else:
            print(f'⚠️  {name:15} — .po file not found')

    print(f'\n✅ Translation complete!')
    print(f'   {translated_langs} languages translated')
    print(f'   {total_strings} total translations added')

    print(f'\n🔨 Now compiling .mo files...')
    import subprocess
    result = subprocess.run([
        'python',
        BASE_DIR / 'compile_messages.py'
    ], cwd=BASE_DIR)

    if result.returncode == 0:
        print(f'\n🎉 All languages ready for testing!')
        print(f'\nTest examples:')
        print(f'  curl -H "Accept-Language: tr" http://localhost:8000/api/v1/admin/gamification-dashboard/')
        print(f'  curl -H "Accept-Language: es" http://localhost:8000/api/v1/admin/gamification-dashboard/')
        print(f'  curl -H "Accept-Language: ja" http://localhost:8000/api/v1/admin/gamification-dashboard/')


if __name__ == '__main__':
    main()
