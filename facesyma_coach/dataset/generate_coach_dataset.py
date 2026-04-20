"""
facesyma_coach/dataset/generate_coach_dataset.py
==================================================
Facesyma'nın mevcut 201 sıfat veritabanını genişletir.
14 yeni "yaşam koçu" modülü için veri üretir ve
BACKUP bir MongoDB veritabanına yazar.

Yeni modüller:
  1.  saglik_esenwlik    — Sağlıklı Yaşam ve Esenlik
  2.  dogruluk_sadakat   — Doğruluk ve Sadakat
  3.  guvenlik           — Güvenlik (kişisel/duygusal)
  4.  suc_egilim         — Risk / Suç Eğilim Analizi
  5.  iliski_yonetimi    — İlişki Yönetimi
  6.  iletisim_becerileri— İletişim Becerileri
  7.  stres_yonetimi     — Stres ve Zaman Yönetimi
  8.  ozguven            — Özgüven Artırma
  9.  zaman_yonetimi     — Zaman Yönetimi
  10. kisisel_hedefler   — Kişisel Gelişim Hedefleri
  11. astroloji_harita   — Astroloji Haritası & Yorumu
  12. dogum_analizi      — Doğum Tarihi/Saati Analizi
  13. yas_koc_ozet       — Yaşam Koçu Genel Özet
  14. vucut_dil          — Beden Dili Analizi (yüz verisinden)

Backup DB: facesyma-coach-backup (mevcut DB'ye dokunmaz)

Kullanım:
  python generate_coach_dataset.py \
      --input  ../facesyma_migrate/sifat_veritabani.json \
      --output sifat_coach_tr.json \
      --lang   tr

  # Tüm diller
  python generate_coach_dataset.py --all-langs

  # MongoDB'ye yaz
  python generate_coach_dataset.py --push-mongo
"""

import json, random, argparse, sys, copy
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# Modül şablonları — 14 yeni modül, 18 dil
# Her modül: sıfata göre farklılaşan metin üretimi için şablon setleri
# ─────────────────────────────────────────────────────────────────────────────

# Kısa yardımcı
def _pick(lst, n=1):
    return random.sample(lst, min(n, len(lst)))

# ─── 1. SAĞLIK VE ESENLİK ────────────────────────────────────────────────────
SAGLIK_TR = {
    "pozitif": [
        "Yüz hatlarındaki denge, vücudunla iyi bir ilişki kurduğuna işaret eder.",
        "Sakin ve dengeli yapın, strese karşı doğal bir tampon oluşturur.",
        "Sistematik karakterin sağlıklı alışkanlıklar edinmeni kolaylaştırır.",
        "Güçlü empatin, başkalarının duygusal sağlığına destek olma kapasiteni artırır.",
    ],
    "gelisim": [
        "Uyku düzenini korumak senin için kritik — biyolojik ritmin güçlü.",
        "Meditasyon veya nefes egzersizleri zihinsel netliğini artırır.",
        "Doğada vakit geçirmek ruhsal dengen için özellikle güçlü bir iyileştirici.",
        "Sosyal bağlantı sağlığın için beslenme kadar önemli.",
    ],
    "risk": [
        "Aşırı sorumluluk alma eğilimin tükenme (burnout) riskini artırabilir.",
        "İç dünyana fazla kapanmak duygusal basıncı biriktirebilir.",
        "Mükemmeliyetçi eğilim kronik strese dönüşebilir — farkında ol.",
    ],
    "pratik": [
        "Günde 20 dk yürüyüş + 10 dk nefes egzersizi ideal başlangıç.",
        "Beslenme günlüğü tutmak farkındalık için güçlü bir araç.",
        "Dijital detoks — haftada bir gün ekransız geçir.",
    ],
}

SAGLIK_EN = {
    "pozitif": [
        "Facial symmetry indicates a good relationship with your body.",
        "Your calm, balanced nature acts as a natural buffer against stress.",
        "Your systematic character makes building healthy habits easier.",
        "Your strong empathy enhances your capacity to support others' emotional wellbeing.",
    ],
    "gelisim": [
        "Maintaining sleep rhythm is critical for you — your biological clock is strong.",
        "Meditation or breathing exercises will sharpen your mental clarity.",
        "Time in nature is a particularly powerful healer for your spiritual balance.",
        "Social connection is as important to your health as nutrition.",
    ],
    "risk": [
        "Your tendency to over-responsible may increase burnout risk.",
        "Withdrawing too much inward can build emotional pressure.",
        "Perfectionist tendencies can turn into chronic stress — stay aware.",
    ],
    "pratik": [
        "20 min walk + 10 min breathing daily is an ideal start.",
        "Keeping a food journal is a powerful awareness tool.",
        "Digital detox — one screen-free day per week.",
    ],
}

# ─── 2. DOĞRULUK VE SADAKAT ──────────────────────────────────────────────────
DOGRULUK_TR = {
    "profil": [
        "Yüz analizin, içsel ahlaki pusulasını yüksek tutan bir yapıya işaret ediyor.",
        "Gözlerindeki derinlik, söz verdiğinde söz tutan bir karakteri yansıtıyor.",
        "Yüz hatların sadakatin kişisel değer sisteminizin merkezinde olduğunu gösteriyor.",
    ],
    "guclu": [
        "Bir kez bağ kurduğunda uzun soluklu ve kararlı ilişkiler kurarsın.",
        "Güven inşa etmekte olağanüstü iyisin — çevrende referans kişisin.",
        "Etik sınırlarını net tutarsın, bu seni iş hayatında değerli kılar.",
    ],
    "dikkat": [
        "Başkalarından aynı dürüstlüğü beklemek bazen hayal kırıklığı yaratabilir.",
        "Sadakatini istismar etmeye çalışan ilişkilere karşı dikkatli ol.",
        "Sınır koymayı öğrenmek, sadakatini güç haline getirir.",
    ],
}

DOGRULUK_EN = {
    "profil": [
        "Your facial analysis points to a structure that keeps a high internal moral compass.",
        "The depth in your eyes reflects a character that keeps its word.",
        "Your facial features show loyalty sits at the center of your personal value system.",
    ],
    "guclu": [
        "Once you form a bond, you build long-lasting, committed relationships.",
        "You are exceptionally good at building trust — a reference person in your circle.",
        "You keep ethical boundaries clear, which makes you valuable in professional life.",
    ],
    "dikkat": [
        "Expecting the same honesty from others can sometimes lead to disappointment.",
        "Be careful with relationships that try to exploit your loyalty.",
        "Learning to set boundaries turns your loyalty into a strength.",
    ],
}

# ─── 3. GÜVENLİK ─────────────────────────────────────────────────────────────
GUVENLIK_TR = {
    "kisisel": [
        "Çevresel farkındalığın yüksek — tehlikeleri erken fark edersin.",
        "Kontrol ihtiyacın kişisel güvenlik reflekslerini güçlendirir.",
        "Temkinli yapın seni risk almadan önce iki kez düşündürür.",
    ],
    "duygusal": [
        "Duygusal güvenlik ihtiyacın güçlü — yakın ilişkilerinde güven zeminine ihtiyaç duyarsın.",
        "Güvenli bağlanma stiliyle ilişki kurma eğilimin var.",
        "İç huzur kaynağın dışarıdan değil içeriden geliyor.",
    ],
    "finansal": [
        "Risk aversif yapın finansal güvenliği önceliklendirir.",
        "Acil durum fonu oluşturma ve uzun vadeli planlama sana doğal gelir.",
        "Spekülatif yatırımlardan kaçınma eğilimin koruyucu bir özellik.",
    ],
    "tavsiye": [
        "Dijital güvenlik alışkanlıkları edin — şifre yöneticisi, iki faktörlü doğrulama.",
        "Duygusal sınırlarını belirle ve buna saygı gösterilmesini talep et.",
        "Finansal olarak: 3-6 aylık gider karşılığı acil fon hedefle.",
    ],
}

