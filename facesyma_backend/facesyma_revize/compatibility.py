"""
compatibility.py
================
Uyum analizi algoritması - Kullanıcılar arasındaki uyum skorunu hesaplar

Score Breakdown:
- Golden Ratio Match: 0-20 pts
- Sıfat Overlap: 0-40 pts
- Module Overlap: 0-20 pts
- Conflict Check: -5 pts each
- Category Bonus: +5 pts

Sonuç: 0-100 score + category (UYUMLU, UYUMSUZ, SAME_CATEGORY, DIFFERENT_CATEGORY)
"""

import json
from typing import Dict, List, Tuple

# ── Conflict Pairs (Karşıt Sıfatlar) ──────────────────────────────────────

CONFLICT_PAIRS = {
    # Kişilik tipi çatışmaları
    'İçedönük': ['Dışadönük', 'Sosyal'],
    'Dışadönük': ['İçedönük', 'Yalnız'],
    'Sosyal': ['İçedönük', 'Yalnız'],
    'Yalnız': ['Sosyal', 'Dışadönük'],

    # Emosyonel çatışmalar
    'Özgüvenli': ['İçine kapalı', 'Endişeli'],
    'İçine kapalı': ['Özgüvenli', 'Disiplinli'],
    'Endişeli': ['Özgüvenli', 'Cesur'],
    'Cesur': ['Endişeli', 'Temkinli'],

    # İş stili çatışmaları
    'Lider': ['Takipçi', 'Pasif'],
    'Takipçi': ['Lider'],
    'Pasif': ['Lider', 'Aktif'],
    'Aktif': ['Pasif'],

    # Analiz vs Sezgi
    'Analitik': ['Sezgisel'],
    'Sezgisel': ['Analitik'],

    # Esnek vs Katı
    'Esnek': ['Katı', 'Disiplinli'],
    'Katı': ['Esnek'],
    'Disiplinli': ['Esnek'],

    # Düşük vs Yüksek enerji
    'Enerjik': ['Sakin', 'Sessiz'],
    'Sakin': ['Enerjik'],
    'Sessiz': ['Enerjik', 'Gürültülü'],
}

# ── Sıfat Kategorileri ──────────────────────────────────────────────────────

SIFAT_CATEGORIES = {
    'Liderlik': ['Lider', 'Otoriter', 'Yönetici', 'Karizmatik', 'Etkileyici'],
    'Sosyallik': ['Sosyal', 'Arkadaş canlısı', 'Dışadönük', 'İletişim kurucu'],
    'Analitik': ['Analitik', 'Mantıklı', 'Sistematik', 'Araştırmacı', 'Detaycı'],
    'Yaratıcılık': ['Yaratıcı', 'Sanatsal', 'İnovatif', 'Hayal gücü', 'Özgün'],
    'Empatik': ['Empatik', 'Sempati', 'Anlayışlı', 'Yardımsever', 'Duyarlı'],
    'Disiplin': ['Disiplinli', 'Düzenli', 'Sorumlu', 'Güvenilir', 'Ciddi'],
    'Estetik': ['Estetik', 'Sanatsal', 'Güzelliğe duyarlı', 'Dekoratif', 'Görsel'],
}


def get_sifat_category(sifat: str) -> str:
    """Sıfatın kategorisini bulur"""
    for category, sifats in SIFAT_CATEGORIES.items():
        if sifat in sifats:
            return category
    return 'Other'


