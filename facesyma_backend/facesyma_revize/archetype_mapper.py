"""
Cluster-based archetype scoring + rotation engine.
Replaces Jaccard-based similarity_matcher.py for the archetype system.
"""
from collections import defaultdict
import random
from datetime import datetime

# ---------------------------------------------------------------------------
# 1. SIFAT → KÜME HARİTASI (68 canonical sıfat)
# ---------------------------------------------------------------------------
SIFAT_CLUSTER_MAP: dict[str, dict[str, float]] = {
    # --- leadership ---
    "dominant":    {"leadership": 0.9, "charisma": 0.5},
    "karizmatik":  {"leadership": 0.8, "charisma": 0.9},
    "charismatic": {"leadership": 0.8, "charisma": 0.9},
    "cesur":       {"leadership": 0.8, "strength": 0.6},
    "brave":       {"leadership": 0.8, "strength": 0.6},
    "güçlü":       {"leadership": 0.6, "strength": 0.9},
    "strong":      {"leadership": 0.6, "strength": 0.9},
    "otoriter":    {"leadership": 0.85, "discipline": 0.5},
    "authoritative": {"leadership": 0.85, "discipline": 0.5},
    "kararlı":     {"leadership": 0.7, "patience": 0.6, "discipline": 0.5},
    "determined":  {"leadership": 0.7, "patience": 0.6, "discipline": 0.5},
    "girişimci":   {"leadership": 0.75, "creativity": 0.4},
    "entrepreneur": {"leadership": 0.75, "creativity": 0.4},
    # --- social ---
    "sosyal":      {"social": 0.95, "charisma": 0.4},
    "social":      {"social": 0.95, "charisma": 0.4},
    "sempatik":    {"social": 0.8, "empathy": 0.5},
    "sympathetic": {"social": 0.8, "empathy": 0.5},
    "uyumlu":      {"social": 0.75, "patience": 0.4},
    "harmonious":  {"social": 0.75, "patience": 0.4},
    "bağlayıcı":   {"social": 0.85, "empathy": 0.4},
    "connecting":  {"social": 0.85, "empathy": 0.4},
    "arkadaşcıl":  {"social": 0.9, "empathy": 0.3},
    "friendly":    {"social": 0.9, "empathy": 0.3},
    # --- patience ---
    "sabırlı":     {"patience": 0.95, "discipline": 0.3},
    "patient":     {"patience": 0.95, "discipline": 0.3},
    "azimli":      {"patience": 0.8, "strength": 0.4, "discipline": 0.4},
    "persistent":  {"patience": 0.8, "strength": 0.4, "discipline": 0.4},
    "sakin":       {"patience": 0.85, "mystery": 0.3},
    "calm":        {"patience": 0.85, "mystery": 0.3},
    "metanetli":   {"patience": 0.9, "strength": 0.3},
    "stoic":       {"patience": 0.9, "strength": 0.3},
    # --- intelligence ---
    "analitik":    {"intelligence": 0.95, "discipline": 0.4},
    "analytical":  {"intelligence": 0.95, "discipline": 0.4},
    "zeki":        {"intelligence": 0.9, "creativity": 0.3},
    "intelligent": {"intelligence": 0.9, "creativity": 0.3},
    "gözlemci":    {"intelligence": 0.8, "mystery": 0.4},
    "observant":   {"intelligence": 0.8, "mystery": 0.4},
    "derin":       {"intelligence": 0.75, "mystery": 0.6},
    "deep":        {"intelligence": 0.75, "mystery": 0.6},
    "meraklı":     {"intelligence": 0.7, "creativity": 0.5},
    "curious":     {"intelligence": 0.7, "creativity": 0.5},
    "hesapçı":     {"intelligence": 0.8, "discipline": 0.6},
    "calculated":  {"intelligence": 0.8, "discipline": 0.6},
    # --- creativity ---
    "yaratıcı":    {"creativity": 0.95, "mystery": 0.3},
    "creative":    {"creativity": 0.95, "mystery": 0.3},
    "özgün":       {"creativity": 0.9, "mystery": 0.4},
    "original":    {"creativity": 0.9, "mystery": 0.4},
    "sanatsal":    {"creativity": 0.85, "empathy": 0.3},
    "artistic":    {"creativity": 0.85, "empathy": 0.3},
    "vizyoner":    {"creativity": 0.8, "leadership": 0.4, "intelligence": 0.3},
    "visionary":   {"creativity": 0.8, "leadership": 0.4, "intelligence": 0.3},
    "hayal gücü":  {"creativity": 0.9, "mystery": 0.4},
    "imaginative": {"creativity": 0.9, "mystery": 0.4},
    # --- strength ---
    "enerjik":     {"strength": 0.85, "leadership": 0.3},
    "energetic":   {"strength": 0.85, "leadership": 0.3},
    "mücadeleci":  {"strength": 0.8, "leadership": 0.5},
    "combative":   {"strength": 0.8, "leadership": 0.5},
    "dirençli":    {"strength": 0.9, "patience": 0.4},
    "resilient":   {"strength": 0.9, "patience": 0.4},
    "dayanıklı":   {"strength": 0.85, "patience": 0.5},
    "enduring":    {"strength": 0.85, "patience": 0.5},
    # --- empathy ---
    "empatik":     {"empathy": 0.95, "social": 0.4},
    "empathetic":  {"empathy": 0.95, "social": 0.4},
    "şefkatli":    {"empathy": 0.9, "social": 0.3},
    "compassionate": {"empathy": 0.9, "social": 0.3},
    "anlayışlı":   {"empathy": 0.85, "social": 0.4},
    "understanding": {"empathy": 0.85, "social": 0.4},
    "fedakâr":     {"empathy": 0.8, "social": 0.5},
    "selfless":    {"empathy": 0.8, "social": 0.5},
    # --- mystery ---
    "gizemli":     {"mystery": 0.95, "intelligence": 0.3},
    "mysterious":  {"mystery": 0.95, "intelligence": 0.3},
    "içedönük":    {"mystery": 0.8, "intelligence": 0.3},
    "introverted": {"mystery": 0.8, "intelligence": 0.3},
    "felsefi":     {"mystery": 0.85, "intelligence": 0.5},
    "philosophical": {"mystery": 0.85, "intelligence": 0.5},
    "sezgisel":    {"mystery": 0.8, "creativity": 0.4},
    "intuitive":   {"mystery": 0.8, "creativity": 0.4},
    # --- discipline ---
    "disiplinli":  {"discipline": 0.95, "leadership": 0.3},
    "disciplined": {"discipline": 0.95, "leadership": 0.3},
    "metodik":     {"discipline": 0.9, "intelligence": 0.4},
    "methodical":  {"discipline": 0.9, "intelligence": 0.4},
    "titiz":       {"discipline": 0.85, "intelligence": 0.3},
    "meticulous":  {"discipline": 0.85, "intelligence": 0.3},
    "sistemli":    {"discipline": 0.9, "intelligence": 0.3},
    "systematic":  {"discipline": 0.9, "intelligence": 0.3},
    # --- charisma ---
    "çekici":      {"charisma": 0.9, "social": 0.4},
    "attractive":  {"charisma": 0.9, "social": 0.4},
    "büyüleyici":  {"charisma": 0.95, "mystery": 0.3},
    "captivating": {"charisma": 0.95, "mystery": 0.3},
    "etkileyici":  {"charisma": 0.85, "leadership": 0.4},
    "impressive":  {"charisma": 0.85, "leadership": 0.4},
    "ilham verici": {"charisma": 0.8, "leadership": 0.5, "creativity": 0.3},
    "inspiring":   {"charisma": 0.8, "leadership": 0.5, "creativity": 0.3},
}