GUVENLIK_EN = {
    "kisisel": [
        "Your environmental awareness is high — you notice dangers early.",
        "Your need for control strengthens your personal security reflexes.",
        "Your cautious nature makes you think twice before taking risks.",
    ],
    "duygusal": [
        "Your emotional security need is strong — you need a trust foundation in close relationships.",
        "You tend to form relationships with a secure attachment style.",
        "Your inner peace comes from within, not from outside.",
    ],
    "finansal": [
        "Your risk-averse nature prioritizes financial security.",
        "Building an emergency fund and long-term planning come naturally to you.",
        "Your tendency to avoid speculative investments is a protective trait.",
    ],
    "tavsiye": [
        "Develop digital security habits — password manager, two-factor auth.",
        "Define emotional boundaries and require them to be respected.",
        "Financially: target an emergency fund covering 3-6 months of expenses.",
    ],
}

# ─── 4. RİSK / SUÇ EĞİLİM ANALİZİ ───────────────────────────────────────────
# NOT: Bu modül klinik değil; kişinin risk alma / kural çiğneme eğilimini
# yapıcı ve etik bir çerçevede ele alır.
SUC_EGILIM_TR = {
    "risk_alma": [
        "Analizin kurallara bağlı, düzene saygılı bir profil gösteriyor (düşük risk).",
        "Girişimci yapın bazen sınırları test etme eğilimi taşıyabilir — farkındalık önemli.",
        "Yüksek özgürlük ihtiyacın zaman zaman sosyal normlarla çatışabilir.",
    ],
    "koruyucu": [
        "Empati kapasitenin yüksek olması başkalarına zarar verme olasılığını azaltır.",
        "Uzun vadeli düşünme yeteneğin anlık riskli kararları dengeleyici etki yapar.",
        "Güçlü vicdan yapın etik bir pusula görevi görüyor.",
    ],
    "tavsiye": [
        "Kural dışı alternatifler yerine sistemi değiştirmeye odaklan.",
        "Öfke ve hayal kırıklığını yapıcı kanallara yönlendir.",
        "Mentor veya koç çalışması kriz anlarında yol gösterici olabilir.",
    ],
    "profesyonel_not": "Bu analiz tanısal amaçlı değildir. Klinik değerlendirme için uzman desteği alınmalıdır.",
}

SUC_EGILIM_EN = {
    "risk_alma": [
        "Your analysis shows a rule-compliant, order-respecting profile (low risk).",
        "Your entrepreneurial nature may sometimes have a tendency to test boundaries — awareness is key.",
        "High need for freedom may occasionally conflict with social norms.",
    ],
    "koruyucu": [
        "Your high empathy capacity reduces the likelihood of harming others.",
        "Your long-term thinking ability counterbalances impulsive risky decisions.",
        "Your strong conscience acts as an ethical compass.",
    ],
    "tavsiye": [
        "Focus on changing the system rather than rule-breaking alternatives.",
        "Channel anger and frustration into constructive outlets.",
        "Mentor or coaching work can be a guide in crisis moments.",
    ],
    "profesyonel_not": "This analysis is not for diagnostic purposes. Seek professional support for clinical assessment.",
}

# ─── 5. İLİŞKİ YÖNETİMİ ─────────────────────────────────────────────────────
ILISKI_TR = {
    "stil": [
        "Güvenli bağlanma stili — ilişkilerinde istikrar ve güven önceliğin.",
        "Kaçınan bağlanma eğilimi — yakınlık bazen rahatsızlık yaratabilir, farkında ol.",
        "Kaygılı bağlanma — onay ihtiyacın ilişkilerinde baskı yaratabilir.",
        "Derin ve anlamlı bağlar kurarsın; yüzeysel ilişkiler seni tatmin etmez.",
    ],
    "guclu": [
        "Empatin partnerlerin ihtiyaçlarını sözden önce hissettiriyor.",
        "Sadık ve güvenilir yapın uzun soluklu ilişkilerin temel taşı.",
        "Sınır koyma konusunda netsin — bu sağlıklı ilişkinin işareti.",
    ],
    "zorluk": [
        "Kontrolcü eğilimin ilişkide boğucu olabilir — farkında ol.",
        "Beklentilerini net ifade etmek ilişkiyi güçlendirir.",
        "Çatışmadan kaçınma eğilimin sorunları biriktirebilir.",
    ],
    "tavsiye": [
        "Haftalık derin sohbet ritüeli kur — telefon yok, göz teması var.",
        "Takdir ve minnettarlığı sesli ifade etmek bağı güçlendirir.",
        "Kişisel alan ihtiyacını ve partnerininkini dengele.",
    ],
}

ILISKI_EN = {
    "stil": [
        "Secure attachment style — stability and trust are your priority in relationships.",
        "Avoidant attachment tendency — closeness can sometimes cause discomfort, be aware.",
        "Anxious attachment — need for approval can create pressure in relationships.",
        "You build deep and meaningful bonds; superficial relationships don't satisfy you.",
    ],
    "guclu": [
        "Your empathy senses partners' needs before they speak.",
        "Your loyal, reliable nature is the cornerstone of long-lasting relationships.",
        "You are clear about setting boundaries — a sign of healthy relationships.",
    ],
    "zorluk": [
        "Controlling tendencies can feel suffocating in relationships — be aware.",
        "Clearly expressing your expectations strengthens relationships.",
        "Conflict-avoidance tendency can let problems accumulate.",
    ],
    "tavsiye": [
        "Establish a weekly deep conversation ritual — no phones, eye contact.",
        "Voicing appreciation and gratitude strengthens the bond.",
        "Balance your personal space needs with your partner's.",
    ],
}

# ─── 6. İLETİŞİM BECERİLERİ ──────────────────────────────────────────────────
ILETISIM_TR = {
    "stil": [
        "Analitik iletişimci — veri ve mantık öncelikli, duygusal ton ikincil.",
        "Ekspresif iletişimci — duygu ve hikaye ağırlıklı, ilişki odaklı.",
        "Otoriter iletişimci — net ve kararlı, bazen katı algılanabilir.",
        "Destekleyici iletişimci — dinleyici, empati kurucu, uzlaşmacı.",
    ],
    "guclu": [
        "Aktif dinleme kapasiten çevrendekilere değer hissettiriyor.",
        "Sözsüz iletişim okuma becerin güçlü — mimik ve beden dilini anlarsın.",
        "Net ve doğrudan mesaj verme yeteneğin belirsizlikleri azaltıyor.",
    ],
    "gelisim": [
        "Konuşmadan önce 3 saniye dur — düşünce kalitesi artar.",
        "Tekrarlayan özetleme (paraphrase) tekniği anlaşılmayı garantiler.",
        "Zor konuşmalar için 'Ben dili' kullan — suçlama değil, ifade.",
    ],
    "dijital": [
        "Yazılı iletişimde tonu fark et — emoji veya tonlama bağlamı değiştirir.",
        "E-posta'yı öfke anında gönderme — 24 saat bekle.",
        "Video toplantılarda kamera aç — sözsüz iletişim güven inşa eder.",
    ],
}