def calculate_compatibility(user1_data: Dict, user2_data: Dict) -> Dict:
    """
    İki kullanıcı arasındaki uyum skorunu hesapla

    Args:
        user1_data: {golden_ratio, top_sifats, modules, id}
        user2_data: {golden_ratio, top_sifats, modules, id}

    Returns:
        {
            'score': 0-100,
            'category': 'UYUMLU' | 'UYUMSUZ' | 'SAME_CATEGORY' | 'DIFFERENT_CATEGORY',
            'can_message': bool,
            'reasons': [...],
            'golden_ratio_diff': float,
            'sifat_overlap': int,
            'module_overlap': int,
            'conflict_count': int
        }
    """

    score = 0
    reasons = []

    # ── 1. Golden Ratio Match (20 pts) ──────────────────────────────────
    ratio1 = user1_data.get('golden_ratio', 0)
    ratio2 = user2_data.get('golden_ratio', 0)
    ratio_diff = abs(ratio1 - ratio2)

    if ratio_diff <= 0.05:  # ±5%
        score += 20
        reasons.append(f"✓ Golden ratio match: {ratio_diff:.1%} difference (Perfect)")
    elif ratio_diff <= 0.10:  # ±10%
        score += 15
        reasons.append(f"✓ Golden ratio match: {ratio_diff:.1%} difference (Very good)")
    elif ratio_diff <= 0.15:  # ±15%
        score += 10
        reasons.append(f"△ Golden ratio match: {ratio_diff:.1%} difference (Good)")
    else:
        reasons.append(f"✗ Golden ratio difference: {ratio_diff:.1%} (Large gap)")

    # ── 2. Sıfat Overlap (40 pts) ──────────────────────────────────────
    sifats1 = set(user1_data.get('top_sifats', []))
    sifats2 = set(user2_data.get('top_sifats', []))

    shared_sifats = len(sifats1 & sifats2)
    total_sifats = max(len(sifats1), len(sifats2), 1)
    sifat_overlap_percent = (shared_sifats / total_sifats) * 100

    sifat_score = (shared_sifats / total_sifats) * 40
    score += sifat_score

    reasons.append(f"✓ Shared sıfats: {shared_sifats}/{total_sifats} ({sifat_overlap_percent:.0f}%)")

    # ── 3. Module Overlap (20 pts) ──────────────────────────────────────
    modules1 = set(user1_data.get('modules', []))
    modules2 = set(user2_data.get('modules', []))

    shared_modules = len(modules1 & modules2)
    total_modules = max(len(modules1), len(modules2), 1)

    if total_modules > 0:
        module_score = (shared_modules / total_modules) * 20
        score += module_score
        reasons.append(f"✓ Shared modules: {shared_modules}/{total_modules}")
    else:
        reasons.append("⚠ No modules data")

    # ── 4. Conflict Check (Subtract) ────────────────────────────────────
    conflict_count = 0
    conflicting_sifats = []

    for s1 in sifats1:
        if s1 in CONFLICT_PAIRS:
            conflicts = CONFLICT_PAIRS[s1]
            for s2 in sifats2:
                if s2 in conflicts:
                    conflict_count += 1
                    conflicting_sifats.append(f"{s1} ↔ {s2}")

    score -= (conflict_count * 5)

    if conflict_count > 0:
        reasons.append(f"✗ Conflicts: {', '.join(conflicting_sifats[:2])}")

    # ── Normalize score to 0-100 ──────────────────────────────────────
    final_score = max(0, min(100, score))

    # ── 5. Category Assignment ──────────────────────────────────────────
    category, can_message = assign_category(
        final_score,
        conflict_count,
        sifats1,
        sifats2
    )

    return {
        'score': round(final_score, 2),
        'category': category,
        'can_message': can_message,
        'reasons': reasons,
        'golden_ratio_diff': round(ratio_diff, 4),
        'sifat_overlap': shared_sifats,
        'module_overlap': shared_modules,
        'conflict_count': conflict_count
    }


def assign_category(score: float, conflicts: int, sifats1: set, sifats2: set) -> Tuple[str, bool]:
    """
    Uyum kategorisini belirle

    Returns: (category, can_message)
    """

    # UYUMLU: High score + no conflicts
    if score >= 70 and conflicts == 0:
        return ('UYUMLU', True)

    # UYUMSUZ: Low score OR many conflicts
    if score < 30 or conflicts >= 2:
        return ('UYUMSUZ', False)

    # Check if same category
    cat1 = get_sifat_category(list(sifats1)[0]) if sifats1 else None
    cat2 = get_sifat_category(list(sifats2)[0]) if sifats2 else None

    if cat1 and cat2 and cat1 == cat2:
        return ('SAME_CATEGORY', True)

    # DIFFERENT_CATEGORY: Complementary (non-conflicting)
    if score >= 40 and conflicts == 0:
        return ('DIFFERENT_CATEGORY', False)  # Limited messaging

    # Default to UYUMSUZ if nothing matches
    return ('UYUMSUZ', False)


