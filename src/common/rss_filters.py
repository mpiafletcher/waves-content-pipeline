import re

BLOCKED_PATTERNS = [
    r"/promo-code/?",
    r"/coupon/?",
    r"/coupons/?",
    r"/deals/?",
    r"/discount-code/?",

    r"\bpromo codes?\b",
    r"\bcoupons?\b",
    r"\bdiscount codes?\b",

    r"\b\d+% off\b",
    r"\bsave up to\b",
    r"\bdeal of the day\b",
    r"\bbest deals\b",

    r"\bfanduel promo\b",
    r"\bsportsbook promo\b",
    r"\bkalshi promo\b",
    r"\bunderdog promo\b",
]

COMPILED_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in BLOCKED_PATTERNS
]


def should_skip_rss_item(item: dict):
    text = " ".join([
        item.get("title", ""),
        item.get("description", ""),
        item.get("caption", ""),
        item.get("url", ""),
        item.get("canonical_url", ""),
    ]).lower()

    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return {
                "skip": True,
                "reason": f"matched_pattern:{pattern.pattern}"
            }

    return {
        "skip": False
    }
