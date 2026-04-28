"""
seed_attribute_databases.py
===========================
Populates MongoDB with personality trait sentences for face analysis.

Sentence style: DIRECT statements about the person — no "Your eyes suggest..." or feature references.
"Derin empati yeteneğine sahipsiniz." NOT "Gözlerinizin yakın mesafesi, derin empatiyi yansıtır."

Databases:
  database_attribute_tr/en/de/etc.  — trait sentences per facial feature+category
  database_categories               — career/leadership/social sentences per trait name
  pos_neg                           — positive/negative/unbiased classification
  contrast                          — conflicting trait pairs
"""
import os
from pymongo import MongoClient, UpdateOne

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/')
client = MongoClient(MONGO_URI)

# ===========================================================================
# TURKISH — facial feature docs (direct style, no feature references)
# ===========================================================================
TR_EYE_DISTANCE = {
    "_id": "eyes_distance",
    "eyes_near": {
        "duygusal": [
            "Derin empati kurma yeteneğiniz son derece güçlüdür.",
            "Sevdiklerinizin duygularını kolayca hisseder ve anında yanlarında olursunuz.",
        ],
        "hassas": [
            "İnce detayları fark eden hassas bir yapınız var; çevrenizdekilerin gözden kaçırdığı şeyleri siz görürsünüz.",
            "Titiz ve ince ruhlu bir kişiliksiniz.",
        ],
        "içgüdüsel": [
            "İçgüdülerinize güvenir ve doğru kararları hızla alırsınız.",
        ],
        "bağlılık": [
            "Derin ve sadık ilişkiler kurarsınız; bağlandığınız kişilere sonuna kadar güvenilir kalırsınız.",
        ],
    },
    "eyes_far": {
        "özgür": [
            "Özgürlüğe değer verir, sınırları aşmayı seversiniz.",
            "Alışılmış kalıpların dışına çıkmaktan korkmaz, kendi yolunuzu çizersiniz.",
        ],
        "yaratıcı": [
            "Zengin hayal gücünüzle özgün fikirler üretirsiniz.",
            "Sanatsal ve yenilikçi bir ruhunuz var.",
        ],
        "vizyoner": [
            "Büyük resmi görür, uzun vadeli düşünürsünüz.",
        ],
        "bağımsız": [
            "Kendi yolunuzu çizer, bağımsız karar verme gücüne sahipsiniz.",
        ],
    },
    "eyes_distance_golden": {
        "dengeli": [
            "Hayatın her alanında mükemmel bir denge kurarsınız.",
            "İç ve dış dünyanızla uyumlu bir ilişki içindesiniz.",
        ],
        "karizmatik": [
            "Doğal bir çekiciliğiniz var; bulunduğunuz ortamı dolduran karizmatik bir enerjiye sahipsiniz.",
        ],
        "çekici": [
            "Doğuştan gelen güçlü bir çekiciliğiniz var.",
        ],
    },
}

TR_EYE_SIZE = {
    "_id": "eyes_size",
    "eyes_size_r_small": {
        "dikkatli": [
            "Her ayrıntıyı gözden geçiren, son derece dikkatli bir gözlemcisiniz.",
        ],
        "analitik": [
            "Olaylara sistematik yaklaşır, analitik bir zekâya sahipsiniz.",
        ],
    },
    "eyes_size_r_big": {
        "açık_kalpli": [
            "Açık kalpli ve sıcakkanlı bir kişiliğiniz var.",
        ],
        "ifadeli": [
            "Duygularınızı açıkça ifade eder, etkileyici bir enerjiniz olur.",
        ],
    },
    "eyes_size_l_small": {
        "koruyucu": [
            "Sevdiklerinizi koruma ve gözetme içgüdüsü güçlüdür.",
        ],
    },
    "eyes_size_l_golden": {
        "dengeli": [
            "Duygusal ve rasyonel yönlerinizi dengeli biçimde kullanırsınız.",
        ],
        "uyumlu": [
            "Farklı ortam ve insanlara kolayca uyum sağlarsınız.",
        ],
    },
    "not_defined": {
        "özgün": [
            "Benzersiz ve özgün bir kişiliğe sahipsiniz; sizi standartlara sokmak mümkün değildir.",
            "Standartların ötesinde, kendine özgü niteliklere sahipsiniz.",
        ],
        "gizemli": [
            "Derinlikli ve gizemli bir iç dünyanız var; insanları merak içinde bırakırsınız.",
        ],
    },
}

TR_EYE_COMPARE = {
    "_id": "eyes_compare",
    "right_eye_bigger_than_left_eye": {
        "lider": [
            "Güçlü liderlik özellikleriniz var; başkalarına yön verir ve ilham verirsiniz.",
            "İnisiyatif alma konusunda çekinmez, grubunuzu kararlılıkla yönetirsiniz.",
        ],
        "kararlı": [
            "Hedeflerinize kararlılıkla ilerler, azminizden taviz vermezsiniz.",
        ],
    },
    "left_eye_bigger_than_right_eye": {
        "sezgisel": [
            "Güçlü sezgilerinize sahipsiniz; yaratıcı içgüdüleriniz sizi doğru yönlere taşır.",
        ],
        "sanatsal": [
            "Sanatsal bir bakış açınız ve derin estetik duyarlılığınız var.",
        ],
    },
    "eyes_equal": {
        "dengeli": [
            "Mükemmel bir iç dengeye sahipsiniz; duygular ve mantık aranızda uyum içinde çalışır.",
        ],
        "adil": [
            "Her duruma adil ve tarafsız yaklaşırsınız.",
        ],
    },
}

TR_EYEBROW_DISTANCE = {
    "_id": "eyebrows_eyes_distance",
    "eyebrows_eyes_distance_far": {
        "özgüveni_yüksek": [
            "Kendinize güveniniz son derece yüksek; eleştirilerden sarsılmadan yolunuza devam edersiniz.",
            "Sağlam bir karakter yapısına sahipsiniz, baskı altında kolayca şekil almazsınız.",
        ],
        "açık_fikirli": [
            "Yeni fikirlere açık ve önyargısız bir zihne sahipsiniz.",
        ],
        "etkileyici": [
            "Başkalarını kolayca etkiler ve ikna edersiniz.",
        ],
    },
    "eyebrows_eyes_distance_near": {
        "odaklı": [
            "Konsantrasyon gücünüz yüksek; bir hedefe odaklandığınızda tam anlamıyla adanırsınız.",
        ],
        "yoğun": [
            "Derin düşünür, olayları yoğun biçimde analiz edersiniz.",
        ],
    },
    "eyebrows_eyes_distance_golden": {
        "cazip": [
            "Doğal bir çekicilik ve güçlü bir ifadesel karizmanız var.",
        ],
        "uyumlu": [
            "Yüzünüzün tüm hatları arasında mükemmel bir uyum kurarsınız.",
        ],
    },
}

