"""5 new game views: Wordle, Speed Match, Community Poll, Memory Cards, Spin Wheel."""
import json
import hashlib
import random
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from admin_api.utils.mongo import _get_db
from gamification.views import _require_user, _add_coins, _add_xp
from gamification.services.badge_service import BadgeService


# ── shared helpers ─────────────────────────────────────────────────────────────

def _today() -> str:
    return datetime.utcnow().strftime('%Y-%m-%d')


# ── SIFAT POOL ─────────────────────────────────────────────────────────────────

SIFAT_POOL = [
    {
        'id': 'analitik',
        'sifat': 'Analitik',
        'emoji': '🔬',
        'hints': [
            'Bu kişilik tipi sorunları parçalara ayırarak çözer',
            'Yüksek alın bu sıfatla ilişkilendirilir',
            'Duygulardan çok veriye güvenir',
            'Sistematik ve metodolojik düşünür',
            'Bir bilim insanı ya da mühendisi tanımlar',
            'Kelime: "veri odaklı" ile eşanlamlı',
        ],
        'wrong_options': ['Empatik', 'Sosyal', 'Romantik', 'Enerjik'],
    },
    {
        'id': 'empatik',
        'sifat': 'Empatik',
        'emoji': '💛',
        'hints': [
            'Başkalarının duygularını hisseder',
            'Büyük, ifadeli gözlerle ilişkilendirilir',
            'İnsanlarla derin bağ kurar',
            'Bir terapist ya da hemşireyi tanımlar',
            'Karşısındakinin acısını kendi içinde yaşar',
            'Kelime: "anlayış" ile eşanlamlı',
        ],
        'wrong_options': ['Analitik', 'Baskın', 'Hırslı', 'Soğuk'],
    },
    {
        'id': 'baskin',
        'sifat': 'Baskın',
        'emoji': '👑',
        'hints': [
            'Bulunduğu ortamda öne çıkar',
            'Güçlü, belirgin çene ile ilişkilendirilir',
            'Liderlik pozisyonlarını doğal bulur',
            'Sessiz kalmak yerine söz almayı tercih eder',
            'Bir komutan ya da CEO\'yu tanımlar',
            'Kelime: "hâkim" ile eşanlamlı',
        ],
        'wrong_options': ['Uyumlu', 'Nazik', 'Çekingen', 'Sakin'],
    },
    {
        'id': 'yaratici',
        'sifat': 'Yaratıcı',
        'emoji': '🎨',
        'hints': [
            'Alışılmışın dışında çözümler üretir',
            'Asimetrik yüz özellikleri ile ilişkilendirilir',
            'Sanat ve tasarıma yatkındır',
            'Rutin işlerden sıkılır',
            'Bir ressam ya da tasarımcıyı tanımlar',
            'Kelime: "özgün" ile eşanlamlı',
        ],
        'wrong_options': ['Analitik', 'Uyumlu', 'Geleneksel', 'Planlı'],
    },
    {
        'id': 'sosyal',
        'sifat': 'Sosyal',
        'emoji': '🤝',
        'hints': [
            'İnsanlardan enerji alır',
            'Geniş, samimi gülümsemeyle ilişkilendirilir',
            'Yalnız kalmaktan hoşlanmaz',
            'Her ortamda arkadaş edinir',
            'Bir organizatör ya da PR uzmanını tanımlar',
            'Kelime: "dışa dönük" ile eşanlamlı',
        ],
        'wrong_options': ['İçedönük', 'Mesafeli', 'Analitik', 'Bağımsız'],
    },
    {
        'id': 'nazik',
        'sifat': 'Nazik',
        'emoji': '🌸',
        'hints': [
            'Başkalarına zarar vermekten kaçınır',
            'Yuvarlak yüz hatları ile ilişkilendirilir',
            'Çevresinde huzur yaratır',
            'Çatışmadan uzak durur',
            'Bir bakıcı ya da öğretmeni tanımlar',
            'Kelime: "şefkatli" ile eşanlamlı',
        ],
        'wrong_options': ['Baskın', 'Hırslı', 'Sert', 'Rekabetçi'],
    },
    {
        'id': 'enerjik',
        'sifat': 'Enerjik',
        'emoji': '⚡',
        'hints': [
            'Dinlenmeden saatlerce çalışabilir',
            'Parlak, hareketli gözlerle ilişkilendirilir',
            'Sabahları yorgun uyanmaz',
            'Bir sporcuyu ya da girişimciyi tanımlar',
            'Etrafına neşe ve hareket katar',
            'Kelime: "dinamik" ile eşanlamlı',
        ],
        'wrong_options': ['Sakin', 'Durağan', 'İçedönük', 'Melankolik'],
    },
    {
        'id': 'icedönük',
        'sifat': 'İçedönük',
        'emoji': '🌙',
        'hints': [
            'Yalnız kalarak enerji toplar',
            'Derin gözler ile ilişkilendirilir',
            'Büyük gruplardan yorulur',
            'Az konuşur, çok düşünür',
            'Bir yazar ya da filozofu tanımlar',
            'Kelime: "içe kapanık" ile eşanlamlı',
        ],
        'wrong_options': ['Sosyal', 'Enerjik', 'Baskın', 'Dışa dönük'],
    },
    {
        'id': 'karizmatik',
        'sifat': 'Karizmatik',
        'emoji': '✨',
        'hints': [
            'İlk bakışta dikkat çeker',
            'Belirgin, dengeli yüz hatları ile ilişkilendirilir',
            'İnsanları etrafında toplar',
            'Sahne ışığı bu kişi için parlar',
            'Bir politikacı ya da aktörü tanımlar',
            'Kelime: "etkileyici" ile eşanlamlı',
        ],
        'wrong_options': ['Sıradan', 'Uyumlu', 'Sessiz', 'Çekingen'],
    },
    {
        'id': 'guvenilir',
        'sifat': 'Güvenilir',
        'emoji': '🛡️',
        'hints': [
            'Verdiği sözü tutar',
            'Dengeli, simetrik yüz hatları ile ilişkilendirilir',
            'Zor günlerde yanında olmaktan kaçınmaz',
            'Sırrı sakladığından emin olunur',
            'Bir avukat ya da denetçiyi tanımlar',
            'Kelime: "sadık" ile eşanlamlı',
        ],
        'wrong_options': ['Değişken', 'Baskın', 'Yaratıcı', 'Aceleci'],
    },
    {
        'id': 'hırslı',
        'sifat': 'Hırslı',
        'emoji': '🏆',
        'hints': [
            'Hedeflerine odaklanır ve vazgeçmez',
            'Güçlü kaş çizgisi ile ilişkilendirilir',
            'Rekabeti sever, ikinci olmaktan hoşlanmaz',
            'Uzun vadeli planlar yapar',
            'Bir girişimciyi ya da sporcuyu tanımlar',
            'Kelime: "motive" ile eşanlamlı',
        ],
        'wrong_options': ['Uyumlu', 'Sakin', 'Nazik', 'Kaygısız'],
    },
    {
        'id': 'sezgisel',
        'sifat': 'Sezgisel',
        'emoji': '🔮',
        'hints': [
            'Verilere ihtiyaç duymadan doğruyu hisseder',
            'Ifadeli, derin bakışla ilişkilendirilir',
            'İç sesi onu nadiren yanıltır',
            'Kalp mi beyin mi diye sorulsa kalbi seçer',
            'Bir sanatçıyı ya da terapisti tanımlar',
            'Kelime: "içgüdüsel" ile eşanlamlı',
        ],
        'wrong_options': ['Analitik', 'Mantıksal', 'Sistematik', 'Planlı'],
    },
    {
        'id': 'diplomatik',
        'sifat': 'Diplomatik',
        'emoji': '🕊️',
        'hints': [
            'Çatışmaları barışçıl yollarla çözer',
            'Dengeli yüz oranları ile ilişkilendirilir',
            'Her iki tarafın da bakış açısını anlar',
            'Söylediği her söze dikkat eder',
            'Bir müzakereciyi ya da elçiyi tanımlar',
            'Kelime: "uzlaşmacı" ile eşanlamlı',
        ],
        'wrong_options': ['Baskın', 'Sert', 'Katı', 'Aceleci'],
    },
    {
        'id': 'merakli',
        'sifat': 'Meraklı',
        'emoji': '🧐',
        'hints': [
            'Her şeyin "neden"ini sormadan duramaz',
            'Büyük, hareketli gözlerle ilişkilendirilir',
            'Yeni konuları hızla öğrenir',
            'Kitap ve belgesel tüketir',
            'Bir araştırmacıyı ya da gazetecisi tanımlar',
            'Kelime: "araştırmacı" ile eşanlamlı',
        ],
        'wrong_options': ['Uyumlu', 'Sakin', 'Durağan', 'Rahat'],
    },
    {
        'id': 'kararli',
        'sifat': 'Kararlı',
        'emoji': '🎯',
        'hints': [
            'Bir kez karar verdi mi geri adım atmaz',
            'Güçlü çene ile ilişkilendirilir',
            'Baskı altında sarsılmaz',
            'Mücadeleyi sonuna kadar sürdürür',
            'Bir sporcuyu ya da askerini tanımlar',
            'Kelime: "azimli" ile eşanlamlı',
        ],
        'wrong_options': ['Uyumlu', 'Kararsız', 'Değişken', 'Rahat'],
    },
    {
        'id': 'romantik',
        'sifat': 'Romantik',
        'emoji': '🌹',
        'hints': [
            'İlişkilerine derin anlam katar',
            'Büyük, ifadeli gözler ve dolgun dudaklarla ilişkilendirilir',
            'Sürprizleri ve jest yapmayı sever',
            'Partneri için ekstra çaba gösterir',
            'Bir şairi ya da müzisyeni tanımlar',
            'Kelime: "duygusal" ile eşanlamlı',
        ],
        'wrong_options': ['Analitik', 'Soğuk', 'Mesafeli', 'Bağımsız'],
    },
    {
        'id': 'bagımsız',
        'sifat': 'Bağımsız',
        'emoji': '🦅',
        'hints': [
            'Kendi yolunu çizmekten zevk alır',
            'Güçlü, belirgin yüz hatları ile ilişkilendirilir',
            'Başkasına muhtaç olmaktan rahatsız olur',
            'Kendi kararlarını kendi verir',
            'Bir serbest çalışanı ya da gezgini tanımlar',
            'Kelime: "özgür ruhlu" ile eşanlamlı',
        ],
        'wrong_options': ['Uyumlu', 'Sosyal', 'Bağımlı', 'Takım oyuncusu'],
    },
    {
        'id': 'uyumlu',
        'sifat': 'Uyumlu',
        'emoji': '🌊',
        'hints': [
            'Her ortama kolayca adapte olur',
            'Yuvarlak, yumuşak yüz hatları ile ilişkilendirilir',
            'Değişikliklerden korkmaz',
            'Farklı gruplarla rahatça çalışır',
            'Bir koordinatörü ya da yöneticiyi tanımlar',
            'Kelime: "esnek" ile eşanlamlı',
        ],
        'wrong_options': ['Katı', 'Baskın', 'Bağımsız', 'Kararlı'],
    },
    {
        'id': 'girişimci',
        'sifat': 'Girişimci',
        'emoji': '🚀',
        'hints': [
            'Fırsatları başkalarından önce görür',
            'Keskin, dikkatli gözlerle ilişkilendirilir',
            'Risk almaktan çekinmez',
            'Sıfırdan bir şeyler inşa etmeyi sever',
            'Bir CEO\'yu ya da startup kurucusunu tanımlar',
            'Kelime: "inovatif" ile eşanlamlı',
        ],
        'wrong_options': ['Uyumlu', 'Sakin', 'Geleneksel', 'Çekingen'],
    },
    {
        'id': 'koruyucu',
        'sifat': 'Koruyucu',
        'emoji': '🛡️',
        'hints': [
            'Sevdiklerini her şeyden önce tutar',
            'Geniş alın ve güçlü çene ile ilişkilendirilir',
            'Tehlike hissedince harekete geçer',
            'Ailesine ve yakınlarına sınır koymaktan çekinmez',
            'Bir ebeveyn ya da güvenlik görevlisini tanımlar',
            'Kelime: "muhafazakâr" değil, "savunucu" ile eşanlamlı',
        ],
        'wrong_options': ['Bağımsız', 'Yaratıcı', 'Meraklı', 'Sosyal'],
    },
]


