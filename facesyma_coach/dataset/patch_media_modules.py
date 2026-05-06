"""
facesyma_coach/dataset/patch_media_modules.py
=============================================
13 yeni modül için veri üretir ve MongoDB'ye patch eder.

Yeni modüller:
  etkinlik_tavsiye  spor_aktivite    kariyer_yolu
  insan_kaynaklari  duygusal_ruhsal  meditasyon_egzersiz
  kitap_tavsiye     film_tavsiye     muzik_tavsiye
  podcast_tavsiye   seyahat_tavsiye  gunluk_afirasyon
  saglik_tavsiye

Kullanım:
  python patch_media_modules.py --dry-run      # sadece içerik üret, DB'ye yazma
  python patch_media_modules.py --lang tr      # sadece TR'yi işle
  python patch_media_modules.py                # tüm 18 dil, MongoDB'ye yaz

Gereksinimler:
  pip install pymongo deep-translator
"""

import argparse
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path

try:
    from pymongo import MongoClient, UpdateOne
    MONGO_OK = True
except ImportError:
    MONGO_OK = False

try:
    from deep_translator import GoogleTranslator
    TRANSLATE_OK = True
except ImportError:
    TRANSLATE_OK = False

# ── Konfigürasyon ─────────────────────────────────────────────────────────────
MONGO_URI  = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
BACKUP_DB  = "facesyma-coach-backup"
ALL_LANGS  = ["tr","en","de","ru","ar","es","ko","ja","zh","hi","fr","pt","bn","id","ur","it","vi","pl"]
_LANG_COL_MAP = {"ko": "kr", "ja": "jp", "zh": "zh"}

ARCHETYPES = [
    "analitik","açık_kalpli","cazip","dengeli","dikkatli","enerjik",
    "güvenilir","güçlü","hassas","kararlı","lider","odaklı",
    "pratik","sezgisel","sosyal","yaratıcı","zarif","çekici",
]

NEW_MODULES = [
    "etkinlik_tavsiye","spor_aktivite","kariyer_yolu","insan_kaynaklari",
    "duygusal_ruhsal","meditasyon_egzersiz","kitap_tavsiye","film_tavsiye",
    "muzik_tavsiye","podcast_tavsiye","seyahat_tavsiye","gunluk_afirasyon",
    "saglik_tavsiye",
]

# ── Arketip kişilik etiketleri (çeviri için) ──────────────────────────────────
ARCH_TRAITS_TR = {
    "analitik":    "analitik ve detaycı",
    "açık_kalpli": "açık kalpli ve empatik",
    "cazip":       "karizmatik ve ikna edici",
    "dengeli":     "dengeli ve sakin",
    "dikkatli":    "dikkatli ve mükemmeliyetçi",
    "enerjik":     "enerjik ve hareketli",
    "güvenilir":   "güvenilir ve tutarlı",
    "güçlü":       "güçlü ve kararlı",
    "hassas":      "hassas ve duygusal zekâsı yüksek",
    "kararlı":     "kararlı ve özgüvenli",
    "lider":       "liderlik ruhuna sahip",
    "odaklı":      "odaklı ve üretken",
    "pratik":      "pratik ve çözüm odaklı",
    "sezgisel":    "sezgisel ve içgüdüsel",
    "sosyal":      "sosyal ve ilişki kurmayı seven",
    "yaratıcı":    "yaratıcı ve özgün düşünen",
    "zarif":       "zarif ve estetik zevki güçlü",
    "çekici":      "çekici ve etkileyici",
}

# ─────────────────────────────────────────────────────────────────────────────
# İÇERİK HAVUZLARI — Türkçe (TR)
# Her modül: 6-8 cümle havuzu, sıfata göre random seçim yapılır
# ─────────────────────────────────────────────────────────────────────────────

# ── etkinlik_tavsiye ─────────────────────────────────────────────────────────
ETK_INDOOR = {
    "analitik":    ["Puzzle ve strateji oyunları zihnini keskin tutar.","Satranç kulübü veya kodlama workshopları sana uygun.","Belgesel maratonu: bilim ve tarih konuları."],
    "açık_kalpli": ["Gönüllülük çalışmaları ruhunu besler.","Yaratıcı yazarlık atölyeleri.","Komşuluk yemekleri organize etmek sana iyi gelir."],
    "cazip":       ["Sunum ve hitabet kursları yeteneğini geliştirir.","İmprov tiyatro atölyeleri karizmanı artırır.","Networking etkinlikleri doğal ortamın."],
    "dengeli":     ["Yoga ve meditasyon seansları.","Bonsai veya ev bitkileri yetiştirme.","Çay / kahve tadım ritüelleri."],
    "dikkatli":    ["Model yapımı veya origami.","Fotoğrafçılık kursu — teknik detaylar sana uygun.","Müzik enstrümanı öğrenmek için ideal profil."],
    "enerjik":     ["Dans kursu veya Zumba.","Duvar tırmanışı / bouldering salonu.","Escape room etkinlikleri."],
    "güvenilir":   ["Topluluk okuma kulüpleri.","Koçluk / mentörlük programlarına destek ver.","Aile yemekleri organize etmek güçlü yanın."],
    "güçlü":       ["Boks veya dövüş sanatları antrenmanlarda içeride de güçlü kalırsın.","Yarışma odaklı e-spor turnuvaları.","Ağırlık antrenmanı programları."],
    "hassas":      ["Sanat terapisi atölyeleri.","Müzik dinleme ve analiz seansları.","Şiir okuma kulüpleri."],
    "kararlı":     ["Liderlik ve kişisel gelişim seminerleri.","İş simülasyonu oyunları.","Hedef belirleme workshop'ları."],
    "lider":       ["Toastmasters konuşma kulübü.","Strateji masa oyunları turnuvaları.","Mentorluk programlarına öncülük et."],
    "odaklı":      ["Deep work seansları için kütüphane üyeliği.","Online kurs ve sertifika programları.","Pomodoro toplulukları."],
    "pratik":      ["DIY (kendin yap) projeleri.","Ev tadilatı ve onarım workshopları.","Araç-gereç eğitimleri."],
    "sezgisel":    ["Tarot veya astroloji atölyeleri.","Rüya günlüğü tutma çevreleri.","Spiritual retreat etkinlikleri."],
    "sosyal":      ["Board game cafelerde grup oyunları.","Improv stand-up atölyeleri.","Sosyal yemek kulüpleri."],
    "yaratıcı":    ["Seramik veya heykel atölyesi.","Dijital illüstrasyon kursları.","Fanzin veya zine yayıncılığı."],
    "zarif":       ["Şarap / gastronomi tadım etkinlikleri.","İç mimari ve estetik workshopları.","Kaligrafi kursu."],
    "çekici":      ["Stil ve moda atölyeleri.","Fotoğraf çekimi / model deneyimi.","Sosyal medya içerik üretim kursları."],
}