TR_LIP_WIDTH = {
    "_id": "lips_width",
    "lips_wide": {
        "cömert": [
            "Cömert ve paylaşımcı bir ruhunuz var; vermekten her zaman keyif alırsınız.",
            "Elindekini paylaşmaktan çekinmez, açık yüreklilikle yaklaşırsınız.",
        ],
        "sosyal": [
            "Sosyal ortamlarda kendinizi rahat hisseder, insanlarla kolayca bağ kurarsınız.",
        ],
        "ifadeli": [
            "Duygularınızı açıkça ifade eden, dinamik bir kişiliğiniz var.",
        ],
    },
    "lips_narrow": {
        "seçici": [
            "İlişkilerinizde seçici ve dikkatli davranırsınız.",
        ],
        "düşünceli": [
            "Konuşmadan önce düşünürsünüz; her sözün ağırlığını bilirsiniz.",
        ],
    },
    "lips_width_golden": {
        "çekici": [
            "Güçlü ve doğal bir çekiciliğiniz var.",
        ],
        "karizmatik": [
            "Etkileyici bir iletişim kurma yeteneğiniz bulunuyor.",
        ],
    },
}

TR_LIP_THICKNESS = {
    "_id": "lips_thickness",
    "lips_thin": {
        "zeki": [
            "Keskin bir zekânız ve güçlü muhakeme yeteneğiniz var.",
            "Sözcükleri özenle seçer, düşünceli konuşursunuz.",
        ],
        "kararlı": [
            "Hedeflerinize kararlılıkla yürür, azminizden ödün vermezsiniz.",
        ],
        "hassas": [
            "Ince ayrıntıları fark eden titiz ve hassas bir yapınız var.",
        ],
    },
    "lips_thick": {
        "tutkulu": [
            "Hayata tutkuyla bağlı, duygularınızı yoğun yaşarsınız.",
        ],
        "şefkatli": [
            "Sevgi dolu ve şefkatli bir kişiliğiniz var.",
        ],
        "çekici": [
            "Güçlü bir çekiciliğiniz ve sıcakkanlılığınız var.",
        ],
    },
    "lips_thickness_golden": {
        "dengeli": [
            "Mükemmel bir uyum ve denge içinde yaşarsınız.",
        ],
        "uyumlu": [
            "İfadenizde ve iletişiminizde kusursuz bir uyum sağlarsınız.",
        ],
    },
}

TR_LIP_COMPARE = {
    "_id": "lips_height_compare",
    "lower_lip_bigger_than_upper_lip": {
        "pratik": [
            "Pratik zekânızla hayata ayakları yere basan bir yaklaşım sergilersiniz.",
            "Güçlü bir uygulama yeteneğiniz ve somut düşünme kapasiteniz var.",
        ],
        "güvenilir": [
            "Sözünüzün eri birisiniz; insanlar size güvenebilir.",
        ],
    },
    "upper_lip_bigger_than_lower_lip": {
        "idealist": [
            "İdealist ve hayalperest bir yapınız var; büyük düşünürsünüz.",
        ],
        "ilhamlı": [
            "Vizyon sahibisiniz ve başkalarına ilham verme gücünüz var.",
        ],
    },
    "lips_height_equal": {
        "dengeli": [
            "Duygusal ve rasyonel denge arasında mükemmel bir denge kurarsınız.",
        ],
        "uyumlu": [
            "İç ve dış dünyanızda uyum içinde yaşarsınız.",
        ],
    },
}

TR_NOSE_SIZE = {
    "_id": "nose_size",
    "nose_big": {
        "güçlü": [
            "Güçlü bir irade ve kararlı bir kişiliğe sahipsiniz.",
            "Zorluklarla yüzleşir, engelleri aşma konusunda öne çıkarsınız.",
        ],
        "girişimci": [
            "Risk almaktan çekinmez, girişimci bir ruha sahipsiniz.",
        ],
        "özgüvenli": [
            "Kendine güvenen ve güçlü bir duruşu olan birisiniz.",
        ],
    },
    "nose_small": {
        "narin": [
            "Zarif ve narin bir kişiliğiniz var.",
        ],
        "uyumlu": [
            "Çatışmalardan kaçınır, uyumlu ilişkiler kurarsınız.",
        ],
    },
    "nose_size_normal": {
        "dengeli": [
            "Dengeli ve uyumlu bir kişilik yapısına sahipsiniz.",
        ],
    },
}

TR_NOSE_LENGTH = {
    "_id": "nose_length",
    "nose_long": {
        "analitik": [
            "Derin analiz yapabilir, ayrıntılara büyük önem verirsiniz.",
            "Sistematik düşünür, uzun vadeli planlama konusunda yeteneklisiniz.",
        ],
        "sabırlı": [
            "Sabırlı ve inatçı bir karakter yapısına sahipsiniz.",
        ],
        "titiz": [
            "Mükemmeliyetçi bir anlayışa ve titiz çalışma disiplinine sahipsiniz.",
        ],
    },
    "nose_short": {
        "pratik": [
            "Pratik çözümler üretir, etkili bir problem çözücüsünüz.",
        ],
        "enerjik": [
            "Enerjik ve dinamik bir kişiliğiniz var.",
        ],
    },
    "nose_length_golden": {
        "çekici": [
            "Dengeli ve kusursuz bir estetik yapıya sahipsiniz.",
        ],
        "dengeli": [
            "Genel uyumunuza büyük katkı sağlayan ideal bir yapınız var.",
        ],
    },
}