def _daily_sifat():
    """Pick today's sıfat deterministically by date hash."""
    today = _today()
    idx = int(hashlib.md5(today.encode()).hexdigest(), 16) % len(SIFAT_POOL)
    return SIFAT_POOL[idx]


# ── SPEED MATCH pairs ──────────────────────────────────────────────────────────

SPEED_PAIRS = [
    ('Yüksek alın', 'Analitik'),
    ('Büyük ifadeli gözler', 'Empatik'),
    ('Güçlü belirgin çene', 'Baskın'),
    ('Asimetrik yüz hatları', 'Yaratıcı'),
    ('Geniş samimi gülümseme', 'Sosyal'),
    ('Yuvarlak yüz hatları', 'Nazik'),
    ('Parlak hareketli gözler', 'Enerjik'),
    ('Derin içe bakan gözler', 'İçedönük'),
    ('Dengeli belirgin hatlar', 'Karizmatik'),
    ('Simetrik yüz oranları', 'Güvenilir'),
    ('Güçlü kaş çizgisi', 'Hırslı'),
    ('İfadeli derin bakış', 'Sezgisel'),
    ('Dengeli yüz oranları', 'Diplomatik'),
    ('Büyük hareketli gözler', 'Meraklı'),
    ('Güçlü çene hattı', 'Kararlı'),
    ('Dolgun dudaklar ve iri gözler', 'Romantik'),
    ('Güçlü belirgin hatlar', 'Bağımsız'),
    ('Yuvarlak yumuşak hatlar', 'Uyumlu'),
    ('Keskin dikkatli gözler', 'Girişimci'),
    ('Geniş alın geniş çene', 'Koruyucu'),
    ('İnce çizgili dudaklar', 'Analitik'),
    ('Açık ve parlak yüz', 'Sosyal'),
    ('Küçük sıkı dudaklar', 'Kararlı'),
    ('Geniş burun kemeri', 'Güvenilir'),
    ('Yüksek elmacık kemikleri', 'Karizmatik'),
    ('Hafif eğik başlangıç', 'Sezgisel'),
    ('İri belirgin kulaklar', 'Meraklı'),
    ('Derin göz çukurları', 'Hırslı'),
    ('Yumuşak dudak hattı', 'Empatik'),
    ('Uzun yüz yapısı', 'Analitik'),
    # 31-100
    ('Geniş açık alın', 'Analitik'),
    ('Titiz kaş çizgisi', 'Analitik'),
    ('Belirgin alın damarları', 'Analitik'),
    ('Dar ve keskin göz kenarları', 'Analitik'),
    ('Hafif gergin çene kasları', 'Analitik'),
    ('Dolgun yanak eti', 'Empatik'),
    ('Nemli parlak gözler', 'Empatik'),
    ('Hafif aşağı dönük ağız köşeleri', 'Empatik'),
    ('Sıcak bakış açısı', 'Empatik'),
    ('Geniş burun delikleri', 'Empatik'),
    ('Öne çıkan çene ucu', 'Baskın'),
    ('Geniş yüz genişliği', 'Baskın'),
    ('Düz sert kaş hattı', 'Baskın'),
    ('Belirgin alt çene kemiği', 'Baskın'),
    ('Sıkı kapalı dudaklar', 'Baskın'),
    ('Dağınık asimetrik kaşlar', 'Yaratıcı'),
    ('Renkli canlı göz çevresi', 'Yaratıcı'),
    ('Özgün yüz tonu', 'Yaratıcı'),
    ('Belirgin yüz ifadesi değişkenliği', 'Yaratıcı'),
    ('Hafif yamuk gülümseme', 'Yaratıcı'),
    ('Yüksek yanak kemikleri ve geniş gülümseme', 'Sosyal'),
    ('Hafif kıvrık dudak uçları', 'Sosyal'),
    ('Parlak ve hareketli göz pınarı', 'Sosyal'),
    ('Açık ve davetkar yüz ifadesi', 'Sosyal'),
    ('Sık ve hızlı göz kırpma', 'Sosyal'),
    ('Küçük yuvarlak burun ucu', 'Nazik'),
    ('Hafif içe çekik yanak', 'Nazik'),
    ('Pürüzsüz alın', 'Nazik'),
    ('Açık renkli ve durgun göz', 'Nazik'),
    ('İnce ve düzgün kaş', 'Nazik'),
    ('Geniş açılmış göz kapakları', 'Enerjik'),
    ('Kabarık ve hareketli kaş', 'Enerjik'),
    ('Gergin ve canlı yüz kası', 'Enerjik'),
    ('Kızarmış ve parlak ten', 'Enerjik'),
    ('Sık göz teması', 'Enerjik'),
    ('Hafif düşük göz kapağı', 'İçedönük'),
    ('Uzakta odaklanan bakış', 'İçedönük'),
    ('Az mimik kullanan yüz', 'İçedönük'),
    ('Düşünceli hafif kırışık alın', 'İçedönük'),
    ('Çekingen yüz ifadesi', 'İçedönük'),
    ('Belirgin simetrik yüz hatları', 'Karizmatik'),
    ('Derin ve çekici göz çukurları', 'Karizmatik'),
    ('Güçlü ve çekici çene', 'Karizmatik'),
    ('Mükemmel diş hattı', 'Karizmatik'),
    ('Doğal ve rahat yüz ifadesi', 'Karizmatik'),
    ('Düzgün ve eşit kaş çifti', 'Güvenilir'),
    ('Hafif kırışık göz kenarı', 'Güvenilir'),
    ('Sabit ve doğrudan bakış', 'Güvenilir'),
    ('Düzgün diş dizilimi', 'Güvenilir'),
    ('Sakin ve ölçülü yüz ifadesi', 'Güvenilir'),
    ('Gergin alın orta çizgisi', 'Hırslı'),
    ('Keskin ve odaklı göz bakışı', 'Hırslı'),
    ('Sıkılı çene kasları', 'Hırslı'),
    ('Hafif öne eğik baş pozu', 'Hırslı'),
    ('Belirgin kaş ortası kırışığı', 'Hırslı'),
    ('Hafif yana kayan bakış', 'Sezgisel'),
    ('Sık kaşların arasında düşünceli çizgi', 'Sezgisel'),
    ('Yarı kapalı ve düşünceli göz', 'Sezgisel'),
    ('Belirsiz gülümseme', 'Sezgisel'),
    ('Hafif baş eğikliği', 'Sezgisel'),
    ('Eşit ve dengeli yüz üçgeni', 'Diplomatik'),
    ('Rahat ve nötr ağız hattı', 'Diplomatik'),
    ('Altın oran oranları', 'Diplomatik'),
    ('Hafif yuvarlak çene', 'Diplomatik'),
    ('Sakin ve ölçülü göz ifadesi', 'Diplomatik'),
    ('Sürekli hareket eden göz bebeği', 'Meraklı'),
    ('Hafif öne uzanan boyun pozu', 'Meraklı'),
    ('Sık değişen bakış noktası', 'Meraklı'),
    ('Kabarık ve kalkık kaş', 'Meraklı'),
    ('Hafif açık ağız ifadesi', 'Meraklı'),
    ('Kare çene yapısı', 'Kararlı'),
    ('Çıkık ve keskin elmacık', 'Kararlı'),
    ('Belirgin çene köşesi', 'Kararlı'),
    ('Sabit ve değişmez bakış', 'Kararlı'),
    ('Gergin ve sıkı dudak hattı', 'Kararlı'),
    ('Hafif titreyen dudak köşesi', 'Romantik'),
    ('Derin ve içten bakış', 'Romantik'),
    ('Hafif kızarmış yanak', 'Romantik'),
    ('Sıcak ve parlak cilt', 'Romantik'),
    ('Yuvarlak ve dolgun yanak', 'Romantik'),
    ('Keskin ve belirgin burun sırtı', 'Bağımsız'),
    ('Sert ve kapalı yüz ifadesi', 'Bağımsız'),
    ('Sabit ve güçlü duruş', 'Bağımsız'),
    ('Az ifade kullanan nötr yüz', 'Bağımsız'),
    ('Dik ve güçlü boyun çizgisi', 'Bağımsız'),
    ('Yuvarlak ve geniş yanak bölgesi', 'Uyumlu'),
    ('Hafif eğilen ve dinleyen baş pozu', 'Uyumlu'),
    ('Açık ve kabul edici yüz ifadesi', 'Uyumlu'),
    ('Pürüzsüz ve sakin alın', 'Uyumlu'),
    ('Sıklıkla onay veren başın eğimi', 'Uyumlu'),
    ('İnce ve keskin göz kenarı', 'Girişimci'),
    ('Hafif öne çıkan alt dudak', 'Girişimci'),
    ('Hızlı ve kararlı göz hareketi', 'Girişimci'),
    ('Belirgin ve güçlü burun yapısı', 'Girişimci'),
    ('Dinamik ve enerjik yüz ifadesi', 'Girişimci'),
    ('Geniş ve ağır çene kemiği', 'Koruyucu'),
    ('Derin ve ciddi kaş çizgisi', 'Koruyucu'),
    ('Geniş omuz ve boyun hattı', 'Koruyucu'),
    ('Belirgin ve sağlam alın kemiği', 'Koruyucu'),
    ('Düşük ve sakin göz kapağı', 'Koruyucu'),
]

