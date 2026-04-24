import math


REQUIRED_EPISODE_FIELDS = [
    "tier",
    "category_id",
    "title",
    "title_internal",
    "caption",
    "duration_sec",
    "score",
    "source_url",
    "source_name",
    "digest_date",
    "status",
    "region",
    "topic",
    "subtopic",
    "segment_key",
    "dedupe_key",
    "source_language",
    "language",
    "subtitles_json",
    "is_shareable",
    "share_slug",
]


def validate_subtitles_json(subtitles_json):
    if not isinstance(subtitles_json, list):
        raise ValueError("subtitles_json must be a list")

    prev_end = 0.0

    for i, item in enumerate(subtitles_json):
        if not isinstance(item, dict):
            raise ValueError(f"subtitles_json[{i}] must be an object")

        if "text" not in item:
            raise ValueError(f"subtitles_json[{i}] missing text")
        if "start_ms" not in item:
            raise ValueError(f"subtitles_json[{i}] missing start_ms")
        if "end_ms" not in item:
            raise ValueError(f"subtitles_json[{i}] missing end_ms")

        text = item["text"]
        start_ms = item["start_ms"]
        end_ms = item["end_ms"]

        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"subtitles_json[{i}].text must be a non-empty string")

        if not isinstance(start_ms, (int, float)):
            raise ValueError(f"subtitles_json[{i}].start_ms must be numeric")

        if not isinstance(end_ms, (int, float)):
            raise ValueError(f"subtitles_json[{i}].end_ms must be numeric")

        if math.isnan(start_ms) or math.isnan(end_ms):
            raise ValueError(f"subtitles_json[{i}] has NaN timing")

        if start_ms < 0 or end_ms < 0:
            raise ValueError(f"subtitles_json[{i}] has negative timing")

        if end_ms <= start_ms:
            raise ValueError(f"subtitles_json[{i}] end_ms must be greater than start_ms")

        if i > 0 and start_ms < prev_end:
            raise ValueError(f"subtitles_json[{i}] starts before previous subtitle ends")

        prev_end = end_ms


def validate_episode(episode):
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dict")

    for field in REQUIRED_EPISODE_FIELDS:
        if field not in episode:
            raise ValueError(f"episode missing required field: {field}")

    if not isinstance(episode["duration_sec"], (int, float)):
        raise ValueError("episode.duration_sec must be numeric")

    if not isinstance(episode["score"], (int, float)):
        raise ValueError("episode.score must be numeric")

    if not isinstance(episode["is_shareable"], bool):
        raise ValueError("episode.is_shareable must be boolean")

    validate_subtitles_json(episode["subtitles_json"])


def validate_tts_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict")

    required = ["text", "path", "category", "subtitles_json", "options", "episode"]
    for field in required:
        if field not in payload:
            raise ValueError(f"payload missing required field: {field}")

    if not isinstance(payload["text"], str) or not payload["text"].strip():
        raise ValueError("payload.text must be a non-empty string")

    if not isinstance(payload["path"], str) or not payload["path"].strip():
        raise ValueError("payload.path must be a non-empty string")

    if not isinstance(payload["category"], str) or not payload["category"].strip():
        raise ValueError("payload.category must be a non-empty string")

    if not isinstance(payload["options"], dict):
        raise ValueError("payload.options must be a dict")

    for opt in ["voice", "language", "engine"]:
        if opt not in payload["options"]:
            raise ValueError(f"payload.options missing {opt}")

    validate_subtitles_json(payload["subtitles_json"])
    validate_episode(payload["episode"])