TR_NOSE_WIDTH = {
    "_id": "nose_width",
    "nose_wide": {
        "cömert": [
            "Cömert ve paylaşımcı bir ruhunuz var.",
            "Açık yürekli ve yardımsever bir kişiliğiniz var.",
        ],
        "enerjik": [
            "Güçlü yaşam enerjisi ve dinamik bir karaktere sahipsiniz.",
        ],
    },
    "nose_narrow": {
        "seçici": [
            "Zevklerinde seçici ve titiz bir karakteriniz var.",
        ],
        "zarif": [
            "Zarif ve estetik bir kişiliğiniz var.",
        ],
    },
    "nose_width_golden": {
        "uyumlu": [
            "Mükemmel bir denge ve uyum içindesiniz.",
        ],
    },
}

TR_FOREHEAD = {
    "_id": "forehead_distance",
    "forehead_distance_golden": {
        "zeki": [
            "Yüksek bir zekâya ve güçlü analitik düşünme kapasitesine sahipsiniz.",
            "Öğrenme hızınız ve kavrama yeteneğiniz son derece gelişmiş.",
        ],
        "yaratıcı": [
            "Yaratıcı zekânız ve yenilikçi düşünme yeteneğiniz sizi öne çıkarıyor.",
        ],
        "lider": [
            "Doğal bir liderlik karizmasına ve güçlü etki alanına sahipsiniz.",
        ],
    },
    "forehead_distance_far": {
        "özgür_ruhlu": [
            "Özgür düşünceli, alışılmış kalıpların dışına çıkan bir ruhunuz var.",
        ],
        "vizyoner": [
            "Büyük resimleri görebilen vizyoner bir bakış açısına sahipsiniz.",
        ],
    },
    "forehead_distance_near": {
        "pratik": [
            "Pratik ve somut düşünür, hızlı karar verirsiniz.",
        ],
        "odaklı": [
            "Güçlü konsantrasyon ve odaklanma yeteneğiniz var.",
        ],
    },
}

# ===========================================================================
# ENGLISH — direct style
# ===========================================================================
EN_EYE_DISTANCE = {
    "_id": "eyes_distance",
    "eyes_near": {
        "emotional": [
            "You have a deep capacity for emotional connection and empathy.",
            "You quickly sense others' feelings and are always there for them.",
        ],
        "perceptive": [
            "You notice subtle details that others often miss.",
            "You are a sharp and perceptive observer of the world around you.",
        ],
        "devoted": [
            "You build deep, loyal relationships and are completely reliable to those you love.",
        ],
    },
    "eyes_far": {
        "free_spirited": [
            "You value freedom, love pushing boundaries, and forge your own path.",
        ],
        "creative": [
            "You produce original ideas with a rich imagination.",
            "You have an artistic and innovative spirit.",
        ],
        "visionary": [
            "You see the big picture and think long-term.",
        ],
        "independent": [
            "You chart your own course and have the strength to make independent decisions.",
        ],
    },
    "eyes_distance_golden": {
        "balanced": [
            "You maintain perfect balance in every area of life.",
        ],
        "charismatic": [
            "You have natural magnetism and a charismatic energy that fills any room.",
        ],
        "attractive": [
            "You possess an innate, powerful attractiveness.",
        ],
    },
}

EN_EYE_SIZE = {
    "_id": "eyes_size",
    "eyes_size_r_small": {
        "analytical": [
            "You are a meticulous, detail-oriented thinker who reviews every angle.",
        ],
        "precise": [
            "You take a systematic approach to problems and value precision.",
        ],
    },
    "eyes_size_r_big": {
        "open_hearted": [
            "You have a warm, open-hearted personality.",
        ],
        "expressive": [
            "You express your emotions openly and have a vivid, energetic presence.",
        ],
    },
    "eyes_size_l_small": {
        "protective": [
            "You have a strong instinct to protect and watch over the people you love.",
        ],
    },
    "eyes_size_l_golden": {
        "balanced": [
            "You use both your emotional and rational sides in perfect balance.",
        ],
        "harmonious": [
            "You adapt easily to different environments and people.",
        ],
    },
    "not_defined": {
        "unique": [
            "You have a truly unique and individual personality — impossible to put in a box.",
            "You carry distinctive qualities that set you apart from everyone else.",
        ],
        "mysterious": [
            "You have a deep, intriguing inner world that draws people in with its mystery.",
        ],
    },
}

EN_EYE_COMPARE = {
    "_id": "eyes_compare",
    "right_eye_bigger_than_left_eye": {
        "leader": [
            "You have strong leadership qualities and naturally guide and inspire others.",
            "You are decisive, take initiative, and lead your group with confidence.",
        ],
        "determined": [
            "You pursue your goals with unwavering determination.",
        ],
    },
    "left_eye_bigger_than_right_eye": {
        "intuitive": [
            "You have powerful intuition that consistently guides you in the right direction.",
        ],
        "artistic": [
            "You have an artistic sensibility and deep aesthetic appreciation.",
        ],
    },
    "eyes_equal": {
        "balanced": [
            "You have remarkable inner balance — emotion and logic work in harmony within you.",
        ],
        "fair": [
            "You approach all situations with fairness and impartiality.",
        ],
    },
}

EN_EYEBROW_DISTANCE = {
    "_id": "eyebrows_eyes_distance",
    "eyebrows_eyes_distance_far": {
        "self_confident": [
            "Your self-confidence is exceptionally strong; you continue on your path unfazed by criticism.",
            "You have a solid character that doesn't bend under pressure.",
        ],
        "open_minded": [
            "You have an open, non-judgmental mind that welcomes new ideas.",
        ],
        "impressive": [
            "You effortlessly influence and persuade those around you.",
        ],
    },
    "eyebrows_eyes_distance_near": {
        "focused": [
            "When you set your mind on a goal, you commit to it completely.",
        ],
        "intense": [
            "You think deeply and analyze situations with great intensity.",
        ],
    },
    "eyebrows_eyes_distance_golden": {
        "attractive": [
            "You have natural magnetism and a charismatic expressiveness.",
        ],
        "harmonious": [
            "You create perfect harmony in everything you do.",
        ],
    },
}

EN_LIP_WIDTH = {
    "_id": "lips_width",
    "lips_wide": {
        "generous": [
            "You are generous and giving by nature — you find joy in sharing.",
            "You approach others with openness and a giving spirit.",
        ],
        "social": [
            "You feel at home in social settings and form connections with ease.",
        ],
        "expressive": [
            "You express your emotions openly and have a dynamic personality.",
        ],
    },
    "lips_narrow": {
        "selective": [
            "You are thoughtful and selective in your relationships.",
        ],
        "thoughtful": [
            "You choose your words carefully and speak with intention.",
        ],
    },
    "lips_width_golden": {
        "attractive": [
            "You have a strong and natural attractiveness.",
        ],
        "charismatic": [
            "You have an impressive communication presence and charisma.",
        ],
    },
}

