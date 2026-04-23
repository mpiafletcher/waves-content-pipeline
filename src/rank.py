from datetime import datetime


def score_item(item):
    score = 0

    # prioridad de fuente
    score += 1000 - item.get("source_priority", 999)

    # primary boost
    if item.get("priority_type") == "primary":
        score += 50

    # recency boost
    if item.get("published"):
        try:
            dt = datetime(*item["published"][:6])
            age_hours = (datetime.utcnow() - dt).total_seconds() / 3600
            score += max(0, 100 - age_hours)
        except:
            pass

    return score


def rank_items(items):
    return sorted(items, key=score_item, reverse=True)