ILETISIM_EN = {
    "stil": [
        "Analytical communicator — data and logic first, emotional tone secondary.",
        "Expressive communicator — emotion and story-heavy, relationship-focused.",
        "Authoritative communicator — clear and decisive, sometimes perceived as rigid.",
        "Supportive communicator — listener, empathetic, conciliatory.",
    ],
    "guclu": [
        "Your active listening capacity makes those around you feel valued.",
        "Your ability to read non-verbal communication is strong — you understand cues.",
        "Your clear, direct messaging style reduces ambiguities.",
    ],
    "gelisim": [
        "Pause 3 seconds before speaking — thought quality improves.",
        "Repetitive summarizing (paraphrase) technique guarantees understanding.",
        "Use 'I language' for difficult conversations — expression, not accusation.",
    ],
    "dijital": [
        "Notice tone in written communication — emojis or phrasing change context.",
        "Don't send emails in anger — wait 24 hours.",
        "Turn on camera in video meetings — non-verbal communication builds trust.",
    ],
}

# ─── 7. STRES YÖNETİMİ ───────────────────────────────────────────────────────
STRES_TR = {
    "tetikleyici": [
        "Kontrol kaybı en güçlü stres tetikleyicin — sistematik planlama dengeleyici.",
        "Belirsizlik yüksek stres kaynağın — net hedefler kaygıyı azaltır.",
        "İlişki çatışmaları duygusal stres yüküne katkıda bulunuyor.",
        "Aşırı yüklenme ve görev birikimi kronik stres riskini artırıyor.",
    ],
    "basa_cikma": [
        "Fiziksel egzersiz kortizol düşürmede en hızlı yöntem — önceliklendir.",
        "Derin nefes (4-7-8 tekniği) ani stres anlarında saniyeler içinde etkili.",
        "Yazma terapisi — kaygıları kağıda dökmek zihnsel yükü hafifltiyor.",
        "Sosyal destek ağını aktive et — yalnız baş etmeye çalışma.",
    ],
    "uzun_vadeli": [
        "Stres günlüğü tut — örüntüleri fark et ve döngüyü kır.",
        "Evet demeden önce duraksama kapasitesi kazan.",
        "Mindfulness temelli stres azaltma (MBSR) 8 haftada ölçülebilir sonuç verir.",
    ],
}

STRES_EN = {
    "tetikleyici": [
        "Loss of control is your strongest stress trigger — systematic planning is a balancer.",
        "Uncertainty is your high stress source — clear goals reduce anxiety.",
        "Relationship conflicts contribute to your emotional stress load.",
        "Overload and task backlog increase chronic stress risk.",
    ],
    "basa_cikma": [
        "Physical exercise is the fastest method for lowering cortisol — prioritize it.",
        "Deep breathing (4-7-8 technique) is effective within seconds for acute stress.",
        "Writing therapy — putting worries on paper lightens mental load.",
        "Activate your social support network — don't try to cope alone.",
    ],
    "uzun_vadeli": [
        "Keep a stress journal — notice patterns and break the cycle.",
        "Develop the capacity to pause before saying yes.",
        "Mindfulness-Based Stress Reduction (MBSR) gives measurable results in 8 weeks.",
    ],
}

# ─── 8. ÖZGÜVEN ARTIRMA ──────────────────────────────────────────────────────
OZGUVEN_TR = {
    "mevcut_duzey": [
        "Yüksek öz farkındalık ve gerçekçi öz değerlendirme yeteneğin özgüveninin sağlam zemini.",
        "Dışsal onay ihtiyacın özgüven inşasının önündeki en büyük engel.",
        "Başarılarını küçümseme eğilimin (impostor sendromu) özgüvenini gölgeliyor.",
        "Güçlü değer sistemin özgüvene doğal bir katkı sağlıyor.",
    ],
    "pratik_adimlar": [
        "Her gün 3 küçük başarı yaz — beyin pozitif kanıt biriktirir.",
        "Güçlü yönlerini listele ve bunu görünür bir yerde tut.",
        "'Henüz değil' zihniyeti benimse — başarısızlık son değil, adım.",
        "Sosyal karşılaştırmayı azalt; kendi dünki halinle kıyasla.",
    ],
    "beden_dili": [
        "Güç pozu (power pose) — 2 dakika geniş duruş, kortizol düşer, testosteron artar.",
        "Göz teması kur — öz güveni hem hissettiren hem de yansıtan en etkili sinyal.",
        "Yürürken omuzları geri al, başı dik tut — beden zihni programlar.",
    ],
}

OZGUVEN_EN = {
    "mevcut_duzey": [
        "High self-awareness and realistic self-assessment are the solid foundation of your confidence.",
        "Need for external approval is the biggest barrier to building self-confidence.",
        "Tendency to downplay achievements (impostor syndrome) overshadows your confidence.",
        "Your strong value system naturally contributes to self-confidence.",
    ],
    "pratik_adimlar": [
        "Write 3 small wins daily — the brain accumulates positive evidence.",
        "List your strengths and keep it somewhere visible.",
        "Adopt a 'not yet' mindset — failure is not an endpoint, it's a step.",
        "Reduce social comparison; compare yourself to yesterday's you.",
    ],
    "beden_dili": [
        "Power pose — 2 minutes wide stance, cortisol drops, testosterone rises.",
        "Make eye contact — the most effective signal that both expresses and reflects self-confidence.",
        "Walk with shoulders back, head up — body programs the mind.",
    ],
}

# ─── 9. ZAMAN YÖNETİMİ ───────────────────────────────────────────────────────
ZAMAN_TR = {
    "stil": [
        "Planlı ve yapılandırılmış zaman yönetici — ajandan ve listeler yaşam tarzın.",
        "Akışa göre zaman yönetici — esneklik güçlü ama son dakika baskısı risk.",
        "Çoklu görev yapıcı — verimli görünür ama derin odak için zorlayıcı.",
        "Tek odak zaman yönetici — derin iş için ideal ama önceliklendirmede zorlanabilir.",
    ],
    "tekniker": [
        "Pomodoro (25+5) — derin çalışma seansları için kanıtlı yöntem.",
        "Zaman engelleme (time blocking) — günü bloklar halinde planla, geçişleri azalt.",
        "İki dakika kuralı — iki dakikadan kısa işleri hemen yap, listeye ekleme.",
        "Sabah ritüeli — gün planını akşamdan yap, sabah enerjiyi ürete harca.",
    ],
    "tuzaklar": [
        "Mükemmeliyetçilik ertelemenin en büyük kaynağı — 'iyi yeterli' felsefesi benimse.",
        "Acil ≠ Önemli — Eisenhower matrisi ile önceliklendir.",
        "Dijital dikkat dağıtıcılar — telefonu 90 dakikalık oturumlar boyunca uzak tut.",
    ],
}