# ---------------------------------------------------------------------------
# 2. ASSESSMENT TEST DOMAIN → KÜME HARİTASI
# ---------------------------------------------------------------------------
ASSESSMENT_CLUSTER_MAP: dict[str, dict[str, float]] = {
    # Big Five (personality)
    "personality.openness":           {"creativity": 0.7, "mystery": 0.4, "intelligence": 0.3},
    "personality.conscientiousness":  {"discipline": 0.9, "patience": 0.3},
    "personality.extraversion":       {"social": 0.5, "leadership": 0.4, "charisma": 0.3},
    "personality.agreeableness":      {"empathy": 0.5, "social": 0.4},
    "personality.neuroticism":        {},  # handled as negative weight where relevant
    # HR
    "hr.leadership":                  {"leadership": 0.9},
    "hr.communication":               {"social": 0.5, "charisma": 0.5},
    "hr.stress_tolerance":            {"patience": 0.5, "discipline": 0.3},
    "hr.teamwork":                    {"social": 0.7, "empathy": 0.3},
    # Skills
    "skills.problem_solving":         {"intelligence": 0.7, "discipline": 0.3},
    "skills.empathy":                 {"empathy": 1.0},
    "skills.creativity":              {"creativity": 0.9},
    "skills.leadership":              {"leadership": 0.9},
    # Career
    "career.analytical":              {"intelligence": 0.9},
    "career.creative":                {"creativity": 1.0},
    "career.social":                  {"social": 0.8, "empathy": 0.3},
    "career.leadership":              {"leadership": 0.9},
    # Psychology (dark triad etc.)
    "psych.narcissism":               {"charisma": 0.3, "leadership": 0.2},
    "psych.machiavellianism":         {"intelligence": 0.3, "discipline": 0.3},
    "psych.resilience":               {"strength": 0.8, "patience": 0.4},
}

