import os
import requests

WORKER_URL = os.getenv("WORKER_URL")
WORKER_API_KEY = os.getenv("WORKER_API_KEY")

def send_to_putter(script, episode):
    if not isinstance(script, str) or not script.strip():
        raise ValueError("script must be a non-empty string")

    language = episode.get("language", "en")
    topic = str(episode.get("topic", "general")).lower().replace(" ", "_")
    subtopic = str(episode.get("subtopic", "general")).lower().replace(" ", "_")
    title_internal = str(episode.get("title_internal", "episode")).lower().replace(" ", "_")
    digest_date = episode.get("digest_date")

    if language.startswith("es"):
        voice = "Lucia"
        tts_language = "es-ES"
    else:
        voice = "Joanna"
        tts_language = "en-US"

    path = f"free/{digest_date}/{topic}/{subtopic}/{title_internal}.mp3"
    category = f"free/{digest_date}/{topic}/{subtopic}"

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
        "episode": {
            "tier": episode.get("tier", "free"),
            "category_id": episode.get("category_id"),
            "title": episode.get("title"),
            "title_internal": episode.get("title_internal"),
            "caption": episode.get("caption"),
            "duration_sec": episode.get("duration_sec", 0),
            "score": episode.get("score", 0),
            "source_url": episode.get("source_url"),
            "source_name": episode.get("source_name"),
            "digest_date": episode.get("digest_date"),
            "status": episode.get("status", "ready"),
            "region": episode.get("region"),
            "topic": episode.get("topic"),
            "subtopic": episode.get("subtopic"),
            "segment_key": episode.get("segment_key"),
            "dedupe_key": episode.get("dedupe_key"),
            "source_language": episode.get("source_language"),
            "is_shareable": episode.get("is_shareable", False),
            "share_slug": episode.get("share_slug")
        }
    }

    res = requests.post(
        WORKER_URL,
        headers={
            "x-api-key": WORKER_API_KEY,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    if not res.ok:
        print("PUTTER STATUS:", res.status_code)
        print("PUTTER BODY:", res.text)
        print("PUTTER PAYLOAD PREVIEW:", {
            "text_preview": script[:200],
            "path": path,
            "category": category,
            "options": payload["options"],
            "episode": payload["episode"]
        })
        res.raise_for_status()

    return res.json()