ALL_SIFAT_OPTIONS = list({p[1] for p in SPEED_PAIRS})


def _make_options(correct: str, n: int = 4) -> list[str]:
    wrong = [s for s in ALL_SIFAT_OPTIONS if s != correct]
    chosen = random.sample(wrong, min(n - 1, len(wrong)))
    opts = [correct] + chosen
    random.shuffle(opts)
    return opts


# ── DAILY POLL questions ───────────────────────────────────────────────────────

POLL_QUESTIONS = [
    {
        'question_tr': 'Güçlü, belirgin çene hangi kişilik sıfatını en çok çağrıştırır?',
        'question_en': 'Which personality trait does a strong, prominent jaw most suggest?',
        'options_tr': ['Baskın', 'Nazik', 'Yaratıcı', 'Empatik'],
        'options_en': ['Dominant', 'Gentle', 'Creative', 'Empathetic'],
        'correct_index': 0,
        'emoji': '👁️',
    },
    {
        'question_tr': 'Büyük ve ifadeli gözler genellikle hangi sıfatla ilişkilendirilir?',
        'question_en': 'Large expressive eyes are most associated with which trait?',
        'options_tr': ['Analitik', 'Empatik', 'Hırslı', 'Baskın'],
        'options_en': ['Analytical', 'Empathetic', 'Ambitious', 'Dominant'],
        'correct_index': 1,
        'emoji': '👀',
    },
    {
        'question_tr': 'Yüksek ve geniş bir alın hangi kişilik özelliğinin işareti sayılır?',
        'question_en': 'A high and wide forehead is a sign of which trait?',
        'options_tr': ['Karizmatik', 'Analitik', 'Romantik', 'Sosyal'],
        'options_en': ['Charismatic', 'Analytical', 'Romantic', 'Social'],
        'correct_index': 1,
        'emoji': '🧠',
    },
    {
        'question_tr': 'Geniş ve samimi bir gülümseme hangi sıfatla örtüşür?',
        'question_en': 'A wide and genuine smile most overlaps with which trait?',
        'options_tr': ['İçedönük', 'Sosyal', 'Analitik', 'Bağımsız'],
        'options_en': ['Introverted', 'Social', 'Analytical', 'Independent'],
        'correct_index': 1,
        'emoji': '😊',
    },
    {
        'question_tr': 'Keskin ve dikkatli bir bakış hangi kişilik özelliğini işaret eder?',
        'question_en': 'A sharp and attentive gaze indicates which personality trait?',
        'options_tr': ['Nazik', 'Girişimci', 'Romantik', 'Uyumlu'],
        'options_en': ['Gentle', 'Entrepreneurial', 'Romantic', 'Adaptable'],
        'correct_index': 1,
        'emoji': '👁️',
    },
    {
        'question_tr': 'Dengeli ve simetrik yüz oranları hangi sıfatı öne çıkarır?',
        'question_en': 'Balanced and symmetrical facial proportions highlight which trait?',
        'options_tr': ['Güvenilir', 'Yaratıcı', 'Bağımsız', 'Meraklı'],
        'options_en': ['Trustworthy', 'Creative', 'Independent', 'Curious'],
        'correct_index': 0,
        'emoji': '⚖️',
    },
    {
        'question_tr': 'Yuvarlak ve yumuşak yüz hatları hangi kişilik tipini yansıtır?',
        'question_en': 'Round and soft facial features reflect which personality type?',
        'options_tr': ['Hırslı', 'Sert', 'Nazik', 'Baskın'],
        'options_en': ['Ambitious', 'Harsh', 'Gentle', 'Dominant'],
        'correct_index': 2,
        'emoji': '🌸',
    },
    {
        'question_tr': 'Yüksek elmacık kemikleri genellikle hangi sıfatla bağdaşır?',
        'question_en': 'High cheekbones are generally associated with which trait?',
        'options_tr': ['Karizmatik', 'Empatik', 'Uyumlu', 'Nazik'],
        'options_en': ['Charismatic', 'Empathetic', 'Adaptable', 'Gentle'],
        'correct_index': 0,
        'emoji': '✨',
    },
    {
        'question_tr': 'Derin ve içe dönük gözler en çok hangi kişiliği çağrıştırır?',
        'question_en': 'Deep and inward-looking eyes most evoke which personality?',
        'options_tr': ['Sosyal', 'Enerjik', 'İçedönük', 'Karizmatik'],
        'options_en': ['Social', 'Energetic', 'Introverted', 'Charismatic'],
        'correct_index': 2,
        'emoji': '🌙',
    },
    {
        'question_tr': 'Güçlü kaş çizgisi hangi kişilik özelliğini ön plana çıkarır?',
        'question_en': 'Strong eyebrow lines bring which personality trait to the fore?',
        'options_tr': ['Uyumlu', 'Hırslı', 'Romantik', 'Sosyal'],
        'options_en': ['Adaptable', 'Ambitious', 'Romantic', 'Social'],
        'correct_index': 1,
        'emoji': '💪',
    },
]


