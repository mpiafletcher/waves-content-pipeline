from fetch_sources import fetch_sources
from rss_parser import parse_rss
from dedupe import build_dedupe_key, build_variant_key
from generator import generate_story
from putter_client import send_to_putter

def run():
    sources = fetch_sources()

    for source in sources:
        print(f"Processing {source['source_name']} ({source['language']})")

        items = parse_rss(source["source_url"])

        for item in items:
            dedupe_key = build_dedupe_key(item["title"], item["url"])
            variant_key = build_variant_key(dedupe_key, source["language"])

            story_json = generate_story(
                item,
                source["categories"]["name"],
                source["language"]
            )

            episode = {
                "category_id": source["category_id"],
                "source_url": item["url"],
                "source_name": source["source_name"],
                "language": source["language"],
                "source_language": source["source_language"],
                "topic": source["categories"]["name"],
                "dedupe_key": variant_key
            }

            result = send_to_putter(
                story_json,
                episode
            )

            print(result)


if __name__ == "__main__":
    run()
