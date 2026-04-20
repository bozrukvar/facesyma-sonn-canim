"""
facesyma_coach/dataset/generate_giyim_dataset.py
================================================
201 sıfat için kişiselleştirilmiş giyim tavsiyesi verisini üretir.

Özellikleri:
- 10 stil profiline sıfat eşlemesi (klasik-minimalist, yaratıcı-bohemyen, vb.)
- Mevsim × Kategori × Parça/Kumaş/Aksesuar/İpucu
- Yüz şekli notları (oval, kare, yuvarlak, kalp, uzun, elmas)
- 18 dil desteği
- MongoDB facesyma-coach-backup'a giyim field olarak upsert

Kullanım:
  python generate_giyim_dataset.py --lang tr --output sifat_giyim_tr.json
  python generate_giyim_dataset.py --all-langs
  python generate_giyim_dataset.py --push-mongo --all-langs
"""

import json
import random
import argparse
import sys
from pathlib import Path
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─────────────────────────────────────────────────────────────────────────────
# OLLAMA LLM — Coaching insights'ları dile çevir (paralel)
# ─────────────────────────────────────────────────────────────────────────────

LANG_NAMES = {
    "tr": "Turkish",
    "en": "English",
    "de": "German",
    "ru": "Russian",
    "ar": "Arabic",
    "es": "Spanish",
    "ko": "Korean",
    "ja": "Japanese",
    "zh": "Chinese",
    "hi": "Hindi",
    "fr": "French",
    "pt": "Portuguese",
    "bn": "Bengali",
    "id": "Indonesian",
    "ur": "Urdu",
    "it": "Italian",
    "vi": "Vietnamese",
    "pl": "Polish",
}

TRANSLATION_CACHE = {}

def translate_coaching(text: str, target_lang: str) -> str:
    """Google Translate ile coaching'i hedef dile çevir (cache ile)."""
    if target_lang == "tr":
        return text  # Türkçe zaten var

    cache_key = f"{target_lang}:{hash(text) % 10000}"
    if cache_key in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[cache_key]

    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source='tr', target=target_lang).translate(text)
        TRANSLATION_CACHE[cache_key] = translated
        return translated
    except Exception as e:
        pass

    return text  # Fallback: original

def translate_coaching_batch(coaching_dict: dict, target_lang: str) -> dict:
    """4 coaching field'ını paralel çevir."""
    if target_lang == "tr":
        return coaching_dict

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            field: executor.submit(translate_coaching, text, target_lang)
            for field, text in coaching_dict.items()
        }
        return {field: futures[field].result() for field in coaching_dict}

# ─────────────────────────────────────────────────────────────────────────────
# CİNSİYETE GÖRE PARÇA DEĞİŞİKLİKLERİ — erkek/kadın tavsiye farkları
# ─────────────────────────────────────────────────────────────────────────────

GENDER_REPLACEMENTS = {
    "erkek": {
        "elbise": "pantolon",
        "bluz": "gömlek",
        "midi skirt": "chino",
        "crop top": "t-shirt",
        "romper": "overall",
        "wrap dress": "blazer pantolon",
        "maxi dress": "long coat pantolon",
        "turuncu midi dress": "turuncu gömlek",
        "rose midi gown": "rose suit",
        "blush dress": "blush gömlek",
        "pale pink dress": "pale blue gömlek",
        "dusty rose dress": "dusty blue gömlek",
        "burgundy maxi dress": "burgundy suit",
        "blush wool coat": "blush cardigan coat",
    },
    "kadın": {},  # Hiçbir değişiklik — base şablonlar kadın-optimized
}

# ─────────────────────────────────────────────────────────────────────────────
# STİL PROFİLİ ŞABLONLARI — 10 tip, mevsim × kategori kombinasyonları
# ─────────────────────────────────────────────────────────────────────────────

