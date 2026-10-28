import os
import re
import json
from datetime import datetime

from free.fetch_sources import fetch_sources
from free.rss_parser import parse_rss, is_recent
from common.generator import generate_story
from common.captions import build_timed_subtitles
from clients.putter_client import send_to_putter
from clients.make_client import send_to_make
from common.validators import validate_episode, validate_tts_payload
from common.subtitles_sql import build_subtitles_update_sql
from common.rss_filters import should_skip_rss_item
from common.dedupe import build_dedupe_key, build_variant_key, build_story_fingerprint

TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
AUDIO_MODE = os.getenv("AUDIO_MODE", "putter_with_fallback").lower()
TEST_SOURCE_NAME = os.getenv("TEST_SOURCE_NAME", "").strip()
TEST_LANGUAGE = os.getenv("TEST_LANGUAGE", "").strip()
PIPELINE_MODE = os.getenv("PIPELINE_MODE", "free").lower()


# defaults producción
ITEMS_PER_SOURCE = 3
MAX_EPISODES_PER_LANGUAGE = 999999

# override automático para test
if TEST_MODE:
    ITEMS_PER_SOURCE = 1
    MAX_EPISODES_PER_LANGUAGE = 1


def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "general"


def build_tts_payload(script: str, episode: dict) -> dict:
    output_language = (episode.get("language") or "en").lower()

    if output_language.startswith("es"):
        voice = "Lucia"
        tts_language = "es-ES"
    else:
        voice = "Joanna"
        tts_language = "en-US"

    digest_date = episode.get("digest_date")
    topic_slug = slugify(episode.get("topic"))
    title_slug = slugify(episode.get("title_internal") or episode.get("title") or "episode")

    path = f"audio/{episode['tier']}/{digest_date}/{topic_slug}/{title_slug}.mp3"
    category = f"audio/{episode['tier']}/{digest_date}/{topic_slug}"

    payload = {
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

    validate_tts_payload(payload)
    return payload


def select_sources(sources):
    selected = sources

    if TEST_SOURCE_NAME:
        selected = [s for s in selected if s.get("source_name") == TEST_SOURCE_NAME]

    if TEST_LANGUAGE:
        selected = [s for s in selected if s.get("language") == TEST_LANGUAGE]

    if TEST_MODE:
        selected = selected[:1]

    return selected


def send_audio(payload):
    if AUDIO_MODE == "make_only":
        print("➡️ AUDIO_MODE=make_only")
        make_result = send_to_make(payload)
        print("MAKE RESULT:", make_result)
        return make_result

    if AUDIO_MODE == "putter_only":
        print("➡️ AUDIO_MODE=putter_only")
        putter_result = send_to_putter(payload)
        print("PUTTER RESULT:", putter_result)
        return putter_result

    print("➡️ AUDIO_MODE=putter_with_fallback")
    putter_result = send_to_putter(payload)

    if putter_result.get("success"):
        print("✅ PUTTER SUCCESS")
        print(putter_result)
        return putter_result
    else:
        print("⚠️ PUTTER FAILED → FALLBACK TO MAKE")
        make_result = send_to_make(payload)
        print("MAKE RESULT:", make_result)
        return make_result


def run():
    sources = fetch_sources()
    sources = select_sources(sources)

    print("TEST_MODE:", TEST_MODE)
    print("ITEMS_PER_SOURCE:", ITEMS_PER_SOURCE)
    print("MAX_EPISODES_PER_LANGUAGE:", MAX_EPISODES_PER_LANGUAGE)
    print("TOTAL SOURCES:", len(sources))

    if not sources:
        print("No sources matched current filters.")
        return

    produced_per_language = {}
    episodes_with_subtitles = []
    seen_dedupe_keys = set()
    seen_story_fingerprints = set()

    for source in sources:
        output_language = source["language"]
        source_language = source["source_language"]

        produced_per_language.setdefault(output_language, 0)

        if produced_per_language[output_language] >= MAX_EPISODES_PER_LANGUAGE:
            continue

        print(
            f"Processing {source['source_name']} | "
            f"source_language={source_language} | "
            f"output_language={output_language}"
        )

        items = parse_rss(source["source_url"])
        items = [item for item in items if is_recent(item, 24)]
        items = items[:ITEMS_PER_SOURCE]

        if not items:
            print("No recent items found.")
            continue

        for item in items:
            if produced_per_language[output_language] >= MAX_EPISODES_PER_LANGUAGE:
                break

            skip_result = should_skip_rss_item(item)
            skip = skip_result.get("skip", False)
            reason = skip_result.get("reason")

            if skip:
                print({
                    "skipped": True,
                    "reason": reason,
                    "source": source.get("source_name"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                })
                continue

            dedupe_key = build_dedupe_key(item["title"], item["url"])
            variant_key = build_variant_key(dedupe_key, output_language)

            if variant_key in seen_dedupe_keys:
                print({
                    "skipped": True,
                    "reason": "duplicate_variant_key_in_current_run",
                    "source": source.get("source_name"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "dedupe_key": variant_key,
                })
                continue

            seen_dedupe_keys.add(variant_key)

            story_fingerprint = build_story_fingerprint(
                item.get("title", ""),
                item.get("summary") or item.get("description") or ""
            )

            story_variant_key = f"{story_fingerprint}_{output_language}"

            if story_variant_key in seen_story_fingerprints:
                print({
                    "skipped": True,
                    "reason": "duplicate_story_fingerprint_in_current_run",
                    "source": source.get("source_name"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "story_fingerprint": story_variant_key,
                })
                continue

            seen_story_fingerprints.add(story_variant_key)

            story = generate_story(
                item=item,
                category=source["categories"]["name"],
                source_language=source_language,
                output_language=output_language
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

            duration_sec = story.get("estimated_duration_sec") or 90
            try:
                duration_sec = float(duration_sec)
            except Exception:
                duration_sec = 90.0

            timed_subtitles = build_timed_subtitles(
                story.get("subtitles", []),
                duration_sec,
                output_language,
                speed_multiplier=1.5,
            )

            episode = {
                "tier": "free",
                "category_id": source["category_id"],
                "title": story.get("title"),
                "title_internal": story.get("title_internal"),
                "caption": story.get("caption"),
                "duration_sec": duration_sec,
                "score": 0,
                "source_url": item["url"],
                "source_name": source["source_name"],
                "digest_date": digest_date,
                "status": "ready",
                "region": source.get("region"),
                "topic": source["categories"]["name"],
                "subtopic": subtopic,
                "segment_key": f"{source['categories']['name']}|{subtopic}|{source.get('region')}|{output_language}",
                "dedupe_key": variant_key,
                "source_language": source_language,
                "language": output_language,
                "subtitles_json": timed_subtitles,
                "is_shareable": False,
                "share_slug": None
            }

            validate_episode(episode)

            payload = build_tts_payload(script, episode)

            print("SCRIPT PREVIEW:", script[:250])
            print("PAYLOAD PATH:", payload["path"])

            tts_response = send_audio(payload)

            # Extract subtitles_json from Worker response (wrapped in 'data' field)
            subtitles_from_worker = []
            if tts_response and isinstance(tts_response, dict):
                worker_data = tts_response.get("data", {})
                if isinstance(worker_data, dict):
                    subtitles_from_worker = worker_data.get("subtitles_json", [])

            episodes_with_subtitles.append({
                "dedupe_key": episode["dedupe_key"],
                "subtitles_json": subtitles_from_worker or timed_subtitles
            })

            if subtitles_from_worker:
                print(f"✅ Got {len(subtitles_from_worker)} subtitle cues from Worker")
            else:
                print("⚠️ No subtitles returned from Worker")

            produced_per_language[output_language] += 1

    print("DONE. Produced per language:", produced_per_language)

    if episodes_with_subtitles:
        filename, sql_content = build_subtitles_update_sql(episodes_with_subtitles)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(sql_content)

        print(f"Generated subtitles SQL file: {filename}")


if __name__ == "__main__":
    if PIPELINE_MODE == "premium":
        from premium.pipeline import run_premium_pipeline

        premium_episodes = run_premium_pipeline(
            build_timed_subtitles=build_timed_subtitles,
            build_tts_payload=build_tts_payload,
            send_audio=send_audio,
        )
        print(f"Generated {len(premium_episodes)} premium episodes")

    elif PIPELINE_MODE == "all":
        from premium.pipeline import run_premium_pipeline

        premium_episodes = run_premium_pipeline(
            build_timed_subtitles=build_timed_subtitles,
            build_tts_payload=build_tts_payload,
            send_audio=send_audio,
        )
        print(f"Generated {len(premium_episodes)} premium episodes")

        run()

    else:
        run()
