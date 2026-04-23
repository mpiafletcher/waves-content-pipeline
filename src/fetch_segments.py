from supabase import create_client
import os
import json

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


def fetch_content_segments():
    res = supabase.table("content_segments") \
        .select("*") \
        .eq("tier", "premium") \
        .eq("is_active", True) \
        .execute()

    segments = []

    for row in res.data:
        sources = row.get("sources_json") or []

        # aseguramos formato consistente
        normalized_sources = []
        for s in sources:
            if not s.get("is_active", True):
                continue

            normalized_sources.append({
                "url": s.get("source_url"),
                "name": s.get("source_name"),
                "priority": s.get("priority", 999),
                "priority_type": s.get("priority_type", "secondary"),
                "source_language": s.get("source_language", row.get("source_language"))
            })

        segments.append({
            "id": row["id"],
            "category_id": row["category_id"],
            "topic": row["topic"],
            "subtopic": row["subtopic"],
            "region": row["region"],
            "language": row["language"],
            "source_language": row["source_language"],
            "sources": normalized_sources,
            "source_strategy": row.get("source_strategy", "dedicated")
        })

    return segments
