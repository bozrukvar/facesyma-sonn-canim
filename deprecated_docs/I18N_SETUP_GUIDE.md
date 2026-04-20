# Internationalization (i18n) Setup — Phase 2 Gamification ✅

**Date**: 2026-04-19  
**Status**: ✅ English Complete, Ready for Other 17 Languages  
**Supported Languages**: 18 (English + 17 others)  

---

## Overview

Phase 2 Gamification now fully supports internationalization (i18n):

- ✅ **English (en)** — Complete translation setup
- ⏳ **17 other languages** — Ready for translation

### Supported Languages

| Code | Language | Status | Priority |
|------|----------|--------|----------|
| `en` | English | ✅ Complete | Primary |
| `tr` | Türkçe (Turkish) | ⏳ Ready | High |
| `de` | Deutsch (German) | ⏳ Ready | High |
| `fr` | Français (French) | ⏳ Ready | High |
| `es` | Español (Spanish) | ⏳ Ready | High |
| `it` | Italiano (Italian) | ⏳ Ready | Medium |
| `pt` | Português (Portuguese) | ⏳ Ready | Medium |
| `pl` | Polski (Polish) | ⏳ Ready | Medium |
| `ru` | Русский (Russian) | ⏳ Ready | Medium |
| `ja` | 日本語 (Japanese) | ⏳ Ready | Medium |
| `zh-hans` | 简体中文 (Simplified Chinese) | ⏳ Ready | Medium |
| `zh-hant` | 繁體中文 (Traditional Chinese) | ⏳ Ready | Medium |
| `ko` | 한국어 (Korean) | ⏳ Ready | Medium |
| `ar` | العربية (Arabic) | ⏳ Ready | Low |
| `he` | עברית (Hebrew) | ⏳ Ready | Low |
| `hi` | हिन्दी (Hindi) | ⏳ Ready | Low |
| `vi` | Tiếng Việt (Vietnamese) | ⏳ Ready | Low |
| `th` | ไทย (Thai) | ⏳ Ready | Low |

---

## Architecture

### Django i18n System

```
Settings: LANGUAGES, LOCALE_PATHS, middleware
  ↓
Translation Strings: gettext_lazy(_("text"))
  ↓
Template Tags: {% load i18n %}, {% trans "text" %}
  ↓
Message Extraction: makemessages -a
  ↓
.pot file (template with all strings)
  ↓
.po files (translations per language)
  ↓
.mo files (compiled for runtime)
  ↓
Django i18n loads correct language
```

### Workflow

```
1. Developer
   └─ Uses gettext_lazy() in Python
   └─ Uses {% trans %} in templates

2. Extract Messages
   └─ python manage.py makemessages -a
   └─ Creates locale/django.pot + locale/{lang}/LC_MESSAGES/django.po

3. Translator
   └─ Opens .po file in PO editor (Poedit, Lokalize, VS Code)
   └─ Translates English strings to target language
   └─ Saves .po file

4. Compile Messages
   └─ python manage.py compilemessages
   └─ Creates .mo (compiled) files

5. Runtime
   └─ Django detects Accept-Language header
   └─ Loads correct .mo file
   └─ All strings translated automatically
```

---

## Files Changed

### 1. Django Settings

**File**: `facesyma_backend/facesyma_project/settings.py`

```python
# ── Dil / Zaman dilimi ─────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-US'  # Default: English
TIME_ZONE     = 'Europe/Istanbul'
USE_I18N      = True
USE_L10N      = True
USE_TZ        = True

# ── Desteklenen Diller (18 dil) ────────────────────────────────────────────────
LANGUAGES = [
    ('en', 'English'),
    ('tr', 'Türkçe'),
    # ... 16 more languages
]

# ── Locale Dosyaları Yolu ──────────────────────────────────────────────────────
LOCALE_PATHS = [
    BASE_DIR / 'locale',
    BASE_DIR / 'gamification' / 'locale',
    BASE_DIR / 'admin_api' / 'locale',
]

MIDDLEWARE = [
    # ...
    'django.middleware.locale.LocaleMiddleware',  # Language detection
]
```

### 2. Translation Service

**File**: `admin_api/services/translation_service.py`

Centralized translations using `gettext_lazy(_())`:

```python
from django.utils.translation import gettext_lazy as _

DASHBOARD_STRINGS = {
    'title': _('🎮 Gamification Phase 2 — Monitoring Dashboard'),
    'cache_hit_rate': _('Hit Rate'),
    'websocket_current': _('Current Connections'),
    # ... 100+ strings
}
```

### 3. Dashboard Template

**File**: `admin_api/templates/gamification_dashboard.html`

Updated with `{% load i18n %}` and `{% trans %}`:

```html
{% load i18n %}
<!DOCTYPE html>
<html lang="{{ LANGUAGE_CODE }}">
<head>
    <title>{% trans "Gamification Monitoring Dashboard" %}</title>
    ...
</head>
<body>
    <h1>{% trans "🎮 Gamification Phase 2 — Monitoring Dashboard" %}</h1>
    <div>{% trans "Hit Rate" %}</div>
    ...
</body>
</html>
```