ZAMAN_EN = {
    "stil": [
        "Planned and structured time manager — agendas and lists are your lifestyle.",
        "Flow-based time manager — flexibility is strong but last-minute pressure is a risk.",
        "Multi-task doer — appears efficient but challenging for deep focus.",
        "Single-focus time manager — ideal for deep work but may struggle with prioritization.",
    ],
    "tekniker": [
        "Pomodoro (25+5) — proven method for deep work sessions.",
        "Time blocking — plan the day in blocks, reduce transitions.",
        "Two-minute rule — do tasks under two minutes immediately, don't add to list.",
        "Morning ritual — plan the day the evening before, spend morning energy on creation.",
    ],
    "tuzaklar": [
        "Perfectionism is the biggest source of procrastination — adopt 'good enough' philosophy.",
        "Urgent ≠ Important — prioritize with the Eisenhower matrix.",
        "Digital distractions — keep phone away during 90-minute work sessions.",
    ],
}

# ─── 10. KİŞİSEL GELİŞİM HEDEFLERİ ──────────────────────────────────────────
HEDEF_TR = {
    "kisa_vadeli": [
        "30 günlük alışkanlık devrimi: her gün tek küçük eylem.",
        "Güçlü yönün listesini hazırla ve haftada bir güncelle.",
        "Geribildirim döngüsü oluştur: güvendiğin 3 kişiden aylık geri bildirim iste.",
    ],
    "orta_vadeli": [
        "12 ay içinde uzmanlık alanında sertifika veya ölçülebilir yetkinlik hedefle.",
        "Mentörlük ilişkisi kur — hem öğrenen hem de öğreten ol.",
        "Kişisel marka inşası: değerlerini yansıtan dijital varlık oluştur.",
    ],
    "uzun_vadeli": [
        "5 yıllık vizyon haritası çiz — her yıl güncelle.",
        "Mirası oluştur: çevrendeki 1 kişinin hayatını anlamlı biçimde değiştir.",
        "Öğrenme kültürü: yılda minimum 12 kitap, 2 kurs, 1 büyük proje.",
    ],
    "engeller": [
        "Korku değil, merak hedef yolculuğunun pusulanız olsun.",
        "Sosyal çevre etkisi: hedeflerinle örtüşen insanları çevren kur.",
        "İlerlemeyi kutla — küçük kazanımlar büyük motivasyon kaynağı.",
    ],
}

HEDEF_EN = {
    "kisa_vadeli": [
        "30-day habit revolution: one small action every day.",
        "Prepare your strengths list and update it weekly.",
        "Build a feedback loop: ask 3 trusted people for monthly feedback.",
    ],
    "orta_vadeli": [
        "Target a certificate or measurable competency in your expertise within 12 months.",
        "Build a mentorship relationship — be both learner and teacher.",
        "Personal brand building: create a digital presence that reflects your values.",
    ],
    "uzun_vadeli": [
        "Draw a 5-year vision map — update it every year.",
        "Build your legacy: meaningfully change 1 person's life in your circle.",
        "Learning culture: minimum 12 books, 2 courses, 1 big project per year.",
    ],
    "engeller": [
        "Let curiosity, not fear, be the compass of your goal journey.",
        "Social circle effect: surround yourself with people aligned with your goals.",
        "Celebrate progress — small wins are a major motivation source.",
    ],
}

# ─── 11. ASTROLOJİ HARİTASI ──────────────────────────────────────────────────
ASTROLOJI_HARITA_TR = {
    "aciklama": (
        "Bu modül kullanıcının doğum tarihi ve saati girildiğinde "
        "Facesyma yüz analizi verileriyle desteklenmiş kişisel astroloji haritası üretir."
    ),
    "elementler": {
        "ates": ["Koç", "Aslan", "Yay"],
        "toprak": ["Boğa", "Başak", "Oğlak"],
        "hava": ["İkizler", "Terazi", "Kova"],
        "su": ["Yengeç", "Akrep", "Balık"],
    },
    "planet_etkileri": {
        "güneş": "Ego, kimlik, yaşam amacı",
        "ay": "Duygular, iç dünya, alışkanlıklar",
        "merkür": "İletişim, düşünce, öğrenme",
        "venüs": "Aşk, estetik, değerler",
        "mars": "Eylem, istek, öfke yönetimi",
        "jüpiter": "Büyüme, şans, bilgelik",
        "satürn": "Sorumluluk, disiplin, sınırlar",
    },
    "yorumlar": [
        "Yüz analizindeki {sifat} özelliğin {burç} enerjisiyle güçlü rezonans taşıyor.",
        "Güneş burcun ile yüz analizindeki dominant özellikler arasındaki uyum olağandışı.",
        "Doğum haritanın {ev}. evi vurgusu yüz analizindeki {sifat} ile destekleniyor.",
        "Natal Venus pozisyonunun ilişki modülüyle örtüşmesi dikkat çekici.",
    ],
}

ASTROLOJI_HARITA_EN = {
    "aciklama": (
        "This module generates a personal astrology chart enhanced with Facesyma "
        "face analysis data when the user's birth date and time are entered."
    ),
    "elementler": {
        "fire": ["Aries", "Leo", "Sagittarius"],
        "earth": ["Taurus", "Virgo", "Capricorn"],
        "air": ["Gemini", "Libra", "Aquarius"],
        "water": ["Cancer", "Scorpio", "Pisces"],
    },
    "planet_etkileri": {
        "sun":     "Ego, identity, life purpose",
        "moon":    "Emotions, inner world, habits",
        "mercury": "Communication, thought, learning",
        "venus":   "Love, aesthetics, values",
        "mars":    "Action, desire, anger management",
        "jupiter": "Growth, luck, wisdom",
        "saturn":  "Responsibility, discipline, boundaries",
    },
    "yorumlar": [
        "Your {sifat} trait from face analysis carries strong resonance with {sign} energy.",
        "The alignment between your sun sign and the dominant traits in your face analysis is remarkable.",
        "The emphasis on house {house} in your natal chart is supported by {sifat} in the face analysis.",
        "The overlap of natal Venus position with the relationship module is noteworthy.",
    ],
}

# ─── 12. DOĞUM TARİHİ / SAATİ ANALİZİ ───────────────────────────────────────
DOGUM_ANALIZI_TR = {
    "aciklama": "Doğum tarihi, saati ve yeri girildiğinde hesaplanır.",
    "numeroloji": {
        "hayat_yolu": "En temel kişilik sayısı — doğum tarihi rakamları toplamı",
        "kader": "Adın harflerinin sayısal karşılıkları",
        "ruh_urtu": "Adındaki sesli harflerin toplamı",
        "kisilik": "Adındaki ünsüz harflerin toplamı",
    },
    "saatlik_enerji": {
        "01-06": "Sezgisel, manevi — içe dönük enerji saatleri",
        "07-11": "Yaratıcı, başlangıç — yeni projelere başlamak için ideal",
        "12-17": "Sosyal, işbirlikçi — ekip çalışması ve görüşmeler için ideal",
        "18-23": "Analitik, planlayıcı — değerlendirme ve strateji için ideal",
        "00-01": "Dönüşümsel — derin kararlar için güçlü an",
    },
    "mevsim_etkisi": {
        "ilkbahar": "Koç-İkizler — başlangıç, merak, dinamizm",
        "yaz":      "Yengeç-Başak — duygu, analiz, mükemmeliyetçilik",
        "sonbahar": "Terazi-Yay — denge, adalet, büyüme",
        "kış":      "Oğlak-Balık — disiplin, sezgi, tamamlanma",
    },
}

