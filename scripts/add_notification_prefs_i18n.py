"""Add account.notifications + account.notif_coach/streak/test after account.privacy_policy in all 18 languages."""
import pathlib, re

path = pathlib.Path(__file__).parent.parent / 'facesyma_mobile/src/utils/i18n.ts'
content = path.read_text(encoding='utf-8')

# Find all account.privacy_policy values
matches = list(re.finditer(r"    'account\.privacy_policy': '([^']+)'", content))
print(f"Found {len(matches)} privacy_policy anchors")

inserts = {
    'Gizlilik Politikası':         ("Bildirimler", "Günlük AI Coach mesajı", "Seri hatırlatıcısı", "Test hatırlatıcısı"),
    'Privacy Policy':              ("Notifications", "Daily AI Coach message", "Streak reminder", "Test reminder"),
    'Datenschutzrichtlinie':       ("Benachrichtigungen", "Tägliche AI-Coach-Nachricht", "Streak-Erinnerung", "Test-Erinnerung"),
    'Политика конфиденциальности': ("Уведомления", "Ежедневное сообщение коуча", "Напоминание серии", "Напоминание теста"),
    'سياسة الخصوصية':             ("الإشعارات", "رسالة المدرب اليومية", "تذكير السلسلة", "تذكير الاختبار"),
    'Política de Privacidad':      ("Notificaciones", "Mensaje diario del coach", "Recordatorio de racha", "Recordatorio de test"),
    '개인정보 보호정책':            ("알림", "일일 AI 코치 메시지", "연속 알림", "테스트 알림"),
    'プライバシーポリシー':         ("通知", "毎日のAIコーチメッセージ", "ストリークリマインダー", "テストリマインダー"),
    '隐私政策':                    ("通知", "每日AI教练消息", "连续提醒", "测试提醒"),
    'गोपनीयता नीति':              ("सूचनाएं", "दैनिक AI कोच संदेश", "स्ट्रीक अनुस्मारक", "टेस्ट अनुस्मारक"),
    'Politique de confidentialité':("Notifications", "Message quotidien du coach", "Rappel de série", "Rappel de test"),
    'Política de Privacidade':     ("Notificações", "Mensagem diária do coach", "Lembrete de sequência", "Lembrete de teste"),
    'গোপনীয়তা নীতি':             ("বিজ্ঞপ্তি", "দৈনিক AI কোচ বার্তা", "স্ট্রিক রিমাইন্ডার", "টেস্ট রিমাইন্ডার"),
    'Kebijakan Privasi':           ("Notifikasi", "Pesan coach harian", "Pengingat streak", "Pengingat tes"),
    'رازداری پالیسی':              ("اطلاعیات", "روزانہ AI کوچ پیغام", "اسٹریک یاد دہانی", "ٹیسٹ یاد دہانی"),
    'رازداری کی پالیسی':           ("اطلاعیات", "روزانہ AI کوچ پیغام", "اسٹریک یاد دہانی", "ٹیسٹ یاد دہانی"),
    'Informativa sulla Privacy':   ("Notifiche", "Messaggio coach giornaliero", "Promemoria streak", "Promemoria test"),
    'Informativa sulla privacy':   ("Notifiche", "Messaggio coach giornaliero", "Promemoria streak", "Promemoria test"),
    'Chính sách Bảo mật':          ("Thông báo", "Tin nhắn huấn luyện viên hàng ngày", "Nhắc nhở chuỗi", "Nhắc nhở bài kiểm tra"),
    'Chính sách quyền riêng tư':   ("Thông báo", "Tin nhắn huấn luyện viên hàng ngày", "Nhắc nhở chuỗi", "Nhắc nhở bài kiểm tra"),
    'Polityka Prywatności':        ("Powiadomienia", "Codzienna wiadomość od coacha", "Przypomnienie serii", "Przypomnienie testu"),
    'Polityka prywatności':        ("Powiadomienia", "Codzienna wiadomość od coacha", "Przypomnienie serii", "Przypomnienie testu"),
    'Política de privacidad':      ("Notificaciones", "Mensaje diario del coach", "Recordatorio de racha", "Recordatorio de test"),
    '개인정보 처리방침':            ("알림", "일일 AI 코치 메시지", "연속 알림", "테스트 알림"),
    'Política de privacidade':     ("Notificações", "Mensagem diária do coach", "Lembrete de sequência", "Lembrete de teste"),
}

count = 0
for m in matches:
    pp_val = m.group(1)
    if pp_val not in inserts:
        print(f"NOT IN MAP: {pp_val}")
        continue
    notif, coach, streak, test = inserts[pp_val]
    anchor = f"    'account.privacy_policy': '{pp_val}',"
    if anchor not in content:
        print(f"ANCHOR NOT FOUND: {anchor[:60]}")
        continue
    nearby_pos = content.index(anchor)
    nearby = content[nearby_pos:nearby_pos+400]
    if "'account.notifications'" in nearby:
        print(f"Already inserted for: {pp_val[:30]}")
        continue
    insertion = (
        f"\n    'account.notifications': '{notif}',"
        f"\n    'account.notif_coach': '{coach}',"
        f"\n    'account.notif_streak': '{streak}',"
        f"\n    'account.notif_test': '{test}',"
    )
    content = content.replace(anchor, anchor + insertion, 1)
    count += 1

path.write_text(content, encoding='utf-8')
print(f"Done: {count}/18 languages updated")
