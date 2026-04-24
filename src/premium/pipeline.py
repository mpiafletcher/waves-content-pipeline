from premium.fetch_segments import fetch_content_segments
from premium.fetch_items import fetch_items_for_segment
from common.dedupe import dedupe_segment_items
from premium.rank import rank_items
from common.generator import generate_story


def run_premium_pipeline():
    segments = fetch_content_segments()

    all_episodes = []

    for segment in segments:
        print(f"Processing segment: {segment['topic']} - {segment['subtopic']}")

        items = fetch_items_for_segment(segment)

       items = dedupe_segment_items(items)

        items = rank_items(items)

        selected = items[:3]  # top 3

        for item in selected:
            story = generate_story(
                item,
                category=segment["topic"],
                source_language=segment["source_language"],
                output_language=segment["language"]
            )

            if not story:
                continue

            # 🔥 override subtopic (CRÍTICO)
            story["subtopic"] = segment["subtopic"]

            episode = {
                "tier": "premium",
                "category_id": segment["category_id"],
                "title": story["title"],
                "title_internal": story["title_internal"],
                "caption": story["caption"],
                "script": story["script"],
                "subtopic": segment["subtopic"],
                "topic": segment["topic"],
                "region": segment["region"],
                "language": segment["language"],
                "source_url": item["url"]
            }

            all_episodes.append(episode)

    return all_episodes
