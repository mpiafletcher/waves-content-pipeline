import feedparser

def parse_rss(url):
    feed = feedparser.parse(url)

    items = []

    for entry in feed.entries[:10]:  # limit
        items.append({
            "title": entry.get("title", ""),
            "description": entry.get("summary", ""),
            "url": entry.get("link", "")
        })

    return items