ETK_OUTDOOR = {
    "analitik":    ["Doğa yürüyüşü + bitki/kuş gözlemi.","Astrofotoğrafçılık geceleri.","Jeoloji turları."],
    "açık_kalpli": ["Topluluk bahçeciliği.","Sokak sanatı etkinlikleri.","Evsizlere yardım gönüllülüğü."],
    "cazip":       ["Outdoor networking piknik etkinlikleri.","Sokak performansları izleme.","Food truck festival turları."],
    "dengeli":     ["Sabah parkı yürüyüşleri.","Plaj veya göl meditasyonu.","Bisiklet ile şehir keşfi."],
    "dikkatli":    ["Makro fotoğrafçılık doğa turları.","Arkeoloji / müze outdoor etkinlikleri.","Bitki tohumları toplama ve dökümantasyon."],
    "enerjik":     ["Parkur veya outdoor crossfit.","Surf / kaya tırmanışı.","Maraton hazırlık koşuları."],
    "güvenilir":   ["Aile piknik ve kamp organizasyonları.","Komşuluk temizlik etkinlikleri.","Ormanlık yürüyüş grupları."],
    "güçlü":       ["Dağ bisikleti.","Kamp ve hayatta kalma kursları.","Obstacle race yarışmaları."],
    "hassas":      ["Güneş doğumu / batımı seyretme ritüelleri.","Doğa seslerini kaydetme.","Çiçek toplamak ve preslemek."],
    "kararlı":     ["Trail running yarışmaları.","Kentsel keşif (urbex) turları.","Uzun mesafe bisiklet rotaları."],
    "lider":       ["Outdoor takım sporları organizasyonu.","Kamp liderliği programları.","Doğa rehberliği eğitimi."],
    "odaklı":      ["Sessiz doğa yürüyüşleri.","Outdoor deep-work seansları (laptop + kafeterya bahçe).","Bisiklet ile podcast dinleme turları."],
    "pratik":      ["Bahçe tasarımı ve peyzaj.","Outdoor market alışverişi rotaları.","Kamp ekipmanı kurulum tatbikatları."],
    "sezgisel":    ["Orman banyosu (shinrin-yoku).","Yıldız gözlemi geceleri.","Doğa ritüelleri / equinox etkinlikleri."],
    "sosyal":      ["Outdoor konser ve festival.","Plaj voleybolu grubu.","Şehir orienteering yarışmaları."],
    "yaratıcı":    ["Plein air resim.","Sokak fotoğrafçılığı.","Doğadan ilham alan sanat projeleri."],
    "zarif":       ["Botanik bahçe turları.","Açık hava sinema etkinlikleri.","Lüks glamping deneyimleri."],
    "çekici":      ["Outdoor fotoğraf çekimi / portföy seansları.","Sosyal outdoor etkinlik organizasyonu.","Kalabalık festival organizasyonu."],
}

# ── spor_aktivite ─────────────────────────────────────────────────────────────
SPOR = {
    "analitik":    ["Satranç gibi strateji içeren sporlar sana uygun.","Yüzme: ritim + teknik analiz gerektiren ideal spor.","Biatlon veya triatlon: çok disiplinli performans."],
    "açık_kalpli": ["Takım sporları ruhunu besler — futbol, voleybol.","Yoga ve tai chi bedenle barışmayı destekler.","Topluluk koşu grupları ile hem spor hem bağ kur."],
    "cazip":       ["Dans: ritim ve görünüş bir arada.","Tenis veya squash: rekabetçi ve sosyal.","Martial arts: disiplin + kişisel marka."],
    "dengeli":     ["Yürüyüş: düzenli ve tempolu.","Pilates: denge ve çekirdek gücü.","Bisiklet: keyifli, ritimli, şehre uyumlu."],
    "dikkatli":    ["Okçuluk: odak ve sabır gerektiriyor.","Jimnastik: teknik mükemmellik senin için anlamlı.","Golf: teknik, sabır ve strateji."],
    "enerjik":     ["HIIT antrenmanları yüksek enerji seviyene uygun.","Basketbol veya futbol: sürekli hareket.","Crossfit: her gün farklı, her gün yoğun."],
    "güvenilir":   ["Oryantiring: takım ve güven üzerine kurulu.","Yüzme: düzenli ve güvenilir bir antrenman.","Yürüyüş kulübü üyeliği: rutin ve topluluk."],
    "güçlü":       ["Halter: kaba güç ve disiplin.","Rugby veya Amerikan futbolu: güç ve dayanıklılık.","Kaya tırmanışı: hem zihinsel hem fiziksel güç."],
    "hassas":      ["Yoga: beden-zihin bütünleşmesi.","Dans terapisi: duygusal ifade aracı.","Aqua fitness: nazik ama etkili."],
    "kararlı":     ["Dövüş sanatları: kararlılık ve disiplin.","Sprint antrenmanları: kısa ve yoğun hedefler.","Triatlon: kendini aşmak için mükemmel."],
    "lider":       ["Kaptan olabileceğin takım sporları.","Koçluk + antrenman kombinasyonu.","Triatlon / maraton: liderlik disiplini."],
    "odaklı":      ["Uzun mesafe koşu: odak ve dayanıklılık.","Teniste uzun ralli pratikleri.","Solo bisiklet turu: kendi hedefin, kendi hızın."],
    "pratik":      ["Evde yapılabilir vücut ağırlığı egzersizleri.","Fonksiyonel antrenman: günlük hayata fayda.","Yüzme: sade, pratik, etkili."],
    "sezgisel":    ["Qi gong: enerji ve sezgi güçlendirme.","Doğa yürüyüşü: içgüdüsel rotalar.","Serbest dalış: sessizlik ve içsel farkındalık."],
    "sosyal":      ["Plaj voleybolu: eğlenceli ve sosyal.","Çift dansı: bağ kuran spor.","Takım orienteering: birlikte kazanma."],
    "yaratıcı":    ["Parkur: yaratıcı hareket ve özgürlük.","Akrobatik dans.","Freestyle dövüş sanatları: kendi tarzını yarat."],
    "zarif":       ["Bale veya modern dans.","Golf: zariflik ve stil.","Equestrianism (binicilik): zariflik simgesi."],
    "çekici":      ["Dans: görünürlük ve çekicilik.","Tenis: sofistike ve sosyal.","Yüzme: vücudu şekillendiren, estetik."],
}

# ── kariyer_yolu ─────────────────────────────────────────────────────────────
KARIYER = {
    "analitik":    ["Veri bilimi, finans analizi, araştırma pozisyonları senin için ideal.","Strateji danışmanlığı veya sistem mühendisliği güçlü yanların.","Akademik kariyer veya AR-GE'de uzun vadeli tatmin bulursun."],
    "açık_kalpli": ["Psikoloji, sosyal hizmet, eğitim veya NGO sektörü sana anlam verir.","İnsan kaynakları veya topluluk yönetimi doğal alanın.","Danışmanlık: dinleyerek, empati kurarak insanları yönlendirme."],
    "cazip":       ["Satış, pazarlama, halkla ilişkiler veya marka yönetimi kariyer alanın.","Girişimcilik: karizman en güçlü satış aracın.","Medya, yayıncılık veya influencer kimliği."],
    "dengeli":     ["Proje yönetimi veya operasyon direktörlüğü dengeleme yeteneğini kullanır.","Arabuluculuk ve uyum danışmanlığı.","Hukuk veya kamu yönetimi: adalet ve denge."],
    "dikkatli":    ["Kalite güvence, denetim veya hukuk sektörü senin için uygun.","Muhasebe, aktüerya veya risk yönetimi.","Araştırma gazeteciliği veya analitik yazarlık."],
    "enerjik":     ["Girişimcilik, satış veya spor yönetimi alanları enerjiyle örtüşür.","Etkinlik organizasyonu veya turizmde hız ve dinamizmin değer görür.","Start-up ekibi: yüksek tempo, yüksek tatmin."],
    "güvenilir":   ["Bankacılık, sigorta veya hukuk: güven en büyük sermaye.","Kamu görevleri veya kurumsal uyum pozisyonları.","Koçluk ve mentorluk programları."],
    "güçlü":       ["Yöneticilik ve üst düzey liderlik pozisyonları.","Askeri veya güvenlik alanları.","İnşaat mühendisliği, madencilik veya enerji sektörü."],
    "hassas":      ["Psikoterapi, hemşirelik veya sosyal hizmetler.","Sanat terapisi veya müzik terapisi.","Yazarlık, şiir veya sinema."],
    "kararlı":     ["Girişimcilik: vizyonu uygulamaya dökmek senin doğan.","Hukuk veya siyaset: sonuç odaklı kariyer.","Operasyonel liderlik: büyük değişimleri yönetmek."],
    "lider":       ["CEO, yönetim kurulu üyeliği, siyaset.","Start-up kuruculuğu veya büyük proje liderliği.","Uluslararası organizasyon yönetimi."],
    "odaklı":      ["Yazılım geliştirme, mühendislik veya bilimsel araştırma.","Derin uzmanlık gerektiren niche danışmanlık.","Finans veya yatırım: uzun vadeli odak."],
    "pratik":      ["Mühendislik, teknik servis veya operasyon yönetimi.","Girişimcilik: fikirden ürüne pratik köprü.","Proje yönetimi sertifikasyonları (PMP, PRINCE2)."],
    "sezgisel":    ["Psikoloji, felsefe veya spiritüel koçluk.","Sanatsal yaratıcılık gerektiren kariyer yolları.","Ürün tasarımı veya kullanıcı deneyimi araştırması."],
    "sosyal":      ["Satış, müşteri ilişkileri veya topluluk yönetimi.","İnsan kaynakları ve organizasyon geliştirme.","Eğitim, koçluk veya kolaylaştırıcılık."],
    "yaratıcı":    ["Grafik tasarım, UX/UI, içerik üretimi.","Film yapımcılığı, oyun geliştirme veya müzik prodüksiyonu.","Reklam yaratıcı direktörlüğü."],
    "zarif":       ["Moda, lüks marka yönetimi veya stil danışmanlığı.","Mimarlık, iç tasarım veya sanat galerisi yönetimi.","Protokol ve diplomasi."],
    "çekici":      ["Oyunculuk, sunum veya medya.","Marka elçiliği ve kişisel marka yönetimi.","Pazarlama direktörlüğü veya kreatif liderlik."],
}

