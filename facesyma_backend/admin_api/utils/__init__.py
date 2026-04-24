# Admin API Utils


def safe_int(value, default: int = 0, min_val: int | None = None, max_val: int | None = None) -> int:
    """Parse an integer from a query parameter safely, with optional clamp."""
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = default
    if min_val is not None:
        result = max(min_val, result)
    if max_val is not None:
        result = min(max_val, result)
    return result
