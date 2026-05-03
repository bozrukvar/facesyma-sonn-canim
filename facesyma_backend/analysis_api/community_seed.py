"""
analysis_api/community_seed.py
===============================
47 seed topluluğu oluşturur (idempotent — tekrar çalıştırılabilir).

Çalıştırma:
    python manage.py runscript community_seed
"""
import time
import logging

log = logging.getLogger(__name__)

_SEEDS = [
    # ASTRO (12)
    ('ASTRO', 'aries',       '♈ Koç Topluluğu',       'Koç burcu mensuplarının toplandığı topluluk.'),
    ('ASTRO', 'taurus',      '♉ Boğa Topluluğu',      'Boğa burcu mensuplarının toplandığı topluluk.'),
    ('ASTRO', 'gemini',      '♊ İkizler Topluluğu',   'İkizler burcu mensuplarının toplandığı topluluk.'),
    ('ASTRO', 'cancer',      '♋ Yengeç Topluluğu',    'Yengeç burcu mensuplarının toplandığı topluluk.'),
    ('ASTRO', 'leo',         '♌ Aslan Topluluğu',     'Aslan burcu mensuplarının toplandığı topluluk.'),
    ('ASTRO', 'virgo',       '♍ Başak Topluluğu',     'Başak burcu mensuplarının toplandığı topluluk.'),
    ('ASTRO', 'libra',       '♎ Terazi Topluluğu',    'Terazi burcu mensuplarının toplandığı topluluk.'),
    ('ASTRO', 'scorpio',     '♏ Akrep Topluluğu',     'Akrep burcu mensuplarının toplandığı topluluk.'),
    ('ASTRO', 'sagittarius', '♐ Yay Topluluğu',       'Yay burcu mensuplarının toplandığı topluluk.'),
    ('ASTRO', 'capricorn',   '♑ Oğlak Topluluğu',     'Oğlak burcu mensuplarının toplandığı topluluk.'),
    ('ASTRO', 'aquarius',    '♒ Kova Topluluğu',      'Kova burcu mensuplarının toplandığı topluluk.'),
    ('ASTRO', 'pisces',      '♓ Balık Topluluğu',     'Balık burcu mensuplarının toplandığı topluluk.'),
    # INTEREST (12)
    ('INTEREST', 'music',       '🎵 Müzik Topluluğu',      'Müzik severlerin bir araya geldiği topluluk.'),
    ('INTEREST', 'film',        '🎬 Film Topluluğu',       'Film tutkunlarının toplandığı topluluk.'),
    ('INTEREST', 'sport',       '🏃 Spor Topluluğu',       'Sporseverler için aktif bir topluluk.'),
    ('INTEREST', 'travel',      '✈️ Seyahat Topluluğu',    'Gezginlerin deneyimlerini paylaştığı topluluk.'),
    ('INTEREST', 'food',        '🍽️ Yemek Topluluğu',     'Gastronomi meraklılarının toplandığı topluluk.'),
    ('INTEREST', 'art',         '🎨 Sanat Topluluğu',      'Sanat severler için ilham verici bir topluluk.'),
    ('INTEREST', 'tech',        '💻 Teknoloji Topluluğu',  'Teknoloji tutkunlarının buluşma noktası.'),
    ('INTEREST', 'nature',      '🌿 Doğa Topluluğu',       'Doğa ve çevre severlerin topluluğu.'),
    ('INTEREST', 'fashion',     '👗 Moda Topluluğu',       'Moda ve stil meraklıları için topluluk.'),
    ('INTEREST', 'gaming',      '🎮 Oyun Topluluğu',       'Oyun severlerin buluştuğu topluluk.'),
    ('INTEREST', 'literature',  '📚 Edebiyat Topluluğu',   'Kitap severlerin bir araya geldiği topluluk.'),
    ('INTEREST', 'health',      '🏥 Sağlık Topluluğu',     'Sağlık ve wellness meraklılarının topluluğu.'),
    # LIFESTYLE (8)
    ('LIFESTYLE', 'vegan',          '🥗 Vegan Topluluğu',          'Vegan yaşam tarzını benimseyen kişilerin topluluğu.'),
    ('LIFESTYLE', 'athlete',        '🏋️ Sporcu Topluluğu',        'Atletlerin ve sporcuların bir araya geldiği topluluk.'),
    ('LIFESTYLE', 'meditation',     '🧘 Meditasyon Topluluğu',     'Meditasyon ve mindfulness pratisyenleri için topluluk.'),
    ('LIFESTYLE', 'freelancer',     '💼 Freelancer Topluluğu',     'Bağımsız çalışanların deneyim paylaştığı topluluk.'),
    ('LIFESTYLE', 'parent',         '👨‍👩‍👧 Ebeveyn Topluluğu',  'Ebeveynlerin destek ve paylaşım yaptığı topluluk.'),
    ('LIFESTYLE', 'student',        '🎓 Öğrenci Topluluğu',        'Öğrencilerin bir araya geldiği topluluk.'),
    ('LIFESTYLE', 'digital_nomad',  '🌍 Dijital Göçebe Topluluğu', 'Uzaktan çalışan gezginlerin topluluğu.'),
    ('LIFESTYLE', 'minimalist',     '🪴 Minimalist Topluluğu',     'Sade yaşamı benimseyenlerin topluluğu.'),
    # FACE (6)
    ('FACE', 'oval',     '😊 Oval Yüz Topluluğu',   'Oval yüz şekline sahip kişilerin topluluğu.'),
    ('FACE', 'round',    '🔵 Yuvarlak Yüz Topluluğu', 'Yuvarlak yüz şekline sahip kişilerin topluluğu.'),
    ('FACE', 'square',   '🟥 Kare Yüz Topluluğu',   'Kare yüz şekline sahip kişilerin topluluğu.'),
    ('FACE', 'heart',    '💜 Kalp Yüz Topluluğu',   'Kalp yüz şekline sahip kişilerin topluluğu.'),
    ('FACE', 'oblong',   '📏 Uzun Yüz Topluluğu',   'Uzun yüz şekline sahip kişilerin topluluğu.'),
    ('FACE', 'diamond',  '💎 Elmas Yüz Topluluğu',  'Elmas yüz şekline sahip kişilerin topluluğu.'),
    # COLORTYPE (4)
    ('COLORTYPE', 'spring', '🌸 İlkbahar Renk Tipi', 'İlkbahar renk tipindeki kişilerin topluluğu.'),
    ('COLORTYPE', 'summer', '☀️ Yaz Renk Tipi',      'Yaz renk tipindeki kişilerin topluluğu.'),
    ('COLORTYPE', 'autumn', '🍂 Sonbahar Renk Tipi', 'Sonbahar renk tipindeki kişilerin topluluğu.'),
    ('COLORTYPE', 'winter', '❄️ Kış Renk Tipi',      'Kış renk tipindeki kişilerin topluluğu.'),
    # GOAL (5)
    ('GOAL', 'career',           '💼 Kariyer Topluluğu',          'Kariyer gelişimi için hedefler koyanların topluluğu.'),
    ('GOAL', 'relationship',     '💖 İlişki Topluluğu',           'İlişki ve bağlantı kurmayı hedefleyenlerin topluluğu.'),
    ('GOAL', 'personal_growth',  '🌱 Kişisel Gelişim Topluluğu', 'Kendini geliştirmek isteyenlerin topluluğu.'),
    ('GOAL', 'health',           '🏃 Sağlık Hedefi Topluluğu',   'Sağlık hedefleri olanların topluluğu.'),
    ('GOAL', 'fun',              '🎉 Eğlence Topluluğu',          'Eğlence ve sosyalleşme odaklı topluluk.'),
]


def run():
    from admin_api.utils.mongo import get_communities_col
    col = get_communities_col()
    now_ts = time.time()
    created = 0
    skipped = 0

    for type_label, trait_name, name, description in _SEEDS:
        existing = col.find_one({'type': type_label, 'trait_name': trait_name}, {'_id': 1})
        if existing:
            skipped += 1
            continue
        col.insert_one({
            'name': name,
            'type': type_label,
            'trait_name': trait_name,
            'description': description,
            'founder_id': 0,
            'member_count': 0,
            'is_active': True,
            'created_at': now_ts,
            'updated_at': now_ts,
            'rules': '',
            'moderation_policy': 'automated',
        })
        created += 1
        log.info(f'Seed: created {type_label} "{trait_name}"')

    log.info(f'Community seed complete: {created} created, {skipped} already existed.')
    print(f'Community seed: {created} created, {skipped} already existed (total {len(_SEEDS)}).')