# ── insan_kaynaklari ─────────────────────────────────────────────────────────
IK = {
    "analitik":    ["Takımlarda veri odaklı kararlar alırsın — performans metrikleri senin güçlü yanın.","Süreç optimizasyonu ve verimlilik iyileştirmelerine doğal olarak katkı koyarsın.","İşe alımda nesnel değerlendirme ölçütleri geliştirirsin."],
    "açık_kalpli": ["Psikolojik güvenlik inşa etmekte ustasın — ekip üyeleri sana kolayca açılır.","Çatışma çözümünde arabulucu rolünü doğal üstlenirsin.","Çeşitlilik ve kapsayıcılık girişimlerine güçlü katkı koyarsın."],
    "cazip":       ["Yetenek çekme ve işveren markası geliştirmede güçlüsün.","Şirket kültürünü dış dünyaya yansıtma konusunda doğal elçisin.","İşe alım süreçlerini daha insancıl ve çekici hale getirirsin."],
    "dengeli":     ["İş-yaşam dengesini destekleyen politikalar geliştirirsin.","Uzlaşı odaklı müzakereler senin için doğal.","Ekip ruh halini istikrarda tutmak güçlü yanın."],
    "dikkatli":    ["Detaylı performans değerlendirme sistemleri tasarlarsın.","Politika ve prosedür dokümantasyonunda ustasın.","Uyumluluk ve etik yönetiminde güvenilir bir kaynak olursun."],
    "enerjik":     ["Yüksek tempolu ortamlarda motivasyon kaynaklısın.","Çalışan bağlılığı programlarını canlandırırsın.","Hızlı büyüyen takımlarda dinamizm sağlarsın."],
    "güvenilir":   ["Çalışanlar sana güvenir — gizliliği titizlikle korursun.","Uzun vadeli çalışan bağlılığı ve elde tutma stratejileri geliştirirsin.","Tutarlı performans değerlendirme süreçleri yönetirsin."],
    "güçlü":       ["Zor kararlar gerektiren işten çıkarma veya yeniden yapılanma süreçlerini yönetirsin.","Güç dinamiklerini iyi okursun — organizasyonel politikada güçlüsün.","Yüksek performanslı takımlar kurma ve yönetme konusunda yeteneklisin."],
    "hassas":      ["Çalışan refahı ve zihinsel sağlık programlarını özenle yönetirsin.","Bireysel ihtiyaçlara duyarlı bire bir koçluk yaparsın.","Zorlu durumları empatiyle ele alırsın."],
    "kararlı":     ["Değişim yönetimi süreçlerinde net mesajlar verirsin.","Hedef odaklı performans kültürü oluşturursun.","Alınan kararlara güçlü sahiplenme gösterirsin."],
    "lider":       ["Kurumsal kültür dönüşümünde vizyon sahibisin.","Yüksek potansiyelli yetenekleri erken tespit edersin.","İK stratejisini iş stratejisiyle entegre edersin."],
    "odaklı":      ["Derin uzmanlık gerektiren L&D (öğrenme ve gelişim) programları tasarlarsın.","Kariyer patikası sistemleri kurarsın.","Performans analitiklerine odaklanırsın."],
    "pratik":      ["Operasyonel İK süreçlerini sadeleştirir ve otomatikleştirirsin.","Maliyet etkin işe alım çözümleri bulursun.","Pratik işe giriş süreçleri tasarlarsın."],
    "sezgisel":    ["Kültürel uyumu sezgisel değerlendirirsin.","İnsanların motivasyonlarını derinlemesine anlarsın.","Yazılı olmayan ekip dinamiklerini okursun."],
    "sosyal":      ["İletişim ve ilişki kurma senin güçlü İK yetkinliğin.","Çalışan toplulukları ve ağ programları oluşturursun.","Onboarding deneyimlerini sıcak ve bağlantılı yaparsın."],
    "yaratıcı":    ["Yenilikçi işe alım kampanyaları ve employer branding geliştirirsin.","Çalışan deneyimini yeniden tasarlarsın.","Oyunlaştırma ve yaratıcı motivasyon araçları kullanırsın."],
    "zarif":       ["Kurumsal protokol ve iletişim standartlarını yönetirsin.","Çalışan etkinlikleri ve şirket kültürü etkinliklerini zarife organize edersin.","Profesyonel gelişim programlarında estetik ve kaliteyi ön plana çıkarırsın."],
    "çekici":      ["Şirket vizyon ve değerlerini ilham verici biçimde anlatırsın.","İşveren markanı iç ve dış paydaşlara etkili sunarsın.","Liderlik gelişim programlarında model olursun."],
}