STIL_TEMPLATES = {
    "klasik-minimalist": {
        "coaching": {
            "felsefe": "Basitlik ve işlevsellik felsefesi. Kalabalık olmayan, amaca yönelik giyim seçimleri. Her parça bir amaç taşır; hiçbir şey tesadüfi değildir.",
            "kombinasyon": "Temel kural: Nötr renk temelinden başla (#2C3E50, #8E9B90), maksimum 2-3 renk kullan. Bir vurgu parçası yeterlidir. Monokrom kombinasyonlar sık sık tercih edilir.",
            "renk_psikolojisi": "Koyu tonlar (antrasit, gri, navy) güven ve profesyonellik verir. Bej ve krem toprak renkleri sıcaklık katarak katılık kırılır. Altın vurgusu incelik ve zarafet sunar.",
            "yaşam_uyarlamasi": "Sabah rutininizi basit tutun: temel parçalar (beyaz tee, siyah pantolon) + bir aksesuar. Minimalist giyim mantığı zaman kazandırır ve karar yorgunluğunu azaltır. Kaliteli, dayanıklı parçalara yatırım yapın."
        },
        "renk_paleti": {
            "ana": ["#2C3E50", "#8E9B90", "#F5F0E8", "#BDC3C7"],
            "vurgu": ["#C9A84C", "#8B6914"],
            "kacin": ["parlak neon", "çok renkli"],
        },
        "ilkbahar": {
            "gunluk": {
                "parca": ["açık mavi gömlek", "bej chino", "beyaz sneaker"],
                "kumas": ["pamuk", "keten"],
                "kesim": "rahat-fitted",
                "aksesuar": ["basit saat", "minimal kolye"],
                "ipucu": "Pastel tonlar ilkbahar enerjisini yansıtır; nötr temel + tek vurgu parçası kuralı.",
            },
            "spor": {
                "parca": ["gri hoodie", "jogger", "running shoe"],
                "kumas": ["cotton blend", "polyester"],
                "kesim": "relaxed-athletic",
                "aksesuar": ["sports watch", "cap"],
                "ipucu": "Nefes alan kumaşlar yoğun aktiviteler için kritik; monoton renkler dikkat dağıtmaz.",
            },
            "resmi": {
                "parca": ["açık gri takım", "beyaz pamuklu gömlek", "loafer"],
                "kumas": ["hafif yün", "pamuk-keten"],
                "kesim": "tailored-slim",
                "aksesuar": ["klasik kravat", "metal kol düğmesi"],
                "ipucu": "Bej-gri takımlar ilkbaharda profesyonelliği ve tazeliği birlikte verir.",
            },
            "davet": {
                "parca": ["navy blazer", "khaki pantolon", "beyaz gömlek"],
                "kumas": ["yün karışımı", "premium pamuk"],
                "kesim": "smart-casual",
                "aksesuar": ["deri ayakkabı", "dünya saati"],
                "ipucu": "Blazer+pantolon kombinasyonu casual-resmi dengesini mükemmel sağlar.",
            },
        },
        "yaz": {
            "gunluk": {
                "parca": ["açık renkli polo", "kısa chino", "sandalet"],
                "kumas": ["hafif pamuk", "viskon"],
                "kesim": "relaxed",
                "aksesuar": ["güneş gözlüğü", "tesa şapka"],
                "ipucu": "Açık renkler sıcağa karşı pratiktir; doğal lifler konfortu artırır.",
            },
            "spor": {
                "parca": ["mesh t-shirt", "şort", "lightweight running ayakkabı"],
                "kumas": ["moisture-wicking", "elastan"],
                "kesim": "slim-athletic",
                "aksesuar": ["sports watch", "headband"],
                "ipucu": "Terleme yönetimi yazın kritik — teknolojik kumaşlar vazgeçilmez.",
            },
            "resmi": {
                "parca": ["açık krem takım", "pamuklu gömlek", "deri ayakkabı"],
                "kumas": ["pamuk", "hafif viskon"],
                "kesim": "tailored",
                "aksesuar": ["hafif fular veya kravat", "bileklik"],
                "ipucu": "Yazın resmi giysiler aydınlık tonlarıyla serinlik hissi verir.",
            },
            "davet": {
                "parca": ["açık blazer", "linen pantolon", "loafer"],
                "kumas": ["linen", "pamuk blend"],
                "kesim": "smart-casual",
                "aksesuar": ["deri kemer", "klasik saat"],
                "ipucu": "Linen blazer yazında resmiyet ile konfor arasında ideal noktayı sağlar.",
            },
        },
        "sonbahar": {
            "gunluk": {
                "parca": ["terre-kaki polo", "koyu chino", "kestane ayakkabı"],
                "kumas": ["pamuk", "keten blend"],
                "kesim": "fitted",
                "aksesuar": ["deri kemer", "cashmere scarf"],
                "ipucu": "Sonbahar toprak renkleri — okra, terracotta, tumbleweed doğal görünüm sağlar.",
            },
            "spor": {
                "parca": ["hoodie", "jogger", "trail shoe"],
                "kumas": ["fleece", "technical nylon"],
                "kesim": "relaxed",
                "aksesuar": ["spor çanta", "sportwear saat"],
                "ipucu": "Katmanlamaya hazır giysiler; dış katman yağmur koruması olsun.",
            },
            "resmi": {
                "parca": ["koyu kahverengi takım", "krem gömlek", "deri ayakkabı"],
                "kumas": ["yün", "pamuk-yün"],
                "kesim": "tailored-slim",
                "aksesuar": ["ipek kravat", "manset düğmesi"],
                "ipucu": "Koyu renkli takımlar sonbaharda saflık ve iddialılığı yansıtır.",
            },
            "davet": {
                "parca": ["tailored blazer", "dress pants", "oxford ayakkabı"],
                "kumas": ["wool blend", "fine cotton"],
                "kesim": "classic-tailored",
                "aksesuar": ["pocket square", "cufflinks"],
                "ipucu": "Kapalı renk paleti sophistication verir; minimal aksesuar yüksek etki yapar.",
            },
        },
        "kis": {
            "gunluk": {
                "parca": ["noir turtleneck", "charcoal pantolon", "Chelsea boot"],
                "kumas": ["yün", "knitwear"],
                "kesim": "fitted",
                "aksesuar": ["wool scarf", "leather gloves"],
                "ipucu": "Kişinin minimalist estetik kışta monokromu ile mükemmel uyum sağlar.",
            },
            "spor": {
                "parca": ["waterproof jacket", "thermal leggings", "winter boot"],
                "kumas": ["Gore-Tex", "thermal wool"],
                "kesim": "layered-ready",
                "aksesuar": ["winter hat", "hand warmers"],
                "ipucu": "Kış sporu için su geçirmez dış katman + thermal iç katman kombinasyonu şart.",
            },
            "resmi": {
                "parca": ["siyah coat", "gray suit", "oxford ayakkabı"],
                "kumas": ["wool coat", "premium wool suit"],
                "kesim": "tailored",
                "aksesuar": ["wool scarf", "leather belt"],
                "ipucu": "Siyah coat klasik görünüme zarafet katar; layering iç kapmanlar keskin korur.",
            },
            "davet": {
                "parca": ["charcoal suit", "crisp white shirt", "polished oxford"],
                "kumas": ["fine wool", "100% cotton"],
                "kesim": "tailored-classic",
                "aksesuar": ["silk scarf", "fine cufflinks"],
                "ipucu": "Kış daveti monokrom elegansı sunar; aksesuar materyali kalitesi vurgular.",
            },
        },
    },
    "yaratici-bohemyen": {
        "coaching": {
            "felsefe": "Özgürlük ve kendi kendine ifade. Sanat ve tasarım yaşamın merkezinde. Geleneksel kuralları kırmak, risk almak, deneysel olmak teşvik edilir.",
            "kombinasyon": "Desen karışımı cesaret ister ama bu tarzın kalpı. Turuncu+kırmızı, desenli+desenli, katmanlar hepsi iyidir. Simetri değil asimetri seç.",
            "renk_psikolojisi": "Sıcak toprak renkleri (turuncu, kestane, altın) sanatsal ruhu yansıtır. Kırmızı vurgu yaratıcılığı uyandırır. Renk cesaret gerektirir; bunu karşılarındakiyle paylaş.",
            "yaşam_uyarlamasi": "Kendi stilini oluşturmaktan çekinme. Pazarlamada satın aldığı parçalar + DIY tasarımlar (batik, nakış) kombinasyonu yap. Sanat galerisine gidermiş gibi giyinmeni hatırla."
        },
        "renk_paleti": {
            "ana": ["#8B4513", "#D2691E", "#C19A6B", "#F4A460"],
            "vurgu": ["#DC143C", "#FF6347"],
            "kacin": ["pastel ağızları", "nötr griler"],
        },
        "ilkbahar": {
            "gunluk": {
                "parca": ["çok renk bohemyen bluz", "hippi jean", "sandalet"],
                "kumas": ["cotton gauze", "viscose"],
                "kesim": "oversized-loose",
                "aksesuar": ["etnik bilezik", "macramé çanta"],
                "ipucu": "Bohemyen tarzı katmanlı tekstürleri ve desen karışımını seviyor — bu güçlüğüne dönüştür.",
            },
            "spor": {
                "parca": ["bohemyen desen leggings", "crop top", "canvas ayakkabı"],
                "kumas": ["organic cotton", "hemp blend"],
                "kesim": "fitted-boho",
                "aksesuar": ["etnik spor çanta", "bohemyen hairband"],
                "ipucu": "Yaratıcı stil sporu da renklendirebilir — pattern mix cesaret gerektirir ama ödül büyük.",
            },
            "resmi": {
                "parca": ["turuncu midi dress", "denim ceket", "wedge ayakkabı"],
                "kumas": ["linen blend", "printed cotton"],
                "kesim": "flowy-midi",
                "aksesuar": ["etnik kolye", "deri cüzdan"],
                "ipucu": "Bohemyen stili formal kombin yapmak — midi elbise + denim ceket = boho-casual formal.",
            },
            "davet": {
                "parca": ["terracotta maxi dress", "gold sandal", "şal"],
                "kumas": ["silk print", "cotton blend"],
                "kesim": "maxi-flowy",
                "aksesuar": ["statement necklace", "folk earrings"],
                "ipucu": "Davetler bohemyen için fırsat — maxi elbiseler ve statement aksesuarlarla adım at.",
            },
        },
        "yaz": {
            "gunluk": {
                "parca": ["tie-dye t-shirt", "hippi shorts", "barefoot sandal"],
                "kumas": ["organic cotton", "linen"],
                "kesim": "oversized",
                "aksesuar": ["friendship bracelets", "bohemyen kolye"],
                "ipucu": "Yaz bohemyen — özgürce renk, açık ter, taze görünüş.",
            },
            "spor": {
                "parca": ["boho-print yoga pants", "tank top", "barefoot ayakkabı"],
                "kumas": ["organic cotton", "bamboo"],
                "kesim": "stretchy-loose",
                "aksesuar": ["yoga mat strap", "eco bag"],
                "ipucu": "Yaratıcı spor tarzı ekoloji ile uyumlu olabilir — organik malzeme seçin.",
            },
            "resmi": {
                "parca": ["cream bohemyen dress", "sandal", "light shawl"],
                "kumas": ["cotton lace", "viscose blend"],
                "kesim": "flowy",
                "aksesuar": ["wooden jewels", "embroidered bag"],
                "ipucu": "Yazın bohemyen resmi — açık renk ve nefes eden kumaşlar şart.",
            },
            "davet": {
                "parca": ["gold maxi dress", "strappy sandal", "silk scarf"],
                "kumas": ["silk blend", "printed cotton"],
                "kesim": "maxi-boho",
                "aksesuar": ["gold jewelry", "bohemyen clutch"],
                "ipucu": "Yaz daveti bohemyen düşük yakı ve ışıl ışıl detaylar ile zarafet verir.",
            },
        },
        "sonbahar": {
            "gunluk": {
                "parca": ["burnt orange blouse", "brown hippi pants", "suede boots"],
                "kumas": ["linen", "suede"],
                "kesim": "loose",
                "aksesuar": ["fringe scarf", "boho bag"],
                "ipucu": "Sonbahar renkleri bohemyen tarzına doğal olarak uyum sağlar.",
            },
            "spor": {
                "parca": ["bohemyen hoodie", "flare leggings", "canvas boot"],
                "kumas": ["soft fleece", "cotton blend"],
                "kesim": "relaxed",
                "aksesuar": ["bohemyen beanie", "hemp bag"],
                "ipucu": "Sonbaharda bohemyen spor katmanlamaya hazır olsun.",
            },
            "resmi": {
                "parca": ["burgundy wrap dress", "ankle boot", "wool shawl"],
                "kumas": ["wool blend", "structured cotton"],
                "kesim": "wrap-elegant",
                "aksesuar": ["statement earrings", "leather bag"],
                "ipucu": "Wrap dress bohemyen stil resmi hale getirmenin en kolay yoludur.",
            },
            "davet": {
                "parca": ["terracotta maxi", "gold jewelry", "suede clutch"],
                "kumas": ["silk", "wool blend"],
                "kesim": "maxi-dramatic",
                "aksesuar": ["ornate necklace", "bohemyen shawl"],
                "ipucu": "Sonbahar daveti bohemyen — yer tonları ve dram maksimum yapalım.",
            },
        },
        "kis": {
            "gunluk": {
                "parca": ["burgundy bohemyen sweater", "leather leggings", "suede boots"],
                "kumas": ["wool blend", "suede"],
                "kesim": "oversized",
                "aksesuar": ["boho scarf", "suede bag"],
                "ipucu": "Kış bohemyen deri ve suede ile lüks hissi verir.",
            },
            "spor": {
                "parca": ["chunky knit sweater", "joggers", "winter boots"],
                "kumas": ["chunky wool", "fleece"],
                "kesim": "cozy-oversized",
                "aksesuar": ["wool hat", "bohemyen bag"],
                "ipucu": "Kış sporu bohemyen tarzı estetik rahatlık ile birleştirir.",
            },
            "resmi": {
                "parca": ["camel coat", "burgundy dress", "leather boots"],
                "kumas": ["wool coat", "fine wool dress"],
                "kesim": "tailored-boho",
                "aksesuar": ["gold scarf", "leather belt"],
                "ipucu": "Kış resmi bohemyen — camel coat klasik temel, bohemyen aksesuar ekleme.",
            },
            "davet": {
                "parca": ["black maxi dress", "velvet shawl", "heeled boots"],
                "kumas": ["velvet", "silk"],
                "kesim": "dramatic-maxi",
                "aksesuar": ["statement jewelry", "ornate bag"],
                "ipucu": "Kış daveti bohemyen — siyah velvet base + gold aksesuar = drama ve elegans.",
            },
        },
    },
    "sportif-aktif": {
        "coaching": {
            "felsefe": "Hareket, enerji, performans. Giyim pratik ve işlevseldir; modası değil, yeteneği önemlidir. Yaşamı dolu dolu yaşadığını giyim yansıtmalı.",
            "kombinasyon": "Teknoloji ile moda buluş. Nefes alan kumaşlar + renkli aktsesuat. Spora münasır renkler (neon, canlı tonlar) seç. Rahatça hareket edebileceğin kombin bul.",
            "renk_psikolojisi": "Canlı renkler (kırmızı, mavi, turuncu) enerjivi yansıtır ve motivasyon sağlar. Spor ve fitness psikolojisinde renkler performansı etkileyebilir — canlı tercih et.",
            "yaşam_uyarlamasi": "Giyim seçimini yaşam programına göre yap: sabah antrenman, akşam sosyal? Hızlı kuru kumaşlar ve çok amaçlı parçalar hayat kurtarır. Spor bileklik+saati tamamla."
        },
        "renk_paleti": {
            "ana": ["#FF6B6B", "#FF8C00", "#FFD700", "#00CED1"],
            "vurgu": ["#FF1493", "#00FF00"],
            "kacin": ["pastel", "gri"],
        },
        "ilkbahar": {
            "gunluk": {
                "parca": ["neon t-shirt", "athletic shorts", "running shoes"],
                "kumas": ["moisture-wicking", "spandex"],
                "kesim": "athletic-fit",
                "aksesuar": ["sports watch", "performance cap"],
                "ipucu": "Aktif stil ilkbaharı hareket ile kutlar — canlı renkler enerji verir.",
            },
            "spor": {
                "parca": ["compression shirt", "performance shorts", "trail shoes"],
                "kumas": ["technical polyester", "elastan"],
                "kesim": "performance-fit",
                "aksesuar": ["sports watch", "running belt"],
                "ipucu": "Performans kumaşları sporda fark yaratır; nem yönetimi kritik.",
            },
            "resmi": {
                "parca": ["athletic polo", "khaki pants", "clean sneaker"],
                "kumas": ["moisture-wicking cotton", "chino"],
                "kesim": "sporty-tailored",
                "aksesuar": ["sports watch", "minimalist belt"],
                "ipucu": "Sportif stil resmi ortamlarda athleisure mix sunabilir — kalite malzeme şart.",
            },
            "davet": {
                "parca": ["premium athletic blazer", "tailored pants", "dress sneaker"],
                "kumas": ["stretch wool", "cotton blend"],
                "kesim": "smart-athletic",
                "aksesuar": ["chronograph watch", "fine belt"],
                "ipucu": "Sportif davet stili — premium athleisure parçalarla sofistikasyon sağla.",
            },
        },
        "yaz": {
            "gunluk": {
                "parca": ["breathable tank", "short shorts", "lightweight running shoes"],
                "kumas": ["mesh", "quick-dry"],
                "kesim": "athletic-loose",
                "aksesuar": ["UV visor", "sports watch"],
                "ipucu": "Yazın aktif stil — hava geçişi ve ağrı yönetimi maksimum yapılsın.",
            },
            "spor": {
                "parca": ["cooling sports top", "minimal shorts", "lightweight trail shoes"],
                "kumas": ["cooling fabric", "mesh"],
                "kesim": "minimal",
                "aksesuar": ["hydration belt", "sports watch"],
                "ipucu": "Yaz sporu cooling teknoloji ile başlıyor — terleme kontrolü hayati.",
            },
            "resmi": {
                "parca": ["bright athletic dress", "sneaker", "cap"],
                "kumas": ["breathable cotton", "technical fabric"],
                "kesim": "athletic-dress",
                "aksesuar": ["sports watch", "minimal jewelry"],
                "ipucu": "Yazın sportif resmi — breathable fabrics ve bright colors birleştirilsin.",
            },
            "davet": {
                "parca": ["premium athleisure dress", "dress sneaker", "minimalist jewelry"],
                "kumas": ["stretch cotton blend", "fine mesh"],
                "kesim": "elegant-athletic",
                "aksesuar": ["luxury watch", "fine bag"],
                "ipucu": "Yaz daveti sportif — premium parçalar ile elegans sağlanabilir.",
            },
        },
        "sonbahar": {
            "gunluk": {
                "parca": ["long sleeve athletic top", "joggers", "trail shoes"],
                "kumas": ["soft fleece", "stretch nylon"],
                "kesim": "layered-ready",
                "aksesuar": ["sports watch", "running cap"],
                "ipucu": "Sonbahar sporu katmanlamaya başlıyor — dış katman yağmur koruması.",
            },
            "spor": {
                "parca": ["compression jacket", "thermal leggings", "trail shoes"],
                "kumas": ["fleece-backed", "thermal blend"],
                "kesim": "performance-layered",
                "aksesuar": ["sports watch", "reflective gear"],
                "ipucu": "Sonbahar sporu güvenlik ve ısı yönetimi ile başlıyor.",
            },
            "resmi": {
                "parca": ["athletic blazer", "dress pants", "clean sneaker"],
                "kumas": ["stretch wool", "cotton"],
                "kesim": "athletic-tailored",
                "aksesuar": ["sports watch", "minimalist belt"],
                "ipucu": "Sonbahar sportif resmi — athleisure premium parçalar ile profesyonel görünüm.",
            },
            "davet": {
                "parca": ["sport-tech blazer", "tailored pants", "premium sneaker"],
                "kumas": ["technical wool blend", "fine cotton"],
                "kesim": "smart-sport",
                "aksesuar": ["chronograph watch", "designer bag"],
                "ipucu": "Sonbahar daveti sportif — designer athleisure ile sophistication sağla.",
            },
        },
        "kis": {
            "gunluk": {
                "parca": ["insulated jacket", "thermal leggings", "winter sports shoes"],
                "kumas": ["thermal insulation", "waterproof nylon"],
                "kesim": "layered-warm",
                "aksesuar": ["winter sports hat", "thermal gloves"],
                "ipucu": "Kış sporu ısı ve su yönetimi şart — kaliteli insulated ceket seç.",
            },
            "spor": {
                "parca": ["Gore-Tex jacket", "thermal compression", "winter trail shoes"],
                "kumas": ["Gore-Tex", "merino wool"],
                "kesim": "performance-winter",
                "aksesuar": ["winter hat", "performance gloves"],
                "ipucu": "Kış sporu yüksek teknoloji gerektirir — Gore-Tex ve merino wool standard.",
            },
            "resmi": {
                "parca": ["sport-tech coat", "dress pants", "winter boot"],
                "kumas": ["thermal wool coat", "fine wool pants"],
                "kesim": "athletic-formal",
                "aksesuar": ["wool hat", "leather gloves"],
                "ipucu": "Kış sportif resmi — coat kalitesi ve aksesuar materyali vurgula.",
            },
            "davet": {
                "parca": ["premium winter jacket", "tailored pants", "dress boot"],
                "kumas": ["luxury wool coat", "fine wool"],
                "kesim": "elegant-winter",
                "aksesuar": ["wool scarf", "leather accessories"],
                "ipucu": "Kış daveti sportif — premium coat ve aksesuar ile elegans sağla.",
            },
        },
    },
    "romantik-zarif": {
        "coaching": {
            "felsefe": "Incelik, zarafet, duygusal ifade. Güzellik detaylarda gizlidir. Yumuşak dokular ve hassas renkler kişiliğini yansıtır.",
            "kombinasyon": "Desen karışımı (çiçek+düz) dengeli olmalı. Yumuşak kumaşlar tercih et. Renk paletine yapış: pastel pembe, lavanta, krem. Oversize kaçın; fitted kesim elegans verir.",
            "renk_psikolojisi": "Pastel pembe zarif, duygusal bağlantı kurar. Lavanda huzur ve kreativitenin sembolü. Altın vurgusu romantizmi modern zarafet ile birleştirir.",
            "yaşam_uyarlamasi": "Sofaykakta detay olan parçalar seç: dantel, ince işleme, ipek. Takılarını deli gibi yanı sıra ender ama yüksek kaliteli aksesuarlar tercih et. Kendini dezavantajlı hissetme; zarafet güç sağlar."
        },
        "renk_paleti": {
            "ana": ["#FFB6C1", "#FFB6D9", "#DDA0DD", "#F0E68C"],
            "vurgu": ["#FF69B4", "#FF1493"],
            "kacin": ["çok koyu", "aşırı renkli"],
        },
        "ilkbahar": {
            "gunluk": {
                "parca": ["pastel bluz", "midi skirt", "flats"],
                "kumas": ["soft cotton", "chiffon"],
                "kesim": "soft-fitted",
                "aksesuar": ["delicate necklace", "soft hair accessory"],
                "ipucu": "İlkbahar romantik — pastel renkler ve soft texturlar doğal seçim.",
            },
            "spor": {
                "parca": ["soft yoga pants", "romantic crop top", "ballet flats"],
                "kumas": ["organic cotton", "bamboo"],
                "kesim": "soft-stretchy",
                "aksesuar": ["delicate watch", "soft bag"],
                "ipucu": "Romantik sporu soft materials ile başlıyor — performance zarara uğramamalı.",
            },
            "resmi": {
                "parca": ["blush dress", "rose gold jewelry", "ballet heels"],
                "kumas": ["silk blend", "cotton lace"],
                "kesim": "romantic-fitted",
                "aksesuar": ["delicate jewelry", "feminine bag"],
                "ipucu": "İlkbahar romantik resmi — blush tones ve delicate detaylar şart.",
            },
            "davet": {
                "parca": ["rose pink midi dress", "delicate heels", "soft shawl"],
                "kumas": ["silk", "lace"],
                "kesim": "romantic-midi",
                "aksesuar": ["rose gold jewelry", "soft clutch"],
                "ipucu": "İlkbahar daveti romantik — midi elbiseler ve rose tones kullansın.",
            },
        },
        "yaz": {
            "gunluk": {
                "parca": ["light pink sundress", "sandal", "sun hat"],
                "kumas": ["linen", "cotton gauze"],
                "kesim": "floaty",
                "aksesuar": ["delicate anklet", "soft bag"],
                "ipucu": "Yazın romantik — açık renkler ve floaty silhouettes dominans sağlar.",
            },
            "spor": {
                "parca": ["romantic yoga set", "sandal", "light cover-up"],
                "kumas": ["organic cotton", "linen blend"],
                "kesim": "soft-stretch",
                "aksesuar": ["delicate jewelry", "yoga bag"],
                "ipucu": "Yazın romantik sporu soft colors ve breathable fabrics ile başlıyor.",
            },
            "resmi": {
                "parca": ["pale pink dress", "delicate sandal", "light shawl"],
                "kumas": ["cotton lace", "silk blend"],
                "kesim": "romantic-dress",
                "aksesuar": ["rose gold jewelry", "feminine bag"],
                "ipucu": "Yazın romantik resmi — pale colors ve lace detaylar yaşam sağla.",
            },
            "davet": {
                "parca": ["rose midi gown", "delicate heels", "silk shawl"],
                "kumas": ["silk", "chiffon"],
                "kesim": "romantic-gown",
                "aksesuar": ["jewelry", "elegant clutch"],
                "ipucu": "Yaz daveti romantik — chiffon ve delicate details ile zarafet sağla.",
            },
        },
        "sonbahar": {
            "gunluk": {
                "parca": ["mauve blouse", "midi skirt", "ankle boot"],
                "kumas": ["soft wool", "cotton blend"],
                "kesim": "soft-fitted",
                "aksesuar": ["delicate scarf", "romantic bag"],
                "ipucu": "Sonbahar romantik — mauve ve dusty rose tones natural ve soft.",
            },
            "spor": {
                "parca": ["romantic hoodie", "joggers", "soft boots"],
                "kumas": ["soft fleece", "cotton blend"],
                "kesim": "cozy-romantic",
                "aksesuar": ["delicate hat", "soft bag"],
                "ipucu": "Sonbahar romantik sporu cozy fabrics ile başlıyor.",
            },
            "resmi": {
                "parca": ["dusty rose dress", "ankle boot", "light cardigan"],
                "kumas": ["wool blend", "fine cotton"],
                "kesim": "romantic-dress",
                "aksesuar": ["rose gold jewelry", "feminine bag"],
                "ipucu": "Sonbahar romantik resmi — dusty colors ve soft layering şart.",
            },
            "davet": {
                "parca": ["burgundy romantic dress", "heels", "shawl"],
                "kumas": ["wool blend", "silk"],
                "kesim": "romantic-gown",
                "aksesuar": ["elegant jewelry", "evening clutch"],
                "ipucu": "Sonbahar daveti romantik — burgundy ve gold kombinasyonu klasik.",
            },
        },
        "kis": {
            "gunluk": {
                "parca": ["blush sweater", "midi skirt", "boots"],
                "kumas": ["soft wool", "cashmere blend"],
                "kesim": "soft-fitted",
                "aksesuar": ["delicate scarf", "romantic bag"],
                "ipucu": "Kış romantik — soft blush tones ve cashmere lüks sağlar.",
            },
            "spor": {
                "parca": ["romantic knit sweater", "soft leggings", "cozy boots"],
                "kumas": ["chunky knit", "thermal blend"],
                "kesim": "cozy-romantic",
                "aksesuar": ["wool hat", "soft gloves"],
                "ipucu": "Kış romantik sporu chunky knits ile başlıyor.",
            },
            "resmi": {
                "parca": ["blush wool coat", "dress", "elegant boots"],
                "kumas": ["wool coat", "fine wool"],
                "kesim": "romantic-tailored",
                "aksesuar": ["delicate jewelry", "luxury bag"],
                "ipucu": "Kış romantik resmi — blush coat ve gold jewelry kombinasyonu zarif.",
            },
            "davet": {
                "parca": ["burgundy maxi dress", "heels", "elegant coat"],
                "kumas": ["velvet", "wool coat"],
                "kesim": "romantic-gown",
                "aksesuar": ["statement jewelry", "evening clutch"],
                "ipucu": "Kış daveti romantik — velvet ve gold ile drama ve elegans sağla.",
            },
        },
    },
    "karma-adaptif": {
        "coaching": {
            "felsefe": "Uyum ve pragmatizm. Giyim işlevsel, temiz ve herkes tarafından kabul edilebilir. Stilleri değişen durumla birlikte fleksibel olarak ayarla.",
            "kombinasyon": "Klasik kombinasyonlar hiçbir zaman başarısız olmaz. Gri+beyaz+lacivert temel ton. Bir aksesuar ekle veya uzaklaştır; uyumlu stil kabul eder.",
            "renk_psikolojisi": "Nötr renkler sakinlik ve profesyonellik verir. Beyaz güvenilirlik, siyah otorite, gri denge temsil eder. Uyum sağlayan kişi için ideal seçimler.",
            "yaşam_uyarlamasi": "Hızlı mix-and-match kombinasyonları haz et. Giyim seçimi minimum zaman almalı. Kaliteli basics ve çok amaçlı parçaların birçok kombinasyonundan yararlan."
        },
        "renk_paleti": {
            "ana": ["#696969", "#808080", "#A9A9A9", "#C0C0C0"],
            "vurgu": ["#000000", "#FFFFFF"],
            "kacin": ["hiç yok"],
        },
        "ilkbahar": {
            "gunluk": {
                "parca": ["grey t-shirt", "navy jeans", "white sneaker"],
                "kumas": ["cotton", "denim"],
                "kesim": "classic-fit",
                "aksesuar": ["simple watch", "basic bag"],
                "ipucu": "Uyumlu stil temel renkler ile başlıyor — gri, beyaz, siyah, lacivert.",
            },
            "spor": {
                "parca": ["neutral hoodie", "black shorts", "grey shoes"],
                "kumas": ["cotton blend", "polyester"],
                "kesim": "relaxed",
                "aksesuar": ["sports watch", "gym bag"],
                "ipucu": "Adaptif sporu nötr renkler ile başlıyor.",
            },
            "resmi": {
                "parca": ["grey blazer", "white shirt", "black pants"],
                "kumas": ["wool blend", "cotton"],
                "kesim": "classic-tailored",
                "aksesuar": ["classic watch", "basic belt"],
                "ipucu": "Uyumlu stil resmi — classic color combination her zaman doğru.",
            },
            "davet": {
                "parca": ["charcoal suit", "white shirt", "navy tie"],
                "kumas": ["wool", "cotton"],
                "kesim": "tailored-classic",
                "aksesuar": ["classic jewelry", "simple bag"],
                "ipucu": "Adaptif davet stili — klasik kombinasyonları güvenle kullan.",
            },
        },
        "yaz": {
            "gunluk": {
                "parca": ["white t-shirt", "grey shorts", "neutral sneaker"],
                "kumas": ["cotton", "linen"],
                "kesim": "relaxed",
                "aksesuar": ["simple watch", "light bag"],
                "ipucu": "Yazın adaptif — açık nötr renkler rahatlık ve yazlılık sağlar.",
            },
            "spor": {
                "parca": ["grey athletic shirt", "black shorts", "white shoes"],
                "kumas": ["moisture-wicking", "spandex"],
                "kesim": "athletic-fit",
                "aksesuar": ["sports watch", "gym bag"],
                "ipucu": "Yazın adaptif sporu nötr athletic wear ile başlıyor.",
            },
            "resmi": {
                "parca": ["light grey suit", "white shirt", "neutral shoes"],
                "kumas": ["linen blend", "cotton"],
                "kesim": "classic-fit",
                "aksesuar": ["simple jewelry", "neutral bag"],
                "ipucu": "Yazın resmi adaptif — açık nötr renkler serinlik sağlar.",
            },
            "davet": {
                "parca": ["light grey suit", "white shirt", "neutral shoes"],
                "kumas": ["cotton blend", "linen"],
                "kesim": "smart-casual",
                "aksesuar": ["classic watch", "simple bag"],
                "ipucu": "Yaz daveti adaptif — nötr renkler ve klasik form her ortama uyar.",
            },
        },
        "sonbahar": {
            "gunluk": {
                "parca": ["charcoal shirt", "grey pants", "brown shoes"],
                "kumas": ["cotton", "wool blend"],
                "kesim": "classic-fit",
                "aksesuar": ["simple watch", "neutral bag"],
                "ipucu": "Sonbahar adaptif — charcoal ve brown kombinasyonu natural ve versatil.",
            },
            "spor": {
                "parca": ["grey hoodie", "black joggers", "neutral shoes"],
                "kumas": ["fleece", "cotton blend"],
                "kesim": "relaxed-athletic",
                "aksesuar": ["sports watch", "gym bag"],
                "ipucu": "Sonbahar adaptif sporu grey-black kombinasyonu ile başlıyor.",
            },
            "resmi": {
                "parca": ["charcoal blazer", "grey pants", "brown shoes"],
                "kumas": ["wool", "cotton"],
                "kesim": "tailored",
                "aksesuar": ["classic jewelry", "neutral bag"],
                "ipucu": "Sonbahar resmi adaptif — charcoal ve brown her ortama uyar.",
            },
            "davet": {
                "parca": ["charcoal suit", "white shirt", "brown shoes"],
                "kumas": ["wool", "fine cotton"],
                "kesim": "tailored-classic",
                "aksesuar": ["classic jewelry", "neutral bag"],
                "ipucu": "Sonbahar daveti adaptif — klasik kombinasyonlar her zaman güvenli.",
            },
        },
        "kis": {
            "gunluk": {
                "parca": ["black sweater", "grey pants", "dark boots"],
                "kumas": ["wool", "cotton blend"],
                "kesim": "classic-fit",
                "aksesuar": ["simple watch", "neutral bag"],
                "ipucu": "Kış adaptif — siyah ve gri kombinasyonu ısıl görünüm sağlar.",
            },
            "spor": {
                "parca": ["black hoodie", "grey thermal", "dark shoes"],
                "kumas": ["fleece", "thermal wool"],
                "kesim": "layered-fit",
                "aksesuar": ["sports watch", "gym bag"],
                "ipucu": "Kış adaptif sporu siyah-gri layering ile başlıyor.",
            },
            "resmi": {
                "parca": ["black coat", "grey suit", "dark shoes"],
                "kumas": ["wool coat", "wool suit"],
                "kesim": "tailored",
                "aksesuar": ["classic jewelry", "neutral bag"],
                "ipucu": "Kış resmi adaptif — siyah coat ve gri suit kombinasyonu sofistike.",
            },
            "davet": {
                "parca": ["black suit", "white shirt", "dark shoes"],
                "kumas": ["fine wool", "cotton"],
                "kesim": "tailored-classic",
                "aksesuar": ["elegant jewelry", "luxury bag"],
                "ipucu": "Kış daveti adaptif — siyah suit ve beyaz shirt klasik ve şık.",
            },
        },
    },
    "gucu-otoriter": {
        "coaching": {
            "felsefe": "Güç ve otorite. Liderlik ve dominans kişiliğin merkezinde. Giyim kararındaki güvenin yüksek sesle duyurulması.",
            "kombinasyon": "Koyu renkler (siyah, lacivert, bordo) otorite verir. Kesim tailored ve fitted — hiçbir esneklik. Aksesuar statement ürünler olmalı.",
            "renk_psikolojisi": "Siyah ve koyu renkler güç ve kontrol yansıtır. Altın ve gümüş aksesuarlar otorite ve prestij simgeler. Parlak renkler tepeden bakılma izlenimi verir.",
            "yaşam_uyarlamasi": "Toplantılar öncesi net kesim parçalar seç. Aksesuar minimal ama yüksek kalite. Giysindeki her detay kararında olmalı — tesadüfi hiç yok."
        },
        "renk_paleti": {
            "ana": ["#000000", "#1A1A1A", "#2D004D", "#8B0000"],
            "vurgu": ["#FFD700", "#C0C0C0"],
            "kacin": ["pastel renkler", "hafif tonlar"],
        },
        "ilkbahar": {
            "gunluk": {
                "parca": ["siyah polo", "koyu gray pantolon", "siyah ayakkabı"],
                "kumas": ["premium cotton", "wool blend"],
                "kesim": "tailored-slim",
                "aksesuar": ["gold watch", "leather belt"],
                "ipucu": "Bahar da otoritesi korumalı — siyah base + minimal vurgu.",
            },
            "spor": {
                "parca": ["navy compression shirt", "black shorts", "premium shoes"],
                "kumas": ["technical fabric", "wool"],
                "kesim": "fitted",
                "aksesuar": ["sports watch", "premium backpack"],
                "ipucu": "Sportif otoritesi — alet seçiminde premium.",
            },
            "resmi": {
                "parca": ["black suit", "white dress shirt", "leather shoes"],
                "kumas": ["fine wool", "cotton"],
                "kesim": "tailored-classic",
                "aksesuar": ["silk tie", "cufflinks", "gold watch"],
                "ipucu": "Siyah suit daima güç verir — aksesuar minimal ama göz alıcı.",
            },
            "davet": {
                "parca": ["navy or black tuxedo", "white shirt", "dress shoes"],
                "kumas": ["premium wool", "silk"],
                "kesim": "tailored-formal",
                "aksesuar": ["bow tie", "cufflinks", "pocket square"],
                "ipucu": "Davette otoritesi — tuxedo ve aksesuar konuşur.",
            },
        },
        "yaz": {
            "gunluk": {
                "parca": ["black t-shirt", "dark shorts", "sunglasses"],
                "kumas": ["lightweight wool", "cotton"],
                "kesim": "fitted",
                "aksesuar": ["sunglasses", "gold chain"],
                "ipucu": "Yazında da siyah tutması karizmasını korur.",
            },
            "spor": {
                "parca": ["black athletic wear", "dark shorts", "premium sneakers"],
                "kumas": ["moisture-wicking", "nylon"],
                "kesim": "athletic-fitted",
                "aksesuar": ["sports watch", "tech bag"],
                "ipucu": "Yazının sporu siyah-koyu ile başlıyor.",
            },
            "resmi": {
                "parca": ["navy blazer", "light gray pants", "dress shoes"],
                "kumas": ["linen blend", "cotton"],
                "kesim": "tailored",
                "aksesuar": ["silk accessories", "gold watch"],
                "ipucu": "Yazında resmi — navy blazer serinlik + otorite.",
            },
            "davet": {
                "parca": ["navy suit", "white shirt", "dress shoes"],
                "kumas": ["linen", "cotton blend"],
                "kesim": "smart-tailored",
                "aksesuar": ["silk accessories", "elegant watch"],
                "ipucu": "Yazın daveti koyu renkler ile başlıyor.",
            },
        },
        "sonbahar": {
            "gunluk": {
                "parca": ["burgundy sweater", "dark jeans", "boots"],
                "kumas": ["wool", "denim"],
                "kesim": "fitted",
                "aksesuar": ["leather belt", "gold jewelry"],
                "ipucu": "Sonbaharın otoritesi burgundy + siyah kombinasyonu.",
            },
            "spor": {
                "parca": ["black hoodie", "dark joggers", "premium boots"],
                "kumas": ["wool blend", "technical"],
                "kesim": "tailored-athletic",
                "aksesuar": ["sports watch", "premium bag"],
                "ipucu": "Sonbahar aktivitesi siyah güçlü renk.",
            },
            "resmi": {
                "parca": ["brown or black suit", "cream shirt", "leather shoes"],
                "kumas": ["wool", "cotton"],
                "kesim": "tailored",
                "aksesuar": ["silk tie", "cufflinks", "premium watch"],
                "ipucu": "Sonbahar resmisi — koyu suit + cream gömlek.",
            },
            "davet": {
                "parca": ["black suit", "white shirt", "dress shoes"],
                "kumas": ["wool", "cotton"],
                "kesim": "tailored-formal",
                "aksesuar": ["statement jewelry", "luxury accessories"],
                "ipucu": "Sonbahar daveti siyah suit — sonsuza kadar doğru.",
            },
        },
        "kis": {
            "gunluk": {
                "parca": ["black coat", "dark pants", "boots"],
                "kumas": ["wool coat", "wool pants"],
                "kesim": "tailored",
                "aksesuar": ["leather gloves", "wool scarf"],
                "ipucu": "Kış otoritesi — siyah coat ve premium aksesuarlar.",
            },
            "spor": {
                "parca": ["black puffer jacket", "thermal leggings", "winter boots"],
                "kumas": ["Gore-Tex", "wool"],
                "kesim": "fitted",
                "aksesuar": ["winter hat", "gloves", "premium watch"],
                "ipucu": "Kış sporu siyah + premium materyaller.",
            },
            "resmi": {
                "parca": ["black coat", "grey suit", "dress shoes"],
                "kumas": ["wool coat", "wool suit"],
                "kesim": "tailored-formal",
                "aksesuar": ["leather accessories", "premium watch"],
                "ipucu": "Kış resmisi — siyah coat üstünde otorite.",
            },
            "davet": {
                "parca": ["black formal coat", "black suit", "dress shoes"],
                "kumas": ["premium wool", "silk"],
                "kesim": "tailored-formal",
                "aksesuar": ["luxury accessories", "premium watch"],
                "ipucu": "Kış daveti — siyah ve premium material.",
            },
        },
    },
    "sosyal-trendy": {
        "coaching": {
            "felsefe": "Sosyallik ve modanın takibi. Trendy ama samimi. Grup aidiyeti ve güncel olmak önemli.",
            "kombinasyon": "Renkli, canlı tonlar tercih et. Trend parçalar karışık — patterned + solid OK. Aksesuar göz alıcı ama uyumlu.",
            "renk_psikolojisi": "Canlı renkler (neon, gradient) sosyalliği ve enerjyiyi yansıtır. Trend renkleri takip — şu sezon ne varsa.",
            "yaşam_uyarlamasi": "Modayı takip et — sosyal medya, influencer, moda blogları. Parçalar mix-and-match hızlı kombinler sağlamalı. Aksesuarlarla yaratıcı ol."
        },
        "renk_paleti": {
            "ana": ["#FF6B9D", "#FFA500", "#00CED1", "#FF1493"],
            "vurgu": ["#FFD700", "#FF69B4"],
            "kacin": ["griler", "nötr"],
        },
        "ilkbahar": {
            "gunluk": {
                "parca": ["pastel blouse", "colorful jeans", "trendy sneakers"],
                "kumas": ["cotton", "denim blend"],
                "kesim": "trendy-fit",
                "aksesuar": ["colorful bag", "statement earrings"],
                "ipucu": "İlkbahar trendy — pastel + canlı aksesuar.",
            },
            "spor": {
                "parca": ["neon sports wear", "geometric leggings", "trendy shoes"],
                "kumas": ["athletic mesh", "spandex"],
                "kesim": "modern-athletic",
                "aksesuar": ["smart watch", "trendy cap"],
                "ipucu": "Spor trendi — neon renkler dikkat çeker.",
            },
            "resmi": {
                "parca": ["pastel blazer", "white pants", "trendy heels"],
                "kumas": ["cotton blend", "linen"],
                "kesim": "modern-tailored",
                "aksesuar": ["chunky jewelry", "modern bag"],
                "ipucu": "Resmi trendi — blazer + trendy aksesuar.",
            },
            "davet": {
                "parca": ["colorful dress", "statement heels", "fashion accessories"],
                "kumas": ["silk blend", "satin"],
                "kesim": "modern-dress",
                "aksesuar": ["statement necklace", "designer bag"],
                "ipucu": "Davet trendy — renk + aksesuar konuşur.",
            },
        },
        "yaz": {
            "gunluk": {
                "parca": ["bright t-shirt", "denim shorts", "casual sneakers"],
                "kumas": ["cotton", "denim"],
                "kesim": "relaxed-modern",
                "aksesuar": ["colorful bag", "sunglasses"],
                "ipucu": "Yazın trendy — renkli ve rahat.",
            },
            "spor": {
                "parca": ["tropical print leggings", "crop top", "trendy shoes"],
                "kumas": ["athletic cotton", "spandex"],
                "kesim": "modern-athletic",
                "aksesuar": ["trendy watch", "sports bag"],
                "ipucu": "Yazın sporu — tropical print trendy.",
            },
            "resmi": {
                "parca": ["modern blazer", "white dress pants", "heels"],
                "kumas": ["linen", "cotton"],
                "kesim": "contemporary-tailored",
                "aksesuar": ["modern jewelry", "fashion bag"],
                "ipucu": "Yazın resmisi — modern blazer + aksesuar.",
            },
            "davet": {
                "parca": ["bright summer dress", "strappy heels", "accessories"],
                "kumas": ["silk", "chiffon"],
                "kesim": "modern-dress",
                "aksesuar": ["statement jewelry", "designer clutch"],
                "ipucu": "Yazın daveti — colorful + chic.",
            },
        },
        "sonbahar": {
            "gunluk": {
                "parca": ["burgundy sweater", "patterned pants", "boots"],
                "kumas": ["wool", "cotton blend"],
                "kesim": "modern-fitted",
                "aksesuar": ["designer scarf", "modern bag"],
                "ipucu": "Sonbahar trendy — pattern mix + aksesuar.",
            },
            "spor": {
                "parca": ["patterned hoodie", "geometric joggers", "trendy boots"],
                "kumas": ["cotton blend", "technical"],
                "kesim": "modern-athletic",
                "aksesuar": ["trendy hat", "premium backpack"],
                "ipucu": "Sonbahar sporu — pattern trend.",
            },
            "resmi": {
                "parca": ["modern blazer", "patterned pants", "loafers"],
                "kumas": ["wool blend", "cotton"],
                "kesim": "contemporary-tailored",
                "aksesuar": ["statement brooch", "designer bag"],
                "ipucu": "Sonbahar resmisi — pattern + modern.",
            },
            "davet": {
                "parca": ["dressy pattern dress", "heels", "cover-up"],
                "kumas": ["velvet", "satin"],
                "kesim": "modern-elegant",
                "aksesuar": ["statement jewelry", "luxury bag"],
                "ipucu": "Sonbahar daveti — pattern + elegance.",
            },
        },
        "kis": {
            "gunluk": {
                "parca": ["colorful sweater", "trendy jeans", "boots"],
                "kumas": ["wool", "denim"],
                "kesim": "modern-fitted",
                "aksesuar": ["colorful scarf", "trendy bag"],
                "ipucu": "Kış trendy — renkli sweater + aksesuar.",
            },
            "spor": {
                "parca": ["patterned puffer", "geometric leggings", "winter boots"],
                "kumas": ["technical wool", "nylon"],
                "kesim": "modern-athletic",
                "aksesuar": ["trendy hat", "designer bag"],
                "ipucu": "Kış sporu — pattern + premium.",
            },
            "resmi": {
                "parca": ["modern coat", "tailored pants", "heels"],
                "kumas": ["wool coat", "wool"],
                "kesim": "contemporary-tailored",
                "aksesuar": ["modern jewelry", "luxury bag"],
                "ipucu": "Kış resmisi — modern coat + aksesuar.",
            },
            "davet": {
                "parca": ["elegant coat", "dressy outfit", "heels"],
                "kumas": ["wool coat", "silk"],
                "kesim": "modern-formal",
                "aksesuar": ["statement jewelry", "designer bag"],
                "ipucu": "Kış daveti — coat + formal chic.",
            },
        },
    },
    "dogal-rahat": {
        "coaching": {
            "felsefe": "Doğallık ve rahatlık. Giyim kısıtlayıcı olmamalı. Özgürlük ve esneklik yaşamın prensibi.",
            "kombinasyon": "Doğal renkler (krem, bej, yeşil, kahverengi) tercih et. Katmanlar rahat ve fonksiyonel. Fitted yerine relaxed kesimler.",
            "renk_psikolojisi": "Toprak renkleri huzur ve doğallık verir. Yeşil ve bej rahatılık ve barış simgeler. Yapay renkler kaçın.",
            "yaşam_uyarlamasi": "Rahat parçalar seç — esneklik ve hareketli olmak önemli. Doğal lifleri tercih et — pamuk, keten, yün. Giyim seçimi hızlı ve stressiz olmalı."
        },
        "renk_paleti": {
            "ana": ["#E8D4B4", "#A59B6C", "#8FBC8F", "#D2B48C"],
            "vurgu": ["#228B22", "#8B4513"],
            "kacin": ["yapay renkler", "çok koyu"],
        },
        "ilkbahar": {
            "gunluk": {
                "parca": ["linen shirt", "cotton pants", "canvas shoes"],
                "kumas": ["linen", "organic cotton"],
                "kesim": "relaxed",
                "aksesuar": ["minimal bag", "simple jewelry"],
                "ipucu": "İlkbahar doğal — linen rahatlık verir.",
            },
            "spor": {
                "parca": ["hemp joggers", "organic cotton top", "natural shoes"],
                "kumas": ["hemp blend", "organic cotton"],
                "kesim": "relaxed-athletic",
                "aksesuar": ["eco bag", "natural watch"],
                "ipucu": "Spor doğal — eco-friendly parçalar.",
            },
            "resmi": {
                "parca": ["linen blazer", "natural pants", "loafers"],
                "kumas": ["linen blend", "natural cotton"],
                "kesim": "relaxed-tailored",
                "aksesuar": ["natural jewelry", "eco bag"],
                "ipucu": "Resmi doğal — linen + natural tones.",
            },
            "davet": {
                "parca": ["linen dress", "natural heels", "accessories"],
                "kumas": ["linen", "natural silk"],
                "kesim": "relaxed-elegant",
                "aksesuar": ["natural jewelry", "eco clutch"],
                "ipucu": "Davet doğal — linen + natural elegance.",
            },
        },
        "yaz": {
            "gunluk": {
                "parca": ["cotton t-shirt", "linen shorts", "sandals"],
                "kumas": ["organic cotton", "linen"],
                "kesim": "relaxed",
                "aksesuar": ["straw bag", "simple hat"],
                "ipucu": "Yazın doğal — hafif linenler.",
            },
            "spor": {
                "parca": ["organic cotton top", "hemp shorts", "barefoot shoes"],
                "kumas": ["organic cotton", "hemp"],
                "kesim": "relaxed-athletic",
                "aksesuar": ["eco watch", "natural bag"],
                "ipucu": "Yazın sporu — hafif doğal parçalar.",
            },
            "resmi": {
                "parca": ["linen dress", "natural sandals", "light cover"],
                "kumas": ["linen", "natural cotton"],
                "kesim": "relaxed-dress",
                "aksesuar": ["natural jewelry", "woven bag"],
                "ipucu": "Yazın resmisi — linen rahatlığı.",
            },
            "davet": {
                "parca": ["linen maxi dress", "natural heels", "shawl"],
                "kumas": ["linen", "natural silk"],
                "kesim": "relaxed-maxi",
                "aksesuar": ["natural jewelry", "woven clutch"],
                "ipucu": "Yazın daveti — linen + natural.",
            },
        },
        "sonbahar": {
            "gunluk": {
                "parca": ["cotton sweater", "natural pants", "boots"],
                "kumas": ["organic cotton", "natural blend"],
                "kesim": "relaxed",
                "aksesuar": ["natural bag", "wool scarf"],
                "ipucu": "Sonbahar doğal — cotton warmth.",
            },
            "spor": {
                "parca": ["hemp hoodie", "natural joggers", "natural boots"],
                "kumas": ["hemp blend", "organic cotton"],
                "kesim": "relaxed-athletic",
                "aksesuar": ["eco bag", "natural hat"],
                "ipucu": "Sonbahar sporu — hemp rahatlığı.",
            },
            "resmi": {
                "parca": ["cotton blazer", "natural pants", "loafers"],
                "kumas": ["organic cotton", "natural blend"],
                "kesim": "relaxed-tailored",
                "aksesuar": ["natural jewelry", "eco bag"],
                "ipucu": "Sonbahar resmisi — cotton + relaxed.",
            },
            "davet": {
                "parca": ["natural dress", "boots", "cover-up"],
                "kumas": ["natural silk", "cotton blend"],
                "kesim": "relaxed-elegant",
                "aksesuar": ["natural jewelry", "eco clutch"],
                "ipucu": "Sonbahar daveti — natural + elegance.",
            },
        },
        "kis": {
            "gunluk": {
                "parca": ["wool sweater", "natural pants", "boots"],
                "kumas": ["organic wool", "natural blend"],
                "kesim": "relaxed",
                "aksesuar": ["wool scarf", "eco bag"],
                "ipucu": "Kış doğal — wool rahatlığı.",
            },
            "spor": {
                "parca": ["wool hoodie", "thermal leggings", "natural boots"],
                "kumas": ["organic wool", "thermal natural"],
                "kesim": "relaxed-athletic",
                "aksesuar": ["wool hat", "natural backpack"],
                "ipucu": "Kış sporu — wool warmth.",
            },
            "resmi": {
                "parca": ["wool blazer", "natural pants", "loafers"],
                "kumas": ["organic wool", "natural blend"],
                "kesim": "relaxed-tailored",
                "aksesuar": ["natural jewelry", "eco bag"],
                "ipucu": "Kış resmisi — wool + natural.",
            },
            "davet": {
                "parca": ["wool dress", "boots", "natural coat"],
                "kumas": ["natural wool", "natural blend"],
                "kesim": "relaxed-elegant",
                "aksesuar": ["natural jewelry", "eco clutch"],
                "ipucu": "Kış daveti — wool + natural elegance.",
            },
        },
    },
    "entelektuel-kasaba": {
        "coaching": {
            "felsefe": "Derinlik ve düşünce. Giysinin arkasında bir hikaye vardır. Kültür, sanat, literature yaklaşım giyime yansır.",
            "kombinasyon": "Monokrom ve nötr renkler — görsel dikkat dağılımını azaltır. Vintage ve klasik parçalar tercih et. Detay ve texture önemli.",
            "renk_psikolojisi": "Koyu renkler (siyah, gri, navy) düşün ve seriözlik yansıtır. Krem ve beyaz intelektüellik ve clarité verir. Sanatçı gri.",
            "yaşam_uyarlamasi": "Kütüphane, müze, kafe'deki stil. Giysinde felsefe ve karakter olmalı. Trend kaçın — zamanüstü elegans. Kitap veya sanat referansı taşısın parçalar."
        },
        "renk_paleti": {
            "ana": ["#2F4F4F", "#696969", "#F5F5DC", "#FFFAF0"],
            "vurgu": ["#8B0000", "#4B0082"],
            "kacin": ["canlı renkler", "çok açık"],
        },
        "ilkbahar": {
            "gunluk": {
                "parca": ["linen shirt", "grey pants", "leather shoes"],
                "kumas": ["linen", "wool blend"],
                "kesim": "classic-intellectual",
                "aksesuar": ["vintage glasses", "classic watch"],
                "ipucu": "İlkbahar entelektüel — linen + vintage.",
            },
            "spor": {
                "parca": ["grey hoodie", "black joggers", "classic shoes"],
                "kumas": ["organic cotton", "wool"],
                "kesim": "relaxed-scholarly",
                "aksesuar": ["minimal bag", "classic watch"],
                "ipucu": "Spor entelektüel — grey + minimal.",
            },
            "resmi": {
                "parca": ["navy blazer", "white shirt", "leather shoes"],
                "kumas": ["wool", "cotton"],
                "kesim": "classic-tailored",
                "aksesuar": ["fountain pen", "vintage watch"],
                "ipucu": "Resmi entelektüel — classic blazer + aksesuar.",
            },
            "davet": {
                "parca": ["black suit", "white shirt", "leather shoes"],
                "kumas": ["wool", "cotton"],
                "kesim": "classic-formal",
                "aksesuar": ["vintage jewelry", "classic watch"],
                "ipucu": "Davet entelektüel — siyah + vintage elegance.",
            },
        },
        "yaz": {
            "gunluk": {
                "parca": ["white linen shirt", "grey shorts", "classic shoes"],
                "kumas": ["linen", "wool"],
                "kesim": "classic-relaxed",
                "aksesuar": ["vintage sunglasses", "classic watch"],
                "ipucu": "Yazın entelektüel — linen + vintage.",
            },
            "spor": {
                "parca": ["grey t-shirt", "linen shorts", "casual shoes"],
                "kumas": ["organic cotton", "linen"],
                "kesim": "classic-athletic",
                "aksesuar": ["minimal bag", "vintage hat"],
                "ipucu": "Yazın sporu — grey + minimal.",
            },
            "resmi": {
                "parca": ["linen blazer", "white pants", "classic shoes"],
                "kumas": ["linen", "cotton"],
                "kesim": "classic-tailored",
                "aksesuar": ["classic jewelry", "vintage bag"],
                "ipucu": "Yazın resmisi — linen blazer + classic.",
            },
            "davet": {
                "parca": ["grey dress", "heels", "classic shawl"],
                "kumas": ["linen blend", "cotton"],
                "kesim": "classic-dress",
                "aksesuar": ["vintage jewelry", "classic clutch"],
                "ipucu": "Yazın daveti — grey + classic elegance.",
            },
        },
        "sonbahar": {
            "gunluk": {
                "parca": ["grey sweater", "dark pants", "leather shoes"],
                "kumas": ["wool", "denim"],
                "kesim": "classic-fitted",
                "aksesuar": ["vintage scarf", "classic watch"],
                "ipucu": "Sonbahar entelektüel — grey + vintage.",
            },
            "spor": {
                "parca": ["grey hoodie", "dark joggers", "classic boots"],
                "kumas": ["wool blend", "cotton"],
                "kesim": "classic-athletic",
                "aksesuar": ["vintage backpack", "classic hat"],
                "ipucu": "Sonbahar sporu — grey + scholar.",
            },
            "resmi": {
                "parca": ["grey blazer", "white shirt", "leather shoes"],
                "kumas": ["wool", "cotton"],
                "kesim": "classic-tailored",
                "aksesuar": ["vintage jewelry", "classic watch"],
                "ipucu": "Sonbahar resmisi — grey blazer + classic.",
            },
            "davet": {
                "parca": ["grey dress", "boots", "classic coat"],
                "kumas": ["wool", "cotton blend"],
                "kesim": "classic-elegant",
                "aksesuar": ["vintage jewelry", "classic clutch"],
                "ipucu": "Sonbahar daveti — grey + intellectual elegance.",
            },
        },
        "kis": {
            "gunluk": {
                "parca": ["grey coat", "dark pants", "leather boots"],
                "kumas": ["wool coat", "wool"],
                "kesim": "classic-tailored",
                "aksesuar": ["wool scarf", "leather gloves"],
                "ipucu": "Kış entelektüel — grey coat + vintage.",
            },
            "spor": {
                "parca": ["wool coat", "dark leggings", "winter boots"],
                "kumas": ["wool coat", "wool"],
                "kesim": "classic-athletic",
                "aksesuar": ["wool hat", "leather backpack"],
                "ipucu": "Kış sporu — wool + classic.",
            },
            "resmi": {
                "parca": ["grey wool coat", "dark suit", "leather shoes"],
                "kumas": ["wool coat", "wool suit"],
                "kesim": "classic-formal",
                "aksesuar": ["vintage jewelry", "leather accessories"],
                "ipucu": "Kış resmisi — grey coat + scholar.",
            },
            "davet": {
                "parca": ["black coat", "dark dress", "heels"],
                "kumas": ["wool coat", "silk"],
                "kesim": "classic-formal",
                "aksesuar": ["vintage jewelry", "leather clutch"],
                "ipucu": "Kış daveti — classic coat + intellectual elegance.",
            },
        },
    },
    "sofistike-elegant": {
        "coaching": {
            "felsefe": "Zarafet ve sofistikasiyon. Lüks basit ama bellidir. Giyim kültür ve refine taste yansıtmalı.",
            "kombinasyon": "Deri, ipek, kaşmir gibi premium materyaller tercih et. Renk paleti sophisticate (krem, taupe, navy, bordo). Minimal ama high-end.",
            "renk_psikolojisi": "Sade renkler (krem, taupe) refine elegansı yansıtır. Navy ve bordo sofistikasiyon verir. Altın aksesuar lüksü tamamlar.",
            "yaşam_uyarlamasi": "Kalite miktar yerine önemlidir. Birkaç iyi parça seç — premium malzemeler, perfect fit. Giyim minimal ama konuşur. Detay ve craftsmanship önemli."
        },
        "renk_paleti": {
            "ana": ["#FFFAF0", "#D4AF37", "#2D5016", "#8B4513"],
            "vurgu": ["#8B0000", "#C0C0C0"],
            "kacin": ["canlı renkler", "çok koyu olmayan"],
        },
        "ilkbahar": {
            "gunluk": {
                "parca": ["cashmere sweater", "taupe pants", "leather loafers"],
                "kumas": ["cashmere", "premium wool"],
                "kesim": "refined-fitted",
                "aksesuar": ["silk scarf", "gold jewelry"],
                "ipucu": "İlkbahar sofistike — cashmere + taupe elegance.",
            },
            "spor": {
                "parca": ["premium jacket", "silk-blend top", "designer sneakers"],
                "kumas": ["silk blend", "premium cotton"],
                "kesim": "refined-athletic",
                "aksesuar": ["designer watch", "premium bag"],
                "ipucu": "Spor sofistike — premium materials.",
            },
            "resmi": {
                "parca": ["tailored blazer", "silk blouse", "leather shoes"],
                "kumas": ["premium wool", "silk"],
                "kesim": "refined-tailored",
                "aksesuar": ["pearl jewelry", "designer bag"],
                "ipucu": "Resmi sofistike — tailored + silk elegance.",
            },
            "davet": {
                "parca": ["designer dress", "heels", "elegant shawl"],
                "kumas": ["silk", "chiffon"],
                "kesim": "refined-formal",
                "aksesuar": ["luxury jewelry", "designer clutch"],
                "ipucu": "Davet sofistike — designer + elegance.",
            },
        },
        "yaz": {
            "gunluk": {
                "parca": ["silk t-shirt", "linen pants", "designer sandals"],
                "kumas": ["silk", "linen"],
                "kesim": "refined-relaxed",
                "aksesuar": ["silk scarf", "gold jewelry"],
                "ipucu": "Yazın sofistike — silk + linen.",
            },
            "spor": {
                "parca": ["silk-blend top", "tailored shorts", "designer shoes"],
                "kumas": ["silk blend", "premium cotton"],
                "kesim": "refined-athletic",
                "aksesuar": ["designer watch", "luxury bag"],
                "ipucu": "Yazın sporu — premium blend.",
            },
            "resmi": {
                "parca": ["linen dress", "designer sandals", "silk cover"],
                "kumas": ["linen", "silk"],
                "kesim": "refined-dress",
                "aksesuar": ["pearl jewelry", "designer bag"],
                "ipucu": "Yazın resmisi — linen + silk elegance.",
            },
            "davet": {
                "parca": ["designer silk dress", "heels", "elegant wrap"],
                "kumas": ["silk", "chiffon"],
                "kesim": "refined-gown",
                "aksesuar": ["luxury jewelry", "designer clutch"],
                "ipucu": "Yazın daveti — silk + designer elegance.",
            },
        },
        "sonbahar": {
            "gunluk": {
                "parca": ["cashmere cardigan", "tailored pants", "leather shoes"],
                "kumas": ["cashmere", "premium wool"],
                "kesim": "refined-fitted",
                "aksesuar": ["silk scarf", "gold jewelry"],
                "ipucu": "Sonbahar sofistike — cashmere + tailored.",
            },
            "spor": {
                "parca": ["premium jacket", "silk-blend top", "designer boots"],
                "kumas": ["wool blend", "silk"],
                "kesim": "refined-athletic",
                "aksesuar": ["designer watch", "luxury backpack"],
                "ipucu": "Sonbahar sporu — premium elegance.",
            },
            "resmi": {
                "parca": ["tailored blazer", "silk blouse", "leather shoes"],
                "kumas": ["premium wool", "silk"],
                "kesim": "refined-tailored",
                "aksesuar": ["pearl jewelry", "designer bag"],
                "ipucu": "Sonbahar resmisi — wool blazer + silk.",
            },
            "davet": {
                "parca": ["designer dress", "heels", "elegant coat"],
                "kumas": ["silk", "wool blend"],
                "kesim": "refined-formal",
                "aksesuar": ["luxury jewelry", "designer clutch"],
                "ipucu": "Sonbahar daveti — silk dress + coat elegance.",
            },
        },
        "kis": {
            "gunluk": {
                "parca": ["cashmere coat", "tailored pants", "leather boots"],
                "kumas": ["cashmere coat", "premium wool"],
                "kesim": "refined-tailored",
                "aksesuar": ["silk scarf", "leather gloves"],
                "ipucu": "Kış sofistike — cashmere coat + elegance.",
            },
            "spor": {
                "parca": ["premium wool jacket", "tailored leggings", "designer boots"],
                "kumas": ["wool coat", "premium blend"],
                "kesim": "refined-athletic",
                "aksesuar": ["luxury hat", "designer backpack"],
                "ipucu": "Kış sporu — wool + premium.",
            },
            "resmi": {
                "parca": ["tailored coat", "silk dress", "leather shoes"],
                "kumas": ["premium wool coat", "silk"],
                "kesim": "refined-formal",
                "aksesuar": ["luxury jewelry", "designer bag"],
                "ipucu": "Kış resmisi — wool coat + silk elegance.",
            },
            "davet": {
                "parca": ["designer gown", "heels", "elegant coat"],
                "kumas": ["silk", "luxury wool"],
                "kesim": "refined-formal-gown",
                "aksesuar": ["statement jewelry", "luxury clutch"],
                "ipucu": "Kış daveti — silk gown + coat elegance.",
            },
        },
    },
}