# ---------------------------------------------------------------------------
# 3. BLEND TEMPLATES (18 dil)
# ---------------------------------------------------------------------------
CLUSTER_LABELS: dict[str, dict[str, str]] = {
    "leadership":    {"tr":"liderlik gücü","en":"leadership strength","de":"Führungsstärke","ru":"сила лидерства","ar":"قوة القيادة","es":"fuerza de liderazgo","ko":"리더십 힘","ja":"リーダーシップの力","zh":"领导力","hi":"नेतृत्व शक्ति","fr":"force de leadership","pt":"força de liderança","bn":"নেতৃত্ব শক্তি","id":"kekuatan kepemimpinan","ur":"قیادت کی طاقت","it":"forza di leadership","vi":"sức mạnh lãnh đạo","pl":"siła przywództwa"},
    "social":        {"tr":"sosyal bağlantısı","en":"social connection","de":"soziale Verbindung","ru":"социальная связь","ar":"التواصل الاجتماعي","es":"conexión social","ko":"사회적 연결","ja":"社会的なつながり","zh":"社交能力","hi":"सामाजिक संबंध","fr":"connexion sociale","pt":"conexão social","bn":"সামাজিক সংযোগ","id":"koneksi sosial","ur":"سماجی تعلق","it":"connessione sociale","vi":"kết nối xã hội","pl":"połączenie społeczne"},
    "patience":      {"tr":"sabır ve kararlılığı","en":"patience and determination","de":"Geduld und Entschlossenheit","ru":"терпение и решимость","ar":"الصبر والعزيمة","es":"paciencia y determinación","ko":"인내와 결단력","ja":"忍耐と決意","zh":"耐心与决心","hi":"धैर्य और दृढ़ता","fr":"patience et détermination","pt":"paciência e determinação","bn":"ধৈর্য ও সংকল্প","id":"kesabaran dan tekad","ur":"صبر اور عزم","it":"pazienza e determinazione","vi":"kiên nhẫn và quyết tâm","pl":"cierpliwość i determinacja"},
    "intelligence":  {"tr":"analitik zekası","en":"analytical intelligence","de":"analytische Intelligenz","ru":"аналитический интеллект","ar":"الذكاء التحليلي","es":"inteligencia analítica","ko":"분석적 지능","ja":"分析的知性","zh":"分析智慧","hi":"विश्लेषणात्मक बुद्धि","fr":"intelligence analytique","pt":"inteligência analítica","bn":"বিশ্লেষণাত্মক বুদ্ধিমত্তা","id":"kecerdasan analitis","ur":"تجزیاتی ذہانت","it":"intelligenza analitica","vi":"trí tuệ phân tích","pl":"inteligencja analityczna"},
    "creativity":    {"tr":"yaratıcı vizyonu","en":"creative vision","de":"kreative Vision","ru":"творческое видение","ar":"الرؤية الإبداعية","es":"visión creativa","ko":"창의적 비전","ja":"創造的ビジョン","zh":"创意视野","hi":"रचनात्मक दृष्टि","fr":"vision créative","pt":"visão criativa","bn":"সৃজনশীল দৃষ্টিভঙ্গি","id":"visi kreatif","ur":"تخلیقی وژن","it":"visione creativa","vi":"tầm nhìn sáng tạo","pl":"twórcza wizja"},
    "strength":      {"tr":"güç ve enerjisi","en":"power and energy","de":"Kraft und Energie","ru":"сила и энергия","ar":"القوة والطاقة","es":"fuerza y energía","ko":"힘과 에너지","ja":"力とエネルギー","zh":"力量与能量","hi":"शक्ति और ऊर्जा","fr":"force et énergie","pt":"força e energia","bn":"শক্তি ও শক্তি","id":"kekuatan dan energi","ur":"طاقت اور توانائی","it":"forza ed energia","vi":"sức mạnh và năng lượng","pl":"siła i energia"},
    "empathy":       {"tr":"derin empatisi","en":"deep empathy","de":"tiefes Einfühlungsvermögen","ru":"глубокая эмпатия","ar":"التعاطف العميق","es":"empatía profunda","ko":"깊은 공감","ja":"深い共感","zh":"深层共情","hi":"गहरी सहानुभूति","fr":"empathie profonde","pt":"empatia profunda","bn":"গভীর সহানুভূতি","id":"empati mendalam","ur":"گہری ہمدردی","it":"empatia profonda","vi":"sự đồng cảm sâu sắc","pl":"głęboka empatia"},
    "mystery":       {"tr":"gizemli derinliği","en":"mysterious depth","de":"geheimnisvolle Tiefe","ru":"таинственная глубина","ar":"العمق الغامض","es":"profundidad misteriosa","ko":"신비로운 깊이","ja":"神秘的な深み","zh":"神秘深度","hi":"रहस्यमय गहराई","fr":"profondeur mystérieuse","pt":"profundidade misteriosa","bn":"রহস্যময় গভীরতা","id":"kedalaman misterius","ur":"پراسرار گہرائی","it":"profondità misteriosa","vi":"chiều sâu bí ẩn","pl":"tajemnicza głębia"},
    "discipline":    {"tr":"disiplin ve düzeni","en":"discipline and order","de":"Disziplin und Ordnung","ru":"дисциплина и порядок","ar":"الانضباط والنظام","es":"disciplina y orden","ko":"규율과 질서","ja":"規律と秩序","zh":"纪律与秩序","hi":"अनुशासन और व्यवस्था","fr":"discipline et ordre","pt":"disciplina e ordem","bn":"শৃঙ্খলা ও শৃঙ্খলা","id":"disiplin dan ketertiban","ur":"نظم و ضبط","it":"disciplina e ordine","vi":"kỷ luật và trật tự","pl":"dyscyplina i porządek"},
    "charisma":      {"tr":"büyüleyici karizması","en":"captivating charisma","de":"fesselnde Ausstrahlung","ru":"захватывающая харизма","ar":"الكاريزما الآسرة","es":"carisma cautivador","ko":"매혹적인 카리스마","ja":"魅惑的なカリスマ","zh":"迷人魅力","hi":"मनमोहक करिश्मा","fr":"charisme captivant","pt":"carisma cativante","bn":"মনোমুগ্ধকর ক্যারিশমা","id":"karisma memukau","ur":"دلفریب کرشمہ","it":"carisma affascinante","vi":"sức hút quyến rũ","pl":"urzekający charyzmat"},
}

