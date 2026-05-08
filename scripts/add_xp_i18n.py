"""
add_xp_i18n.py
==============
Adds xp.* i18n keys to all 18 languages in i18n.ts.
Inserted after the 'coin.empty' key in each language block.
"""

from pathlib import Path

I18N_FILE = Path(__file__).parent.parent / "facesyma_mobile" / "src" / "utils" / "i18n.ts"

XP_KEYS: dict = {
    "tr": {
        "xp.title":          "XP & Seviye",
        "xp.level":          "Seviye",
        "xp.progress":       "İlerleme",
        "xp.xp_to_next":     "Sonraki seviyeye",
        "xp.history":        "XP Geçmişi",
        "xp.daily_quest":    "Günlük Görev",
        "xp.earned":         "Kazanılan XP",
        "xp.streak":         "günlük seri",
        "xp.empty":          "Henüz XP işlemi yok",
        "xp.level_up":       "Seviye atladın!",
        "xp.already_claimed":"Bugünkü görev zaten alındı",
    },
    "en": {
        "xp.title":          "XP & Level",
        "xp.level":          "Level",
        "xp.progress":       "Progress",
        "xp.xp_to_next":     "XP to next level",
        "xp.history":        "XP History",
        "xp.daily_quest":    "Daily Quest",
        "xp.earned":         "XP Earned",
        "xp.streak":         "day streak",
        "xp.empty":          "No XP transactions yet",
        "xp.level_up":       "Level Up!",
        "xp.already_claimed":"Today's quest already claimed",
    },
    "de": {
        "xp.title":          "XP & Level",
        "xp.level":          "Level",
        "xp.progress":       "Fortschritt",
        "xp.xp_to_next":     "XP bis nächstes Level",
        "xp.history":        "XP-Verlauf",
        "xp.daily_quest":    "Tagesquest",
        "xp.earned":         "Verdiente XP",
        "xp.streak":         "Tage-Serie",
        "xp.empty":          "Noch keine XP-Transaktionen",
        "xp.level_up":       "Level Up!",
        "xp.already_claimed":"Heutige Quest bereits abgeholt",
    },
    "ru": {
        "xp.title":          "XP и Уровень",
        "xp.level":          "Уровень",
        "xp.progress":       "Прогресс",
        "xp.xp_to_next":     "XP до следующего уровня",
        "xp.history":        "История XP",
        "xp.daily_quest":    "Ежедневное задание",
        "xp.earned":         "Заработано XP",
        "xp.streak":         "дней подряд",
        "xp.empty":          "Пока нет транзакций XP",
        "xp.level_up":       "Новый уровень!",
        "xp.already_claimed":"Сегодняшнее задание уже получено",
    },
    "ar": {
        "xp.title":          "XP والمستوى",
        "xp.level":          "المستوى",
        "xp.progress":       "التقدم",
        "xp.xp_to_next":     "XP للمستوى التالي",
        "xp.history":        "سجل XP",
        "xp.daily_quest":    "المهمة اليومية",
        "xp.earned":         "XP المكتسبة",
        "xp.streak":         "أيام متتالية",
        "xp.empty":          "لا توجد معاملات XP بعد",
        "xp.level_up":       "ترقية مستوى!",
        "xp.already_claimed":"تمت المطالبة بمهمة اليوم بالفعل",
    },
    "es": {
        "xp.title":          "XP y Nivel",
        "xp.level":          "Nivel",
        "xp.progress":       "Progreso",
        "xp.xp_to_next":     "XP para siguiente nivel",
        "xp.history":        "Historial XP",
        "xp.daily_quest":    "Misión diaria",
        "xp.earned":         "XP ganados",
        "xp.streak":         "días seguidos",
        "xp.empty":          "Sin transacciones XP aún",
        "xp.level_up":       "¡Subiste de nivel!",
        "xp.already_claimed":"La misión de hoy ya fue reclamada",
    },
    "ko": {
        "xp.title":          "XP & 레벨",
        "xp.level":          "레벨",
        "xp.progress":       "진행도",
        "xp.xp_to_next":     "다음 레벨까지 XP",
        "xp.history":        "XP 기록",
        "xp.daily_quest":    "일일 퀘스트",
        "xp.earned":         "획득 XP",
        "xp.streak":         "일 연속",
        "xp.empty":          "아직 XP 거래 없음",
        "xp.level_up":       "레벨 업!",
        "xp.already_claimed":"오늘 퀘스트는 이미 완료됨",
    },
    "ja": {
        "xp.title":          "XP & レベル",
        "xp.level":          "レベル",
        "xp.progress":       "進捗",
        "xp.xp_to_next":     "次のレベルまでのXP",
        "xp.history":        "XP履歴",
        "xp.daily_quest":    "デイリークエスト",
        "xp.earned":         "獲得XP",
        "xp.streak":         "日連続",
        "xp.empty":          "まだXPトランザクションがありません",
        "xp.level_up":       "レベルアップ！",
        "xp.already_claimed":"本日のクエストは受け取り済みです",
    },
    "zh": {
        "xp.title":          "XP与等级",
        "xp.level":          "等级",
        "xp.progress":       "进度",
        "xp.xp_to_next":     "升级所需XP",
        "xp.history":        "XP记录",
        "xp.daily_quest":    "每日任务",
        "xp.earned":         "获得的XP",
        "xp.streak":         "天连续",
        "xp.empty":          "暂无XP记录",
        "xp.level_up":       "升级了！",
        "xp.already_claimed":"今日任务已领取",
    },
    "hi": {
        "xp.title":          "XP और स्तर",
        "xp.level":          "स्तर",
        "xp.progress":       "प्रगति",
        "xp.xp_to_next":     "अगले स्तर के लिए XP",
        "xp.history":        "XP इतिहास",
        "xp.daily_quest":    "दैनिक क्वेस्ट",
        "xp.earned":         "अर्जित XP",
        "xp.streak":         "दिन की लकीर",
        "xp.empty":          "अभी तक कोई XP लेनदेन नहीं",
        "xp.level_up":       "स्तर अप!",
        "xp.already_claimed":"आज का क्वेस्ट पहले ही दावा किया गया",
    },
    "fr": {
        "xp.title":          "XP et Niveau",
        "xp.level":          "Niveau",
        "xp.progress":       "Progression",
        "xp.xp_to_next":     "XP pour le prochain niveau",
        "xp.history":        "Historique XP",
        "xp.daily_quest":    "Quête quotidienne",
        "xp.earned":         "XP gagnés",
        "xp.streak":         "jours consécutifs",
        "xp.empty":          "Aucune transaction XP pour l\\'instant",
        "xp.level_up":       "Niveau supérieur !",
        "xp.already_claimed":"La quête d\\'aujourd\\'hui a déjà été réclamée",
    },
    "pt": {
        "xp.title":          "XP e Nível",
        "xp.level":          "Nível",
        "xp.progress":       "Progresso",
        "xp.xp_to_next":     "XP para o próximo nível",
        "xp.history":        "Histórico XP",
        "xp.daily_quest":    "Missão diária",
        "xp.earned":         "XP ganhos",
        "xp.streak":         "dias seguidos",
        "xp.empty":          "Sem transações XP ainda",
        "xp.level_up":       "Subiu de nível!",
        "xp.already_claimed":"A missão de hoje já foi reivindicada",
    },
    "bn": {
        "xp.title":          "XP ও লেভেল",
        "xp.level":          "লেভেল",
        "xp.progress":       "অগ্রগতি",
        "xp.xp_to_next":     "পরবর্তী লেভেলে XP",
        "xp.history":        "XP ইতিহাস",
        "xp.daily_quest":    "দৈনিক কোয়েস্ট",
        "xp.earned":         "অর্জিত XP",
        "xp.streak":         "দিনের ধারা",
        "xp.empty":          "এখনও কোনো XP লেনদেন নেই",
        "xp.level_up":       "লেভেল আপ!",
        "xp.already_claimed":"আজকের কোয়েস্ট ইতিমধ্যে দাবি করা হয়েছে",
    },
    "id": {
        "xp.title":          "XP & Level",
        "xp.level":          "Level",
        "xp.progress":       "Kemajuan",
        "xp.xp_to_next":     "XP ke level berikutnya",
        "xp.history":        "Riwayat XP",
        "xp.daily_quest":    "Misi Harian",
        "xp.earned":         "XP Diperoleh",
        "xp.streak":         "hari beruntun",
        "xp.empty":          "Belum ada transaksi XP",
        "xp.level_up":       "Naik Level!",
        "xp.already_claimed":"Misi hari ini sudah diklaim",
    },
    "ur": {
        "xp.title":          "XP اور لیول",
        "xp.level":          "لیول",
        "xp.progress":       "پیشرفت",
        "xp.xp_to_next":     "اگلے لیول کے لیے XP",
        "xp.history":        "XP تاریخ",
        "xp.daily_quest":    "روزانہ کا کام",
        "xp.earned":         "حاصل شدہ XP",
        "xp.streak":         "دن کا سلسلہ",
        "xp.empty":          "ابھی تک کوئی XP لین دین نہیں",
        "xp.level_up":       "لیول اپ!",
        "xp.already_claimed":"آج کا کام پہلے ہی حاصل کیا جا چکا ہے",
    },
    "it": {
        "xp.title":          "XP e Livello",
        "xp.level":          "Livello",
        "xp.progress":       "Progresso",
        "xp.xp_to_next":     "XP per il prossimo livello",
        "xp.history":        "Cronologia XP",
        "xp.daily_quest":    "Quest giornaliera",
        "xp.earned":         "XP guadagnati",
        "xp.streak":         "giorni consecutivi",
        "xp.empty":          "Nessuna transazione XP ancora",
        "xp.level_up":       "Salito di livello!",
        "xp.already_claimed":"La quest di oggi è già stata riscattata",
    },
    "vi": {
        "xp.title":          "XP và Cấp độ",
        "xp.level":          "Cấp độ",
        "xp.progress":       "Tiến độ",
        "xp.xp_to_next":     "XP đến cấp tiếp theo",
        "xp.history":        "Lịch sử XP",
        "xp.daily_quest":    "Nhiệm vụ hàng ngày",
        "xp.earned":         "XP kiếm được",
        "xp.streak":         "ngày liên tiếp",
        "xp.empty":          "Chưa có giao dịch XP",
        "xp.level_up":       "Lên cấp!",
        "xp.already_claimed":"Nhiệm vụ hôm nay đã được nhận",
    },
    "pl": {
        "xp.title":          "XP i Poziom",
        "xp.level":          "Poziom",
        "xp.progress":       "Postęp",
        "xp.xp_to_next":     "XP do następnego poziomu",
        "xp.history":        "Historia XP",
        "xp.daily_quest":    "Dzienne zadanie",
        "xp.earned":         "Zdobyte XP",
        "xp.streak":         "dni z rzędu",
        "xp.empty":          "Brak jeszcze transakcji XP",
        "xp.level_up":       "Awans!",
        "xp.already_claimed":"Dzisiejsze zadanie zostało już odebrane",
    },
}