# ── duygusal_ruhsal ──────────────────────────────────────────────────────────
DUYGUSAL = {
    "analitik":    ["Duygusal süreçlerini 'sistemler' gibi analiz etmek sana netlik sağlar.","Düşünceli öz-farkındalık çalışmaları: günlük tutma, psikoterapi.","Rasyonel ve duygusal zekânı entegre etmek seni tamamlar."],
    "açık_kalpli": ["Derin empatin duygusal gelişimde büyük avantaj.","Başkalarına yardım ederken kendi sınırlarını korumayı öğren.","Şükran pratiği senin için özellikle dönüştürücü."],
    "cazip":       ["Gerçek bağlantı kurma — karizma yüzeyin altında derin ilişkiler.","Kendinle yalnız kalma pratiği iç dünyayla bağı güçlendirir.","Ego ve öz-değer arasındaki farkı keşfetmek gelişim alanın."],
    "dengeli":     ["Denge hali senin için hem güç hem de gelişim alanı.","Duygusal derinliğe izin vermek dengeni tehdit etmez — zenginleştirir.","Orta yolu bulan ruhen dinginsin, bunu besle."],
    "dikkatli":    ["Mükemmeliyetçilik kökenli kaygıyı fark etmek ve serbest bırakmak.","Kendine karşı şefkat geliştirmek — hata yapmak insanlık.","Kontrol ihtiyacını azaltmak özgürleştirici olur."],
    "enerjik":     ["Duraksama ve sessizliğin gücünü keşfet.","Yüksek enerjiyi duygusal ifadeye kanalize etmek sağlıklı çıkış yolu.","Hız kesimlerde içsel sesini duymak gelişim fırsatı."],
    "güvenilir":   ["Güven verirken aynı zamanda kendin için de güvenli bir alan yarat.","Başkalarından beklentilerin hayal kırıklığı yaratmasın — seçici güven.","Uzun vadeli duygusal istikrar senin doğal halin."],
    "güçlü":       ["Kırılganlığı güçsüzlük değil derin güç olarak yeniden çerçevele.","Öfkeyi dönüştürmek: enerjini yapıcı güce çevir.","Güç imgeni aşırı taşımanın yorgunluğuna dikkat et."],
    "hassas":      ["Derin duygusal işleme kapasiten büyük bir güç — onu koru.","Duygusal taşmayı yönetmek: ground etme (topraklanma) teknikleri.","Sanat ve müzik duygusal ifade için güçlü kanallar."],
    "kararlı":     ["Kararlılık ile esneklik arasındaki denge ruhsal büyüme alanın.","Kontrolü bırakmayı öğrenmek — bazı şeyler akışa bırakılır.","Başarı dışında kim olduğunu keşfetmek derinleştirir."],
    "lider":       ["Lider sorumluluğu altındaki kırılgan insanı fark et ve besle.","Empati ve otorite arasındaki dengeyi bulmak olgunluk işareti.","Spiritüel liderlik: vizyonu içsel anlam ile buluştur."],
    "odaklı":      ["Dur ve hisset — sadece yapma, ol.","Zihinsel sessizlik uygulamaları (vipassana, sessiz günler).","Üretkenlik kimliğinin ötesinde kim olduğunu keşfet."],
    "pratik":      ["Pratik ruhsal disiplinler: günlük rutinler, namaz/meditasyon/dua.","Duygusal sağlığın da bir 'sistem' gerektirdiğini kabul et.","Sonuç odaklı düşünceden süreç hazzına geçiş."],
    "sezgisel":    ["Sezgisel içgüdülerini güven veren ritüellerle güçlendir.","Rüya çalışması, aktif hayal gücü, sembolik düşünme.","İç bilgeliğe güven — dıştan çok içe bak."],
    "sosyal":      ["Derin ilişkiler kurmak yüzeysel bağlantıdan daha besleyici.","Yalnız kalma zamanlarını duygusal şarj aracı olarak kullan.","Sosyal enerjiyi duygusal ihtiyaçlarla karıştırma."],
    "yaratıcı":    ["Yaratıcı ifade en güçlü duygusal işleme aracın.","Yaratıcı blokların arkasındaki duyguları keşfet.","Sanat ve ruh birlikte senin için anlam üretir."],
    "zarif":       ["Zarafet dışsal değil içsel bir hal olduğunda en güçlü formuna ulaşır.","Estetik duyarlılığını ruhsal beslenme kaynağına dönüştür.","Ritüel ve güzelliği günlük hayatına ek."],
    "çekici":      ["Dış çekicilik ile iç derinliği buluşturmak bütünlük sağlar.","Seni gerçekten görebilen bağlantılar kurmak duygusal tatmin verir.","Onay ihtiyacından bağımsız güçlü bir iç değer inşa et."],
}

# ── meditasyon_egzersiz ──────────────────────────────────────────────────────
MEDITASYON = {
    "analitik":    ["Nefes sayma meditasyonu: zihin bir sistem gibi çalışır.","Binaural beats ile odak meditasyonu.","Günlük 10 dk 'zihin taraması' (body scan)."],
    "açık_kalpli": ["Metta (sevgi-şefkat) meditasyonu senin için özellikle güçlü.","Şükran meditasyonu: her sabah 3 şükran.","Doğa meditasyonu ve ağaçlarla bağlantı."],
    "cazip":       ["Vizyon meditasyonu: kendin ve etkinin görsel pratiği.","Nefes çalışması ile karizmatik varlık.","Performans öncesi merkez bulma ritüeli."],
    "dengeli":     ["Yin yoga + meditasyon kombinasyonu.","Eşit nefes tekniği (sama vritti): 4-4-4-4.","Günlük 'denge check-in' meditasyonu."],
    "dikkatli":    ["Vipassana meditasyonu: derinlemesine gözlem.","Vücut tarama meditasyonu.","Mindful yürüyüş: her adım farkındalıkla."],
    "enerjik":     ["Dinamik meditasyon (Osho tarzı).","Nefes patlaması (Wim Hof yöntemi).","Enerji meditasyonu ve qi gong."],
    "güvenilir":   ["Düzenli sabah meditasyonu: istikrar ve ritim.","Topraklanma meditasyonu (grounding).","Niyetini belirleme (sankalpa) pratiği."],
    "güçlü":       ["Warrior meditasyonu: güç ve netlik.","Nefes tutma egzersizleri.","Visualization: hedefleri görsel olarak deneyimle."],
    "hassas":      ["Şefkat meditasyonu: önce kendin, sonra diğerleri.","Su sesi veya doğa sesleriyle meditasyon.","Duygu günlüğü + kısa meditasyon kombinasyonu."],
    "kararlı":     ["Hedef meditasyonu: netlik ve odak.","Niyetini sabah sessizliğinde kristalleştir.","Engel aşma meditasyonu: 'bu da geçecek' mantrası."],
    "lider":       ["Liderlik vizyonu meditasyonu.","Sessizlik retreat'leri lider için şarj aracı.","Kolektif başarı görselleştirme."],
    "odaklı":      ["Single-tasking meditasyonu: bir nesneye tam odak.","Pomodoro + kısa meditasyon arası kombinasyonu.","Akış hali (flow state) meditasyonu."],
    "pratik":      ["10 dakikalık minimal meditasyon uygulaması.","Günlük aktiviteler sırasında mindfulness.","Uygulama tabanlı meditasyon (Calm, Headspace)."],
    "sezgisel":    ["Sezgi meditasyonu: 'içgüdüme güven' pratiği.","Aktif hayal gücü ve rehber meditasyonu.","Sessizlik içinde gelen cevapları bekle."],
    "sosyal":      ["Çift veya grup meditasyonu.","Topluluk sağlık ritüelleri.","Paylaşım meditasyonu: deneyimleri anlatmak."],
    "yaratıcı":    ["Yaratıcı akış meditasyonu.","Otomatik yazma öncesi sessizlik ritüeli.","Müzik veya ses ile meditasyon."],
    "zarif":       ["Estetik meditasyon: güzelliğe tam dikkat.","Çay seremonisi / kahve ritüeli meditasyonu.","Aromaterapi + meditasyon kombinasyonu."],
    "çekici":      ["Varlık meditasyonu: ol, izlen, fark et.","Ayna meditasyonu: kendine şefkatle bakma.","Güven inşa meditasyonu."],
}