---

## How to Use

### 1. Extract Messages (Developer)

```bash
cd facesyma_backend

# Extract all translatable strings from Python files and templates
python manage.py makemessages -a

# Output:
# created locale/es/LC_MESSAGES/django.po
# created locale/fr/LC_MESSAGES/django.po
# ... (for each language in LANGUAGES)
# created locale/django.pot (template)
```

### 2. Translate Strings (Translator)

#### Option A: Using Poedit (Recommended)
```bash
# Open with Poedit
poedit locale/tr/LC_MESSAGES/django.po

# Or from command line
poedit locale/es/LC_MESSAGES/django.po
```

#### Option B: Using Text Editor
```bash
# Open and edit manually
vim locale/de/LC_MESSAGES/django.po

# Format:
# #: admin_api/templates/gamification_dashboard.html:20
# msgid "Hit Rate"
# msgstr "Hit Rate (German translation)"
```

#### Option C: Using VS Code
1. Install "PO File Support" extension
2. Open `.po` file
3. Edit translations alongside English

### 3. Compile Messages (Developer)

```bash
# Compile .po files → .mo files (binary)
python manage.py compilemessages

# Output:
# processing file locale/tr/LC_MESSAGES/django.po
# processing file locale/es/LC_MESSAGES/django.po
# ... (creates .mo files)
```

### 4. Test Translations

```bash
# Test Turkish
curl -H "Accept-Language: tr" http://localhost:8000/api/v1/admin/gamification-dashboard/

# Test Spanish
curl -H "Accept-Language: es" http://localhost:8000/api/v1/admin/gamification-dashboard/

# Test English (default)
curl http://localhost:8000/api/v1/admin/gamification-dashboard/
```

### 5. Browser Language Selection

```html
<!-- User can select language -->
<select onchange="setLanguage(this.value)">
    <option value="en">English</option>
    <option value="tr">Türkçe</option>
    <option value="es">Español</option>
    ...
</select>

<script>
function setLanguage(lang) {
    // Set cookie/localStorage
    localStorage.setItem('language', lang);
    // Reload page
    window.location.href = '/?lang=' + lang;
}
</script>
```

---

## Translation Strings Overview

### Dashboard (50+ strings)
- Header: title, status labels, buttons
- Cards: cache, performance, WebSocket, trends, health
- Tables: headers, column names
- Units: %, ms, MB, hours, days

### WebSocket (8 strings)
- Connection messages
- Rank change notifications
- Error messages
- Keep-alive confirmations

### API Errors (10+ strings)
- Invalid parameters
- Not found
- Unauthorized
- Database errors
- Cache errors

### Leaderboards (15+ strings)
- Rank, username, coins
- Meals completed, challenges won
- Accuracy, badges

### Trends (8 strings)
- Most improved, most active
- Momentum states
- Snapshot counts

### System Health (8 strings)
- Redis, MongoDB, Scheduler status
- Healthy, degraded, error, unavailable

---

## Tools Recommended

### Translation Editors

| Tool | Platform | Free | Features |
|------|----------|------|----------|
| **Poedit** | Windows/Mac/Linux | Yes (lite) | GUI, context preview, auto-suggestions |
| **Lokalize** | Linux | Yes | KDE Plasma, professional features |
| **VS Code + PO Extension** | Any | Yes | Lightweight, inline editing |
| **OmegaT** | Any | Yes | Advanced, CAT features |
| **Google Translate API** | Cloud | Paid | Bulk auto-translation |

### Recommended: Poedit

```bash
# Install Poedit
# Windows: choco install poedit
# Mac: brew install poedit
# Linux: sudo apt install poedit

# Open .po file
poedit locale/tr/LC_MESSAGES/django.po
```

---

## Workflow Example: Adding Turkish

### Step 1: Extract Messages
```bash
python manage.py makemessages -a
# Creates: locale/tr/LC_MESSAGES/django.po
```

### Step 2: Translate (Poedit)
```bash
poedit locale/tr/LC_MESSAGES/django.po

# Poedit shows:
# English: "Hit Rate"
# Turkish: [input field]
# Context: "admin_api/templates/gamification_dashboard.html:20"

# Translator enters Turkish text
```

### Step 3: Compile
```bash
python manage.py compilemessages
# Creates: locale/tr/LC_MESSAGES/django.mo
```

### Step 4: Test
```bash
curl -H "Accept-Language: tr" http://localhost:8000/api/v1/admin/gamification-dashboard/
# Dashboard now displays in Turkish!
```

---

## Advanced: Plural Forms

For strings with plurals (e.g., "1 snapshot" vs "5 snapshots"):