EN_LIP_THICKNESS = {
    "_id": "lips_thickness",
    "lips_thin": {
        "intelligent": [
            "You have a sharp intellect and strong reasoning ability.",
            "You choose your words carefully and think before you speak.",
        ],
        "determined": [
            "You pursue your goals with focus and never compromise your drive.",
        ],
        "precise": [
            "You have a meticulous nature and attention to fine details.",
        ],
    },
    "lips_thick": {
        "passionate": [
            "You are passionate about life and experience emotions intensely.",
        ],
        "compassionate": [
            "You are warm, loving, and compassionate by nature.",
        ],
        "attractive": [
            "You radiate natural warmth and attractiveness.",
        ],
    },
    "lips_thickness_golden": {
        "balanced": [
            "You live with a wonderful sense of harmony and balance.",
        ],
        "harmonious": [
            "You bring seamless harmony to everything you do.",
        ],
    },
}

EN_LIP_COMPARE = {
    "_id": "lips_height_compare",
    "lower_lip_bigger_than_upper_lip": {
        "practical": [
            "You apply practical intelligence and a grounded, feet-on-the-earth approach to life.",
            "You have strong implementation skills and concrete thinking.",
        ],
        "reliable": [
            "You are a person of your word — people can count on you.",
        ],
    },
    "upper_lip_bigger_than_lower_lip": {
        "idealistic": [
            "You are idealistic and visionary — you think big.",
        ],
        "inspired": [
            "You are a visionary who has the power to inspire others.",
        ],
    },
    "lips_height_equal": {
        "balanced": [
            "You maintain perfect balance between emotions and reason.",
        ],
        "harmonious": [
            "You live in harmony with both your inner and outer world.",
        ],
    },
}

EN_NOSE_SIZE = {
    "_id": "nose_size",
    "nose_big": {
        "strong": [
            "You have a strong will and a determined character.",
            "You confront challenges head-on and rise above obstacles.",
        ],
        "entrepreneurial": [
            "You are not afraid to take risks — you have an entrepreneurial spirit.",
        ],
        "confident": [
            "You project strong self-confidence and an assertive presence.",
        ],
    },
    "nose_small": {
        "delicate": [
            "You have an elegant and refined personality.",
        ],
        "harmonious": [
            "You prefer cooperation and harmony over conflict.",
        ],
    },
    "nose_size_normal": {
        "balanced": [
            "You have a balanced, adaptable personality.",
        ],
    },
}

EN_NOSE_LENGTH = {
    "_id": "nose_length",
    "nose_long": {
        "analytical": [
            "You think deeply and pay close attention to detail.",
            "You approach problems systematically and plan for the long term.",
        ],
        "patient": [
            "You are patient and persistent in the pursuit of your goals.",
        ],
        "thorough": [
            "You work with great thoroughness and hold yourself to high standards.",
        ],
    },
    "nose_short": {
        "practical": [
            "You are a practical thinker who produces effective solutions.",
        ],
        "energetic": [
            "You have high energy and a dynamic, action-oriented personality.",
        ],
    },
    "nose_length_golden": {
        "attractive": [
            "You have a beautifully balanced and aesthetic character.",
        ],
        "balanced": [
            "You bring ideal proportions and harmony to everything.",
        ],
    },
}

EN_NOSE_WIDTH = {
    "_id": "nose_width",
    "nose_wide": {
        "generous": [
            "You are generous and open-hearted.",
            "You are warm and always willing to help others.",
        ],
        "energetic": [
            "You have strong life energy and a dynamic character.",
        ],
    },
    "nose_narrow": {
        "selective": [
            "You have refined taste and are selective in your choices.",
        ],
        "elegant": [
            "You have an elegant and aesthetically refined personality.",
        ],
    },
    "nose_width_golden": {
        "harmonious": [
            "You create perfect balance and harmony.",
        ],
    },
}

EN_FOREHEAD = {
    "_id": "forehead_distance",
    "forehead_distance_golden": {
        "intelligent": [
            "You have a high intellect and strong analytical thinking capacity.",
            "Your learning speed and comprehension are exceptionally developed.",
        ],
        "creative": [
            "Your creative intelligence and innovative thinking set you apart.",
        ],
        "leader": [
            "You have a natural leadership charisma and a powerful sphere of influence.",
        ],
    },
    "forehead_distance_far": {
        "free_spirited": [
            "You are a free thinker who goes beyond conventional boundaries.",
        ],
        "visionary": [
            "You have a visionary perspective and can see the big picture.",
        ],
    },
    "forehead_distance_near": {
        "practical": [
            "You think in practical and concrete terms, making quick decisions.",
        ],
        "focused": [
            "You have powerful concentration and the ability to focus deeply.",
        ],
    },
}

