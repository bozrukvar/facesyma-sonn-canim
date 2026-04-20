# Translation Guide — Phase 2 Gamification

**Quick Start**: Add translations for any of the 17 languages in 3 steps.

---

## Available Languages

| Code | Language | Status |
|------|----------|--------|
| `en` | English | ✅ Complete |
| `tr` | Türkçe (Turkish) | ⏳ Ready |
| `de` | Deutsch (German) | ⏳ Ready |
| `fr` | Français (French) | ⏳ Ready |
| `es` | Español (Spanish) | ⏳ Ready |
| `it` | Italiano (Italian) | ⏳ Ready |
| `pt` | Português (Portuguese) | ⏳ Ready |
| `pl` | Polski (Polish) | ⏳ Ready |
| `ru` | Русский (Russian) | ⏳ Ready |
| `ja` | 日本語 (Japanese) | ⏳ Ready |
| `zh-hans` | 简体中文 (Simplified Chinese) | ⏳ Ready |
| `zh-hant` | 繁體中文 (Traditional Chinese) | ⏳ Ready |
| `ko` | 한국어 (Korean) | ⏳ Ready |
| `ar` | العربية (Arabic) | ⏳ Ready |
| `he` | עברית (Hebrew) | ⏳ Ready |
| `hi` | हिन्दी (Hindi) | ⏳ Ready |
| `vi` | Tiếng Việt (Vietnamese) | ⏳ Ready |
| `th` | ไทย (Thai) | ⏳ Ready |

---

## Steps to Translate

### Step 1: Open .po File

#### Option A: Using Poedit (Recommended)

**Install Poedit** (free):
- Windows: `choco install poedit` or download from poedit.net
- macOS: `brew install poedit`
- Linux: `sudo apt install poedit`

**Open .po file**:
```bash
cd facesyma_backend
poedit locale/tr/LC_MESSAGES/django.po
```

Poedit will show:
- **Left**: English source text
- **Right**: Translation input field
- **Bottom**: Context (where string is used)

#### Option B: Using VS Code

1. Install **"PO File Support"** extension (ID: `arjun.a.gupta.po-file-support`)
2. Open `facesyma_backend/locale/tr/LC_MESSAGES/django.po`
3. Switch to **"Translation"** view
4. Enter translations in the msgstr field

#### Option C: Manual Edit

Edit `.po` file with any text editor:

```po
#: admin_api/services/translation_service.py:19
msgid "Cache Performance"
msgstr "Hiş Performansı"

#: admin_api/services/translation_service.py:30
msgid "Hit Rate"
msgstr "Hit Oranı"
```

### Step 2: Translate 97 Strings

You'll find strings grouped by location. **Total time**: ~2-3 hours per language.

#### Common String Types

**Nouns** (straightforward translation):
```
msgid "Coins"
msgstr "Madeni Paralar"  # Turkish
```

**Verbs** (action words):
```
msgid "Refresh Now"
msgstr "Şimdi Yenile"  # Turkish
```

**UI Labels** (buttons, headers):
```
msgid "Total Snapshots"
msgstr "Toplam Anlık Görüntüler"  # Turkish
```

**Placeholders** (keep `%s`, `%d` as-is):
```
msgid "Cache error: %s"
msgstr "Önbellek hatası: %s"  # Turkish (keep %s)

msgid "%d days tracked"
msgstr "%d gün izlendi"  # Turkish (keep %d)
```

**Emojis** (keep as-is):
```
msgid "🎮 Gamification Phase 2 — Monitoring Dashboard"
msgstr "🎮 Oyunlaştırma Faz 2 — İzleme Panosu"  # Turkish
```

### Step 3: Compile and Test

**Compile** .po → .mo (binary):
```bash
cd facesyma_backend
python compile_messages.py
```

**Test** with curl:
```bash
# Turkish
curl -H "Accept-Language: tr" \
  http://localhost:8000/api/v1/admin/gamification-dashboard/

# Should display in Turkish!
```