def _daily_poll():
    today = _today()
    idx = int(hashlib.md5((today + 'poll').encode()).hexdigest(), 16) % len(POLL_QUESTIONS)
    return idx, POLL_QUESTIONS[idx]


# ── MEMORY CARD pairs ──────────────────────────────────────────────────────────

MEMORY_PAIRS = [
    ('🔬 Yüksek Alın', 'Analitik'),
    ('💛 İfadeli Gözler', 'Empatik'),
    ('👑 Belirgin Çene', 'Baskın'),
    ('🎨 Asimetrik Hatlar', 'Yaratıcı'),
    ('🤝 Geniş Gülümseme', 'Sosyal'),
    ('🌸 Yuvarlak Hatlar', 'Nazik'),
    ('⚡ Parlak Gözler', 'Enerjik'),
    ('🌙 Derin Bakış', 'İçedönük'),
    ('✨ Dengeli Hatlar', 'Karizmatik'),
    ('🛡️ Simetrik Oran', 'Güvenilir'),
    ('🏆 Güçlü Kaş', 'Hırslı'),
    ('🔮 İfadeli Bakış', 'Sezgisel'),
]


# ── SPIN WHEEL config ──────────────────────────────────────────────────────────

WHEEL_SEGMENTS = [
    {'label': '10 ✨ XP',   'reward_type': 'xp',       'reward_value': 10,  'weight': 30},
    {'label': '20 ✨ XP',   'reward_type': 'xp',       'reward_value': 20,  'weight': 25},
    {'label': '50 ✨ XP',   'reward_type': 'xp',       'reward_value': 50,  'weight': 15},
    {'label': '5 ✨ XP',    'reward_type': 'xp',       'reward_value': 5,   'weight': 20},
    {'label': '100 ✨ XP',  'reward_type': 'xp',       'reward_value': 100, 'weight': 5},
    {'label': '+Rozet 🎖️', 'reward_type': 'badge_xp', 'reward_value': 1,   'weight': 10},
    {'label': 'Seri 🔥',   'reward_type': 'streak',    'reward_value': 1,   'weight': 8},
    {'label': '200 ✨ 🎰',  'reward_type': 'jackpot',  'reward_value': 200, 'weight': 2},
]

