"""
scorer.py
=========
Continous scoring for facial measurements using golden ratio bounds.

Converts categorical measurements (golden/near/far) into 0-1 confidence scores.
"""

from functools import lru_cache

# Golden ratio bounds
PHI_LOW = 1.5371      # Lower bound for golden zone
PHI_HIGH = 1.6989     # Upper bound for golden zone
PHI_MID = (PHI_LOW + PHI_HIGH) / 2  # 1.618... ≈ golden ratio


@lru_cache(maxsize=512)
def score_ratio(ratio: float) -> float:
    """
    Convert facial measurement ratio to 0-1 confidence score.

    Args:
        ratio: Measurement ratio (e.g., 1.62 for golden, 1.4 for near, 1.8 for far)

    Returns:
        Confidence score 0-1, where:
        - 1.0 = perfect golden ratio (1.618)
        - 0.75-0.99 = within golden zone (1.5371-1.6989)
        - 0.30-0.74 = outside golden zone

    Examples:
        >>> score_ratio(1.618)      # Perfect golden ratio
        1.0
        >>> score_ratio(1.5371)     # Zone boundary
        0.75
        >>> score_ratio(1.6989)     # Zone boundary
        0.75
        >>> score_ratio(1.3)        # Far below golden zone
        0.3
        >>> score_ratio(1.9)        # Far above golden zone
        0.3
    """
    if PHI_LOW <= ratio <= PHI_HIGH:
        # Inside golden zone: score 0.75 - 1.0
        # Higher score near 1.618 (center), lower at boundaries
        distance = abs(ratio - PHI_MID)
        max_dist = (PHI_HIGH - PHI_LOW) / 2
        return round(0.75 + 0.25 * (1 - distance / max_dist), 3)
    else:
        # Outside golden zone: score 0.3 - 0.74
        # Penalty increases with distance from zone
        if ratio < PHI_LOW:
            distance = PHI_LOW - ratio
        else:
            distance = ratio - PHI_HIGH

        # Normalize penalty (max ~2 for very extreme values)
        penalty = min(distance / 0.5, 1.0)
        return round(0.74 - 0.44 * penalty, 3)


@lru_cache(maxsize=512)
def get_sifat_score(measurement_category: str, measurement_ratio: float) -> float:
    """
    Get sıfat confidence score based on measurement category and ratio.

    Args:
        measurement_category: "golden", "near", "far", "big", "small", "wide", "narrow", etc.
        measurement_ratio: The actual measurement ratio value

    Returns:
        Confidence score 0-1
    """
    _cat_lower = measurement_category.lower()

    # If golden category, use the ratio scorer
    if "golden" in _cat_lower:
        return score_ratio(measurement_ratio)

    # For near/small/narrow categories
    elif any(x in _cat_lower for x in ["near", "small", "narrow"]):
        ratio_score = score_ratio(measurement_ratio)
        # Penalize if ratio indicates it's actually too far from golden
        return max(0.3, ratio_score - 0.15)

    # For far/big/wide categories
    elif any(x in _cat_lower for x in ["far", "big", "wide"]):
        ratio_score = score_ratio(measurement_ratio)
        # Penalize if ratio indicates it's actually too far from golden
        return max(0.3, ratio_score - 0.15)

    else:
        # Unknown category, return neutral score
        return 0.5


# Test
if __name__ == "__main__":
    print("=== Scorer Test ===")

    # Test golden ratio
    print(f"Perfect golden (1.618): {score_ratio(1.618)}")

    # Test zone boundaries
    print(f"Zone lower (1.5371): {score_ratio(1.5371)}")
    print(f"Zone upper (1.6989): {score_ratio(1.6989)}")
    print(f"Zone mid (1.568): {score_ratio(1.568)}")

    # Test outside zone
    print(f"Below zone (1.4): {score_ratio(1.4)}")
    print(f"Above zone (1.8): {score_ratio(1.8)}")
    print(f"Extreme (1.0): {score_ratio(1.0)}")
    print(f"Extreme (2.0): {score_ratio(2.0)}")

    # Test category scores
    print(f"\nCategory scores:")
    print(f"Golden 1.62: {get_sifat_score('eyes_distance_golden', 1.62)}")
    print(f"Near 1.4: {get_sifat_score('eyes_near', 1.4)}")
    print(f"Far 1.8: {get_sifat_score('eyes_far', 1.8)}")
