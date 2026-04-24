import os
import json
import requests


def fetch_content_segments():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY")

    url = f"{supabase_url}/rest/v1/content_segments"

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
    }

    params = {
        "tier": "eq.premium",
        "is_active": "eq.true",
        "status": "eq.active",
        "select": "*",
        "order": "priority.desc",
    }

    res = requests.get(url, headers=headers, params=params, timeout=30)
    res.raise_for_status()

    rows = res.json()
    segments = []

    for row in rows:
        raw_sources = row.get("sources_json") or []

        if isinstance(raw_sources, str):
            raw_sources = json.loads(raw_sources)

        normalized_sources = []

        for s in raw_sources:
            if not s.get("is_active", True):
                continue

            normalized_sources.append({
                "url": s.get("source_url"),
                "name": s.get("source_name") or "Unknown Source",
                "priority": s.get("priority", 999),
                "priority_type": s.get("priority_type", "secondary"),
                "source_language": s.get("source_language") or row.get("source_language"),
            })

        if not normalized_sources:
            continue

        segments.append({
            "id": row["id"],
            "category_id": row["category_id"],
            "topic": row["topic"],
            "subtopic": row["subtopic"],
            "region": row["region"],
            "language": row["language"],
            "source_language": row.get("source_language"),
            "tier": row["tier"],
            "source_strategy": row.get("source_strategy", "dedicated"),
            "sources": normalized_sources,
        })

    return segments