BLEND_TEMPLATES: dict[str, str] = {
    "tr": "{celeb} ile {animal} arasındaki nadir buluşma: {c1} ve {c2} mükemmel uyumda.",
    "en": "A rare meeting of {celeb} and {animal}: {c1} and {c2} in perfect harmony.",
    "de": "Eine seltene Begegnung von {celeb} und {animal}: {c1} und {c2} in perfekter Harmonie.",
    "ru": "Редкое сочетание {celeb} и {animal}: {c1} и {c2} в идеальной гармонии.",
    "ar": "لقاء نادر بين {celeb} و{animal}: {c1} و{c2} في انسجام تام.",
    "es": "Un raro encuentro de {celeb} y {animal}: {c1} y {c2} en perfecta armonía.",
    "ko": "{celeb}과 {animal}의 드문 만남: {c1}과 {c2}가 완벽한 조화를 이룸.",
    "ja": "{celeb}と{animal}の稀な出会い: {c1}と{c2}が完璧に調和。",
    "zh": "{celeb}与{animal}的罕见相遇：{c1}与{c2}完美和谐。",
    "hi": "{celeb} और {animal} का दुर्लभ मिलन: {c1} और {c2} सही सामंजस्य में।",
    "fr": "Une rencontre rare entre {celeb} et {animal}: {c1} et {c2} en parfaite harmonie.",
    "pt": "Um raro encontro entre {celeb} e {animal}: {c1} e {c2} em perfeita harmonia.",
    "bn": "{celeb} এবং {animal}-এর বিরল মিলন: {c1} এবং {c2} নিখুঁত সামঞ্জস্যে।",
    "id": "Pertemuan langka antara {celeb} dan {animal}: {c1} dan {c2} dalam harmoni sempurna.",
    "ur": "{celeb} اور {animal} کی نادر ملاقات: {c1} اور {c2} کامل ہم آہنگی میں۔",
    "it": "Un raro incontro tra {celeb} e {animal}: {c1} e {c2} in perfetta armonia.",
    "vi": "Cuộc gặp gỡ hiếm có của {celeb} và {animal}: {c1} và {c2} trong sự hài hòa hoàn hảo.",
    "pl": "Rzadkie spotkanie {celeb} i {animal}: {c1} i {c2} w doskonałej harmonii.",
}