_SEGMENT_POOL = []
for i, seg in enumerate(WHEEL_SEGMENTS):
    _SEGMENT_POOL.extend([i] * seg['weight'])


# ══════════════════════════════════════════════════════════════════════════════
#  VIEW FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

# ── 1. SIFAT BUL (Wordle-style) ────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def wordle_daily(request):
    uid, err = _require_user(request)
    if err:
        return err
    db = _get_db()
    today = _today()
    sifat_data = _daily_sifat()
    existing = db['wordle_attempts'].find_one({'user_id': uid, 'date': today})
    hints_revealed = existing.get('hints_revealed', 0) if existing else 0
    attempts = existing.get('attempts', []) if existing else []
    won = existing.get('won', False) if existing else False

    hints_so_far = sifat_data['hints'][:max(1, hints_revealed)]
    all_options = [s['sifat'] for s in SIFAT_POOL]
    random.shuffle(all_options)

    return JsonResponse({
        'date': today,
        'hints': hints_so_far,
        'total_hints': len(sifat_data['hints']),
        'attempts_used': len(attempts),
        'max_attempts': 6,
        'won': won,
        'options': all_options,
        'correct_sifat': sifat_data['sifat'] if (won or len(attempts) >= 6) else None,
        'emoji': sifat_data['emoji'],
        'xp_if_win': max(5, 35 - len(attempts) * 5),
    })


