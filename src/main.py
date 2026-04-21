from datetime import datetime
import re

from fetch_sources import fetch_sources
from rss_parser import parse_rss, is_recent
from dedupe import build_dedupe_key, build_variant_key
from generator import generate_story
from putter_client import send_to_putter
from make_client import send_to_make

TEST_MODE = True


def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "general"


def build_tts_payload(script, episode):
    language = episode.get("language", "en")

    if language.startswith("es"):
        voice = "Lucia"
        tts_language = "es-ES"
    else:
        voice = "Joanna"
        tts_language = "en-US"

    digest_date = episode.get("digest_date")
    topic_slug = slugify(episode.get("topic"))
    subtopic_slug = slugify(episode.get("subtopic") or "general")
    title_slug = slugify(episode.get("title_internal") or episode.get("title") or "episode")

    path = f"free/{digest_date}/{topic_slug}/{subtopic_slug}/{title_slug}.mp3"
    category = f"free/{digest_date}/{topic_slug}/{subtopic_slug}"

    return {
        "text": script,
        "path": path,
        "category": category,
        "subtitles_json": episode.get("subtitles_json", []),
        "options": {
            "voice": voice,
            "language": tts_language,
            "engine": "standard"
        },
        "test_mode": False,
        "episode": episode
    }


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

            subtopic = story.get("subtopic") or "general"
            digest_date = datetime.utcnow().strftime("%Y-%m-%d")

            episode = {
                "tier": "free",
                "category_id": source["category_id"],
                "title": story.get("title"),
                "title_internal": story.get("title_internal"),
                "caption": story.get("caption"),
                "duration_sec": story.get("estimated_duration_sec") or 0,
                "score": 0,
                "source_url": item["url"],
                "source_name": source["source_name"],
                "digest_date": digest_date,
                "status": "ready",
                "region": source.get("region"),
                "topic": source["categories"]["name"],
                "subtopic": subtopic,
                "segment_key": f"{source['categories']['name']}|{subtopic}|{source.get('region')}|{source['language']}",
                "dedupe_key": variant_key,
                "source_language": source["source_language"],
                "language": source["language"],
                "subtitles_json": story.get("subtitles", []),
                "is_shareable": False,
                "share_slug": None
            }

            payload = build_tts_payload(script, episode)

            print("SCRIPT PREVIEW:", script[:300])
            print("SCRIPT TYPE:", type(script))

            putter_result = send_to_putter(payload)

            if putter_result.get("success"):
                print("✅ PUTTER SUCCESS")
                print(putter_result)
            else:
                print("⚠️ PUTTER FAILED → FALLBACK TO MAKE")
                make_result = send_to_make(payload)
                print("MAKE RESULT:", make_result)


if __name__ == "__main__":
    run()
