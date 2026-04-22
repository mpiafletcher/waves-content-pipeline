import feedparser
from datetime import datetime, timezone
import re
import html


def clean_title(title):
    if not title:
        return ""

    title = html.unescape(title)
    title = re.sub(r"\s*-\s*[^-]+$", "", title)
    return title.strip()


def extract_real_url(entry):
    link = entry.get("link")
    if not link:
        return None
    return link


def parse_rss(url):
    feed = feedparser.parse(url)

    items = []

    for entry in feed.entries:
        title = clean_title(entry.get("title"))
        link = extract_real_url(entry)

        if not title or not link:
            continue

        items.append({
            "title": title,
            "url": link,
            "published": entry.get("published"),
            "published_parsed": entry.get("published_parsed"),
            "summary": entry.get("summary", ""),
        })

    return items


def is_recent(item, hours=6):
    published_parsed = item.get("published_parsed")

    if not published_parsed:
        return True

    published = datetime(*published_parsed[:6], tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)

    diff = (now - published).total_seconds()
    return diff < hours * 3600