# ===========================================================================
# CATEGORY-SPECIFIC SENTENCES per trait
# Stored in `database_categories` collection
# Keys: trait_name → {kariyer_tr, kariyer_en, liderlik_tr, liderlik_en, sosyal_tr, sosyal_en, kisilik_tr, kisilik_en}
# ===========================================================================
CATEGORY_SENTENCES = [
    {
        "_id": "duygusal",
        "kariyer_tr": "İş hayatında empati yeteneğiniz en büyük gücünüzdür; müşteriler ve iş arkadaşları sizi güvenilir bulur.",
        "kariyer_en": "Your empathy is your greatest professional asset; colleagues and clients naturally trust you.",
        "liderlik_tr": "Ekibinizi duygusal zeka ile yönetir, her bireyin motivasyonunu anlayarak ilham verirsiniz.",
        "liderlik_en": "You lead your team with emotional intelligence, inspiring each person by understanding what drives them.",
        "sosyal_tr": "Derin ve anlamlı ilişkiler kurarsınız; çevreniz sizi dinleyen ve anlayan biri olarak tanır.",
        "sosyal_en": "You build deep, meaningful connections; people around you know you as someone who truly listens and understands.",
        "kisilik_tr": "Zengin bir iç dünyanız ve güçlü bir empati yeteneğiniz var.",
        "kisilik_en": "You have a rich inner world and a powerful capacity for empathy.",
    },
    {
        "_id": "analitik",
        "kariyer_tr": "Verileri ve durumları derinlemesine analiz eder, iş hayatında çözüm odaklı yaklaşımınızla fark yaratırsınız.",
        "kariyer_en": "You analyze data and situations in depth, making a difference professionally with your solution-focused approach.",
        "liderlik_tr": "Analitik düşünceniz sayesinde stratejik kararlar alır, ekibinizi doğru hedeflere yönlendirirsiniz.",
        "liderlik_en": "Your analytical thinking enables you to make strategic decisions and direct your team toward the right goals.",
        "sosyal_tr": "Sorunlara mantıklı çözümler sunar; çevreniz tavsiyelerinize güvenir.",
        "sosyal_en": "You offer logical solutions to problems; those around you trust your advice.",
        "kisilik_tr": "Sistematik ve analitik bir zekânız var.",
        "kisilik_en": "You have a systematic and analytical intellect.",
    },
    {
        "_id": "lider",
        "kariyer_tr": "Doğal liderlik özellikleriniz kariyer yolculuğunuzda sizi yöneticilik pozisyonlarına taşır.",
        "kariyer_en": "Your natural leadership qualities will carry you to management positions throughout your career.",
        "liderlik_tr": "İnsanları bir araya getirir, ortak hedeflere doğru ilham vererek yönetirsiniz.",
        "liderlik_en": "You bring people together and lead them toward common goals with inspiration.",
        "sosyal_tr": "Gruplarda doğal olarak öne çıkar, insanların güvenini hızla kazanırsınız.",
        "sosyal_en": "You naturally stand out in groups and quickly earn people's trust.",
        "kisilik_tr": "Güçlü bir liderlik karakterine sahipsiniz.",
        "kisilik_en": "You have a powerful leadership character.",
    },
    {
        "_id": "yaratıcı",
        "kariyer_tr": "Yaratıcı düşünceniz sanat, tasarım, pazarlama gibi alanlarda size büyük avantaj sağlar.",
        "kariyer_en": "Your creativity gives you a great advantage in fields like art, design, and marketing.",
        "liderlik_tr": "Yenilikçi fikirleri hayata geçirme konusunda ekibinizi motive edersiniz.",
        "liderlik_en": "You motivate your team to bring innovative ideas to life.",
        "sosyal_tr": "Özgün bakış açınız sizi sohbet ortamlarında ilgi çekici kılar.",
        "sosyal_en": "Your original perspective makes you compelling and interesting in social settings.",
        "kisilik_tr": "Zengin hayal gücüne sahip, yaratıcı bir ruhunuz var.",
        "kisilik_en": "You have a rich imagination and a creative spirit.",
    },
    {
        "_id": "güçlü",
        "kariyer_tr": "Zorlu koşullarda bile performansınızı korur, iş hayatında güvenilir bir sütun olursunuz.",
        "kariyer_en": "You maintain your performance even under tough conditions, becoming a reliable pillar in professional life.",
        "liderlik_tr": "Krizlerde sakinliğinizi ve gücünüzü koruyarak ekibinize güven verirsiniz.",
        "liderlik_en": "You give your team confidence by maintaining your composure and strength in crises.",
        "sosyal_tr": "Zor anlarda insanların yanında olan, güvenilir bir dost olursunuz.",
        "sosyal_en": "You are a reliable friend who stands by people in difficult moments.",
        "kisilik_tr": "Güçlü irade ve kararlı bir kişilik yapısına sahipsiniz.",
        "kisilik_en": "You have a strong will and a determined personality.",
    },
    {
        "_id": "vizyoner",
        "kariyer_tr": "Geleceği öngörerek uzun vadeli stratejiler geliştirirsiniz; inovasyon alanlarında öne çıkarsınız.",
        "kariyer_en": "You anticipate the future and develop long-term strategies; you stand out in innovation.",
        "liderlik_tr": "Ekibinize net bir gelecek vizyonu çizer, onları büyük hedeflere doğru motive edersiniz.",
        "liderlik_en": "You paint a clear future vision for your team, motivating them toward ambitious goals.",
        "sosyal_tr": "Konuşmalarınızda ilham verici; insanlar sizden yeni perspektifler öğrenir.",
        "sosyal_en": "You are inspiring in conversation; people learn new perspectives from you.",
        "kisilik_tr": "Büyük resmi görür, uzun vadeli düşünürsünüz.",
        "kisilik_en": "You see the big picture and think long-term.",
    },
    {
        "_id": "sosyal",
        "kariyer_tr": "Güçlü sosyal becerileriniz networking ve müşteri ilişkilerinde büyük avantaj sağlar.",
        "kariyer_en": "Your strong social skills give you a big advantage in networking and client relationships.",
        "liderlik_tr": "Ekip ruhunu canlandırır, iş arkadaşlarınızı bir arada tutarsınız.",
        "liderlik_en": "You energize team spirit and keep your colleagues united.",
        "sosyal_tr": "Her ortamda kendinizi rahat hisseder, kolayca arkadaş edinirsiniz.",
        "sosyal_en": "You feel comfortable in any environment and make friends easily.",
        "kisilik_tr": "Sosyal bir doğanız var; insanlarla bağ kurmaktan güç alırsınız.",
        "kisilik_en": "You have a social nature; you draw energy from connecting with people.",
    },
    {
        "_id": "cömert",
        "kariyer_tr": "Bilgi ve deneyimlerinizi paylaşmaktan çekinmez; mentorluk ve eğitim rollerinde parlaırsınız.",
        "kariyer_en": "You freely share your knowledge and experience; you shine in mentoring and training roles.",
        "liderlik_tr": "Takımınıza kaynaklarını ve bilgisini cömertçe sunar, herkesin gelişimine katkıda bulunursunuz.",
        "liderlik_en": "You generously offer resources and knowledge to your team, contributing to everyone's growth.",
        "sosyal_tr": "Elinizi açık tutmanız insanların sizi sevmesini sağlar; etrafınızda hep vefa görürsünüz.",
        "sosyal_en": "Your generosity makes people love you; you are surrounded by loyalty.",
        "kisilik_tr": "Cömert ve paylaşımcı bir ruhunuz var.",
        "kisilik_en": "You have a generous and giving spirit.",
    },
    {
        "_id": "kararlı",
        "kariyer_tr": "Hedefe odaklandığınızda hiçbir engel sizi durduramaz; zor projeleri başarıyla teslim edersiniz.",
        "kariyer_en": "Once you set your sights on a goal, nothing stops you; you deliver on tough projects.",
        "liderlik_tr": "Kararlı tutumunuz ekibinize güven verir ve onlara örnek olursunuz.",
        "liderlik_en": "Your decisive stance gives your team confidence and sets an example for them.",
        "sosyal_tr": "İnsanlar fikirlerinizin arkasında durduğunuzu gördüklerinde size daha fazla güvenir.",
        "sosyal_en": "When people see you stand behind your convictions, they trust you even more.",
        "kisilik_tr": "Hedeflerinize kararlılıkla ilerler, azminizden ödün vermezsiniz.",
        "kisilik_en": "You pursue your goals with unwavering determination.",
    },
    {
        "_id": "hassas",
        "kariyer_tr": "İnce ayrıntıları fark etme yeteneğiniz araştırma, tasarım ve kalite kontrolde değer taşır.",
        "kariyer_en": "Your ability to notice fine details is valuable in research, design, and quality control.",
        "liderlik_tr": "Ekibinizdeki küçük gerilimleri erken fark eder, çatışmaları önlersiniz.",
        "liderlik_en": "You notice small tensions in your team early and prevent conflicts.",
        "sosyal_tr": "İnsanların söylemediği şeyleri hisseder, onlara özel ve değerli hissettirirsiniz.",
        "sosyal_en": "You sense what people leave unsaid, making them feel seen and valued.",
        "kisilik_tr": "İnce ve hassas bir ruha sahipsiniz.",
        "kisilik_en": "You have a delicate and sensitive soul.",
    },
    {
        "_id": "özgüvenli",
        "kariyer_tr": "Sunum ve müzakerelerde güçlü bir izlenim bırakır, kariyer fırsatlarını elinize geçirirsiniz.",
        "kariyer_en": "You make a strong impression in presentations and negotiations, seizing career opportunities.",
        "liderlik_tr": "Güvenli duruşunuz ekibinize moral verir ve onların sizin arkanızda durmasını sağlar.",
        "liderlik_en": "Your confident presence boosts your team's morale and earns their support.",
        "sosyal_tr": "İnsanlar varlığınızda kendini güvende ve rahat hisseder.",
        "sosyal_en": "People feel safe and at ease in your presence.",
        "kisilik_tr": "Kendinize güvenen, güçlü bir duruşa sahipsiniz.",
        "kisilik_en": "You project strong self-confidence and a powerful presence.",
    },
    {
        "_id": "pratik",
        "kariyer_tr": "Hızlı ve etkili çözümler üretir, iş süreçlerini optimize edersiniz.",
        "kariyer_en": "You produce quick, effective solutions and optimize work processes.",
        "liderlik_tr": "Gereksiz karmaşıklıkları ortadan kaldırır, ekibinizi net hedeflere yönlendirirsiniz.",
        "liderlik_en": "You eliminate unnecessary complexity and direct your team toward clear goals.",
        "sosyal_tr": "Pratik tavsiyelerinizle insanlara somut yardım sağlarsınız.",
        "sosyal_en": "You provide concrete, practical help to people with your advice.",
        "kisilik_tr": "Pratik zekânızla hayata ayakları yere basan yaklaşım sergilersiniz.",
        "kisilik_en": "You approach life practically with a feet-on-the-ground mindset.",
    },
    {
        "_id": "tutkulu",
        "kariyer_tr": "İşinize tutkuyla bağlanır; bu tutku sizi sektörünüzde tanınan bir isim yapar.",
        "kariyer_en": "You connect to your work with passion; this passion makes you a recognized name in your field.",
        "liderlik_tr": "Coşkunuz ve tutkunuz etrafınızdakileri harekete geçirir.",
        "liderlik_en": "Your enthusiasm and passion set those around you in motion.",
        "sosyal_tr": "Hayata coşkuyla bağlı kişiliğiniz etrafınıza enerji saçar.",
        "sosyal_en": "Your passionate, enthusiastic personality radiates energy to those around you.",
        "kisilik_tr": "Hayata tutkuyla bağlı, duygularınızı yoğun yaşarsınız.",
        "kisilik_en": "You are passionately connected to life and experience emotions with great intensity.",
    },
    {
        "_id": "girişimci",
        "kariyer_tr": "Risk almaktan çekinmez, yeni iş fırsatlarını değerlendirirsiniz; girişimcilik size göre.",
        "kariyer_en": "You are not afraid to take risks and seize new opportunities; entrepreneurship suits you.",
        "liderlik_tr": "Yeni girişimleri başlatmak ve ekibinizi bu yolda motive etmek konusunda doğal bir yeteneğiniz var.",
        "liderlik_en": "You have a natural talent for launching new initiatives and motivating your team along the way.",
        "sosyal_tr": "Yenilikçi düşüncelerinizle etrafınıza ilham verirsiniz.",
        "sosyal_en": "You inspire those around you with your innovative thinking.",
        "kisilik_tr": "Girişimci bir ruha sahipsiniz; risk almaktan çekinmezsiniz.",
        "kisilik_en": "You have an entrepreneurial spirit and are not afraid to take risks.",
    },
    {
        "_id": "sezgisel",
        "kariyer_tr": "Sezgileriniz iş hayatında doğru kişileri ve fırsatları tanımanızı sağlar.",
        "kariyer_en": "Your intuition helps you recognize the right people and opportunities in professional life.",
        "liderlik_tr": "Ekibinizdeki dinamikleri sezgisel olarak kavrar, doğru müdahaleler yaparsınız.",
        "liderlik_en": "You intuitively grasp team dynamics and make the right interventions.",
        "sosyal_tr": "İnsanların gerçek niyetlerini hızla okur, güvenilir bağlar kurarsınız.",
        "sosyal_en": "You quickly read people's true intentions and build trustworthy bonds.",
        "kisilik_tr": "Güçlü sezgilerinize sahipsiniz; bu içgüdüler sizi doğru yönlere taşır.",
        "kisilik_en": "You have powerful intuitions that consistently guide you in the right direction.",
    },
    {
        "_id": "zeki",
        "kariyer_tr": "Keskin zekânız karmaşık sorunları çözmenizi ve hızlı öğrenmenizi sağlar.",
        "kariyer_en": "Your sharp intellect allows you to solve complex problems and learn quickly.",
        "liderlik_tr": "Zekanız, ekibinize stratejik yol haritaları çizmenize yardımcı olur.",
        "liderlik_en": "Your intelligence helps you draw strategic roadmaps for your team.",
        "sosyal_tr": "Zekice yorumlarınız sizi sohbet ortamlarında değerli kılar.",
        "sosyal_en": "Your intelligent observations make you valuable in conversation.",
        "kisilik_tr": "Keskin bir zekânız ve güçlü muhakeme yeteneğiniz var.",
        "kisilik_en": "You have a sharp intellect and strong reasoning ability.",
    },
    {
        "_id": "sabırlı",
        "kariyer_tr": "Uzun soluklu projelerde çalışma disiplinine sahipsiniz; mükemmel sonuçlar için sabırla beklersiniz.",
        "kariyer_en": "You have the discipline for long-term projects and patiently wait for excellent results.",
        "liderlik_tr": "Ekibinize yeterli süreyi tanır, sonuçları aceleye getirmezsiniz.",
        "liderlik_en": "You give your team adequate time and don't rush results.",
        "sosyal_tr": "Sabırlı dinleyici özelliğiniz insanların size açılmasını sağlar.",
        "sosyal_en": "Your patient listening nature causes people to open up to you.",
        "kisilik_tr": "Sabırlı ve ısrarcı bir karakter yapısına sahipsiniz.",
        "kisilik_en": "You have a patient and persistent character.",
    },
    {
        "_id": "dengeli",
        "kariyer_tr": "İş ve özel yaşam dengesini korur, uzun vadede verimli ve sağlıklı bir kariyer sürdürürsünüz.",
        "kariyer_en": "You maintain work-life balance and sustain a productive, healthy career long-term.",
        "liderlik_tr": "Farklı görüşleri dengeleyen, uzlaşma sağlayan bir lider profili çizersiniz.",
        "liderlik_en": "You balance different views and build consensus as a leader.",
        "sosyal_tr": "Dengeli tutumunuz çatışma ortamlarını yatıştırır; arabulucu rolü üstlenirsiniz.",
        "sosyal_en": "Your balanced nature calms conflicts; you naturally take on the mediator role.",
        "kisilik_tr": "Hayatın her alanında mükemmel bir denge kurarsınız.",
        "kisilik_en": "You maintain perfect balance in every area of life.",
    },
    {
        "_id": "karizmatik",
        "kariyer_tr": "Güçlü karizmanız sizi toplantılarda, sunumlarda ve müzakerelerde öne çıkarır.",
        "kariyer_en": "Your strong charisma makes you stand out in meetings, presentations, and negotiations.",
        "liderlik_tr": "İnsanlar doğal olarak sizi takip etmek ister; karizmatik liderlik size özgü.",
        "liderlik_en": "People naturally want to follow you; charismatic leadership is your signature.",
        "sosyal_tr": "Girdiğiniz her ortamı aydınlatır; insanlar sizi hatırlar.",
        "sosyal_en": "You light up every room you enter; people remember you.",
        "kisilik_tr": "Doğal ve güçlü bir karizmanız var.",
        "kisilik_en": "You have a natural and powerful charisma.",
    },
    # English-primary traits
    {
        "_id": "leader",
        "kariyer_tr": "Doğal liderlik özellikleriniz kariyer yolculuğunuzda sizi yönetici pozisyonlarına taşır.",
        "kariyer_en": "Your natural leadership carries you to management positions throughout your career.",
        "liderlik_tr": "İnsanları bir araya getirir ve ortak hedeflere ilham vererek yönetirsiniz.",
        "liderlik_en": "You bring people together and lead them toward shared goals with inspiration.",
        "sosyal_tr": "Gruplarda doğal olarak öne çıkar, insanların güvenini kazanırsınız.",
        "sosyal_en": "You naturally stand out in groups and earn people's trust.",
        "kisilik_tr": "Güçlü bir liderlik karakterine sahipsiniz.",
        "kisilik_en": "You have a powerful leadership character.",
    },
    {
        "_id": "creative",
        "kariyer_tr": "Yaratıcı zekânız size sanat, tasarım ve yenilikçilik alanlarında büyük avantaj sağlar.",
        "kariyer_en": "Your creative intellect gives you a great advantage in art, design, and innovation.",
        "liderlik_tr": "Yenilikçi fikirleri hayata geçirme konusunda ekibinizi motive edersiniz.",
        "liderlik_en": "You motivate your team to bring innovative ideas to life.",
        "sosyal_tr": "Özgün bakış açınız sizi her sohbette ilgi çekici kılar.",
        "sosyal_en": "Your original perspective makes you compelling in every conversation.",
        "kisilik_tr": "Zengin hayal gücü ve yaratıcı bir ruhunuz var.",
        "kisilik_en": "You have a rich imagination and a creative spirit.",
    },
    {
        "_id": "analytical",
        "kariyer_tr": "Verileri derinlemesine analiz eder, çözüm odaklı yaklaşımınızla iş hayatında fark yaratırsınız.",
        "kariyer_en": "You analyze data in depth and make a difference professionally with your solution-focused approach.",
        "liderlik_tr": "Analitik düşünceniz stratejik kararlar almanıza ve ekibinizi doğru hedeflere yönlendirmenize olanak tanır.",
        "liderlik_en": "Your analytical thinking allows you to make strategic decisions and guide your team.",
        "sosyal_tr": "Sorunlara mantıklı çözümler sunar; çevreniz tavsiyelerinize güvenir.",
        "sosyal_en": "You offer logical solutions; people trust your advice.",
        "kisilik_tr": "Sistematik ve analitik bir zekânız var.",
        "kisilik_en": "You have a systematic and analytical intellect.",
    },
]