# Her sıfatı stil profiline eşle
SIFAT_STIL_MAP = {
    "ciddi": "klasik-minimalist",
    "düzenli": "klasik-minimalist",
    "titiz": "klasik-minimalist",
    "analitik": "klasik-minimalist",
    "planlı": "klasik-minimalist",
    "detayda": "klasik-minimalist",
    "sistemli": "klasik-minimalist",
    "kontrollü": "klasik-minimalist",

    "yaratıcı": "yaratici-bohemyen",
    "özgün": "yaratici-bohemyen",
    "sanatçı": "yaratici-bohemyen",
    "estetik": "yaratici-bohemyen",
    "renkli": "yaratici-bohemyen",
    "özgür": "yaratici-bohemyen",

    "enerjik": "sportif-aktif",
    "aktif": "sportif-aktif",
    "dinamik": "sportif-aktif",
    "atletik": "sportif-aktif",
    "hareket": "sportif-aktif",
    "uyumlu": "sportif-aktif",

    "hassas": "romantik-zarif",
    "duygusal": "romantik-zarif",
    "romantik": "romantik-zarif",
    "zarif": "romantik-zarif",
    "yumuşak": "romantik-zarif",
    "empatik": "romantik-zarif",

    "liderlik": "gucu-otoriter",
    "karizmatik": "gucu-otoriter",
    "dominant": "gucu-otoriter",
    "güçlü": "gucu-otoriter",
    "kararçı": "gucu-otoriter",

    "sosyal": "sosyal-trendy",
    "eğlenceli": "sosyal-trendy",
    "moda": "sosyal-trendy",
    "canlı": "sosyal-trendy",
    "sohbetçi": "sosyal-trendy",
    "uyumlu": "sosyal-trendy",

    "doğal": "dogal-rahat",
    "rahat": "dogal-rahat",
    "özgür": "dogal-rahat",
    "samimi": "dogal-rahat",
    "açık": "dogal-rahat",
    "tedirgin olmaz": "dogal-rahat",

    "entellektüel": "entelektuel-kasaba",
    "içe dönük": "entelektuel-kasaba",
    "derin": "entelektuel-kasaba",
    "merak": "entelektuel-kasaba",
    "reflektif": "entelektuel-kasaba",
    "akademik": "entelektuel-kasaba",

    "seçkin": "sofistike-elegant",
    "zarif": "sofistike-elegant",
    "sofistike": "sofistike-elegant",
    "premium": "sofistike-elegant",
    "refine": "sofistike-elegant",
    "saflık": "sofistike-elegant",
}

