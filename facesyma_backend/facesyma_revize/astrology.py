"""
astrology.py
============
Astrology reading from facial features + optional birth date/time.
Combines Western zodiac (from birth_date), Chinese zodiac (birth year),
and face-based element reading.
"""
import random
from datetime import datetime
from functools import lru_cache
from calculator import Cal

_WESTERN_SIGNS = [
    ('Capricorn',   (12, 22), (1, 19)),
    ('Aquarius',    (1, 20),  (2, 18)),
    ('Pisces',      (2, 19),  (3, 20)),
    ('Aries',       (3, 21),  (4, 19)),
    ('Taurus',      (4, 20),  (5, 20)),
    ('Gemini',      (5, 21),  (6, 20)),
    ('Cancer',      (6, 21),  (7, 22)),
    ('Leo',         (7, 23),  (8, 22)),
    ('Virgo',       (8, 23),  (9, 22)),
    ('Libra',       (9, 23),  (10, 22)),
    ('Scorpio',     (10, 23), (11, 21)),
    ('Sagittarius', (11, 22), (12, 21)),
]

_SIGN_TRANSLATIONS = {
    'Aries':       {'tr': 'Koç',       'en': 'Aries'},
    'Taurus':      {'tr': 'Boğa',      'en': 'Taurus'},
    'Gemini':      {'tr': 'İkizler',   'en': 'Gemini'},
    'Cancer':      {'tr': 'Yengeç',    'en': 'Cancer'},
    'Leo':         {'tr': 'Aslan',     'en': 'Leo'},
    'Virgo':       {'tr': 'Başak',     'en': 'Virgo'},
    'Libra':       {'tr': 'Terazi',    'en': 'Libra'},
    'Scorpio':     {'tr': 'Akrep',     'en': 'Scorpio'},
    'Sagittarius': {'tr': 'Yay',       'en': 'Sagittarius'},
    'Capricorn':   {'tr': 'Oğlak',     'en': 'Capricorn'},
    'Aquarius':    {'tr': 'Kova',      'en': 'Aquarius'},
    'Pisces':      {'tr': 'Balık',     'en': 'Pisces'},
}

_SIGN_EMOJIS = {
    'Aries': '♈', 'Taurus': '♉', 'Gemini': '♊', 'Cancer': '♋',
    'Leo': '♌', 'Virgo': '♍', 'Libra': '♎', 'Scorpio': '♏',
    'Sagittarius': '♐', 'Capricorn': '♑', 'Aquarius': '♒', 'Pisces': '♓',
}

_CHINESE_ANIMALS = ['Rat', 'Ox', 'Tiger', 'Rabbit', 'Dragon', 'Snake',
                    'Horse', 'Goat', 'Monkey', 'Rooster', 'Dog', 'Pig']
_CHINESE_TRANSLATIONS = {
    'Rat':     {'tr': 'Fare',    'en': 'Rat'},
    'Ox':      {'tr': 'Öküz',   'en': 'Ox'},
    'Tiger':   {'tr': 'Kaplan', 'en': 'Tiger'},
    'Rabbit':  {'tr': 'Tavşan', 'en': 'Rabbit'},
    'Dragon':  {'tr': 'Ejderha','en': 'Dragon'},
    'Snake':   {'tr': 'Yılan',  'en': 'Snake'},
    'Horse':   {'tr': 'At',     'en': 'Horse'},
    'Goat':    {'tr': 'Keçi',   'en': 'Goat'},
    'Monkey':  {'tr': 'Maymun', 'en': 'Monkey'},
    'Rooster': {'tr': 'Horoz',  'en': 'Rooster'},
    'Dog':     {'tr': 'Köpek',  'en': 'Dog'},
    'Pig':     {'tr': 'Domuz',  'en': 'Pig'},
}

_ELEMENTS = ['Fire', 'Earth', 'Air', 'Water']
_ELEMENT_TRANSLATIONS = {
    'Fire':  {'tr': 'Ateş',  'en': 'Fire'},
    'Earth': {'tr': 'Toprak','en': 'Earth'},
    'Air':   {'tr': 'Hava',  'en': 'Air'},
    'Water': {'tr': 'Su',    'en': 'Water'},
}
_SIGN_ELEMENTS = {
    'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
    'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
    'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
    'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water',
}