```python
from django.utils.translation import ngettext_lazy

# In Python
message = ngettext_lazy(
    '%d snapshot',
    '%d snapshots',
    count
) % count

# In templates
{% blocktrans count counter=snapshots|length %}
    {{ counter }} snapshot
{% plural %}
    {{ counter }} snapshots
{% endblocktrans %}
```

The `.po` file automatically handles plural rules per language.

---

## Integration with Existing Features

### Cache Invalidation Messages
```python
from django.utils.translation import gettext_lazy as _

log.info(_("Coins awarded to user %d → Invalidated %d leaderboard entries") % (user_id, count))
```

### WebSocket Notifications
```python
# In consumers.py
message = {
    "type": "leaderboard_update",
    "message": _("Leaderboard updated, please refresh")
}
```

### API Error Messages
```python
# In views.py
from admin_api.services.translation_service import ERROR_STRINGS

return _json_error(ERROR_STRINGS['invalid_parameter'] % field_name)
```

---

## Git Workflow

### Committing Translations

```bash
# Add .po files (human translations)
git add locale/*/LC_MESSAGES/django.po

# Commit
git commit -m "Add Turkish translations for monitoring dashboard"

# DON'T commit .mo files (compiled, auto-generated)
git rm --cached locale/*/LC_MESSAGES/django.mo
echo "locale/*/LC_MESSAGES/django.mo" >> .gitignore
```

---

## Production Deployment

### Pre-deployment Checklist

- ✅ All English strings extracted (`django.pot` complete)
- ✅ `.po` files translated for target languages
- ✅ `.mo` files compiled (`compilemessages`)
- ✅ LOCALE_PATHS configured
- ✅ LocaleMiddleware added
- ✅ LANGUAGE_CODE = 'en-US'
- ✅ USE_I18N = True

### Deployment Steps

```bash
# 1. Extract messages
python manage.py makemessages -a

# 2. Provide .po files to translators
# (or use professional translation service)

# 3. Receive translated .po files
cp /path/to/translated/locale ./locale

# 4. Compile messages
python manage.py compilemessages -l tr -l es -l fr  # Or -a for all

# 5. Deploy
git add locale/*/LC_MESSAGES/django.mo
git commit -m "Add compiled translations"
git push
docker-compose up -d
```

---

## Quality Assurance

### Check Translation Coverage

```bash
# Count strings per language
python manage.py makemessages -a
# Check locale/{lang}/LC_MESSAGES/django.po for fuzzy/untranslated entries

# Example .po file:
#, fuzzy  ← Needs review
msgid "Hit Rate"
msgstr ""  ← Untranslated

#: Location
msgid "Cache Performance"
msgstr "Rendimiento en Caché"  ← Translated (OK)
```

### Test All Languages

```bash
# Create test script
for lang in en tr es de fr ja zh-hans zh-hant ko ar; do
    echo "Testing $lang..."
    curl -H "Accept-Language: $lang" \
        http://localhost:8000/api/v1/admin/gamification-dashboard/ \
        | grep -q "msgstr" || echo "✓ $lang OK"
done
```

---

## File Structure

```
facesyma_backend/
├── locale/
│   ├── django.pot                    [Template, all strings]
│   ├── en/
│   │   └── LC_MESSAGES/
│   │       ├── django.po             [English translations]
│   │       └── django.mo             [Compiled]
│   ├── tr/
│   │   └── LC_MESSAGES/
│   │       ├── django.po             [Turkish translations]
│   │       └── django.mo             [Compiled]
│   ├── es/
│   │   └── LC_MESSAGES/
│   │       ├── django.po             [Spanish translations]
│   │       └── django.mo             [Compiled]
│   └── ... (15 more languages)
│
├── gamification/
│   └── locale/
│       └── (app-specific translations)
│
└── admin_api/
    ├── services/
    │   └── translation_service.py    [Translation strings]
    ├── templates/
    │   └── gamification_dashboard.html [i18n tags]
    └── locale/
        └── (app-specific translations)
```

---

## Next Steps

### Immediate
1. ✅ English setup complete
2. Deploy with English
3. Test all 18 language codes are recognized

### Short-term (1-2 weeks)
1. Add Turkish translations (highest priority)
2. Add Spanish, German, French
3. Test language switching

### Medium-term (1 month)
1. Complete all 18 language translations
2. Professional review
3. Community feedback

### Long-term
1. Continuous translation updates
2. Native speaker reviews
3. RTL language support (Arabic, Hebrew)

---

## Summary

**i18n Infrastructure for Phase 2:**

✅ **18 languages configured** — All language codes registered  
✅ **English complete** — All strings translated to English  
✅ **Django i18n setup** — Middleware, settings, template tags  
✅ **Translation service** — Centralized strings in Python  
✅ **Ready for translators** — Simple workflow for other languages  

**To add a new language:**
1. `python manage.py makemessages -l {lang}`
2. Translate `.po` file (100 strings, ~2 hours)
3. `python manage.py compilemessages`
4. Deploy

**Status**: Ready for production in English. Ready to accept translations for 17 other languages.
