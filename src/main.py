from datetime import datetime

from fetch_sources import fetch_sources
from rss_parser import parse_rss, is_recent
from dedupe import build_dedupe_key, build_variant_key
from generator import generate_story
from putter_client import send_to_putter

TEST_MODE = True


def run():
    sources = fetch_sources()

    if TEST_MODE:
        sources = sources[:1]

    for source in sources:
        print(f"Processing {source['source_name']} ({source['language']})")

        items = parse_rss(source["source_url"])
        items = [item for item in items if is_recent(item, 6)]

        if TEST_MODE:
            items = items[:1]

        for item in items:
            dedupe_key = build_dedupe_key(item["title"], item["url"])
            variant_key = build_variant_key(dedupe_key, source["language"])

            story = generate_story(
                item,
                source["categories"]["name"],
                source["language"]
            )

            if not story:
                print({
                    "error": "story_generation_failed",
                    "title": item.get("title"),
                    "source": source.get("source_name")
                })
                continue

            script = (story.get("script") or "").strip()
            if not script:
                print({
                    "error": "missing_script",
                    "title": item.get("title"),
                    "story_preview": str(story)[:500]
                })
                continue

            episode = {
                "tier": "free",
                "category_id": source["category_id"],
                "title": story.get("title"),
                "title_internal": story.get("title_internal"),
                "caption": story.get("caption"),
                "duration_sec": story.get("estimated_duration_sec"),
                "score": 0,
                "source_url": item["url"],
                "source_name": source["source_name"],
                "digest_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "status": "ready",
                "region": source.get("region"),
                "topic": source["categories"]["name"],
                "subtopic": story.get("subtopic"),
                "segment_key": f"{source['categories']['name']}|{story.get('subtopic')}|{source.get('region')}|{source['language']}",
                "dedupe_key": variant_key,
                "source_language": source["source_language"],
                "language": source["language"],
                "subtitles_json": story.get("subtitles", []),
                "is_shareable": False,
                "share_slug": None
            }

            print("SCRIPT PREVIEW:", script[:300])
            print("SCRIPT TYPE:", type(script))

            result = send_to_putter(script, episode)
            print(result)


if __name__ == "__main__":
    run()