**Test with browser**:
1. Open browser settings
2. Change language to Turkish
3. Visit `http://localhost:8000/admin_api/gamification-dashboard.html`
4. Should display in Turkish!

---

## String Categories

All 97 strings are grouped into these categories:

### Dashboard Strings (50 strings)
**File**: `facesyma_backend/admin_api/services/translation_service.py` (lines 17-78)

Includes:
- **Header**: Dashboard title, status labels
- **Cache Card**: "Hit Rate", "Total Queries", "Memory Used"
- **Performance Card**: "Average Query Time", "P95 Latency"
- **WebSocket Card**: "Current Connections", "Peak Today"
- **Trends Card**: "Total Snapshots", "Latest Snapshot Age"
- **Health Card**: "Status", "Components"
- **Chart**: "Average", "Min", "Max"
- **Tables**: "Leaderboard Type", "Snapshots", "Queries"
- **Units**: "h" (hours), "days", "MB", "%", "ms"

### WebSocket Strings (8 strings)
**Location**: Lines 84-94

Connection messages, notifications, errors.

### API Error Strings (10+ strings)
**Location**: Lines 100-112

Error messages for invalid parameters, not found, unauthorized, etc.

### Leaderboard Strings (13 strings)
**Location**: Lines 118-133

Rank, username, coins, badges, accuracy, etc.

### Trend Strings (8 strings)
**Location**: Lines 139-150

"Most Improved", "Most Active", momentum states.

### System Health Strings (8 strings)
**Location**: Lines 156-167

"Redis", "MongoDB", "Healthy", "Degraded", etc.

### Cache Event Strings (5 strings)
**Location**: Lines 173-179

"Coins awarded", "Badge unlocked", "Mission completed".

---

## Translation Tips

### 1. **Keep Variables Intact**
Always preserve `%s`, `%d`, `%f` placeholders:
```
❌ "Cache error: Fehler" (removed %s)
✅ "Cachefehler: %s" (kept %s)
```

### 2. **Keep Emojis**
Emojis are part of the message:
```
✅ "🎮 Gamifikasyon Faz 2" (emoji included)
❌ "Gamifikasyon Faz 2" (emoji removed)
```

### 3. **Preserve Punctuation**
Keep the same punctuation as English:
```
English: "Hit Rate"
Turkish: "Hit Oranı"  (same punctuation)

English: "Error: %s"
Turkish: "Hata: %s"  (same colon and space)
```

### 4. **Use Consistent Terminology**
Create a glossary for recurring terms:
- "Leaderboard" → Use same translation throughout
- "Coins" → Use same translation throughout
- "Rank" → Use same translation throughout

### 5. **Match Context When Possible**
Some strings appear in multiple locations with different contexts:
```
msgid "Avg Time"  # Table header
msgstr "Ort. Zaman"  # German abbreviation

msgid "Average Query Time"  # Card label
msgstr "Durchschnittliche Abfragezeit"  # German full form
```

---

## File Locations

```
facesyma_backend/locale/
├── django.pot                          (Template with all English strings)
│
├── en/LC_MESSAGES/
│   ├── django.po                       (English translations, filled)
│   └── django.mo                       (Compiled, binary)
│
├── tr/LC_MESSAGES/
│   ├── django.po      ← EDIT THIS      (Empty, ready for Turkish)
│   └── django.mo      ← AUTO-GENERATED (Recompile after editing)
│
├── es/LC_MESSAGES/
│   ├── django.po      ← EDIT THIS      (Empty, ready for Spanish)
│   └── django.mo      ← AUTO-GENERATED
│
└── ... (15 more languages)
```

**Only edit** the `.po` files. The `.mo` files are auto-generated.

---

## Workflow Example: Turkish Translation

### 1. Extract Strings (Already Done ✅)
```bash
python extract_messages.py
# Creates: locale/tr/LC_MESSAGES/django.po (empty)
```

### 2. Open & Translate
```bash
poedit locale/tr/LC_MESSAGES/django.po

# Poedit shows 97 strings to translate
# Translator fills in Turkish for each
# File auto-saves
```

