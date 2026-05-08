"""
add_diet_i18n.py
================
i18n.ts dosyasına 18 dil için diet.sides ve diet.history_title anahtarlarını ekler.
"""

from pathlib import Path

I18N_FILE = Path(__file__).parent.parent / "facesyma_mobile" / "src" / "utils" / "i18n.ts"

NEW_KEYS: dict = {
    "tr": {
        "diet.sides":         "Yanında",
        "diet.history_title": "Öneri Geçmişi",
        "diet.history_empty": "Henüz öneri geçmişi yok",
    },
    "en": {
        "diet.sides":         "With",
        "diet.history_title": "Recommendation History",
        "diet.history_empty": "No recommendation history yet",
    },
    "de": {
        "diet.sides":         "Dazu",
        "diet.history_title": "Empfehlungsverlauf",
        "diet.history_empty": "Noch kein Empfehlungsverlauf",
    },
    "ru": {
        "diet.sides":         "К блюду",
        "diet.history_title": "История рекомендаций",
        "diet.history_empty": "Истории рекомендаций пока нет",
    },
    "ar": {
        "diet.sides":         "مع",
        "diet.history_title": "تاريخ التوصيات",
        "diet.history_empty": "لا يوجد تاريخ توصيات بعد",
    },
    "es": {
        "diet.sides":         "Acompañado de",
        "diet.history_title": "Historial de recomendaciones",
        "diet.history_empty": "Aún no hay historial de recomendaciones",
    },
    "ko": {
        "diet.sides":         "곁들임",
        "diet.history_title": "추천 기록",
        "diet.history_empty": "아직 추천 기록이 없습니다",
    },
    "ja": {
        "diet.sides":         "副菜",
        "diet.history_title": "推薦履歴",
        "diet.history_empty": "まだ推薦履歴がありません",
    },
    "zh": {
        "diet.sides":         "配菜",
        "diet.history_title": "推荐历史",
        "diet.history_empty": "暂无推荐历史",
    },
    "hi": {
        "diet.sides":         "साथ में",
        "diet.history_title": "अनुशंसा इतिहास",
        "diet.history_empty": "अभी तक कोई अनुशंसा इतिहास नहीं",
    },
    "fr": {
        "diet.sides":         "Accompagné de",
        "diet.history_title": "Historique des recommandations",
        "diet.history_empty": "Pas encore d'historique de recommandations",
    },
    "pt": {
        "diet.sides":         "Acompanhado de",
        "diet.history_title": "Histórico de recomendações",
        "diet.history_empty": "Ainda não há histórico de recomendações",
    },
    "bn": {
        "diet.sides":         "সাথে",
        "diet.history_title": "সুপারিশ ইতিহাস",
        "diet.history_empty": "এখনও কোনো সুপারিশ ইতিহাস নেই",
    },
    "id": {
        "diet.sides":         "Pelengkap",
        "diet.history_title": "Riwayat rekomendasi",
        "diet.history_empty": "Belum ada riwayat rekomendasi",
    },
    "ur": {
        "diet.sides":         "ساتھ میں",
        "diet.history_title": "سفارش کی تاریخ",
        "diet.history_empty": "ابھی تک کوئی سفارش کی تاریخ نہیں",
    },
    "it": {
        "diet.sides":         "Accompagnato da",
        "diet.history_title": "Storico raccomandazioni",
        "diet.history_empty": "Nessuno storico di raccomandazioni ancora",
    },
    "vi": {
        "diet.sides":         "Kèm theo",
        "diet.history_title": "Lịch sử gợi ý",
        "diet.history_empty": "Chưa có lịch sử gợi ý",
    },
    "pl": {
        "diet.sides":         "Do tego",
        "diet.history_title": "Historia rekomendacji",
        "diet.history_empty": "Brak historii rekomendacji",
    },
}


def run():
    content = I18N_FILE.read_text(encoding="utf-8")
    lines = content.split("\n")
    updated = 0

    for lang, keys in NEW_KEYS.items():
        # Find the 'diet.empty': line for this language
        # We search from the lang section header forward
        lang_header = f"  {lang}: {{"
        lang_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{lang}:") and "{" in line:
                lang_idx = i
                break

        if lang_idx is None:
            print(f"  ✗ '{lang}' dil bloğu bulunamadı")
            continue

        # Find 'diet.empty' AFTER the lang section
        empty_idx = None
        for i in range(lang_idx, min(lang_idx + 1500, len(lines))):
            if "'diet.empty'" in lines[i]:
                empty_idx = i
                break

        if empty_idx is None:
            print(f"  ✗ '{lang}' için diet.empty bulunamadı")
            continue

        # Check if keys already exist in this language's block
        # Look in the range [lang_idx, empty_idx+50]
        block_text = "\n".join(lines[lang_idx:min(empty_idx + 50, len(lines))])
        new_lines_to_insert = []
        for key, val in keys.items():
            if f"'{key}'" in block_text:
                continue  # already exists
            # Escape single quotes in val
            safe_val = val.replace("'", "\\'")
            indent = "    "  # 4 spaces (inside language block)
            new_lines_to_insert.append(f"{indent}'{key}': '{safe_val}',")

        if not new_lines_to_insert:
            print(f"  – '{lang}': zaten güncel")
            continue

        # Insert after the diet.empty line
        insert_pos = empty_idx + 1
        lines = lines[:insert_pos] + new_lines_to_insert + lines[insert_pos:]
        updated += len(new_lines_to_insert)
        print(f"  ✓ '{lang}': {len(new_lines_to_insert)} anahtar eklendi")

    I18N_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nTamamlandı: {updated} anahtar eklendi.")


if __name__ == "__main__":
    run()
