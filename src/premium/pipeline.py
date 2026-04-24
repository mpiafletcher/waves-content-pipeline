import os
from datetime import datetime

from premium.fetch_segments import fetch_content_segments
from premium.fetch_items import fetch_items_for_segment
from common.dedupe import dedupe_segment_items, build_dedupe_key, build_variant_key
from premium.rank import rank_items
from common.generator import generate_story
from common.validators import validate_episode


TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

MAX_SEGMENTS = 1 if TEST_MODE else 999999
MAX_ITEMS_PER_SEGMENT = 1 if TEST_MODE else 3


def run_premium_pipeline(build_timed_subtitles, build_tts_payload, send_audio):
    segments = fetch_content_segments()

    if TEST_MODE:
        segments = segments[:MAX_SEGMENTS]

    all_episodes = []

    print("PREMIUM TEST_MODE:", TEST_MODE)
    print("PREMIUM MAX_SEGMENTS:", MAX_SEGMENTS)
    print("PREMIUM MAX_ITEMS_PER_SEGMENT:", MAX_ITEMS_PER_SEGMENT)

    for segment in segments:
        print(f"Processing segment: {segment['topic']} - {segment['subtopic']}")

        items = fetch_items_for_segment(segment)
        items = dedupe_segment_items(items, threshold=0.85)
        items = rank_items(items)

        selected = items[:MAX_ITEMS_PER_SEGMENT]

        for item in selected:
            source_language = item.get("source_language") or segment["source_language"]
            output_language = segment["language"]

            story = generate_story(
                item=item,
                category=segment["topic"],
                source_language=source_language,
                output_language=output_language,
            )

            if not story:
                print("Story generation failed:", item.get("title"))
                continue

            script = (story.get("script") or "").strip()

            if not script:
                print("Missing script:", item.get("title"))
                continue

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

            dedupe_key = build_dedupe_key(item["title"], item["url"])
            variant_key = build_variant_key(dedupe_key, output_language)

            episode = {
                "tier": "premium",
                "category_id": segment["category_id"],
                "title": story.get("title"),
                "title_internal": story.get("title_internal"),
                "caption": story.get("caption"),
                "duration_sec": duration_sec,
                "score": 0,
                "source_url": item["url"],
                "source_name": item.get("source_name"),
                "digest_date": digest_date,
                "status": "ready",
                "region": segment["region"],
                "topic": segment["topic"],
                "subtopic": segment["subtopic"],
                "segment_key": f"{segment['topic']}|{segment['subtopic']}|{segment['region']}|{output_language}",
                "dedupe_key": variant_key,
                "source_language": source_language,
                "language": output_language,
                "subtitles_json": timed_subtitles,
                "is_shareable": False,
                "share_slug": None,
            }

            validate_episode(episode)

            payload = build_tts_payload(script, episode)

            print("PREMIUM SCRIPT PREVIEW:", script[:250])
            print("PREMIUM PAYLOAD PATH:", payload["path"])

            send_audio(payload)

            all_episodes.append(episode)

    return all_episodes
