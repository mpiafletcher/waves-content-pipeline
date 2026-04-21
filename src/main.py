import os
import re
from datetime import datetime

from fetch_sources import fetch_sources
from rss_parser import parse_rss, is_recent
from dedupe import build_dedupe_key, build_variant_key
from generator import generate_story
from putter_client import send_to_putter
from make_client import send_to_make

TEST_MODE = True
AUDIO_MODE = os.getenv("AUDIO_MODE", "putter_with_fallback").lower()
TEST_SOURCE_NAME = os.getenv("TEST_SOURCE_NAME", "").strip()
TEST_LANGUAGE = os.getenv("TEST_LANGUAGE", "").strip()


def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "general"


def build_timed_subtitles(subtitles, language="en"):
    if not isinstance(subtitles, list):
        return []

    chars_per_second = 13 if str(language).startswith("es") else 15
    timed = []
    cursor = 0

    for seg in subtitles:
        text = (seg.get("text") or "").strip()
        if not text:
            continue

        duration_ms = max(800, round((len(text) / chars_per_second) * 1000))
        start_ms = cursor
        end_ms = cursor + duration_ms

        timed.append({
            "text": text,
            "start_ms": start_ms,
            "end_ms": end_ms
        })

        cursor = end_ms

    return timed


def build_tts_payload(script: str, episode: dict) -> dict:
    language = (episode.get("language") or "en").lower()

    if language.startswith("es"):
        voice = "Lucia"
        tts_language = "es-ES"
    else:
        voice = "Joanna"
        tts_language = "en-US"

    digest_date = episode.get("digest_date")
    topic_slug = slugify(episode.get("topic"))
    title_slug = slugify(episode.get("title_internal") or episode.get("title") or "episode")

    path = f"free/{digest_date}/{topic_slug}/{title_slug}.mp3"
    category = f"free/{digest_date}/{topic_slug}"

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


def select_sources(sources: list[dict]) -> list[dict]:
    selected = sources

    if TEST_SOURCE_NAME:
        selected = [s for s in selected if s.get("source_name") == TEST_SOURCE_NAME]

    if TEST_LANGUAGE:
        selected = [s for s in selected if s.get("language") == TEST_LANGUAGE]

    if TEST_MODE:
        selected = selected[:1]

    return selected


def send_audio(payload: dict) -> None:
    if AUDIO_MODE == "make_only":
        print("➡️ AUDIO_MODE=make_only")
        make_result = send_to_make(payload)
        print("MAKE RESULT:", make_result)
        return

    if AUDIO_MODE == "putter_only":
        print("➡️ AUDIO_MODE=putter_only")
        putter_result = send_to_putter(payload)
        print("PUTTER RESULT:", putter_result)
        return

    print("➡️ AUDIO_MODE=putter_with_fallback")
    putter_result = send_to_putter(payload)

    if putter_result.get("success"):
        print("✅ PUTTER SUCCESS")
        print(putter_result)
    else:
        print("⚠️ PUTTER FAILED → FALLBACK TO MAKE")
        make_result = send_to_make(payload)
        print("MAKE RESULT:", make_result)


def run():
    sources = fetch_sources()
    sources = select_sources(sources)

    if not sources:
        print("No sources matched current filters.")
        return

    for source in sources:
        print(f"Processing {source['source_name']} ({source['language']})")

        items = parse_rss(source["source_url"])
        items = [item for item in items if is_recent(item, 6)]

        if TEST_MODE:
            items = items[:1]

        if not items:
            print("No recent items found.")
            continue

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
            timed_subtitles = build_timed_subtitles(
                story.get("subtitles", []),
                source["language"]
            )

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
                "subtitles_json": timed_subtitles,
                "is_shareable": False,
                "share_slug": None
            }

            payload = build_tts_payload(script, episode)

            print("SCRIPT PREVIEW:", script[:300])
            print("SCRIPT TYPE:", type(script))
            print("PAYLOAD PATH:", payload["path"])

            send_audio(payload)


if __name__ == "__main__":
    run()