**Sample translations**:
| English | Turkish |
|---------|---------|
| Cache Performance | Hiş Performansı |
| Hit Rate | Hit Oranı |
| Total Queries | Toplam Sorgular |
| Memory Used | Kullanılan Bellek |
| Leaderboard updated | Lider Tablosu Güncellendi |

### 3. Compile
```bash
python compile_messages.py
# Creates: locale/tr/LC_MESSAGES/django.mo (binary)
```

### 4. Test
```bash
curl -H "Accept-Language: tr" \
  http://localhost:8000/api/v1/admin/gamification-dashboard/
  
# Returns Turkish content!
```

### 5. Commit
```bash
git add locale/tr/LC_MESSAGES/django.po
git commit -m "Add Turkish translations for Phase 2 Gamification"
git push
```

### 6. Deploy
```bash
# Commit is included in docker-compose up -d
docker-compose up -d

# Turkish now available on production!
```

---

## Common Issues

### Issue: Translated strings still show English
**Cause**: `.mo` file not recompiled  
**Fix**:
```bash
python compile_messages.py
```

### Issue: New strings not in .po file
**Cause**: Need to re-extract after code changes  
**Fix**:
```bash
python extract_messages.py
# Then retranslate new strings
python compile_messages.py
```

### Issue: Poedit shows "Untranslated (0)" but you translated them
**Cause**: Need to mark strings as translated in Poedit  
**Fix**: In Poedit, each string needs a msgstr value (not empty)

### Issue: Strange characters in translation
**Cause**: Text encoding issue  
**Fix**: Ensure .po file is saved as **UTF-8** (not ASCII or other)

---

## Professional Translation Services

If you prefer professional translation instead of manual:

### Fiverr / Upwork
- Cost: $50-150 for 100 strings to 17 languages
- Time: 1-2 weeks
- Quality: Professional native speakers

### Google Sheets + Auto-Translation
1. Export all English strings to Google Sheets
2. Use Google Translate for each language (free)
3. Manual review by native speakers
4. Update .po files

### Translation Management Platform
- **Crowdin.net**: Free for open-source, paid for commercial
- **Lokalise.app**: Professional translation platform
- **Transifex**: Community translation management

---

## Quality Assurance

### Before Committing Translation

1. **Check .po file syntax**:
   ```bash
   # In Poedit: File > Validate
   # Or: grep -c "^msgstr" locale/tr/LC_MESSAGES/django.po
   # Should show 98 (97 strings + header)
   ```

2. **Verify compilation**:
   ```bash
   python compile_messages.py
   # Should complete without errors
   # Should create .mo file (~6KB)
   ```

3. **Test language**:
   ```bash
   curl -H "Accept-Language: tr" http://localhost:8000/...
   # Verify Turkish appears
   ```

4. **Check for untranslated strings**:
   ```bash
   grep -A1 'msgstr ""' locale/tr/LC_MESSAGES/django.po
   # Should only show header, no empty msgstr entries
   ```

---

## Timeline

| Week | Languages | Effort |
|------|-----------|--------|
| 1 | Turkish | 2-3h |
| 2 | Spanish, German, French | 6-9h |
| 3 | Japanese, Chinese (Simplified & Traditional) | 6-9h |
| 4+ | Arabic, Hebrew, Hindi, Vietnamese, Thai, etc. | 10-15h |

**Total effort for all 17 languages**: ~25-35 hours (or 2-3 weeks)

---

## Next Steps

1. **Choose a language** to start with (recommend: Turkish)
2. **Download & install Poedit**
3. **Open** `locale/{lang}/LC_MESSAGES/django.po`
4. **Translate** all 97 strings (~2-3 hours)
5. **Save** the .po file
6. **Run** `python compile_messages.py`
7. **Test** with `curl -H "Accept-Language: {lang}" ...`
8. **Commit** and push to git
9. **Deploy** with docker-compose

Let me know which language you'd like to start with! 🌍