# ---------------------------------------------------------------------------
# 4. SCORING FUNCTIONS
# ---------------------------------------------------------------------------

def score_from_sifatlar(sifatlar: list[str]) -> dict[str, float]:
    """Convert face-analysis sıfatlar to cluster scores (0–1)."""
    scores: dict[str, float] = defaultdict(float)
    for s in sifatlar:
        for cluster, w in SIFAT_CLUSTER_MAP.get(s.lower(), {}).items():
            scores[cluster] += w
    return {k: min(v / 3.0, 1.0) for k, v in scores.items()}


def get_assessment_cluster_scores(user_id: int) -> dict[str, float]:
    """Derive cluster scores from the user's latest assessment results."""
    try:
        from admin_api.utils.mongo import _get_db
        db = _get_db()
        # fetch latest results sorted by created_at; schema: {breakdown: {domain: val}}
        cursor = db['assessment_results'].find(
            {'user_id': user_id},
            {'_id': 0, 'breakdown': 1, 'created_at': 1},
        ).sort('created_at', -1)

        # keep the most recent score per domain (first doc wins)
        domain_scores: dict[str, float] = {}
        for doc in cursor:
            for domain, score in doc.get('breakdown', {}).items():
                if domain not in domain_scores:
                    domain_scores[domain] = float(score)

        if not domain_scores:
            return {}

        # convert to cluster scores
        cluster_acc: dict[str, float] = defaultdict(float)
        cluster_cnt: dict[str, int] = defaultdict(int)
        for domain, score in domain_scores.items():
            for cluster, w in ASSESSMENT_CLUSTER_MAP.get(domain, {}).items():
                cluster_acc[cluster] += score * w
                cluster_cnt[cluster] += 1

        return {
            k: min(v / max(cluster_cnt[k], 1), 1.0)
            for k, v in cluster_acc.items()
        }
    except Exception:
        return {}