def run():
    content = I18N_FILE.read_text(encoding="utf-8")
    lines = content.split("\n")
    updated = 0

    for lang, keys in XP_KEYS.items():
        # Find the lang section header
        lang_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{lang}:") and "{" in line:
                lang_idx = i
                break

        if lang_idx is None:
            print(f"  ✗ '{lang}' dil bloğu bulunamadı")
            continue

        # Find 'coin.empty' AFTER the lang section
        anchor_idx = None
        for i in range(lang_idx, min(lang_idx + 2000, len(lines))):
            if "'coin.empty'" in lines[i]:
                anchor_idx = i
                break

        if anchor_idx is None:
            print(f"  ✗ '{lang}' için coin.empty bulunamadı")
            continue

        # Check which keys already exist
        block_text = "\n".join(lines[lang_idx:min(anchor_idx + 100, len(lines))])
        new_lines_to_insert = []
        for key, val in keys.items():
            if f"'{key}'" in block_text:
                continue
            safe_val = val.replace("'", "\\'")
            new_lines_to_insert.append(f"    '{key}': '{safe_val}',")

        if not new_lines_to_insert:
            print(f"  – '{lang}': zaten güncel")
            continue

        insert_pos = anchor_idx + 1
        lines = lines[:insert_pos] + new_lines_to_insert + lines[insert_pos:]
        updated += len(new_lines_to_insert)
        print(f"  ✓ '{lang}': {len(new_lines_to_insert)} anahtar eklendi")

    I18N_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nTamamlandı: {updated} anahtar eklendi.")


if __name__ == "__main__":
    run()