# ── kitap_tavsiye ────────────────────────────────────────────────────────────
KITAP = {
    "analitik":    ["'Thinking, Fast and Slow' — Daniel Kahneman","'The Signal and the Noise' — Nate Silver","'Sapiens' — Yuval Noah Harari"],
    "açık_kalpli": ["'Kırılganlığın Gücü' — Brené Brown","'Man's Search for Meaning' — Viktor Frankl","'The Art of Empathy' — Karla McLaren"],
    "cazip":       ["'How to Win Friends and Influence People' — Dale Carnegie","'Pre-Suasion' — Robert Cialdini","'The Charisma Myth' — Olivia Fox Cabane"],
    "dengeli":     ["'The Subtle Art of Not Giving a F*ck' — Mark Manson","'Stoicism and the Art of Happiness' — Donald Robertson","'Essentialism' — Greg McKeown"],
    "dikkatli":    ["'Deep Work' — Cal Newport","'Atomic Habits' — James Clear","'The Checklist Manifesto' — Atul Gawande"],
    "enerjik":     ["'Spark' — John Ratey","'Can't Hurt Me' — David Goggins","'Drive' — Daniel Pink"],
    "güvenilir":   ["'The Speed of Trust' — Stephen Covey","'Start with Why' — Simon Sinek","'Integrity' — Henry Cloud"],
    "güçlü":       ["'Extreme Ownership' — Jocko Willink","'12 Rules for Life' — Jordan Peterson","'The Way of the Superior Man' — David Deida"],
    "hassas":      ["'Highly Sensitive Person' — Elaine Aron","'Healing the Child Within' — Charles Whitfield","'The Gifts of Imperfection' — Brené Brown"],
    "kararlı":     ["'Mindset' — Carol Dweck","'Grit' — Angela Duckworth","'The 5 AM Club' — Robin Sharma"],
    "lider":       ["'Leaders Eat Last' — Simon Sinek","'Good to Great' — Jim Collins","'The 21 Irrefutable Laws of Leadership' — John Maxwell"],
    "odaklı":      ["'Flow' — Mihaly Csikszentmihalyi","'Deep Work' — Cal Newport","'The One Thing' — Gary Keller"],
    "pratik":      ["'Getting Things Done' — David Allen","'The Lean Startup' — Eric Ries","'Tools of Titans' — Tim Ferriss"],
    "sezgisel":    ["'Blink' — Malcolm Gladwell","'The Power of Now' — Eckhart Tolle","'Gut' — Giulia Enders"],
    "sosyal":      ["'Never Eat Alone' — Keith Ferrazzi","'Connected' — Nicholas Christakis","'The Like Switch' — Jack Schafer"],
    "yaratıcı":    ["'Steal Like an Artist' — Austin Kleon","'Big Magic' — Elizabeth Gilbert","'The Artist's Way' — Julia Cameron"],
    "zarif":       ["'The Life-Changing Magic of Tidying Up' — Marie Kondo","'S'habiller sans se ruiner' — Ines de la Fressange","'The Art of Elegance' — Madeleine Marsh"],
    "çekici":      ["'The Attraction Code' — Vin DiCarlo","'Presence' — Amy Cuddy","'The Laws of Human Nature' — Robert Greene"],
}

# ── film_tavsiye ─────────────────────────────────────────────────────────────
FILM = {
    "analitik":    ["'The Imitation Game' (2014) — Alan Turing'in dehası","'A Beautiful Mind' (2001) — matematik ve akıl","'Ex Machina' (2014) — yapay zeka ve etik"],
    "açık_kalpli": ["'Forrest Gump' (1994) — sevgi ve anlam","'The Pursuit of Happyness' (2006) — umut","'Patch Adams' (1998) — şefkat ve iyileşme"],
    "cazip":       ["'The Wolf of Wall Street' (2013) — ikna gücü","'Catch Me If You Can' (2002) — karizmatik kimlik","'The Great Gatsby' (2013) — çekicilik ve hayal"],
    "dengeli":     ["'The Peaceful Warrior' (2006) — denge ve anlam","'Into the Wild' (2007) — sadelik arayışı","'Zen and the Art of Archery' — belgesel"],
    "dikkatli":    ["'Zodiac' (2007) — titiz araştırma","'Whiplash' (2014) — mükemmeliyetçilik ve bedeli","'The Girl with the Dragon Tattoo' (2011) — detaycı bakış"],
    "enerjik":     ["'Rocky' serisi — kararlılık ve enerji","'Mad Max: Fury Road' (2015) — yüksek tempo","'The Social Network' (2010) — girişim hızı"],
    "güvenilir":   ["'Spotlight' (2015) — dürüstlük ve sorumluluk","'12 Angry Men' (1957) — adalet ve güven","'The Blind Side' (2009) — sadakat"],
    "güçlü":       ["'Gladiator' (2000) — güç ve onur","'The Dark Knight' (2008) — irade","'Braveheart' (1995) — cesaret"],
    "hassas":      ["'Her' (2013) — derin bağlantı arayışı","'Inside Out' (2015) — duygusal dünya","'A Monster Calls' (2016) — acı ve kabul"],
    "kararlı":     ["'The Pursuit of Happyness' (2006) — asla vazgeçme","'Interstellar' (2014) — sınır ötesi kararlılık","'127 Hours' (2010) — hayatta kalma iradesi"],
    "lider":       ["'Lincoln' (2012) — vizyoner liderlik","'The King's Speech' (2010) — liderlik ve dönüşüm","'Moneyball' (2011) — veriye dayalı liderlik"],
    "odaklı":      ["'Shutter Island' (2010) — odak ve gerçeklik","'Black Swan' (2010) — mükemmeliyete odak","'The Martian' (2015) — çözüm odaklılık"],
    "pratik":      ["'The Intern' (2015) — pratik bilgelik","'Office Space' (1999) — iş hayatı satiri","'Julie & Julia' (2009) — pratik tutku"],
    "sezgisel":    ["'Inception' (2010) — bilinç ve rüya","'Donnie Darko' (2001) — sezgisel gerçeklik","'The Matrix' (1999) — algı ve sezgi"],
    "sosyal":      ["'The Social Network' (2010) — bağlantı gücü","'Love Actually' (2003) — ilişkiler ağı","'Eat Pray Love' (2010) — sosyal yolculuk"],
    "yaratıcı":    ["'Whiplash' (2014) — sanatsal tutku","'Big Eyes' (2014) — yaratıcı kimlik","'Ed Wood' (1994) — saf yaratıcılık"],
    "zarif":       ["'The Grand Budapest Hotel' (2014) — estetik şaheser","'Amélie' (2001) — zarif hayaller","'Midnight in Paris' (2011) — nostaljik güzellik"],
    "çekici":      ["'Crazy, Stupid, Love' (2011) — dönüşüm ve çekicilik","'The Tao of Steve' (2000) — çekim kanunları","'Hitch' (2005) — sosyal çekicilik"],
}

# ── muzik_tavsiye ─────────────────────────────────────────────────────────────
MUZIK = {
    "analitik":    ["Bach fügleri — matematik ve müzik birliği","Hans Zimmer soundtrackler — sinematik odak","Radiohead — kompleks yapılar ve derin düşünce"],
    "açık_kalpli": ["Norah Jones — sıcak ve içten","Nick Drake — hassas ve derin","Florence + the Machine — ruhsal yükseliş"],
    "cazip":       ["Frank Sinatra — karizmatik klasik","The Weeknd — modern karizmatik ses","Marvin Gaye — duygusal ikna gücü"],
    "dengeli":     ["Brian Eno — ambient denge","Bon Iver — organik denge","Sigur Rós — minimalist huzur"],
    "dikkatli":    ["Beethoven sonatları — titiz yapı","Thom Yorke solo — detayı duyumsamak","Sufjan Stevens — özenli katmanlı ses"],
    "enerjik":     ["Daft Punk — enerji ve ritim","Rage Against the Machine — patlayıcı enerji","Linkin Park — yoğun ifade"],
    "güvenilir":   ["Johnny Cash — güvenilir ve derin","Adele — tutarlı duygusal güç","Tom Waits — özgün ve samimi"],
    "güçlü":       ["Hans Zimmer — 'Inception' OST","Queens of the Stone Age — ham güç","Metallica — çelik iradenin müziği"],
    "hassas":      ["Billie Eilish — hassas ve şeffaf","Lana Del Rey — derin duygusal katmanlar","Ólafur Arnalds — kırılgan güzellik"],
    "kararlı":     ["Rocky OST — 'Eye of the Tiger'","Kanye West — kararlı üretim","Jay-Z — irade ve başarı anlatısı"],
    "lider":       ["U2 — vizyoner rock","Hans Zimmer — lider sahne müzikleri","The Beatles — evrensel ilham"],
    "odaklı":      ["Tycho — odak ambient","Brian Eno — Music for Airports","Lo-fi hip hop — çalışma müziği"],
    "pratik":      ["Jack Johnson — sade ve keyifli","Ben Harper — doğrudan ve sıcak","Vampire Weekend — pratik zevk"],
    "sezgisel":    ["Bjork — sezgisel keşif","Portishead — sezgisel karanlık","Massive Attack — alt bilinç müziği"],
    "sosyal":      ["Pharrell Williams — sosyal mutluluk","Stevie Wonder — evrensel bağlantı","Ed Sheeran — samimi yakınlık"],
    "yaratıcı":    ["David Bowie — sınırsız yaratıcılık","Beck — deneysel özgünlük","Frank Zappa — sınırları zorlamak"],
    "zarif":       ["Chet Baker — zarif caz","Satie Gymnopédies — minimal zarafet","Édith Piaf — Fransız zarif derinlik"],
    "çekici":      ["The Weeknd — çekicilik ve gece","Dua Lipa — modern karizmatik pop","Justin Timberlake — sofistike pop çekicilik"],
}

