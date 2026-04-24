"""
art_match.py
============
Match a face to iconic artworks based on facial proportions and features.
Returns closest artwork matches with similarity scores.
"""

import random
from operator import itemgetter
from calculator import Cal

_KEY_SCORE = itemgetter(0)

_ARTWORKS = [
    {
        'id': 'mona_lisa',
        'title': {'tr': 'Mona Lisa', 'en': 'Mona Lisa'},
        'artist': 'Leonardo da Vinci',
        'year': '1503–1519',
        'style': {'tr': 'Rönesans Portresi', 'en': 'Renaissance Portrait'},
        'museum': 'Louvre, Paris',
        'image_url': '',
        'traits': {'jaw_width': (0.85, 1.0), 'face_len_ratio': (1.3, 1.6), 'eye_distance': (0.9, 1.1)},
    },
    {
        'id': 'girl_with_pearl_earring',
        'title': {'tr': 'İnci Küpeli Kız', 'en': 'Girl with a Pearl Earring'},
        'artist': 'Johannes Vermeer',
        'year': '1665',
        'style': {'tr': 'Barok Portresi', 'en': 'Baroque Portrait'},
        'museum': 'Mauritshuis, The Hague',
        'image_url': '',
        'traits': {'jaw_width': (0.8, 0.95), 'face_len_ratio': (1.4, 1.7), 'eye_distance': (0.85, 1.05)},
    },
    {
        'id': 'birth_of_venus',
        'title': {'tr': 'Venüsün Doğuşu', 'en': 'The Birth of Venus'},
        'artist': 'Sandro Botticelli',
        'year': '1484–1486',
        'style': {'tr': 'Rönesans İdeali', 'en': 'Renaissance Ideal'},
        'museum': 'Uffizi, Florence',
        'image_url': '',
        'traits': {'jaw_width': (0.75, 0.9), 'face_len_ratio': (1.5, 1.8), 'eye_distance': (0.9, 1.1)},
    },
    {
        'id': 'self_portrait_rembrandt',
        'title': {'tr': 'Otoportre', 'en': 'Self-Portrait'},
        'artist': 'Rembrandt van Rijn',
        'year': '1659',
        'style': {'tr': 'Barok Realizm', 'en': 'Baroque Realism'},
        'museum': 'National Gallery of Art, Washington',
        'image_url': '',
        'traits': {'jaw_width': (1.0, 1.15), 'face_len_ratio': (1.2, 1.5), 'eye_distance': (0.9, 1.1)},
    },
    {
        'id': 'the_scream',
        'title': {'tr': 'Çığlık', 'en': 'The Scream'},
        'artist': 'Edvard Munch',
        'year': '1893',
        'style': {'tr': 'Ekspresyonizm', 'en': 'Expressionism'},
        'museum': 'National Museum, Oslo',
        'image_url': '',
        'traits': {'jaw_width': (0.7, 0.85), 'face_len_ratio': (1.7, 2.1), 'eye_distance': (0.75, 0.95)},
    },
    {
        'id': 'venus_de_milo',
        'title': {'tr': 'Milo Venüsü', 'en': 'Venus de Milo'},
        'artist': 'Alexandros of Antioch',
        'year': 'c. 100 BC',
        'style': {'tr': 'Helenistik Heykel', 'en': 'Hellenistic Sculpture'},
        'museum': 'Louvre, Paris',
        'image_url': '',
        'traits': {'jaw_width': (0.82, 0.98), 'face_len_ratio': (1.35, 1.65), 'eye_distance': (0.9, 1.1)},
    },
]


def _score_match(traits: dict, jaw_width: float, face_len_ratio: float, eye_dist: float) -> float:
    """Returns a 0–100 similarity score for one artwork."""
    score = 0.0
    total = 0.0

    def _range_score(val, lo, hi):
        mid = (lo + hi) / 2.0
        span = (hi - lo) / 2.0 or 0.1
        diff = abs(val - mid) / span
        return max(0.0, 1.0 - diff)

    for key, val, weight in [
        ('jaw_width',      jaw_width,      0.35),
        ('face_len_ratio', face_len_ratio, 0.40),
        ('eye_distance',   eye_dist,       0.25),
    ]:
        if key in traits:
            lo, hi = traits[key]
            score += _range_score(val, lo, hi) * weight
            total += weight

    return round((score / total) * 100, 1) if total > 0 else 50.0


def match_artwork(img: str, lang: str = 'tr') -> dict:
    """
    Match face to iconic artworks.
    Returns top-3 matches with similarity scores and artwork details.
    """
    result = Cal(img)
    lang_key = lang.split('-')[0] if '-' in lang else lang

    try:
        _rget = result.get
        jaw_width      = _rget('Jaw',  {}).get('jaw_width_ratio',   1.0)
        face_len_ratio = _rget('Nose', {}).get('face_length_ratio', 1.45)
        eye_dist       = _rget('Eye',  {}).get('eyes_distance',     1.0)
    except Exception:
        jaw_width, face_len_ratio, eye_dist = 1.0, 1.45, 1.0

    scored = []
    for art in _ARTWORKS:
        s = _score_match(art['traits'], jaw_width, face_len_ratio, eye_dist)
        # Add small random variation so results are less deterministic
        s = min(99.9, max(40.0, s + random.uniform(-5, 5)))
        scored.append((s, art))

    scored.sort(key=_KEY_SCORE, reverse=True)
    top3 = scored[:3]

    matches = []
    for rank, (score, art) in enumerate(top3, 1):
        _at = art['title']
        _as = art['style']
        _atget = _at.get
        _asget = _as.get
        _aid = art['id']
        matches.append({
            'rank':        rank,
            'id':          _aid,
            'title':       _atget(lang_key, _atget('en', _aid)),
            'artist':      art['artist'],
            'year':        art['year'],
            'style':       _asget(lang_key, _asget('en', '')),
            'museum':      art['museum'],
            'similarity':  round(score, 1),
            'image_url':   art['image_url'],
        })

    _m0 = matches[0] if matches else None
    top_score = _m0['similarity'] if _m0 else 75.0
    grade = 'A+' if top_score >= 90 else 'A' if top_score >= 80 else 'B+' if top_score >= 70 else 'B'
    _m0_artist = _m0['artist'] if _m0 else ''

    return {
        'matches':      matches,
        'best_match':   _m0,
        'overall_score': round(top_score, 1),
        'grade':         grade,
        'message': {
            'tr': f'Yüzünüz {_m0_artist} eserini en çok çağrıştırıyor.' if _m0_artist else '',
            'en': f'Your face most resembles the work of {_m0_artist}.' if _m0_artist else '',
        }.get(lang_key, ''),
    }