# ===========================================================================
# POS / NEG / UNBIASED
# ===========================================================================
POS_TR = [
    "duygusal", "hassas", "içgüdüsel", "bağlılık", "özgür", "yaratıcı", "vizyoner",
    "bağımsız", "dengeli", "karizmatik", "çekici", "açık_kalpli", "ifadeli", "koruyucu",
    "uyumlu", "özgüveni_yüksek", "açık_fikirli", "etkileyici", "cazip", "cömert", "sosyal",
    "güçlü", "girişimci", "özgüvenli", "narin", "analitik", "sabırlı", "titiz",
    "pratik", "enerjik", "lider", "kararlı", "sezgisel", "sanatsal", "adil",
    "odaklı", "zeki", "şefkatli", "tutkulu", "güvenilir", "idealist", "ilhamlı",
    "özgür_ruhlu", "zarif", "yoğun", "dikkatli",
]
NEG_TR = ["gizemli", "düşünceli", "seçici", "yoğun"]
UNBIASED_TR = ["özgün"]

POS_EN = [
    "emotional", "perceptive", "devoted", "free_spirited", "creative", "visionary",
    "balanced", "charismatic", "attractive", "open_hearted", "expressive", "protective",
    "harmonious", "self_confident", "open_minded", "impressive", "generous", "social",
    "strong", "entrepreneurial", "confident", "delicate", "analytical", "patient",
    "thorough", "practical", "energetic", "leader", "determined", "intuitive",
    "artistic", "fair", "focused", "intelligent", "compassionate", "passionate",
    "reliable", "idealistic", "inspired", "free_spirited", "independent",
]
NEG_EN = ["mysterious", "intense"]
UNBIASED_EN = ["unique", "selective", "thoughtful"]