def find_compatible_users(
    user_id: int,
    all_users: List[Dict],
    category_filter: str = None,
    limit: int = 10
) -> List[Dict]:
    """
    Uyumlu kullanıcıları bul ve sırala

    Args:
        user_id: Sorgulanacak kullanıcı ID
        all_users: Tüm kullanıcılar listesi
        category_filter: Optional filter (UYUMLU, UYUMSUZ, etc.)
        limit: Döndürülecek sonuç sayısı

    Returns:
        [{user, score, category, can_message}, ...]
    """

    # User data fetch
    user_data = next((u for u in all_users if u['id'] == user_id), None)
    if not user_data:
        return []

    results = []

    for other_user in all_users:
        if other_user['id'] == user_id:
            continue

        compatibility = calculate_compatibility(user_data, other_user)

        # Apply filter if specified
        if category_filter and compatibility['category'] != category_filter:
            continue

        results.append({
            'user_id': other_user['id'],
            'username': other_user.get('username', 'User'),
            'score': compatibility['score'],
            'category': compatibility['category'],
            'can_message': compatibility['can_message'],
            'golden_ratio': other_user.get('golden_ratio', 0),
            'top_sifats': other_user.get('top_sifats', [])[:3]  # Top 3 only
        })

    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)

    return results[:limit]


def batch_calculate_compatibility(user_pairs: List[Tuple[int, int]], users_data: Dict) -> List[Dict]:
    """
    Birden fazla kullanıcı çiftini hesapla (bulk operation)

    Args:
        user_pairs: [(user1_id, user2_id), ...]
        users_data: {user_id: user_data, ...}

    Returns:
        [compatibility_result, ...]
    """

    results = []

    for user1_id, user2_id in user_pairs:
        user1 = users_data.get(user1_id)
        user2 = users_data.get(user2_id)

        if not user1 or not user2:
            continue

        compatibility = calculate_compatibility(user1, user2)
        compatibility['user1_id'] = user1_id
        compatibility['user2_id'] = user2_id

        results.append(compatibility)

    return results


def get_conflict_analysis(sifats: List[str]) -> Dict:
    """
    Sıfat grubunun çatışma analizi

    Returns:
        {
            'conflicts': [...],
            'risk_level': 'low' | 'medium' | 'high',
            'recommendations': [...]
        }
    """

    sifat_set = set(sifats)
    conflicts = []

    for sifat in sifat_set:
        if sifat in CONFLICT_PAIRS:
            conflicting = CONFLICT_PAIRS[sifat]
            for other_sifat in sifat_set:
                if other_sifat in conflicting:
                    conflicts.append((sifat, other_sifat))

    risk_level = 'low'
    if len(conflicts) >= 2:
        risk_level = 'high'
    elif len(conflicts) >= 1:
        risk_level = 'medium'

    recommendations = []
    if risk_level == 'high':
        recommendations = [
            "Bu sıfat kombinasyonunda iç çatışma olabilir",
            "Coaching modülleri dışa dönüklük/içedönüklük üzerinde çalışmayı önerir",
            "Empatik modülü ile başlamayı deneyin"
        ]
    elif risk_level == 'medium':
        recommendations = [
            "Bazı sıfatlarda uyum sağlamak gerekebilir",
            "Farkındalık koçluğu yararlı olabilir"
        ]

    return {
        'conflicts': conflicts,
        'risk_level': risk_level,
        'recommendations': recommendations
    }


# ── Test / Örnek ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Test verisi
    user1 = {
        'id': 1,
        'username': 'Ali',
        'golden_ratio': 1.618,
        'top_sifats': ['Lider', 'Disiplinli', 'Analitik'],
        'modules': ['Liderlik', 'Kariyer', 'İletişim']
    }

    user2 = {
        'id': 2,
        'username': 'Ayşe',
        'golden_ratio': 1.625,
        'top_sifats': ['Lider', 'Sosyal', 'Analitik'],
        'modules': ['Liderlik', 'Duygusal Zeka', 'İletişim']
    }

    result = calculate_compatibility(user1, user2)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Conflict analysis
    conflict_analysis = get_conflict_analysis(user1['top_sifats'])
    print("\n" + "="*50)
    print("Conflict Analysis:")
    print(json.dumps(conflict_analysis, indent=2, ensure_ascii=False))