# ── podcast_tavsiye ──────────────────────────────────────────────────────────
PODCAST = {
    "analitik":    ["'Lex Fridman Podcast' — derin teknoloji ve bilim","'The Knowledge Project' — Farnam Street zihinsel modeller","'Freakonomics Radio' — veriyle hayatı anlamak"],
    "açık_kalpli": ["'On Being' — Krista Tippett ile anlam ve ruh","'The Tim Ferriss Show' — insan hikayeleri","'Unlocking Us' — Brené Brown ile bağlantı"],
    "cazip":       ["'The Art of Charm' — sosyal etki ve karizm","'How I Built This' — girişimcilik hikayeleri","'Jocko Podcast' — disiplin ve etki"],
    "dengeli":     ["'The Daily Stoic' — günlük denge","'10% Happier' — meditasyon ve gündelik yaşam","'On Purpose' — Jay Shetty ile denge"],
    "dikkatli":    ["'Stuff You Should Know' — detaylı bilgi","'Revisionist History' — Malcolm Gladwell","'Hidden Brain' — bilinçaltı ve davranış"],
    "enerjik":     ["'The School of Greatness' — yüksek performans","'Impact Theory' — enerji ve büyüme","'MFCEO Project' — yüksek enerji iş hayatı"],
    "güvenilir":   ["'Invest Like the Best' — güvenilir yatırım","'Masters of Scale' — Reid Hoffman","'The Moth' — hikaye güvenilirliği"],
    "güçlü":       ["'Jocko Podcast' — güç ve disiplin","'Jordan Harbinger Show' — güç dinamikleri","'No Mercy / No Malice' — Scott Galloway"],
    "hassas":      ["'Unlocking Us' — Brené Brown","'Where Should We Begin?' — Esther Perel","'This American Life' — insan hikayeleri"],
    "kararlı":     ["'Finding Mastery' — zihinsel performans","'Mindset Mentor' — Rob Dial","'The Daily Stoic' — günlük kararlılık"],
    "lider":       ["'HBR IdeaCast' — liderlik araştırmaları","'Masters of Scale' — lider hikayeleri","'The Knowledge Project' — lider zihniyeti"],
    "odaklı":      ["'Deep Questions' — Cal Newport","'The Knowledge Project' — Farnam Street","'Huberman Lab' — beyin ve odak bilimi"],
    "pratik":      ["'How I Built This' — pratik girişimcilik","'The GaryVee Audio Experience' — pratik tavsiye","'My First Million' — pratik iş fikirleri"],
    "sezgisel":    ["'The Moth' — içgüdüsel hikaye","'Invisibilia' — görünmez güçler","'Future of Life Institute' — derin sezgi"],
    "sosyal":      ["'SmartLess' — eğlenceli sosyal","'Conan O'Brien Needs a Friend' — sosyal komedi","'Call Her Daddy' — ilişki ve sosyal dinamik"],
    "yaratıcı":    ["'Creative Pep Talk' — yaratıcı güçlenme","'99% Invisible' — tasarım ve yaratıcılık","'Song Exploder' — müzik yaratım süreci"],
    "zarif":       ["'The Business of Fashion' — moda ve estetik","'The Tim Ferriss Show' — zevkli üretim","'Design Matters' — Debbie Millman ile tasarım"],
    "çekici":      ["'The Art of Charm' — çekicilik ve etki","'Charisma on Command' (YouTube) — karizmatik iletişim","'The School of Greatness' — çekici liderlik"],
}

# ── seyahat_tavsiye ──────────────────────────────────────────────────────────
SEYAHAT = {
    "analitik":    ["Japonya — sistemler, verimlilik ve hassas kültür.","İskandinavya — sosyal düzen ve tasarım mükemmeliyeti.","Almanya — mühendislik ve pratik güzellik."],
    "açık_kalpli": ["Hindistan — renkli, karmaşık, insancıl.","Güney Amerika — açık yürekli insanlar ve sıcaklık.","Fas — kültürler arası köprü ve misafirperver kültür."],
    "cazip":       ["İtalya — çekicilik, stil ve tarih.","Fransa — zarafet ve etkileyici kültür.","Dubai — lüks ve görünürlük."],
    "dengeli":     ["Bali — denge, ruhsallık ve doğa.","Portekiz — sakin, dengeli yaşam temposu.","Yeni Zelanda — doğa ve huzur."],
    "dikkatli":    ["Atina — tarih ve detaylar.","Vatikan — sanat ve mimari mükemmeliyeti.","Kyoto — titiz geleneksel kültür."],
    "enerjik":     ["Brezilya — enerji, festival ve canlılık.","Barcelona — dinamizm ve gece hayatı.","New York — yüksek hız ve şehir enerjisi."],
    "güvenilir":   ["İsviçre — güvenlik, istikrar ve dürüstlük.","Kanada — güvenli ve kapsayıcı.","Norveç — güvenilir kamu sistemleri."],
    "güçlü":       ["Peru / Machu Picchu — güç ve meydan okuma.","Nepal / Everest bölgesi — insanın sınırları.","İzlanda — doğanın ham gücü."],
    "hassas":      ["Toskana / İtalya — sanat ve hassas güzellik.","Kyoto — sessizlik ve hassas estetik.","İrlanda — doğa ve melankoli."],
    "kararlı":     ["Alaska — uç koşullarda karar verme.","Patagonya — sınır testi ve kararlılık.","Moğolistan — özgür ve kararlı yaşam."],
    "lider":       ["Washington D.C. — güç merkezleri.","Brüksel / Cenevre — uluslararası organizasyonlar.","Singapur — küresel liderlik modeli."],
    "odaklı":      ["Japonya (Kyoto + Tokyo) — odak ve ritüel.","Finlandiya — sakin, derin odak kültürü.","Tibet — derin sessizlik ve içe bakış."],
    "pratik":      ["Hollanda — pratik ve fonksiyonel şehir yaşamı.","Singapur — verimli ve pratik uluslararası şehir.","Almanya — seyahat lojistiği mükemmel."],
    "sezgisel":    ["Peru / Şamanizm rotaları — sezgi ve ritüel.","Hindistan (Rishikesh, Varanasi) — ruhsal sezgi.","Meksika — efsane ve mitoloji kültürü."],
    "sosyal":      ["Brezilya (Rio) — en sosyal kültürlerden biri.","İspanya — tapas kültürü ve sosyal akşamlar.","Tayland — misafirperver ve canlı sosyal ortam."],
    "yaratıcı":    ["Berlin — sanat, müzik ve yaratıcı özgürlük.","Buenos Aires — bohemyen ve yaratıcı.","Çek Cumhuriyeti / Prag — mimari yaratıcılık."],
    "zarif":       ["Paris — zarafetin başkenti.","Floransa — sanat ve estetik zirve.","Viyana — klasik zarafet ve kültür."],
    "çekici":      ["Monaco — lüks ve çekicilik.","Los Angeles — imaj ve güzellik kültürü.","Miami — çekicilik ve uluslararası kozmopolit."],
}

