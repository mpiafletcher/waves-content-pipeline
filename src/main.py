TEST_MODE = True
import json
from fetch_sources import fetch_sources
from rss_parser import parse_rss
from dedupe import build_dedupe_key, build_variant_key
from generator import generate_story
from putter_client import send_to_putter

def run():
    sources = fetch_sources()

    if TEST_MODE:
        sources = sources[:1]

    for source in sources:
        print(f"Processing {source['source_name']} ({source['language']})")

        items = parse_rss(source["source_url"])

    if TEST_MODE:
        items = items[:1]

        for item in items:
            dedupe_key = build_dedupe_key(item["title"], item["url"])
            variant_key = build_variant_key(dedupe_key, source["language"])

            story_raw = generate_story(
                item,
                source["categories"]["name"],
                source["language"]
            )

            try:
                story = json.loads(story_raw)
            except json.JSONDecodeError as e:
                print({
                    "error": "invalid_openai_json",
                    "detail": str(e),
                    "raw_preview": story_raw[:500]
                })
                continue

            script = story.get("script", "").strip()
            if not script:
                print({
                    "error": "missing_script",
                    "title": item["title"],
                    "raw_preview": story_raw[:500]
                })
                continue

            episode = {
                "category_id": source["category_id"],
                "source_url": item["url"],
                "source_name": source["source_name"],
                "language": source["language"],
                "source_language": source["source_language"],
                "topic": source["categories"]["name"],
                "title": story.get("title"),
                "title_internal": story.get("title_internal"),
                "caption": story.get("caption"),
                "subtopic": story.get("subtopic"),
                "duration_sec": story.get("estimated_duration_sec"),
                "subtitles_json": story.get("subtitles", []),
                "dedupe_key": variant_key,
            }
            
            print("SCRIPT PREVIEW:", script[:300])
            print("SCRIPT TYPE:", type(script))   
            result = send_to_putter(script, episode)
            print(result)

if __name__ == "__main__":
    run()