def merge_scores(face_scores: dict[str, float], test_scores: dict[str, float]) -> dict[str, float]:
    """60 % face + 40 % test. If no tests, 100 % face."""
    if not test_scores:
        return face_scores
    all_keys = set(face_scores) | set(test_scores)
    return {
        k: face_scores.get(k, 0.0) * 0.6 + test_scores.get(k, 0.0) * 0.4
        for k in all_keys
    }


def score_archetype(archetype_clusters: dict[str, float], user_scores: dict[str, float]) -> float:
    """Weighted dot-product similarity (0–1)."""
    total = sum(archetype_clusters.values())
    if not total:
        return 0.0
    dot = sum(w * user_scores.get(c, 0.0) for c, w in archetype_clusters.items())
    return dot / total

# ---------------------------------------------------------------------------
# 5. ROTATION ENGINE
# ---------------------------------------------------------------------------

def _get_db():
    from admin_api.utils.mongo import _get_db as _mongo_get_db
    return _mongo_get_db()


def _get_shown(user_id: int, archetype_type: str) -> list[str]:
    db = _get_db()
    doc = db['user_archetype_history'].find_one({'user_id': user_id})
    if not doc:
        return []
    return doc.get(f'{archetype_type}_shown', [])


def _mark_shown(user_id: int, archetype_type: str, archetype_id: str) -> None:
    db = _get_db()
    db['user_archetype_history'].update_one(
        {'user_id': user_id},
        {
            '$addToSet': {f'{archetype_type}_shown': archetype_id},
            '$set': {'updated_at': datetime.utcnow()},
            '$setOnInsert': {'user_id': user_id},
        },
        upsert=True,
    )


def _reset_shown(user_id: int, archetype_type: str) -> None:
    db = _get_db()
    db['user_archetype_history'].update_one(
        {'user_id': user_id},
        {'$set': {f'{archetype_type}_shown': [], 'updated_at': datetime.utcnow()}},
        upsert=True,
    )


def _load_pool(archetype_type: str) -> list[dict]:
    db = _get_db()
    return list(db['archetype_pool'].find({'type': archetype_type}, {'_id': 0}))