_FACE_ELEMENT_MAP = {
    'Fire':  {'tr': 'Yüzünüzde güçlü enerji ve liderlik izleri var.',
              'en': 'Your face carries strong energy and leadership marks.'},
    'Earth': {'tr': 'Yüzünüz güvenilirlik ve kararlılık yansıtıyor.',
              'en': 'Your face reflects reliability and determination.'},
    'Air':   {'tr': 'Yüzünüzde zeka ve iletişim gücü görünüyor.',
              'en': 'Your face shows intelligence and communication power.'},
    'Water': {'tr': 'Yüzünüzde derin duygusallık ve sezgi var.',
              'en': 'Your face holds deep emotionality and intuition.'},
}

_DAILY_READING = {
    'tr': [
        'Bugün enerjiniz yüksek, yeni başlangıçlar için uygun bir gün.',
        'Duygusal zekânızı kullanarak ilişkilerinizi güçlendirin.',
        'Yaratıcı projeler için uygun bir dönemdesiniz.',
        'İçsel güçünüze güvenin, doğru yoldasınız.',
        'Bugün şans sizin tarafınızda, fırsatları kaçırmayın.',
    ],
    'en': [
        'Your energy is high today — a good day for new beginnings.',
        'Strengthen your relationships using your emotional intelligence.',
        'You are in a creative phase — ideal for new projects.',
        'Trust your inner strength, you are on the right path.',
        'Luck is on your side today — do not miss the opportunities.',
    ],
}


@lru_cache(maxsize=512)
def _get_western_sign(birth_date: str) -> str:
    try:
        dt = datetime.strptime(birth_date[:10], '%Y-%m-%d')
        m, d = dt.month, dt.day
        for sign, (sm, sd), (em, ed) in _WESTERN_SIGNS:
            if (m == sm and d >= sd) or (m == em and d <= ed):
                return sign
        return 'Capricorn'
    except Exception:
        return None


@lru_cache(maxsize=512)
def _get_chinese_animal(birth_date: str) -> str:
    try:
        year = int(birth_date[:4])
        return _CHINESE_ANIMALS[(year - 4) % 12]
    except Exception:
        return None


def _face_element(result: dict) -> str:
    """Determine dominant element from face features."""
    try:
        _rget = result.get
        eye_dict  = _rget('Eye', {})
        jaw_dict  = _rget('Jaw', {})
        nose_dict = _rget('Nose', {})

        eye_dist   = eye_dict.get('eyes_distance', 1.0)
        jaw_width  = jaw_dict.get('jaw_width_ratio', 1.0)
        face_ratio = nose_dict.get('face_length_ratio', 1.45)

        if jaw_width > 1.05:
            return 'Fire'
        elif face_ratio > 1.65:
            return 'Air'
        elif eye_dist < 0.92:
            return 'Water'
        else:
            return 'Earth'
    except Exception:
        return random.choice(_ELEMENTS)


def analyze_astrology(img: str, lang: str = 'tr',
                      birth_date: str = '', birth_time: str = '') -> dict:
    """
    Combine face-based element reading with birth-date astrology.
    """
    result = Cal(img)
    lang_key = lang.split('-')[0] if '-' in lang else lang

    # Face-based element
    element = _face_element(result)

    # Western zodiac
    western_sign = _get_western_sign(birth_date) if birth_date else None
    if western_sign:
        element = _SIGN_ELEMENTS.get(western_sign, element)

    # Chinese zodiac
    chinese_animal = _get_chinese_animal(birth_date) if birth_date else None

    # Daily reading
    daily_msgs = _DAILY_READING.get(lang_key, _DAILY_READING['en'])
    daily_msg  = random.choice(daily_msgs)

    sign_label = None
    sign_emoji = None
    if western_sign:
        sign_label = _SIGN_TRANSLATIONS.get(western_sign, {}).get(lang_key, western_sign)
        sign_emoji = _SIGN_EMOJIS.get(western_sign, '⭐')

    chinese_label = None
    if chinese_animal:
        chinese_label = _CHINESE_TRANSLATIONS.get(chinese_animal, {}).get(lang_key, chinese_animal)

    element_label = _ELEMENT_TRANSLATIONS.get(element, {}).get(lang_key, element)
    face_reading  = _FACE_ELEMENT_MAP.get(element, {}).get(lang_key, '')

    response = {
        'element':        element,
        'element_label':  element_label,
        'face_reading':   face_reading,
        'daily_message':  daily_msg,
    }
    _rupdate = response.update

    if western_sign:
        _rupdate({
            'western_sign':        western_sign,
            'western_sign_label':  sign_label,
            'western_sign_emoji':  sign_emoji,
        })

    if chinese_animal:
        _rupdate({
            'chinese_animal':       chinese_animal,
            'chinese_animal_label': chinese_label,
        })

    return response