@csrf_exempt
@require_http_methods(['POST'])
def wordle_guess(request):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    guess = body.get('guess', '').strip()
    db = _get_db()
    today = _today()
    sifat_data = _daily_sifat()
    correct_sifat = sifat_data['sifat']
    col = db['wordle_attempts']
    existing = col.find_one({'user_id': uid, 'date': today})
    attempts = existing.get('attempts', []) if existing else []
    hints_revealed = existing.get('hints_revealed', 0) if existing else 0
    won = existing.get('won', False) if existing else False

    if won or len(attempts) >= 6:
        return JsonResponse({'detail': 'Game already finished'}, status=400)

    is_correct = guess == correct_sifat
    attempts.append(guess)
    new_hints_revealed = min(len(sifat_data['hints']), hints_revealed + 1)
    new_won = is_correct
    xp_earned = 0

    if is_correct:
        xp_earned = max(5, 35 - (len(attempts) - 1) * 5)
        _add_xp(uid, xp_earned, f'wordle_win_{today}')

    col.update_one(
        {'user_id': uid, 'date': today},
        {'$set': {
            'user_id': uid,
            'date': today,
            'attempts': attempts,
            'hints_revealed': new_hints_revealed,
            'won': new_won,
            'correct_sifat': correct_sifat,
            'completed': new_won or len(attempts) >= 6,
            'updated_at': datetime.utcnow().isoformat(),
        }},
        upsert=True,
    )
    game_over = new_won or len(attempts) >= 6
    next_hint = sifat_data['hints'][new_hints_revealed - 1] if new_hints_revealed <= len(sifat_data['hints']) and not game_over else None

    return JsonResponse({
        'correct': is_correct,
        'attempts_used': len(attempts),
        'max_attempts': 6,
        'game_over': game_over,
        'won': new_won,
        'next_hint': next_hint,
        'xp_earned': xp_earned,
        'correct_sifat': correct_sifat if game_over else None,
    })


@csrf_exempt
@require_http_methods(['GET'])
def wordle_leaderboard(request):
    uid, err = _require_user(request)
    if err:
        return err
    db = _get_db()
    today = _today()
    docs = list(
        db['wordle_attempts'].find(
            {'date': today, 'won': True},
            {'user_id': 1, 'attempts': 1, '_id': 0}
        ).sort('attempts', 1).limit(20)
    )
    user_ids = [d['user_id'] for d in docs]
    users = {
        u['id']: u.get('username', f"user_{u['id']}")
        for u in db['appfaceapi_myuser'].find({'id': {'$in': user_ids}}, {'id': 1, 'username': 1, '_id': 0})
    }
    entries = [
        {
            'rank': i + 1,
            'user_id': d['user_id'],
            'username': users.get(d['user_id'], f"user_{d['user_id']}"),
            'attempts': len(d.get('attempts', [])),
        }
        for i, d in enumerate(docs)
    ]
    return JsonResponse({'entries': entries, 'date': today})