# ── gunluk_afirasyon ─────────────────────────────────────────────────────────
AFIRASYON = {
    "analitik":    ["Zihnim berrak, kararlarım isabetli.","Verilerin ardındaki gerçeği görme yetkim güçleniyor.","Her analiz beni daha derin bir anlayışa taşır."],
    "açık_kalpli": ["Kalbim açık, dünyam geniş.","Sevmek benim en güçlü eylemim.","Empatin bir güçtür — onu taşımaya değer."],
    "cazip":       ["Varlığım ilham verir.","Doğal karizmayla insanlara ulaşıyorum.","Etkim olumlu — hayatları dokunsam da iz kalır."],
    "dengeli":     ["Her durumda merkezimi buluyorum.","Denge benim doğal halim.","Sakinlik kaos içinde en güçlü silahım."],
    "dikkatli":    ["Detaylar sihir taşır — ben onu görüyorum.","Titizliğim başarının temelidir.","Her şeyi zamanında ve eksiksiz yapabilirim."],
    "enerjik":     ["Enerjim bir hediyedir — onu akıllıca kullanıyorum.","Her sabah dolu ve canlı uyanıyorum.","Hareketle büyüyorum, dinginlikle şarj oluyorum."],
    "güvenilir":   ["Sözlerim bağlanma değeri taşır.","Güven inşa etmek benim doğal gücüm.","Tutarlılığım en büyük sermayem."],
    "güçlü":       ["Gücüm dışarıdan değil içerimden geliyor.","Zorluklar beni keskinleştirir.","Korkuyu hissedip yine de ilerliyorum."],
    "hassas":      ["Duyarlılığım bir zayıflık değil, derinliktir.","Duymak, hissetmek ve anlamak benim güçlerim.","Kırılganlığım bağlantı kapım."],
    "kararlı":     ["Kararım aldığımda dünya beni durduramaz.","İradem her engelin üstündedir.","Bugün aldığım adım yarınımı kuruyor."],
    "lider":       ["İnsanlar bende bir yön buluyor.","Liderlik sözde değil, eylemde yaşıyor.","Vizyonum gerçeğe dönüşmek için bekliyor."],
    "odaklı":      ["Dikkatim nereye giderse güç oraya akar.","Bir şeye tam odaklandığımda sınırım yok.","Derin çalışma benim süper gücüm."],
    "pratik":      ["Hayal değil, adım attığımda gerçek olur.","Pratik çözümler benim dilimidir.","Ellerim ve zihnimle dünyayı şekillendiriyorum."],
    "sezgisel":    ["İçgüdülerimi duyuyorum ve güveniyorum.","Sezgim yol haritam.","Sessizlikte gerçeği buluyorum."],
    "sosyal":      ["Bağlantılar kurduğumda hem ben hem diğerleri büyüyor.","Her ilişki bir öğrenme fırsatıdır.","Sevgi ve merakla yaklaştığımda kapılar açılır."],
    "yaratıcı":    ["Her gün biraz daha özgün oluyorum.","Yaratıcılığım sonsuz bir kaynaktan besleniyor.","Dünya benim için bir tuval."],
    "zarif":       ["Zarafet içten gelir — onu taşıyorum.","Güzelliği görmek ve yaratmak benim ayrıcalığım.","Her jest, her söz, her bakış özen taşır."],
    "çekici":      ["Kendim olduğumda en çekiciyimdir.","Özgünlüğüm benim en büyük çekimim.","Varlığım değer katar."],
}

# ── saglik_tavsiye ─────────────────────────────────────────────────────────────
SAGLIK_TAV = {
    "analitik":    {"beslenme": "Bilinçli kalori takibi ve makro hesaplama.","uyku": "Uyku kalitesini izlemek için wearable veya uygulama kullan.","hareket": "Veriye dayalı antrenman takibi."},
    "açık_kalpli": {"beslenme": "Bitkisel ve tam gıda odaklı beslenme.","uyku": "Akşam yatmadan 1 saat dijital detoks.","hareket": "Grup fitness dersleri veya topluluk koşusu."},
    "cazip":       {"beslenme": "Görsel sunumu da güzel olan sağlıklı öğünler.","uyku": "Uyku öncesi cilt bakımı ritüeli.","hareket": "Dans veya sosyal sporlar."},
    "dengeli":     {"beslenme": "Mevsimsel ve dengeli tabak: protein + karbonhidrat + yağ.","uyku": "8 saat + düzenli uyku saati.","hareket": "Yoga, pilates veya hafif kardiyo."},
    "dikkatli":    {"beslenme": "Besin değeri etiketlerini oku ve takip et.","uyku": "Uyku ortamını optimize et: oda sıcaklığı, karanlık, sessizlik.","hareket": "Haftalık antrenman programı planlama."},
    "enerjik":     {"beslenme": "Yüksek proteinli ve enerji yoğun öğünler.","uyku": "Gün içinde kısa 20 dk power nap.","hareket": "Günlük yüksek yoğunluklu antrenman (HIIT)."},
    "güvenilir":   {"beslenme": "Tutarlı öğün saatleri ve düzenli yemek.","uyku": "Düzenli uyku rutini — haftasonu da bozma.","hareket": "Haftalık yapılandırılmış fitness planı."},
    "güçlü":       {"beslenme": "Kas yapımı için yeterli protein ve kalori.","uyku": "Antrenman sonrası iyileşme için 8 saat uyku.","hareket": "Güç antrenmanı + aktif iyileşme günleri."},
    "hassas":      {"beslenme": "Bağırsak dostu beslenme: fermente gıda, prebiyotik.","uyku": "Uyku öncesi gevşeme ritüeli — meditasyon veya nefes.","hareket": "Nazik, sürdürülebilir hareket: yürüyüş, yüzme, yin yoga."},
    "kararlı":     {"beslenme": "Hedef odaklı beslenme planı ve kişisel protokol.","uyku": "Uyku verimliliğini takip et ve optimize et.","hareket": "Kısa sürede maksimum sonuç: HIIT veya tabata."},
    "lider":       {"beslenme": "Lider enerjisi için anti-enflamatuar diyet.","uyku": "Lider recovery: uyku en güçlü iyileşme aracı.","hareket": "Sabah rutini: egzersiz + meditasyon + soğuk duş."},
    "odaklı":      {"beslenme": "Beyin için omega-3, magnezyum ve B vitaminleri.","uyku": "REM uykusu için kafein sınırı (14:00 sonrası yok).","hareket": "Çalışma aralarında kısa yürüyüş ve germe."},
    "pratik":      {"beslenme": "Haftalık meal prep: pratik ve besleyici hazırlık.","uyku": "Basit uyku hijyeni kuralları listesi.","hareket": "Her gün 30 dk, herhangi bir hareket."},
    "sezgisel":    {"beslenme": "Sezgisel yeme: vücudun sinyallerini dinle.","uyku": "Uyku sinyallerine güven — vücudun ne zaman yorulduğunu bilir.","hareket": "Bedeni dinleyerek hareket — zorlama değil, akış."},
    "sosyal":      {"beslenme": "Sosyal yemekler: paylaşımın verdiği enerji.","uyku": "Sosyal etkinlik sonrası introverted iyileşme uykusu.","hareket": "Grup sporları ve takım egzersizleri."},
    "yaratıcı":    {"beslenme": "Deneysel yemek yapımı: sağlıklı + yaratıcı tarifler.","uyku": "Rüya günlüğü: uyku seni de besler.","hareket": "Yaratıcı hareket: dans, akrobasi, parkur."},
    "zarif":       {"beslenme": "Estetik tabak sunumu + kaliteli malzeme.","uyku": "Premium uyku deneyimi: kaliteli yatak, ipek yastık.","hareket": "Bale egzersizleri, pilates veya yüzme."},
    "çekici":      {"beslenme": "Deri ve saç sağlığı için antioksidan zengin beslenme.","uyku": "Beauty sleep: cilt yenilenmesi için 8 saat.","hareket": "Estetiği destekleyen egzersizler: dans, yüzme, yoga."},
}

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _join(items): return '\n'.join(items)