DOGUM_ANALIZI_EN = {
    "aciklama": "Calculated when birth date, time and location are entered.",
    "numeroloji": {
        "life_path":    "Most basic personality number — sum of birth date digits",
        "destiny":      "Numerical values of name letters",
        "soul_urge":    "Sum of vowels in your name",
        "personality":  "Sum of consonants in your name",
    },
    "saatlik_enerji": {
        "01-06": "Intuitive, spiritual — hours of introverted energy",
        "07-11": "Creative, initiating — ideal for starting new projects",
        "12-17": "Social, collaborative — ideal for teamwork and meetings",
        "18-23": "Analytical, planning — ideal for assessment and strategy",
        "00-01": "Transformational — a powerful moment for deep decisions",
    },
    "mevsim_etkisi": {
        "spring": "Aries-Gemini — initiation, curiosity, dynamism",
        "summer": "Cancer-Virgo — emotion, analysis, perfectionism",
        "autumn": "Libra-Sagittarius — balance, justice, growth",
        "winter": "Capricorn-Pisces — discipline, intuition, completion",
    },
}

# ─── 13. YAŞAM KOÇU GENEL ÖZET ───────────────────────────────────────────────
KOC_OZET_TR = {
    "giriş": [
        "Facesyma yüz analizi ve yaşam koçu verileri entegre edildiğinde ortaya çıkan profil:",
        "Yüzündeki özellikler ve yaşam koçu değerlendirmesi şu genel tabloyu ortaya koyuyor:",
    ],
    "alanlar": [
        "🧠 Zihinsel Alan: Analitik kapasite güçlü, duygusal entegrasyon gelişim alanı",
        "❤️ Duygusal Alan: Empati yüksek, sınır koyma gelişim alanı",
        "💼 Kariyer Alanı: Liderlik potansiyeli var, görünürlük artırılmalı",
        "🌿 Sağlık Alanı: Stres yönetimi öncelikli, fiziksel ritüeller güçlendirilmeli",
        "🤝 İlişki Alanı: Derin bağlar için doğal yetenek, koşulsuzluk gelişim alanı",
        "🎯 Amaç Alanı: Vizyon net, eylem planı somutlaştırılmalı",
    ],
    "eylem_plani": [
        "Bu hafta: Güçlü yönler listesi oluştur ve 1 küçük eylem başlat.",
        "Bu ay: Stres tetikleyicilerini belirle ve baş etme stratejisi geliştir.",
        "Bu yıl: Kişisel vizyonunu yaz ve mentörlük ilişkisi kur.",
    ],
}

KOC_OZET_EN = {
    "giriş": [
        "The profile that emerges when Facesyma face analysis and life coach data are integrated:",
        "Your facial features and life coach assessment reveal the following overall picture:",
    ],
    "alanlar": [
        "🧠 Mental Domain: Analytical capacity strong, emotional integration is a growth area",
        "❤️ Emotional Domain: Empathy high, boundary setting is a growth area",
        "💼 Career Domain: Leadership potential exists, visibility needs to be increased",
        "🌿 Health Domain: Stress management is a priority, physical rituals need strengthening",
        "🤝 Relationship Domain: Natural talent for deep bonds, unconditional love is a growth area",
        "🎯 Purpose Domain: Vision is clear, action plan needs to be concretized",
    ],
    "eylem_plani": [
        "This week: Build a strengths list and start 1 small action.",
        "This month: Identify stress triggers and develop coping strategies.",
        "This year: Write your personal vision and build a mentorship relationship.",
    ],
}

# ─── 14. BEDEN DİLİ ANALİZİ ──────────────────────────────────────────────────
VUCUT_DIL_TR = {
    "yuz_ifadesi": [
        "Kaş yapısı otoriteyi destekliyor — kararlılık ilk izlenimde algılanıyor.",
        "Gözlerdeki yumuşaklık sıcaklık ve güven iletişimini güçlendiriyor.",
        "Çene hattı irade gücünü yansıtıyor — liderlik mesajını destekliyor.",
        "Dudak hatları ifade zenginliğini gösteriyor — duygusal iletişim güçlü.",
    ],
    "postür_tavsiye": [
        "Dinlerken hafifçe öne eğil — ilgi ve saygı mesajı verir.",
        "Kolları açık tut — savunmacı olmayan, davetkar bir beden dili.",
        "Yüz ifadesi ve sözcükler uyumlu olduğunda güvenilirlik artar.",
    ],
    "profesyonel": [
        "İş görüşmelerinde ilk 7 saniyede kurulan göz teması belirleyici.",
        "El sıkışmada orta sertlik ve 2-3 saniyelik süre güven iletir.",
        "Sunum yaparken hareketli eller mesajı güçlendirir — donuk duruş zayıflatır.",
    ],
}