# Yüz şekli notları
YUZ_SEKLI_NOTLARI = {
    "oval": "Her kesim uygundur; V-yaka ve uzun kolye önerilir.",
    "kare": "Yumuşak yuvarlak yaka hatları keskin hatları dengeler.",
    "yuvarlak": "V-yaka ve dikey çizgiler yüzü uzatır.",
    "kalp": "Geniş omuz çizgileri alt yüzü dengeler.",
    "uzun": "Yatay çizgiler ve yüksek yaka oranı dengeler.",
    "elmas": "Geniş yaka ve çan etek alt yapıyı dengeler.",
}

# ─────────────────────────────────────────────────────────────────────────────
# Veri üretim fonksiyonları
# ─────────────────────────────────────────────────────────────────────────────

def _get_stil_tipi(sifat_adi: str) -> str:
    """Sıfat adından stil profilini belirle."""
    sifat_lower = sifat_adi.lower()
    for key, stil in SIFAT_STIL_MAP.items():
        if key in sifat_lower:
            return stil
    return "karma-adaptif"  # Default


def generate_giyim_for_sifat(sifat_adi: str, lang: str = "tr") -> dict:
    """Bir sıfat için tam giyim tavsiyesi oluştur."""
    stil_tipi = _get_stil_tipi(sifat_adi)
    template = STIL_TEMPLATES.get(stil_tipi, STIL_TEMPLATES["karma-adaptif"])

    # Coaching'i dile çevir (paralel batch)
    coaching = template.get("coaching", {})
    if lang != "tr" and coaching:
        coaching = translate_coaching_batch(coaching, lang)

    giyim_data = {
        "stil_tipi": stil_tipi,
        "coaching": coaching,
        "renk_paleti": template.get("renk_paleti", {}),
        "yuz_sekli_notu": YUZ_SEKLI_NOTLARI,
        "mevsim": {}
    }

    # Mevsim ve kategori kombinasyonlarını ekle
    for mevsim in ["ilkbahar", "yaz", "sonbahar", "kis"]:
        giyim_data["mevsim"][mevsim] = template.get(mevsim, {})

    return giyim_data