def build_entry_tr(archetype: str) -> dict:
    a = archetype
    etk_in  = ETK_INDOOR.get(a,  ETK_INDOOR["analitik"])
    etk_out = ETK_OUTDOOR.get(a, ETK_OUTDOOR["analitik"])
    spor    = SPOR.get(a,  SPOR["analitik"])
    kariyer = KARIYER.get(a, KARIYER["analitik"])
    ik      = IK.get(a, IK["analitik"])
    duyg    = DUYGUSAL.get(a, DUYGUSAL["analitik"])
    medit   = MEDITASYON.get(a, MEDITASYON["analitik"])
    kitap   = KITAP.get(a, KITAP["analitik"])
    film    = FILM.get(a, FILM["analitik"])
    muzik   = MUZIK.get(a, MUZIK["analitik"])
    pod     = PODCAST.get(a, PODCAST["analitik"])
    seyah   = SEYAHAT.get(a, SEYAHAT["analitik"])
    afir    = AFIRASYON.get(a, AFIRASYON["analitik"])
    saglik  = SAGLIK_TAV.get(a, SAGLIK_TAV["analitik"])
    trait   = ARCH_TRAITS_TR.get(a, a)

    return {
        "etkinlik_tavsiye": _join([
            f"🏠 Kapalı Alan Etkinlikleri",
            *random.sample(etk_in, min(3, len(etk_in))),
            "",
            f"🌳 Açık Alan Etkinlikleri",
            *random.sample(etk_out, min(3, len(etk_out))),
        ]),
        "spor_aktivite": _join([
            f"🏅 Sana Uygun Sporlar ({trait})",
            *random.sample(spor, min(3, len(spor))),
        ]),
        "kariyer_yolu": _join([
            f"💼 Kariyer Profili ({trait})",
            *random.sample(kariyer, min(3, len(kariyer))),
        ]),
        "insan_kaynaklari": _join([
            f"👥 İş Hayatında Güçlü Yanların",
            *random.sample(ik, min(3, len(ik))),
        ]),
        "duygusal_ruhsal": _join([
            f"💜 Duygusal ve Ruhsal Gelişim",
            *random.sample(duyg, min(3, len(duyg))),
        ]),
        "meditasyon_egzersiz": _join([
            f"🧘 Meditasyon Önerileri",
            *random.sample(medit, min(3, len(medit))),
        ]),
        "kitap_tavsiye": _join([
            f"📚 Kitap Tavsiyeleri",
            *random.sample(kitap, min(3, len(kitap))),
        ]),
        "film_tavsiye": _join([
            f"🎬 Film ve Dizi Tavsiyeleri",
            *random.sample(film, min(3, len(film))),
        ]),
        "muzik_tavsiye": _join([
            f"🎵 Müzik Tavsiyeleri",
            *random.sample(muzik, min(3, len(muzik))),
        ]),
        "podcast_tavsiye": _join([
            f"🎙️ Podcast Tavsiyeleri",
            *random.sample(pod, min(3, len(pod))),
        ]),
        "seyahat_tavsiye": _join([
            f"✈️ Seyahat Tavsiyeleri",
            *random.sample(seyah, min(3, len(seyah))),
        ]),
        "gunluk_afirasyon": _join([
            f"✨ Günlük Afirmasyonlar",
            *random.sample(afir, min(3, len(afir))),
        ]),
        "saglik_tavsiye": _join([
            f"🌿 Sağlık Tavsiyeleri",
            f"🥗 Beslenme: {saglik['beslenme']}",
            f"😴 Uyku: {saglik['uyku']}",
            f"🏃 Hareket: {saglik['hareket']}",
        ]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# TRANSLATION
# ─────────────────────────────────────────────────────────────────────────────

def translate_entry(entry: dict, target_lang: str) -> dict:
    if not TRANSLATE_OK:
        return entry
    result = {}
    translator = GoogleTranslator(source='tr', target=target_lang)
    for key, text in entry.items():
        try:
            time.sleep(0.2)  # rate limit
            translated = translator.translate(text[:4500])
            result[key] = translated if translated else text
        except Exception as e:
            print(f"  ⚠️ translate error [{key}]: {e}")
            result[key] = text
    return result


# Google Translate lang codes differ from our codes
_GT_MAP = {
    "tr": "tr", "en": "en", "de": "de", "ru": "ru", "ar": "ar",
    "es": "es", "ko": "ko", "ja": "ja", "zh": "zh-CN", "hi": "hi",
    "fr": "fr", "pt": "pt", "bn": "bn", "id": "id", "ur": "ur",
    "it": "it", "vi": "vi", "pl": "pl",
}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def generate_for_lang(lang: str) -> dict:
    """Generate all archetypes for a language."""
    print(f"\n  [{lang}] generating {len(ARCHETYPES)} archetypes...")
    result = {}
    for arch in ARCHETYPES:
        tr_entry = build_entry_tr(arch)
        if lang == "tr":
            result[arch] = tr_entry
        else:
            gt_lang = _GT_MAP.get(lang, lang)
            print(f"    translating {arch} → {lang}...", end=" ", flush=True)
            result[arch] = translate_entry(tr_entry, gt_lang)
            print("✓")
    return result


def push_to_mongo(lang: str, data: dict, dry_run: bool = False):
    if not MONGO_OK:
        print("  ⚠️ pymongo yok — MongoDB'ye yazılamıyor")
        return
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    db     = client[BACKUP_DB]
    lang_col = _LANG_COL_MAP.get(lang, lang)
    col    = db[f"coach_attributes_{lang_col}"]

    ops = [
        UpdateOne(
            {"_id": arch},
            {"$set": {
                **entry,
                "updated_at": datetime.now().isoformat(),
                "patch_v": "media_modules_v1",
            }},
            upsert=True,
        )
        for arch, entry in data.items()
    ]

    if dry_run:
        print(f"  [DRY RUN] {lang}: {len(ops)} ops hazır (yazılmadı)")
        return

    result = col.bulk_write(ops)
    total  = result.upserted_count + result.modified_count
    print(f"  {lang}: {total} kayıt güncellendi → {BACKUP_DB}.coach_attributes_{lang_col}")
    client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",  action="store_true", help="MongoDB'ye yazma")
    parser.add_argument("--lang",     default=None, help="Tek bir dil işle (tr, en, ...)")
    parser.add_argument("--no-mongo", action="store_true", help="MongoDB adımını atla")
    parser.add_argument("--save-json",action="store_true", help="Her dil için JSON dosyası kaydet")
    args = parser.parse_args()

    langs = [args.lang] if args.lang else ALL_LANGS
    out_dir = Path(__file__).parent

    print(f"patch_media_modules.py — {len(NEW_MODULES)} yeni modül, {len(langs)} dil")
    print("=" * 60)

    for lang in langs:
        data = generate_for_lang(lang)

        if args.save_json:
            out_path = out_dir / f"patch_media_{lang}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  [{lang}] JSON kaydedildi → {out_path.name}")

        if not args.no_mongo and not args.dry_run:
            push_to_mongo(lang, data, dry_run=False)
        elif args.dry_run:
            push_to_mongo(lang, data, dry_run=True)

    print("\n✅ Tamamlandı.")


if __name__ == "__main__":
    main()
