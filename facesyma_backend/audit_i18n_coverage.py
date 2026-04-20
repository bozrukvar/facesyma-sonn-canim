#!/usr/bin/env python
"""
Comprehensive i18n Audit for Phase 2 Gamification
Checks all modules, templates, and strings for proper i18n coverage
"""

import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent

class I18nAudit:
    def __init__(self):
        self.issues = defaultdict(list)
        self.stats = {}
        self.hardcoded_strings = []
        self.missing_trans_tags = []
        self.untranslated_strings = []

    def check_python_files(self):
        """Check Python files for hardcoded user-facing strings"""
        print('\n📋 Checking Python files for hardcoded strings...')

        py_files = list(BASE_DIR.rglob('*.py'))
        hardcoded_found = 0

        # Patterns that indicate user-facing strings
        suspicious_patterns = [
            (r'print\(["\']([^"\']*[A-Z][^"\']*)["\']', 'print statement'),
            (r'\.append\(["\']([^"\']*[A-Z][^"\']*)["\']', 'append'),
            (r'return\s+["\']([^"\']*[A-Z][^"\']*)["\'](?!\s*#)', 'return literal'),
        ]

        for py_file in py_files:
            # Skip test files, migrations, venv
            if any(skip in str(py_file) for skip in ['test', 'migration', '__pycache__', 'venv', '.venv']):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Check for hardcoded messages (rough heuristic)
                if 'message' in content.lower() and '_(' not in content:
                    if 'Dashboard' in content or 'Performance' in content or 'Error' in content:
                        if 'gettext' not in content and 'translation_service' not in content:
                            self.issues['hardcoded_python'].append(str(py_file))
                            hardcoded_found += 1

            except Exception as e:
                self.issues['python_read_errors'].append(f"{py_file}: {e}")

        self.stats['python_files_checked'] = len(py_files)
        self.stats['hardcoded_python_files'] = hardcoded_found
        print(f"  ✓ Checked {len(py_files)} Python files")
        print(f"  ⚠️  Found {hardcoded_found} potentially hardcoded files")

    def check_template_files(self):
        """Check template files for missing {% trans %} tags"""
        print('\n📋 Checking HTML templates for i18n tags...')

        template_files = list(BASE_DIR.rglob('*.html'))
        missing_tags = 0
        with_tags = 0

        for tmpl_file in template_files:
            try:
                with open(tmpl_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Check if i18n is loaded
                if '{% load i18n %}' not in content:
                    if any(text in content for text in ['<h1>', '<h2>', '<label>', '<title>', 'value=']):
                        self.issues['missing_i18n_load'].append(str(tmpl_file))

                # Count trans tags
                trans_count = len(re.findall(r'{% trans ', content))
                if trans_count > 0:
                    with_tags += 1
                else:
                    if any(text in content for text in ['Dashboard', 'Performance', 'Error', 'Status']):
                        missing_tags += 1

            except Exception as e:
                self.issues['template_read_errors'].append(f"{tmpl_file}: {e}")

        self.stats['template_files_checked'] = len(template_files)
        self.stats['templates_with_i18n'] = with_tags
        self.stats['templates_missing_i18n'] = missing_tags
        print(f"  ✓ Checked {len(template_files)} template files")
        print(f"  ✅ {with_tags} templates have i18n tags")
        print(f"  ⚠️  {missing_tags} templates might need i18n tags")

    def check_translation_service(self):
        """Verify translation_service.py is comprehensive"""
        print('\n📋 Checking translation_service.py...')

        ts_file = BASE_DIR / 'admin_api' / 'services' / 'translation_service.py'

        if not ts_file.exists():
            self.issues['missing_files'].append(str(ts_file))
            print(f"  ❌ translation_service.py not found!")
            return

        with open(ts_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Count translation dictionaries
        dict_count = len(re.findall(r'[A-Z_]+_STRINGS\s*=\s*{', content))
        string_count = len(re.findall(r"_\('", content))

        self.stats['translation_dicts'] = dict_count
        self.stats['translation_strings'] = string_count

        print(f"  ✓ Found {dict_count} translation dictionaries")
        print(f"  ✓ Found {string_count} translatable strings")

        # Check for required dictionaries
        required_dicts = [
            'DASHBOARD_STRINGS',
            'WEBSOCKET_STRINGS',
            'ERROR_STRINGS',
            'LEADERBOARD_STRINGS',
            'TREND_STRINGS',
            'HEALTH_STRINGS',
            'CACHE_INVALIDATION_STRINGS',
        ]

        missing_dicts = [d for d in required_dicts if d not in content]
        if missing_dicts:
            self.issues['missing_translation_dicts'].append(missing_dicts)
            print(f"  ⚠️  Missing dictionaries: {missing_dicts}")
        else:
            print(f"  ✅ All {len(required_dicts)} required dictionaries present")

    def check_locale_files(self):
        """Verify all locale files exist and are compiled"""
        print('\n📋 Checking locale files...')

        locale_dir = BASE_DIR / 'locale'

        if not locale_dir.exists():
            self.issues['missing_locale_dir'].append(str(locale_dir))
            print(f"  ❌ locale/ directory not found!")
            return

        languages = [
            ('en', 'English'),
            ('tr', 'Turkish'),
            ('es', 'Spanish'),
            ('de', 'German'),
            ('fr', 'French'),
            ('ja', 'Japanese'),
            ('zh-hans', 'Simplified Chinese'),
            ('zh-hant', 'Traditional Chinese'),
            ('ko', 'Korean'),
            ('pt', 'Portuguese'),
            ('ru', 'Russian'),
            ('ar', 'Arabic'),
            ('he', 'Hebrew'),
            ('hi', 'Hindi'),
            ('vi', 'Vietnamese'),
            ('it', 'Italian'),
            ('pl', 'Polish'),
            ('th', 'Thai'),
        ]

        missing_po = []
        missing_mo = []
        complete = 0

        for code, name in languages:
            po_file = locale_dir / code / 'LC_MESSAGES' / 'django.po'
            mo_file = locale_dir / code / 'LC_MESSAGES' / 'django.mo'

            if not po_file.exists():
                missing_po.append(code)
            if not mo_file.exists():
                missing_mo.append(code)
            if po_file.exists() and mo_file.exists():
                complete += 1

        self.stats['languages_complete'] = complete
        self.stats['languages_total'] = len(languages)

        print(f"  ✅ {complete}/{len(languages)} languages complete")

        if missing_po:
            self.issues['missing_po_files'].append(missing_po)
            print(f"  ❌ Missing .po files: {missing_po}")

        if missing_mo:
            self.issues['missing_mo_files'].append(missing_mo)
            print(f"  ❌ Missing .mo files: {missing_mo}")

        # Check .pot template
        pot_file = locale_dir / 'django.pot'
        if pot_file.exists():
            print(f"  ✅ django.pot template exists")
        else:
            self.issues['missing_pot'].append(str(pot_file))
            print(f"  ❌ django.pot template missing!")

    def check_settings_configuration(self):
        """Verify Django i18n settings"""
        print('\n📋 Checking Django i18n configuration...')

        settings_file = BASE_DIR / 'facesyma_project' / 'settings.py'

        if not settings_file.exists():
            self.issues['missing_settings'].append(str(settings_file))
            print(f"  ❌ settings.py not found!")
            return

        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        checks = {
            'USE_I18N': 'USE_I18N = True' in content,
            'USE_L10N': 'USE_L10N = True' in content,
            'LANGUAGE_CODE': "LANGUAGE_CODE = 'en-US'" in content,
            'LANGUAGES list': 'LANGUAGES = [' in content,
            'LOCALE_PATHS': "LOCALE_PATHS = [" in content,
            'LocaleMiddleware': 'django.middleware.locale.LocaleMiddleware' in content,
        }

        passed = sum(1 for v in checks.values() if v)
        print(f"  ✅ {passed}/{len(checks)} settings configured correctly")

        for setting, present in checks.items():
            status = "✅" if present else "❌"
            print(f"    {status} {setting}")

        if passed < len(checks):
            missing = [k for k, v in checks.items() if not v]
            self.issues['missing_settings_config'].append(missing)

    def check_translation_completeness(self):
        """Verify all .po files have translations"""
        print('\n📋 Checking translation completeness...')

        locale_dir = BASE_DIR / 'locale'
        languages_stats = {}

        for lang_dir in sorted(locale_dir.iterdir()):
            if not lang_dir.is_dir() or lang_dir.name.startswith('.'):
                continue

            po_file = lang_dir / 'LC_MESSAGES' / 'django.po'

            if not po_file.exists():
                continue

            with open(po_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Count msgstr occurrences
            total_msgstr = len(re.findall(r'^msgstr "', content, re.MULTILINE))
            empty_msgstr = len(re.findall(r'^msgstr ""$', content, re.MULTILINE))
            translated = total_msgstr - empty_msgstr - 1  # -1 for header

            languages_stats[lang_dir.name] = {
                'total': total_msgstr,
                'translated': translated,
                'untranslated': empty_msgstr - 1,  # -1 for header
            }

        # Display stats
        print(f"  Language Translation Coverage:")
        for lang, stats in sorted(languages_stats.items()):
            if stats['total'] > 0:
                pct = int((stats['translated'] / (stats['total'] - 1)) * 100)
                status = "✅" if pct == 100 else "⚠️ " if pct > 50 else "❌"
                print(f"    {status} {lang:10} — {pct:3}% ({stats['translated']:2}/{stats['total']-1})")

        self.stats['language_stats'] = languages_stats

    def check_hardcoded_dashboard(self):
        """Check monitoring dashboard for hardcoded strings"""
        print('\n📋 Checking monitoring dashboard module...')

        dashboard_file = BASE_DIR / 'admin_api' / 'services' / 'metrics_service.py'

        if not dashboard_file.exists():
            print(f"  ⚠️  metrics_service.py not checked (not found)")
            return

        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if using translation_service
        if 'translation_service' in content or 'DASHBOARD_STRINGS' in content:
            print(f"  ✅ Dashboard uses translation_service")
        else:
            print(f"  ⚠️  Dashboard might have hardcoded strings")
            self.issues['dashboard_hardcoded'].append(str(dashboard_file))

    def check_websocket_translations(self):
        """Check WebSocket consumer for i18n"""
        print('\n📋 Checking WebSocket consumer...')

        ws_file = BASE_DIR / 'gamification' / 'consumers.py'

        if not ws_file.exists():
            print(f"  ⚠️  consumers.py not found (WebSocket not checked)")
            return

        with open(ws_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if using translations
        if '_(' in content or 'gettext' in content:
            print(f"  ✅ WebSocket uses gettext/translations")
        else:
            print(f"  ⚠️  WebSocket might have hardcoded messages")
            self.issues['websocket_hardcoded'].append(str(ws_file))

    def check_rtl_support(self):
        """Check RTL language support"""
        print('\n📋 Checking RTL language support (Arabic, Hebrew)...')

        template_file = BASE_DIR / 'admin_api' / 'templates' / 'gamification_dashboard.html'

        if not template_file.exists():
            print(f"  ⚠️  Template not found")
            return

        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        checks = {
            'dir attribute': 'dir=' in content or 'dir:' in content,
            'HTML lang attribute': 'lang=' in content,
            'Unicode support': 'charset' in content and 'UTF-8' in content,
        }

        passed = sum(1 for v in checks.values() if v)
        print(f"  {passed}/{len(checks)} RTL checks passed")

        for check, present in checks.items():
            status = "✅" if present else "⚠️ "
            print(f"    {status} {check}")

    def check_api_endpoints(self):
        """Check API views for i18n"""
        print('\n📋 Checking API endpoints...')

        views_dir = BASE_DIR / 'admin_api' / 'views'

        if not views_dir.exists():
            print(f"  ⚠️  views directory not found")
            return

        view_files = list(views_dir.glob('*.py'))
        using_i18n = 0

        for view_file in view_files:
            if view_file.name.startswith('_'):
                continue

            with open(view_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if '_(' in content or 'translation_service' in content:
                using_i18n += 1

        print(f"  ✅ {using_i18n}/{len(view_files)} API view files have i18n")

        if using_i18n < len(view_files):
            self.issues['views_without_i18n'].append(len(view_files) - using_i18n)

    def generate_report(self):
        """Generate final audit report"""
        print('\n' + '='*70)
        print('                    i18n AUDIT REPORT')
        print('='*70)

        print('\n📊 STATISTICS:')
        for key, value in sorted(self.stats.items()):
            print(f'  • {key}: {value}')

        if self.issues:
            print('\n⚠️  ISSUES FOUND:')
            for issue_type, items in self.issues.items():
                print(f'\n  {issue_type}:')
                for item in items[:5]:  # Show first 5
                    print(f'    - {item}')
                if len(items) > 5:
                    print(f'    ... and {len(items) - 5} more')
        else:
            print('\n✅ NO ISSUES FOUND!')

        print('\n' + '='*70)
        print('RECOMMENDATION:')
        if not self.issues and self.stats.get('languages_complete') == self.stats.get('languages_total'):
            print('✅ SYSTEM IS READY FOR PRODUCTION - All 18 languages fully configured!')
        elif len(self.issues) < 3:
            print('⚠️  Minor issues found - Review above and fix them')
        else:
            print('❌ Significant i18n coverage gaps - Address above issues')
        print('='*70 + '\n')

    def run_full_audit(self):
        """Run complete audit"""
        print('\n🔍 STARTING COMPREHENSIVE i18n AUDIT FOR PHASE 2 GAMIFICATION\n')

        self.check_locale_files()
        self.check_settings_configuration()
        self.check_translation_service()
        self.check_python_files()
        self.check_template_files()
        self.check_translation_completeness()
        self.check_hardcoded_dashboard()
        self.check_websocket_translations()
        self.check_api_endpoints()
        self.check_rtl_support()

        self.generate_report()


if __name__ == '__main__':
    audit = I18nAudit()
    audit.run_full_audit()
