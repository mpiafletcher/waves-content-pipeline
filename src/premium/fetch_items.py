from free.rss_parser import parse_rss, is_recent


def fetch_items_for_segment(segment, hours=24):
    items = []

    for source in segment["sources"]:
        if not source.get("url"):
            continue

        try:
            feed_items = parse_rss(source["url"])
        except Exception as e:
            print(f"RSS fetch failed: {source.get('name')} | {e}")
            continue

        feed_items = [item for item in feed_items if is_recent(item, hours)]

        for item in feed_items:
            items.append({
                "title": item.get("title"),
                "url": item.get("url") or item.get("link"),
                "summary": item.get("summary") or item.get("description") or "",
                "description": item.get("description") or item.get("summary") or "",
                "published": item.get("published"),

                "source_name": source["name"],
                "source_priority": source["priority"],
                "priority_type": source["priority_type"],
                "source_language": source["source_language"],

                "segment": segment,
            })

    return items
