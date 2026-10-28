"""Estimated captions for UI testing; audio alignment should take precedence."""

import math


def script_subtitles(script, words_per_cue=10):
    words = (script or "").split()
    return [
        {"text": " ".join(words[i:i + words_per_cue])}
        for i in range(0, len(words), words_per_cue)
    ]


def build_timed_subtitles(subtitles, total_duration_sec, language="en", speed_multiplier=1.0):
    if not isinstance(subtitles, list):
        return []
    chunks = [
        (cue.get("text") or "").split()
        for cue in subtitles if isinstance(cue, dict)
    ]
    chunks = [words for words in chunks if words]
    word_count = sum(len(words) for words in chunks)
    if not word_count:
        return []
    try:
        duration = float(total_duration_sec)
    except (TypeError, ValueError):
        duration = 90.0
    if not math.isfinite(duration) or duration <= 0:
        duration = 90.0
    if not math.isfinite(speed_multiplier) or speed_multiplier <= 0:
        raise ValueError("speed_multiplier must be positive and finite")
    duration_ms = max(word_count, round(duration * 1000 / speed_multiplier))
    result = []
    offset = 0
    for words in chunks:
        timed_words = []
        for word in words:
            timed_words.append({
                "text": word,
                "start_ms": round(offset * duration_ms / word_count),
                "end_ms": round((offset + 1) * duration_ms / word_count),
            })
            offset += 1
        result.append({
            "text": " ".join(words),
            "start_ms": timed_words[0]["start_ms"],
            "end_ms": timed_words[-1]["end_ms"],
            "words": timed_words,
            "timing_source": "estimated",
        })
    return result