# ── 2. HIZLI EŞLEŞTİR (Speed Match) ──────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def speed_match_start(request):
    uid, err = _require_user(request)
    if err:
        return err
    count = 10
    pairs = random.sample(SPEED_PAIRS, min(count, len(SPEED_PAIRS)))
    questions = [
        {
            'index': i,
            'feature': p[0],
            'correct': p[1],
            'options': _make_options(p[1]),
        }
        for i, p in enumerate(pairs)
    ]
    return JsonResponse({'questions': questions, 'duration_seconds': 30})


@csrf_exempt
@require_http_methods(['POST'])
def speed_match_submit(request):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    answers = body.get('answers', [])
    time_ms = int(body.get('time_ms', 30000))
    correct_count = sum(1 for a in answers if a.get('correct', False))
    total = len(answers) or 1
    accuracy = round(correct_count / total * 100, 1)
    speed_bonus = max(0, int((30000 - time_ms) / 1000) * 2)
    score = correct_count * 10 + speed_bonus
    xp_earned = min(50, correct_count * 4 + (5 if accuracy == 100 else 0))
    xp_info = {}
    if xp_earned > 0:
        xp_info = _add_xp(uid, xp_earned, 'speed_match')
    db = _get_db()
    db['speed_match_scores'].insert_one({
        'user_id': uid,
        'score': score,
        'correct': correct_count,
        'total': total,
        'accuracy': accuracy,
        'time_ms': time_ms,
        'created_at': datetime.utcnow().isoformat(),
    })
    return JsonResponse({
        'score':      score,
        'correct':    correct_count,
        'total':      total,
        'accuracy':   accuracy,
        'xp_earned':  xp_earned,
        'level':      xp_info.get('level', 1),
    })


@csrf_exempt
@require_http_methods(['GET'])
def speed_match_leaderboard(request):
    uid, err = _require_user(request)
    if err:
        return err
    limit = min(int(request.GET.get('limit', 20)), 100)
    db = _get_db()
    pipeline = [
        {'$group': {'_id': '$user_id', 'best_score': {'$max': '$score'}, 'best_accuracy': {'$max': '$accuracy'}}},
        {'$sort': {'best_score': -1}},
        {'$limit': limit},
    ]
    docs = list(db['speed_match_scores'].aggregate(pipeline))
    user_ids = [d['_id'] for d in docs]
    users = {
        u['id']: u.get('username', f"user_{u['id']}")
        for u in db['appfaceapi_myuser'].find({'id': {'$in': user_ids}}, {'id': 1, 'username': 1, '_id': 0})
    }
    entries = [
        {
            'rank': i + 1,
            'user_id': d['_id'],
            'username': users.get(d['_id'], f"user_{d['_id']}"),
            'best_score': d['best_score'],
            'best_accuracy': d['best_accuracy'],
        }
        for i, d in enumerate(docs)
    ]
    return JsonResponse({'entries': entries})


# ── 3. TOPLULUK OYU (Daily Poll) ──────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def poll_daily(request):
    uid, err = _require_user(request)
    if err:
        return err
    db = _get_db()
    today = _today()
    q_idx, q = _daily_poll()
    lang = request.GET.get('lang', 'tr')
    user_vote = db['poll_votes'].find_one({'user_id': uid, 'date': today}, {'option_index': 1})
    total_votes = db['poll_votes'].count_documents({'date': today})
    vote_counts = [0, 0, 0, 0]
    if user_vote is not None:
        for doc in db['poll_votes'].find({'date': today}, {'option_index': 1}):
            idx = doc.get('option_index', 0)
            if 0 <= idx < 4:
                vote_counts[idx] += 1
    options = q['options_tr'] if lang == 'tr' else q['options_en']
    return JsonResponse({
        'date': today,
        'question': q['question_tr'] if lang == 'tr' else q['question_en'],
        'emoji': q['emoji'],
        'options': options,
        'user_voted': user_vote is not None,
        'user_vote_index': user_vote.get('option_index') if user_vote else None,
        'vote_counts': vote_counts if user_vote is not None else None,
        'total_votes': total_votes,
        'correct_index': q['correct_index'] if user_vote is not None else None,
    })


@csrf_exempt
@require_http_methods(['POST'])
def poll_vote(request):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    option_index = int(body.get('option_index', 0))
    db = _get_db()
    today = _today()
    already = db['poll_votes'].find_one({'user_id': uid, 'date': today})
    if already:
        return JsonResponse({'detail': 'already_voted'}, status=409)
    _, q = _daily_poll()
    is_correct = option_index == q['correct_index']
    xp_earned = 15 if is_correct else 5
    _add_xp(uid, xp_earned, f'poll_vote_{today}')
    db['poll_votes'].insert_one({
        'user_id': uid,
        'date': today,
        'option_index': option_index,
        'correct': is_correct,
        'created_at': datetime.utcnow().isoformat(),
    })
    vote_counts = [0, 0, 0, 0]
    for doc in db['poll_votes'].find({'date': today}, {'option_index': 1}):
        idx = doc.get('option_index', 0)
        if 0 <= idx < 4:
            vote_counts[idx] += 1
    return JsonResponse({
        'success': True,
        'correct': is_correct,
        'xp_earned': xp_earned,
        'correct_index': q['correct_index'],
        'vote_counts': vote_counts,
    })


