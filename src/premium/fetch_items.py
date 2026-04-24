from utils.rss import fetch_rss_feed  # asumo que ya tenés algo así


def fetch_items_for_segment(segment):
    items = []

    for source in segment["sources"]:
        feed_items = fetch_rss_feed(source["url"])

        for item in feed_items:
            items.append({
                "title": item.get("title"),
                "url": item.get("link"),
                "summary": item.get("summary"),
                "published": item.get("published"),

                "source_name": source["name"],
                "source_priority": source["priority"],
                "priority_type": source["priority_type"],

                "segment": segment
            })

    return items