CONTRAST_DATA = {
    "_id": "compare",
    "duygusal": ["analitik", "titiz"],
    "analitik": ["duygusal", "tutkulu"],
    "özgür": ["bağlılık"],
    "bağlılık": ["özgür"],
    "vizyoner": ["pratik"],
    "pratik": ["vizyoner", "idealist"],
    "idealist": ["pratik"],
    "girişimci": ["titiz", "sabırlı"],
    "titiz": ["girişimci"],
    "emotional": ["analytical"],
    "analytical": ["emotional", "passionate"],
    "free_spirited": ["devoted"],
    "devoted": ["free_spirited"],
    "visionary": ["practical"],
    "practical": ["visionary", "idealistic"],
    "idealistic": ["practical"],
    "entrepreneurial": ["thorough"],
    "thorough": ["entrepreneurial"],
}


# ===========================================================================
# Seed functions
# ===========================================================================
def seed_language(db_name, eye_dist, eye_size, eye_cmp, eyebrow, lip_w, lip_t, lip_c, nose_s, nose_l, nose_w, forehead):
    db = client[db_name]
    docs_cols = [
        ("eye",      eye_dist),
        ("eye",      eye_size),
        ("eye",      eye_cmp),
        ("eyebrow",  eyebrow),
        ("lip",      lip_w),
        ("lip",      lip_t),
        ("lip",      lip_c),
        ("nose",     nose_s),
        ("nose",     nose_l),
        ("nose",     nose_w),
        ("forehead", forehead),
    ]
    ops_by_col = {}
    for col_name, doc in docs_cols:
        ops_by_col.setdefault(col_name, []).append(
            UpdateOne({'_id': doc['_id']}, {'$set': doc}, upsert=True)
        )
    for col_name, ops in ops_by_col.items():
        r = db[col_name].bulk_write(ops)
        print(f"  {db_name}.{col_name}: upserted={r.upserted_count}, modified={r.modified_count}")