VUCUT_DIL_EN = {
    "yuz_ifadesi": [
        "Brow structure supports authority — decisiveness is perceived in first impressions.",
        "Softness in the eyes strengthens warmth and trust communication.",
        "Jaw line reflects strength of will — supports the leadership message.",
        "Lip lines show expressive richness — emotional communication is strong.",
    ],
    "postür_tavsiye": [
        "Lean slightly forward when listening — conveys interest and respect.",
        "Keep arms open — non-defensive, inviting body language.",
        "When facial expression and words are aligned, credibility increases.",
    ],
    "profesyonel": [
        "In job interviews, eye contact established in the first 7 seconds is decisive.",
        "In handshakes, medium firmness and 2-3 second duration conveys confidence.",
        "Moving hands when presenting strengthens the message — rigid posture weakens it.",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Dil desteği — 18 dil için başlık map
# ─────────────────────────────────────────────────────────────────────────────
MODULE_NAMES = {
    "tr": {
        "saglik_esenwlik":     "Sağlık ve Esenlik",
        "dogruluk_sadakat":    "Doğruluk ve Sadakat",
        "guvenlik":            "Güvenlik Profili",
        "suc_egilim":          "Risk Analizi",
        "iliski_yonetimi":     "İlişki Yönetimi",
        "iletisim_becerileri": "İletişim Becerileri",
        "stres_yonetimi":      "Stres Yönetimi",
        "ozguven":             "Özgüven Artırma",
        "zaman_yonetimi":      "Zaman Yönetimi",
        "kisisel_hedefler":    "Kişisel Gelişim Hedefleri",
        "astroloji_harita":    "Astroloji Haritası",
        "dogum_analizi":       "Doğum Analizi",
        "yas_koc_ozet":        "Yaşam Koçu Özeti",
        "vucut_dil":           "Beden Dili Analizi",
    },
    "en": {
        "saglik_esenwlik":     "Health & Wellbeing",
        "dogruluk_sadakat":    "Truthfulness & Loyalty",
        "guvenlik":            "Security Profile",
        "suc_egilim":          "Risk Analysis",
        "iliski_yonetimi":     "Relationship Management",
        "iletisim_becerileri": "Communication Skills",
        "stres_yonetimi":      "Stress Management",
        "ozguven":             "Confidence Building",
        "zaman_yonetimi":      "Time Management",
        "kisisel_hedefler":    "Personal Growth Goals",
        "astroloji_harita":    "Astrology Chart",
        "dogum_analizi":       "Birth Analysis",
        "yas_koc_ozet":        "Life Coach Summary",
        "vucut_dil":           "Body Language Analysis",
    },
    "de": {
        "saglik_esenwlik":     "Gesundheit & Wohlbefinden",
        "dogruluk_sadakat":    "Wahrhaftigkeit & Treue",
        "guvenlik":            "Sicherheitsprofil",
        "suc_egilim":          "Risikoanalyse",
        "iliski_yonetimi":     "Beziehungsmanagement",
        "iletisim_becerileri": "Kommunikationsfahigkeiten",
        "stres_yonetimi":      "Stressmanagement",
        "ozguven":             "Selbstvertrauen starken",
        "zaman_yonetimi":      "Zeitmanagement",
        "kisisel_hedefler":    "Personliche Entwicklungsziele",
        "astroloji_harita":    "Astrologie-Karte",
        "dogum_analizi":       "Geburtsanalyse",
        "yas_koc_ozet":        "Lebenscoach-Zusammenfassung",
        "vucut_dil":           "Korpersprachenanalyse",
    },
    "ru": {
        "saglik_esenwlik":     "Здоровье и благополучие",
        "dogruluk_sadakat":    "Честность и верность",
        "guvenlik":            "Профиль безопасности",
        "suc_egilim":          "Анализ рисков",
        "iliski_yonetimi":     "Управление отношениями",
        "iletisim_becerileri": "Коммуникативные навыки",
        "stres_yonetimi":      "Управление стрессом",
        "ozguven":             "Повышение уверенности",
        "zaman_yonetimi":      "Управление временем",
        "kisisel_hedefler":    "Цели личностного роста",
        "astroloji_harita":    "Астрологическая карта",
        "dogum_analizi":       "Анализ рождения",
        "yas_koc_ozet":        "Резюме жизненного коуча",
        "vucut_dil":           "Анализ языка тела",
    },
    "ar": {
        "saglik_esenwlik":     "الصحة والعافية",
        "dogruluk_sadakat":    "الصدق والولاء",
        "guvenlik":            "ملف الأمان",
        "suc_egilim":          "تحليل المخاطر",
        "iliski_yonetimi":     "إدارة العلاقات",
        "iletisim_becerileri": "مهارات التواصل",
        "stres_yonetimi":      "إدارة الضغط",
        "ozguven":             "تعزيز الثقة بالنفس",
        "zaman_yonetimi":      "إدارة الوقت",
        "kisisel_hedefler":    "أهداف التطوير الشخصي",
        "astroloji_harita":    "خريطة الأبراج",
        "dogum_analizi":       "تحليل الولادة",
        "yas_koc_ozet":        "ملخص مدرب الحياة",
        "vucut_dil":           "تحليل لغة الجسد",
    },
    "es": {
        "saglik_esenwlik":     "Salud y bienestar",
        "dogruluk_sadakat":    "Veracidad y lealtad",
        "guvenlik":            "Perfil de seguridad",
        "suc_egilim":          "Analisis de riesgo",
        "iliski_yonetimi":     "Gestion de relaciones",
        "iletisim_becerileri": "Habilidades de comunicacion",
        "stres_yonetimi":      "Gestion del estres",
        "ozguven":             "Desarrollo de la autoconfianza",
        "zaman_yonetimi":      "Gestion del tiempo",
        "kisisel_hedefler":    "Metas de crecimiento personal",
        "astroloji_harita":    "Carta astrologica",
        "dogum_analizi":       "Analisis natal",
        "yas_koc_ozet":        "Resumen del coach de vida",
        "vucut_dil":           "Analisis del lenguaje corporal",
    },
    "ko": {
        "saglik_esenwlik":     "건강과 웰빙",
        "dogruluk_sadakat":    "진실성과 충실함",
        "guvenlik":            "보안 프로필",
        "suc_egilim":          "위험 분석",
        "iliski_yonetimi":     "관계 관리",
        "iletisim_becerileri": "의사소통 기술",
        "stres_yonetimi":      "스트레스 관리",
        "ozguven":             "자신감 향상",
        "zaman_yonetimi":      "시간 관리",
        "kisisel_hedefler":    "개인 성장 목표",
        "astroloji_harita":    "점성술 차트",
        "dogum_analizi":       "출생 분석",
        "yas_koc_ozet":        "라이프 코치 요약",
        "vucut_dil":           "바디 랭귀지 분석",
    },
    "ja": {
        "saglik_esenwlik":     "健康とウェルビーイング",
        "dogruluk_sadakat":    "誠実さと忠実さ",
        "guvenlik":            "セキュリティプロフィール",
        "suc_egilim":          "リスク分析",
        "iliski_yonetimi":     "関係管理",
        "iletisim_becerileri": "コミュニケーションスキル",
        "stres_yonetimi":      "ストレス管理",
        "ozguven":             "自己肯定感向上",
        "zaman_yonetimi":      "時間管理",
        "kisisel_hedefler":    "個人成長目標",
        "astroloji_harita":    "占星術チャート",
        "dogum_analizi":       "誕生分析",
        "yas_koc_ozet":        "ライフコーチサマリー",
        "vucut_dil":           "ボディランゲージ分析",
    },
}

# Diğer 10 dil için kısa isimler (EN fallback ile)
for lang in ["zh","hi","fr","pt","bn","id","ur","it","vi","pl"]:
    MODULE_NAMES[lang] = MODULE_NAMES["en"]


# ─────────────────────────────────────────────────────────────────────────────
# Sıfat bazlı veri üretici
# ─────────────────────────────────────────────────────────────────────────────
def generate_coach_entry(sifat: str, existing: dict, lang: str) -> dict:
    """
    Mevcut bir sıfat girişine 14 yeni yaşam koçu modülü ekler.
    Mevcut veriye DOKUNMAZ — yeni modülleri ayrı dict olarak döner.
    """
    is_tr = (lang == "tr")

    # Sıfatın kişilik yönünü tahmin et (basit kural tabanlı)
    pos_keywords = ["açık","sıcak","güçlü","analitik","dürüst","kararlı","empati","sakin","dengeli"]
    neg_keywords = ["aceleci","saldırgan","kontrolcü","kaçınma","gergin","kaygı"]
    is_positive = any(k in sifat.lower() for k in pos_keywords)

    def pick(*lists):
        combined = [item for lst in lists for item in lst]
        return random.choice(combined) if combined else ""

    if is_tr:
        entry = {
            "saglik_esenwlik": "\n".join([
                "🌿 Güçlü Yönler",
                *_pick(SAGLIK_TR["pozitif"], 2),
                "\n📈 Gelişim Alanları",
                *_pick(SAGLIK_TR["gelisim"], 2),
                "\n⚠️ Dikkat",
                *_pick(SAGLIK_TR["risk"], 1),
                "\n✅ Pratik Adımlar",
                *_pick(SAGLIK_TR["pratik"], 2),
            ]),
            "dogruluk_sadakat": "\n".join([
                "🔍 Profil",
                *_pick(DOGRULUK_TR["profil"], 1),
                "\n💪 Güçlü Yönler",
                *_pick(DOGRULUK_TR["guclu"], 2),
                "\n⚠️ Dikkat",
                *_pick(DOGRULUK_TR["dikkat"], 1),
            ]),
            "guvenlik": "\n".join([
                "🛡️ Kişisel Güvenlik",
                *_pick(GUVENLIK_TR["kisisel"], 1),
                "\n💙 Duygusal Güvenlik",
                *_pick(GUVENLIK_TR["duygusal"], 1),
                "\n💰 Finansal Güvenlik",
                *_pick(GUVENLIK_TR["finansal"], 1),
                "\n✅ Tavsiyeler",
                *_pick(GUVENLIK_TR["tavsiye"], 2),
            ]),
            "suc_egilim": "\n".join([
                "📊 Risk Profili",
                *_pick(SUC_EGILIM_TR["risk_alma"], 1),
                "\n🛡️ Koruyucu Faktörler",
                *_pick(SUC_EGILIM_TR["koruyucu"], 2),
                "\n💡 Tavsiyeler",
                *_pick(SUC_EGILIM_TR["tavsiye"], 1),
                f"\n⚕️ Not: {SUC_EGILIM_TR['profesyonel_not']}",
            ]),
            "iliski_yonetimi": "\n".join([
                "💑 İlişki Stili",
                *_pick(ILISKI_TR["stil"], 1),
                "\n💪 Güçlü Yönler",
                *_pick(ILISKI_TR["guclu"], 2),
                "\n⚠️ Zorluklar",
                *_pick(ILISKI_TR["zorluk"], 1),
                "\n✅ Tavsiyeler",
                *_pick(ILISKI_TR["tavsiye"], 2),
            ]),
            "iletisim_becerileri": "\n".join([
                "🗣️ İletişim Stili",
                *_pick(ILETISIM_TR["stil"], 1),
                "\n💪 Güçlü Yönler",
                *_pick(ILETISIM_TR["guclu"], 2),
                "\n📈 Gelişim Adımları",
                *_pick(ILETISIM_TR["gelisim"], 2),
                "\n💻 Dijital İletişim",
                *_pick(ILETISIM_TR["dijital"], 1),
            ]),
            "stres_yonetimi": "\n".join([
                "🔴 Tetikleyiciler",
                *_pick(STRES_TR["tetikleyici"], 2),
                "\n💚 Başa Çıkma Yöntemleri",
                *_pick(STRES_TR["basa_cikma"], 2),
                "\n🔵 Uzun Vadeli Stratejiler",
                *_pick(STRES_TR["uzun_vadeli"], 1),
            ]),
            "ozguven": "\n".join([
                "📊 Mevcut Düzey",
                *_pick(OZGUVEN_TR["mevcut_duzey"], 1),
                "\n🎯 Pratik Adımlar",
                *_pick(OZGUVEN_TR["pratik_adimlar"], 2),
                "\n🧍 Beden Dili",
                *_pick(OZGUVEN_TR["beden_dili"], 1),
            ]),
            "zaman_yonetimi": "\n".join([
                "⏰ Zaman Stili",
                *_pick(ZAMAN_TR["stil"], 1),
                "\n🛠️ Teknikler",
                *_pick(ZAMAN_TR["tekniker"], 2),
                "\n⚠️ Tuzaklar",
                *_pick(ZAMAN_TR["tuzaklar"], 1),
            ]),
            "kisisel_hedefler": "\n".join([
                "🎯 Kısa Vadeli (1-3 ay)",
                *_pick(HEDEF_TR["kisa_vadeli"], 1),
                "\n📅 Orta Vadeli (3-12 ay)",
                *_pick(HEDEF_TR["orta_vadeli"], 1),
                "\n🚀 Uzun Vadeli (1-5 yıl)",
                *_pick(HEDEF_TR["uzun_vadeli"], 1),
                "\n💪 Engelleri Aşmak",
                *_pick(HEDEF_TR["engeller"], 1),
            ]),
            "astroloji_harita": "\n".join([
                f"ℹ️ {ASTROLOJI_HARITA_TR['aciklama']}",
                "\n🪐 Gezegen Etkileri",
                *[f"• {k.capitalize()}: {v}" for k, v in ASTROLOJI_HARITA_TR["planet_etkileri"].items()],
                "\n🔮 Yorumlar",
                *_pick(ASTROLOJI_HARITA_TR["yorumlar"], 2),
            ]),
            "dogum_analizi": "\n".join([
                f"ℹ️ {DOGUM_ANALIZI_TR['aciklama']}",
                "\n🔢 Numeroloji",
                *[f"• {k}: {v}" for k, v in DOGUM_ANALIZI_TR["numeroloji"].items()],
                "\n⏰ Doğum Saati Enerjisi",
                *[f"• {k}: {v}" for k, v in DOGUM_ANALIZI_TR["saatlik_enerji"].items()],
            ]),
            "yas_koc_ozet": "\n".join([
                *_pick(KOC_OZET_TR["giriş"], 1),
                "\n📊 Yaşam Alanları",
                *KOC_OZET_TR["alanlar"],
                "\n🎯 Eylem Planı",
                *KOC_OZET_TR["eylem_plani"],
            ]),
            "vucut_dil": "\n".join([
                "😊 Yüz İfadesi",
                *_pick(VUCUT_DIL_TR["yuz_ifadesi"], 2),
                "\n🧍 Postür Tavsiyeleri",
                *_pick(VUCUT_DIL_TR["postür_tavsiye"], 2),
                "\n💼 Profesyonel Ortam",
                *_pick(VUCUT_DIL_TR["profesyonel"], 2),
            ]),
        }
    else:
        # EN (diğer tüm diller EN şablonla üretilir, daha sonra çeviri API ile çevrilir)
        entry = {
            "saglik_esenwlik": "\n".join([
                "🌿 Strengths", *_pick(SAGLIK_EN["pozitif"], 2),
                "\n📈 Growth Areas", *_pick(SAGLIK_EN["gelisim"], 2),
                "\n⚠️ Watch Out", *_pick(SAGLIK_EN["risk"], 1),
                "\n✅ Practical Steps", *_pick(SAGLIK_EN["pratik"], 2),
            ]),
            "dogruluk_sadakat": "\n".join([
                "🔍 Profile", *_pick(DOGRULUK_EN["profil"], 1),
                "\n💪 Strengths", *_pick(DOGRULUK_EN["guclu"], 2),
                "\n⚠️ Watch Out", *_pick(DOGRULUK_EN["dikkat"], 1),
            ]),
            "guvenlik": "\n".join([
                "🛡️ Personal Security", *_pick(GUVENLIK_EN["kisisel"], 1),
                "\n💙 Emotional Security", *_pick(GUVENLIK_EN["duygusal"], 1),
                "\n💰 Financial Security", *_pick(GUVENLIK_EN["finansal"], 1),
                "\n✅ Recommendations", *_pick(GUVENLIK_EN["tavsiye"], 2),
            ]),
            "suc_egilim": "\n".join([
                "📊 Risk Profile", *_pick(SUC_EGILIM_EN["risk_alma"], 1),
                "\n🛡️ Protective Factors", *_pick(SUC_EGILIM_EN["koruyucu"], 2),
                "\n💡 Recommendations", *_pick(SUC_EGILIM_EN["tavsiye"], 1),
                f"\n⚕️ Note: {SUC_EGILIM_EN['profesyonel_not']}",
            ]),
            "iliski_yonetimi": "\n".join([
                "💑 Relationship Style", *_pick(ILISKI_EN["stil"], 1),
                "\n💪 Strengths", *_pick(ILISKI_EN["guclu"], 2),
                "\n⚠️ Challenges", *_pick(ILISKI_EN["zorluk"], 1),
                "\n✅ Recommendations", *_pick(ILISKI_EN["tavsiye"], 2),
            ]),
            "iletisim_becerileri": "\n".join([
                "🗣️ Communication Style", *_pick(ILETISIM_EN["stil"], 1),
                "\n💪 Strengths", *_pick(ILETISIM_EN["guclu"], 2),
                "\n📈 Growth Steps", *_pick(ILETISIM_EN["gelisim"], 2),
                "\n💻 Digital Communication", *_pick(ILETISIM_EN["dijital"], 1),
            ]),
            "stres_yonetimi": "\n".join([
                "🔴 Triggers", *_pick(STRES_EN["tetikleyici"], 2),
                "\n💚 Coping Methods", *_pick(STRES_EN["basa_cikma"], 2),
                "\n🔵 Long-Term Strategies", *_pick(STRES_EN["uzun_vadeli"], 1),
            ]),
            "ozguven": "\n".join([
                "📊 Current Level", *_pick(OZGUVEN_EN["mevcut_duzey"], 1),
                "\n🎯 Practical Steps", *_pick(OZGUVEN_EN["pratik_adimlar"], 2),
                "\n🧍 Body Language", *_pick(OZGUVEN_EN["beden_dili"], 1),
            ]),
            "zaman_yonetimi": "\n".join([
                "⏰ Time Style", *_pick(ZAMAN_EN["stil"], 1),
                "\n🛠️ Techniques", *_pick(ZAMAN_EN["tekniker"], 2),
                "\n⚠️ Pitfalls", *_pick(ZAMAN_EN["tuzaklar"], 1),
            ]),
            "kisisel_hedefler": "\n".join([
                "🎯 Short-Term (1-3 months)", *_pick(HEDEF_EN["kisa_vadeli"], 1),
                "\n📅 Mid-Term (3-12 months)", *_pick(HEDEF_EN["orta_vadeli"], 1),
                "\n🚀 Long-Term (1-5 years)", *_pick(HEDEF_EN["uzun_vadeli"], 1),
                "\n💪 Overcoming Barriers", *_pick(HEDEF_EN["engeller"], 1),
            ]),
            "astroloji_harita": "\n".join([
                f"ℹ️ {ASTROLOJI_HARITA_EN['aciklama']}",
                "\n🪐 Planetary Influences",
                *[f"• {k.capitalize()}: {v}" for k, v in ASTROLOJI_HARITA_EN["planet_etkileri"].items()],
                "\n🔮 Interpretations",
                *_pick(ASTROLOJI_HARITA_EN["yorumlar"], 2),
            ]),
            "dogum_analizi": "\n".join([
                f"ℹ️ {DOGUM_ANALIZI_EN['aciklama']}",
                "\n🔢 Numerology",
                *[f"• {k}: {v}" for k, v in DOGUM_ANALIZI_EN["numeroloji"].items()],
                "\n⏰ Birth Time Energy",
                *[f"• {k}: {v}" for k, v in DOGUM_ANALIZI_EN["saatlik_enerji"].items()],
            ]),
            "yas_koc_ozet": "\n".join([
                *_pick(KOC_OZET_EN["giriş"], 1),
                "\n📊 Life Domains",
                *KOC_OZET_EN["alanlar"],
                "\n🎯 Action Plan",
                *KOC_OZET_EN["eylem_plani"],
            ]),
            "vucut_dil": "\n".join([
                "😊 Facial Expression", *_pick(VUCUT_DIL_EN["yuz_ifadesi"], 2),
                "\n🧍 Posture Recommendations", *_pick(VUCUT_DIL_EN["postür_tavsiye"], 2),
                "\n💼 Professional Setting", *_pick(VUCUT_DIL_EN["profesyonel"], 2),
            ]),
        }

    return entry


# ─────────────────────────────────────────────────────────────────────────────
# Ana üretici
# ─────────────────────────────────────────────────────────────────────────────
def generate_full_coach_db(
    input_path:  Path,
    output_path: Path,
    lang:        str = "tr",
) -> dict:
    """
    Mevcut sifat_veritabani.json'u okur,
    her sıfata 14 yeni modül ekler,
    yeni bir JSON dosyasına yazar (orijinale dokunmaz).
    """
    with open(input_path, encoding="utf-8") as f:
        source_db = json.load(f)

    print(f"Kaynak: {len(source_db)} sıfat okundu")
    print(f"Dil: {lang} | Çıktı: {output_path}")

    coach_db = {}
    for i, (sifat, data) in enumerate(source_db.items()):
        # Mevcut modülleri koru
        merged = copy.deepcopy(data)
        # Yeni koç modüllerini ekle
        coach_modules = generate_coach_entry(sifat, data, lang)
        merged.update(coach_modules)
        coach_db[sifat] = merged

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(source_db)} sıfat işlendi...")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(coach_db, f, ensure_ascii=False, indent=2)

    print(f"\nTamamlandı: {len(coach_db)} sıfat, {len(list(coach_db.values())[0])} modül")
    print(f"Çıktı: {output_path}")
    return coach_db


# ─────────────────────────────────────────────────────────────────────────────
# MongoDB push — backup DB'ye yaz
# ─────────────────────────────────────────────────────────────────────────────
def push_to_backup_mongodb(
    coach_db:  dict,
    lang:      str,
    mongo_uri: str,
):
    """
    Üretilen veriyi facesyma-coach-backup DB'ye yazar.
    Mevcut facesyma-backend DB'ye DOKUNMAZ.

    Koleksiyon adları: coach_attributes_tr, coach_attributes_en, vb.
    """
    try:
        from pymongo import MongoClient, UpdateOne
    except ImportError:
        print("HATA: pymongo kurulu değil — pip install pymongo")
        return

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=8000)
    # ── BACKUP veritabanı — mevcut DB değil ──────────────────────────────────
    db   = client["facesyma-coach-backup"]
    col  = db[f"coach_attributes_{lang}"]

    ops = [
        UpdateOne(
            {"_id": sifat},
            {"$set": {**data, "_id": sifat, "lang": lang,
                      "updated_at": datetime.now().isoformat()}},
            upsert=True,
        )
        for sifat, data in coach_db.items()
    ]

    if ops:
        result = col.bulk_write(ops)
        print(f"MongoDB backup: {result.upserted_count} eklendi, "
              f"{result.modified_count} güncellendi — "
              f"DB: facesyma-coach-backup, Koleksiyon: coach_attributes_{lang}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(
        description="Facesyma koç veri seti üreticisi — 14 yeni modül, 18 dil"
    )
    p.add_argument("--input",  default="../facesyma_migrate/sifat_veritabani.json")
    p.add_argument("--output", default="sifat_coach_{lang}.json")
    p.add_argument("--lang",   default="tr",
                   choices=["tr","en","de","ru","ar","es","ko","ja",
                            "zh","hi","fr","pt","bn","id","ur","it","vi","pl"])
    p.add_argument("--all-langs",  action="store_true", help="Tüm dilleri üret")
    p.add_argument("--push-mongo", action="store_true", help="MongoDB backup'a yaz")
    p.add_argument("--mongo-uri",
                   default="mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/"
                           "myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE")
    args = p.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"HATA: {input_path} bulunamadı")
        sys.exit(1)

    langs = (["tr","en","de","ru","ar","es","ko","ja","zh","hi","fr","pt","bn","id","ur","it","vi","pl"]
             if args.all_langs else [args.lang])

    for lang in langs:
        out = Path(args.output.replace("{lang}", lang))
        db  = generate_full_coach_db(input_path, out, lang)

        if args.push_mongo:
            push_to_backup_mongodb(db, lang, args.mongo_uri)

    print("\n✓ Tüm işlemler tamamlandı")
    if not args.push_mongo:
        print("\nMongoDB'ye yazmak için:")
        print("  python generate_coach_dataset.py --push-mongo")


if __name__ == "__main__":
    main()
