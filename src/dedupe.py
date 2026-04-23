import hashlib
import re
from difflib import SequenceMatcher


def normalize_text(value: str) -> str:
    value = (value or "").strip().lower()
    value = value.replace("’", "'").replace("`", "'")
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_title(title: str) -> str:
    title = normalize_text(title)
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def build_dedupe_key(title: str, url: str) -> str:
    base = f"{normalize_title(title)}|{normalize_text(url)}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def build_variant_key(dedupe_key: str, language: str) -> str:
    return f"{dedupe_key}_{language}"


def similar_titles(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


def score_source_priority(item: dict) -> tuple:
    """
    Menor priority = mejor.
    priority_type 'primary' gana frente a 'secondary'.
    """
    priority = item.get("source_priority", 999)
    priority_type = item.get("priority_type", "secondary")

    primary_bonus = 0 if priority_type == "primary" else 1
    return (primary_bonus, priority)


def pick_best_item(a: dict, b: dict) -> dict:
    """
    Si dos items parecen duplicados, nos quedamos con el mejor:
    1. primary sobre secondary
    2. menor priority numérica
    3. descripción más larga
    """
    a_score = score_source_priority(a)
    b_score = score_source_priority(b)

    if a_score < b_score:
        return a
    if b_score < a_score:
        return b

    a_desc_len = len((a.get("summary") or a.get("description") or "").strip())
    b_desc_len = len((b.get("summary") or b.get("description") or "").strip())

    return a if a_desc_len >= b_desc_len else b


def hard_dedupe_items(items: list[dict]) -> list[dict]:
    """
    Dedupe fuerte por URL exacta o título normalizado exacto.
    """
    seen_urls = set()
    seen_titles = set()
    result = []

    for item in items:
        url = normalize_text(item.get("url") or item.get("link") or "")
        title = normalize_title(item.get("title") or "")

        if url and url in seen_urls:
            continue
        if title and title in seen_titles:
            continue

        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)

        result.append(item)

    return result


def soft_dedupe_items(items: list[dict], threshold: float = 0.85) -> list[dict]:
    """
    Dedupe blando por similitud de títulos.
    Si encuentra duplicado, conserva el mejor item.
    """
    result = []

    for item in items:
        matched_index = None

        for idx, existing in enumerate(result):
            similarity = similar_titles(
                item.get("title", ""),
                existing.get("title", "")
            )
            if similarity >= threshold:
                matched_index = idx
                break

        if matched_index is None:
            result.append(item)
        else:
            result[matched_index] = pick_best_item(result[matched_index], item)

    return result


def dedupe_segment_items(items: list[dict], threshold: float = 0.85) -> list[dict]:
    """
    Dedupe recomendado para premium:
    1. hard dedupe
    2. soft dedupe
    """
    items = hard_dedupe_items(items)
    items = soft_dedupe_items(items, threshold=threshold)
    return items