def seed_categories():
    db = client['database_categories']
    ops = [UpdateOne({'_id': d['_id']}, {'$set': d}, upsert=True) for d in CATEGORY_SENTENCES]
    r = db['traits'].bulk_write(ops)
    print(f"  database_categories.traits: upserted={r.upserted_count}, modified={r.modified_count}")


def seed_pos_neg():
    col = client['pos_neg']['attribute']
    combined_doc = {
        '_id': 'values',
        'positive': list(set(POS_TR + POS_EN)),
        'negative': list(set(NEG_TR + NEG_EN)),
        'unbiased': list(set(UNBIASED_TR + UNBIASED_EN)),
    }
    col.replace_one({'_id': 'values'}, combined_doc, upsert=True)
    print(f"  pos_neg.attribute: seeded")


def seed_contrast():
    client['contrast']['attribute'].replace_one({'_id': 'compare'}, CONTRAST_DATA, upsert=True)
    print(f"  contrast.attribute: seeded")


def main():
    print("Seeding database_attribute_tr ...")
    seed_language('database_attribute_tr',
        TR_EYE_DISTANCE, TR_EYE_SIZE, TR_EYE_COMPARE, TR_EYEBROW_DISTANCE,
        TR_LIP_WIDTH, TR_LIP_THICKNESS, TR_LIP_COMPARE,
        TR_NOSE_SIZE, TR_NOSE_LENGTH, TR_NOSE_WIDTH, TR_FOREHEAD)

    print("Seeding database_attribute_en ...")
    seed_language('database_attribute_en',
        EN_EYE_DISTANCE, EN_EYE_SIZE, EN_EYE_COMPARE, EN_EYEBROW_DISTANCE,
        EN_LIP_WIDTH, EN_LIP_THICKNESS, EN_LIP_COMPARE,
        EN_NOSE_SIZE, EN_NOSE_LENGTH, EN_NOSE_WIDTH, EN_FOREHEAD)

    for lang_db in ['database_attribute_de', 'database_attribute_ru', 'database_attribute_ar',
                    'database_attribute_sp', 'database_attribute_kr', 'database_attribute_jp']:
        print(f"Seeding {lang_db} (EN base) ...")
        seed_language(lang_db,
            EN_EYE_DISTANCE, EN_EYE_SIZE, EN_EYE_COMPARE, EN_EYEBROW_DISTANCE,
            EN_LIP_WIDTH, EN_LIP_THICKNESS, EN_LIP_COMPARE,
            EN_NOSE_SIZE, EN_NOSE_LENGTH, EN_NOSE_WIDTH, EN_FOREHEAD)

    print("Seeding database_categories ...")
    seed_categories()

    print("Seeding pos_neg ...")
    seed_pos_neg()

    print("Seeding contrast ...")
    seed_contrast()

    # Verify
    print("\nVerification:")
    db = client['database_attribute_tr']
    doc = db['eye'].find_one({'_id': 'eyes_distance'})
    print("  TR eyes_distance keys:", list(k for k in doc.keys() if k != '_id') if doc else "NOT FOUND")

    cat_count = client['database_categories']['traits'].count_documents({})
    print(f"  database_categories.traits: {cat_count} docs")

    pn = client['pos_neg']['attribute'].find_one({'_id': 'values'})
    print(f"  pos_neg positive count: {len(pn.get('positive', [])) if pn else 0}")

    print("Done!")


if __name__ == '__main__':
    main()