def generate_giyim_dataset(input_path: Path, output_path: Path, lang: str = "tr") -> dict:
    """Tüm sıfatlar için giyim verisini üret."""
    print(f"\n{'='*60}")
    print(f"Giyim Veri Seti Üretiliyor — {lang.upper()}")
    print(f"{'='*60}")

    # Input dosyasını oku
    with open(input_path, "r", encoding="utf-8") as f:
        source_data = json.load(f)

    # Handle both nested ("sifatlar" key) and flat structures
    if "sifatlar" in source_data:
        sifatlar = source_data.get("sifatlar", {})
    else:
        sifatlar = source_data

    giyim_db = {}

    print(f"Toplam sıfat: {len(sifatlar)}")
    print(f"Mevsim × Kategori kombinasyonu: 4 × 4 = 16")
    print(f"Toplam kombinasyon: {len(sifatlar)} × 16 = {len(sifatlar) * 16}")

    for i, (sifat_id, sifat_data) in enumerate(sifatlar.items()):
        # Handle different data types
        if isinstance(sifat_data, dict):
            sifat_adi = sifat_data.get("ad", str(sifat_id))
        else:
            sifat_adi = str(sifat_id)

        giyim_data = generate_giyim_for_sifat(sifat_adi, lang)
        giyim_db[sifat_adi] = giyim_data

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(sifatlar)} sıfat işlendi...")

    # JSON'a yaz
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(giyim_db, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Tamamlandı: {len(giyim_db)} sıfat")
    print(f"Çıktı: {output_path}")

    return giyim_db


def push_to_mongodb(giyim_db: dict, lang: str, mongo_uri: str):
    """MongoDB'ye giyim verisi upsert et."""
    try:
        from pymongo import MongoClient, UpdateOne
    except ImportError:
        print("HATA: pymongo kurulu değil — pip install pymongo")
        return

    print(f"\nMongoDB'ye yazılıyor (giyim field)...")

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=8000)
        db = client["facesyma-coach-backup"]
        col = db[f"coach_attributes_{lang}"]

        ops = [
            UpdateOne(
                {"_id": sifat},
                {"$set": {"giyim": data, "updated_at": datetime.now().isoformat()}},
                upsert=True,  # Yoksa oluştur
            )
            for sifat, data in giyim_db.items()
        ]

        if ops:
            result = col.bulk_write(ops)
            total = result.modified_count + result.upserted_count
            print(f"✓ MongoDB: {result.modified_count} güncellendi, {result.upserted_count} yeni oluşturuldu (toplam: {total})")
            print(f"  DB: facesyma-coach-backup")
            print(f"  Koleksiyon: coach_attributes_{lang}")

        client.close()
    except Exception as e:
        print(f"HATA MongoDB: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Facesyma giyim veri seti üreticisi")
    p.add_argument("--input",  default="../facesyma_migrate/sifat_veritabani.json")
    p.add_argument("--output", default="sifat_giyim_{lang}.json")
    p.add_argument("--lang", default="tr",
                   choices=["tr","en","de","ru","ar","es","ko","ja",
                           "zh","hi","fr","pt","bn","id","ur","it","vi","pl"])
    p.add_argument("--all-langs", action="store_true", help="Tüm dilleri üret")
    p.add_argument("--push-mongo", action="store_true", help="MongoDB'ye yaz")
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
        db = generate_giyim_dataset(input_path, out, lang)

        if args.push_mongo:
            push_to_mongodb(db, lang, args.mongo_uri)

    print("\n✓ Tüm işlemler tamamlandı")
    if not args.push_mongo:
        print("\nMongoDB'ye yazmak için:")
        print("  python generate_giyim_dataset.py --push-mongo")


if __name__ == "__main__":
    main()