# ── 4. HAFIZA KARTLARI (Memory Cards) ─────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def memory_cards(request):
    uid, err = _require_user(request)
    if err:
        return err
    size = int(request.GET.get('size', 4))
    pair_count = 8 if size == 4 else 12
    pairs = random.sample(MEMORY_PAIRS, min(pair_count, len(MEMORY_PAIRS)))
    cards = []
    for i, (feature, sifat) in enumerate(pairs):
        cards.append({'id': f'f_{i}', 'content': feature, 'pair_id': i, 'type': 'feature'})
        cards.append({'id': f's_{i}', 'content': sifat,   'pair_id': i, 'type': 'sifat'})
    random.shuffle(cards)
    return JsonResponse({'cards': cards, 'pair_count': pair_count, 'size': size})


@csrf_exempt
@require_http_methods(['POST'])
def memory_complete(request):
    uid, err = _require_user(request)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    moves = int(body.get('moves', 99))
    time_ms = int(body.get('time_ms', 120000))
    pair_count = int(body.get('pair_count', 8))
    perfect = pair_count * 2
    xp_earned = max(5, 40 - max(0, moves - perfect) * 2)
    xp_info = _add_xp(uid, xp_earned, 'memory_cards')
    db = _get_db()
    db['memory_scores'].insert_one({
        'user_id': uid,
        'moves': moves,
        'time_ms': time_ms,
        'pair_count': pair_count,
        'xp_earned': xp_earned,
        'created_at': datetime.utcnow().isoformat(),
    })
    return JsonResponse({'xp_earned': xp_earned, 'moves': moves, 'level': xp_info.get('level', 1)})


@csrf_exempt
@require_http_methods(['GET'])
def memory_leaderboard(request):
    uid, err = _require_user(request)
    if err:
        return err
    limit = min(int(request.GET.get('limit', 20)), 100)
    db = _get_db()
    pipeline = [
        {'$group': {'_id': '$user_id', 'best_moves': {'$min': '$moves'}, 'best_time': {'$min': '$time_ms'}}},
        {'$sort': {'best_moves': 1, 'best_time': 1}},
        {'$limit': limit},
    ]
    docs = list(db['memory_scores'].aggregate(pipeline))
    user_ids = [d['_id'] for d in docs]
    users = {
        u['id']: u.get('username', f"user_{u['id']}")
        for u in db['appfaceapi_myuser'].find({'id': {'$in': user_ids}}, {'id': 1, 'username': 1, '_id': 0})
    }
    entries = [
        {
            'rank': i + 1,
            'user_id': d['_id'],
            'username': users.get(d['_id'], f"user_{d['_id']}"),
            'best_moves': d['best_moves'],
        }
        for i, d in enumerate(docs)
    ]
    return JsonResponse({'entries': entries})


# ── 5. GÜNLÜK ÇARK (Spin Wheel) ───────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def spin_status(request):
    uid, err = _require_user(request)
    if err:
        return err
    db = _get_db()
    today = _today()
    existing = db['daily_spins'].find_one({'user_id': uid, 'date': today})
    segments = [
        {'label': s['label'], 'reward_type': s['reward_type'], 'weight': s['weight']}
        for s in WHEEL_SEGMENTS
    ]
    return JsonResponse({
        'can_spin': existing is None,
        'segments': segments,
        'last_reward': existing.get('reward') if existing else None,
    })


@csrf_exempt
@require_http_methods(['POST'])
def spin_wheel(request):
    uid, err = _require_user(request)
    if err:
        return err
    db = _get_db()
    today = _today()
    existing = db['daily_spins'].find_one({'user_id': uid, 'date': today})
    if existing:
        return JsonResponse({'detail': 'already_spun', 'reward': existing.get('reward')}, status=409)
    segment_idx = random.choice(_SEGMENT_POOL)
    segment = WHEEL_SEGMENTS[segment_idx]
    xp_earned = 0
    message_tr = ''
    message_en = ''
    if segment['reward_type'] in ('xp', 'jackpot'):
        xp_earned = segment['reward_value']
        _add_xp(uid, xp_earned, 'spin_wheel')
        message_tr = f'🎉 {xp_earned} XP kazandın!'
        message_en = f'🎉 You won {xp_earned} XP!'
    elif segment['reward_type'] == 'badge_xp':
        BadgeService.award_badge(uid, 'streak_keeper', 1)
        message_tr = '🎖️ Rozet XP kazandın!'
        message_en = '🎖️ You earned Badge XP!'
    elif segment['reward_type'] == 'streak':
        xp_earned = 5
        _add_xp(uid, xp_earned, 'spin_streak_bonus')
        message_tr = '🔥 Seri bonusu: 5 XP!'
        message_en = '🔥 Streak bonus: 5 XP!'
    reward = {
        'segment_index': segment_idx,
        'label':         segment['label'],
        'reward_type':   segment['reward_type'],
        'reward_value':  segment['reward_value'],
        'xp_earned':     xp_earned,
        'message_tr':    message_tr,
        'message_en':    message_en,
    }
    db['daily_spins'].insert_one({
        'user_id': uid,
        'date': today,
        'reward': reward,
        'spun_at': datetime.utcnow().isoformat(),
    })
    return JsonResponse({'success': True, 'reward': reward})


from datetime import datetime