def _pick_one(
    user_id: int | None,
    archetype_type: str,
    user_scores: dict[str, float],
    lang: str,
    min_score: float = 0.15,
) -> dict | None:
    pool = _load_pool(archetype_type)
    if not pool:
        return None

    # score & sort
    scored = sorted(
        [(a, score_archetype(a.get('clusters', {}), user_scores)) for a in pool],
        key=lambda x: x[1],
        reverse=True,
    )
    compatible = [(a, s) for a, s in scored if s >= min_score]
    if not compatible:
        compatible = scored[:5]  # fallback: take top-5 regardless

    if user_id is None:
        # anonymous: random from top-5
        top = compatible[:5]
        chosen, sc = random.choice(top)
    else:
        shown = _get_shown(user_id, archetype_type)
        unseen = [(a, s) for a, s in compatible if a['id'] not in shown]

        if not unseen:
            _reset_shown(user_id, archetype_type)
            unseen = compatible

        top = unseen[:5]
        chosen, sc = random.choice(top)
        _mark_shown(user_id, archetype_type, chosen['id'])

    name = (
        chosen.get('name', {}).get(lang)
        or chosen.get('name', {}).get('en')
        or chosen.get('name_en', chosen.get('name_tr', ''))
    )
    reason = (
        chosen.get('reason', {}).get(lang)
        or chosen.get('reason', {}).get('en')
        or chosen.get('reason_en', chosen.get('reason_tr', ''))
    )
    primary_cluster = max(chosen.get('clusters', {}).items(), key=lambda x: x[1], default=('', 0))[0]

    return {
        'id':              chosen['id'],
        'name':            name,
        'emoji':           chosen.get('emoji', ''),
        'reason':          reason,
        'primary_cluster': primary_cluster,
        'score':           round(sc, 3),
    }

# ---------------------------------------------------------------------------
# 6. BLEND GENERATION
# ---------------------------------------------------------------------------

def generate_blend(
    primary_cluster: str,
    secondary_cluster: str,
    celebrity_name: str,
    animal_name: str,
    lang: str = 'tr',
) -> str:
    tpl = BLEND_TEMPLATES.get(lang) or BLEND_TEMPLATES['en']
    c1 = CLUSTER_LABELS.get(primary_cluster, {}).get(lang) or CLUSTER_LABELS.get(primary_cluster, {}).get('en', primary_cluster)
    c2 = CLUSTER_LABELS.get(secondary_cluster, {}).get(lang) or CLUSTER_LABELS.get(secondary_cluster, {}).get('en', secondary_cluster)
    return tpl.format(celeb=celebrity_name, animal=animal_name, c1=c1, c2=c2)

# ---------------------------------------------------------------------------
# 7. MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def pick_archetypes(
    sifatlar: list[str],
    lang: str = 'tr',
    user_id: int | None = None,
) -> dict:
    """
    Returns one archetype per category + blend sentence.
    Merges face sıfat scores with assessment scores (if user_id provided).
    """
    face_scores = score_from_sifatlar(sifatlar)
    test_scores = get_assessment_cluster_scores(user_id) if user_id else {}
    merged = merge_scores(face_scores, test_scores)

    celebrity = _pick_one(user_id, 'celebrity', merged, lang)
    animal    = _pick_one(user_id, 'animal',    merged, lang)
    plant     = _pick_one(user_id, 'plant',     merged, lang)
    obj       = _pick_one(user_id, 'object',    merged, lang)

    # determine primary + secondary cluster
    sorted_clusters = sorted(merged.items(), key=lambda x: x[1], reverse=True)
    primary   = sorted_clusters[0][0] if len(sorted_clusters) > 0 else 'intelligence'
    secondary = sorted_clusters[1][0] if len(sorted_clusters) > 1 else 'creativity'

    blend = generate_blend(
        primary, secondary,
        celebrity['name'] if celebrity else '',
        animal['name']    if animal    else '',
        lang,
    )

    return {
        'celebrity':         celebrity,
        'animal':            animal,
        'plant':             plant,
        'object':            obj,
        'blend':             blend,
        'primary_cluster':   primary,
        'secondary_cluster': secondary,
    }


# ---------------------------------------------------------------------------
# 8. SINGLETON (optional convenience)
# ---------------------------------------------------------------------------

class ArchetypeMatcher:
    def pick_archetypes(self, sifatlar, lang='tr', user_id=None):
        return pick_archetypes(sifatlar, lang, user_id)


_matcher: ArchetypeMatcher | None = None


def get_archetype_matcher() -> ArchetypeMatcher:
    global _matcher
    if _matcher is None:
        _matcher = ArchetypeMatcher()
    return _matcher
