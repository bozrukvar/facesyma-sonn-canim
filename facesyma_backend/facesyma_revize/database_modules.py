"""
database_modules.py
===================
Runs all analysis modules in a single call and returns a combined result.
Used by mode='modules' in AnalyzeBaseView.
"""
import logging

_log = logging.getLogger(__name__)


def get_all_modules(img: str, lang: str = 'tr') -> dict:
    """
    Run character, golden ratio, face type, and art match in one pass.
    Returns a dict with keys: character, golden, face_type, art_match.
    Each sub-result is the same shape as the individual endpoint returns.
    """
    _logerr = _log.error
    results = {}
    errors  = {}

    # --- Character analysis ---
    try:
        from database import databases
        results['character'] = databases(img, lang)
    except Exception:
        _logerr('database_modules character analysis failed', exc_info=True)
        errors['character'] = 'Analysis failed.'
        results['character'] = None

    # --- Golden ratio ---
    try:
        from golden_ratio import analyze_golden_ratio
        r = analyze_golden_ratio(img, lang=lang, save_output=False)
        _rget = r.get
        results['golden'] = {
            'score':    r['score'],
            'grade':    r['grade'],
            'phi':      _rget('phi', 1.618),
            'features': _rget('features', {}),
        }
    except Exception:
        _logerr('database_modules golden ratio failed', exc_info=True)
        errors['golden'] = 'Analysis failed.'
        results['golden'] = None

    # --- Face type ---
    try:
        from face_type import analyze_face_type
        results['face_type'] = analyze_face_type(img, lang=lang)
    except Exception:
        _logerr('database_modules face_type failed', exc_info=True)
        errors['face_type'] = 'Analysis failed.'
        results['face_type'] = None

    # --- Art match ---
    try:
        from art_match import match_artwork
        results['art_match'] = match_artwork(img, lang=lang)
    except Exception:
        _logerr('database_modules art_match failed', exc_info=True)
        errors['art_match'] = 'Analysis failed.'
        results['art_match'] = None

    response = {'modules': results}
    if errors:
        response['partial_errors'] = errors

    return response
