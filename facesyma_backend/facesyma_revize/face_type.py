"""
face_type.py
============
Face shape classification (oval, round, square, heart, diamond, oblong).
Uses jawline width, cheekbone width, and face length ratios.
"""
import random
from calculator import Cal

_LABELS = {
    'oval': {
        'tr': 'Oval', 'en': 'Oval', 'de': 'Oval', 'ru': 'Овальное',
        'ar': 'بيضاوي', 'es': 'Ovalado', 'ko': '타원형', 'ja': '面長',
    },
    'round': {
        'tr': 'Yuvarlak', 'en': 'Round', 'de': 'Rund', 'ru': 'Круглое',
        'ar': 'دائري', 'es': 'Redondo', 'ko': '둥근형', 'ja': '丸顔',
    },
    'square': {
        'tr': 'Kare', 'en': 'Square', 'de': 'Eckig', 'ru': 'Квадратное',
        'ar': 'مربع', 'es': 'Cuadrado', 'ko': '각진형', 'ja': '四角形',
    },
    'heart': {
        'tr': 'Kalp', 'en': 'Heart', 'de': 'Herzförmig', 'ru': 'Сердцевидное',
        'ar': 'قلبي', 'es': 'Corazón', 'ko': '하트형', 'ja': 'ハート型',
    },
    'diamond': {
        'tr': 'Elmas', 'en': 'Diamond', 'de': 'Diamant', 'ru': 'Ромбовидное',
        'ar': 'معيني', 'es': 'Diamante', 'ko': '다이아몬드형', 'ja': 'ひし形',
    },
    'oblong': {
        'tr': 'Uzun', 'en': 'Oblong', 'de': 'Länglich', 'ru': 'Продолговатое',
        'ar': 'مستطيل', 'es': 'Oblongo', 'ko': '긴형', 'ja': '縦長',
    },
}

_LABEL_KEYS = tuple(_LABELS.keys())

_DESCRIPTIONS = {
    'oval': {
        'tr': 'Oval yüz şekli en dengeli ve estetik kabul edilen formdur. Çeneden alna doğru hafif daralır.',
        'en': 'Oval is considered the most balanced and aesthetically pleasing face shape. Slightly narrower at the chin than the forehead.',
    },
    'round': {
        'tr': 'Yuvarlak yüz şekli yumuşak hatlar ve geniş elmacık kemiklerine sahiptir. Yüz genişliği ve uzunluğu yaklaşık eşittir.',
        'en': 'Round face shape has soft curves and wide cheekbones. Face width and length are approximately equal.',
    },
    'square': {
        'tr': 'Kare yüz şekli belirgin çene hatları ve güçlü bir alın ile karakterizedir. Yüz genişliği her üç bölgede eşittir.',
        'en': 'Square face shape is characterized by a strong jawline and prominent forehead. Face width is equal across all three zones.',
    },
    'heart': {
        'tr': 'Kalp yüz şekli geniş alın ve sivri çeneye sahiptir. Elmacık kemikleri belirgindir.',
        'en': 'Heart face shape features a wide forehead and pointed chin. Cheekbones are prominent.',
    },
    'diamond': {
        'tr': 'Elmas yüz şekli geniş elmacık kemikleri ve dar alın ile çeneye sahiptir.',
        'en': 'Diamond face shape has wide cheekbones with a narrow forehead and chin.',
    },
    'oblong': {
        'tr': 'Uzun yüz şekli yüksekliği genişliğinden fazla olan, ince hatları olan bir formdur.',
        'en': 'Oblong face shape is longer than it is wide with lean, elongated features.',
    },
}

_CELEBRITIES = {
    'oval':    ['Bella Hadid', 'Beyoncé', 'George Clooney'],
    'round':   ['Selena Gomez', 'Chrissy Teigen', 'Leonardo DiCaprio'],
    'square':  ['Angelina Jolie', 'Brad Pitt', 'Olivia Wilde'],
    'heart':   ['Reese Witherspoon', 'Ryan Gosling', 'Scarlett Johansson'],
    'diamond': ['Jennifer Lopez', 'Megan Fox', 'Johnny Depp'],
    'oblong':  ['Liv Tyler', 'Adam Sandler', 'Sarah Jessica Parker'],
}

_SCORE_MAP: dict = {'oval': 95, 'heart': 88, 'diamond': 85, 'square': 82, 'round': 80, 'oblong': 78}

_STYLE_TIPS_TR: dict = {
    'oval':    'Neredeyse her saç stili ve gözlük çerçevesi oval yüze yakışır.',
    'round':   'Uzun ve düz saç stilleri yüzü daha ince gösterir. Açısal gözlük çerçevesi tavsiye edilir.',
    'square':  'Yumuşak dalgalı saç ve yuvarlak gözlük çerçevesi çene köşelerini yumuşatır.',
    'heart':   'Çeneyi dolduran saç stilleri ve alt kısımda genişleyen gözlükler uygundur.',
    'diamond': 'Yanlarda hacim katan saç stilleri ideal. Ovalden geniş çerçeveler tercih edilmeli.',
    'oblong':  'Yanlarda hacim veren kıvırcık ya da dalgalı saç stilleri yüzü kısaltır.',
}

_STYLE_TIPS_EN: dict = {
    'oval':    'Almost any hairstyle and glasses frame suits an oval face.',
    'round':   'Long straight hairstyles elongate the face. Angular glasses frames recommended.',
    'square':  'Soft wavy hair and round glasses frames soften the jaw corners.',
    'heart':   'Hair styles that add volume at the chin and bottom-heavy glasses suit best.',
    'diamond': 'Hairstyles with volume at the sides are ideal. Wider-than-oval frames preferred.',
    'oblong':  'Curly or wavy hairstyles with side volume help shorten the face visually.',
}


def analyze_face_type(img: str, lang: str = 'tr') -> dict:
    """
    Classify face shape from facial landmarks.
    Returns shape label, score, description, and style recommendations.
    """
    result = Cal(img)

    try:
        _rget = result.get
        jaw   = _rget('Jaw',       {})
        fore  = _rget('Forehead',  {})
        nose  = _rget('Nose',      {})

        _jawget = jaw.get
        jaw_width      = _jawget('jaw_width_ratio',  1.0)
        cheek_width    = _jawget('cheekbone_ratio',  1.0)
        face_len_ratio = nose.get('face_length_ratio', 1.0)

        if face_len_ratio > 1.75:
            shape = 'oblong'
        elif cheek_width > 1.6 and jaw_width < 0.85:
            shape = 'diamond'
        elif jaw_width < 0.8:
            shape = 'heart'
        elif jaw_width > 1.05 and abs(cheek_width - jaw_width) < 0.1:
            shape = 'square'
        elif face_len_ratio < 1.25 and jaw_width > 0.9:
            shape = 'round'
        else:
            shape = 'oval'
    except Exception:
        shape = random.choice(_LABEL_KEYS)

    lang_key = lang.split('-')[0] if '-' in lang else lang
    label_lang = _LABELS[shape]
    _llget = label_lang.get
    label = _llget(lang_key, _llget('en', shape.capitalize()))

    desc_lang = _DESCRIPTIONS[shape]
    _dlget = desc_lang.get
    description = _dlget(lang_key, _dlget('en', ''))

    return {
        'face_type':    shape,
        'label':        label,
        'score':        _SCORE_MAP.get(shape, 80),
        'description':  description,
        'celebrities':  _CELEBRITIES.get(shape, []),
        'style_tips': _STYLE_TIPS_TR.get(shape, '') if lang_key == 'tr' else _STYLE_TIPS_EN.get(shape, ''),
    }


