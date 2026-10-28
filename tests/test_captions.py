import unittest

from common.captions import build_timed_subtitles, script_subtitles


class CaptionTests(unittest.TestCase):
    def test_script_is_preserved_in_small_cues(self):
        script = "One two three four five six seven eight nine ten eleven."
        cues = script_subtitles(script)
        self.assertEqual(len(cues), 2)
        self.assertEqual(" ".join(c["text"] for c in cues), script)

    def test_word_timings_cover_duration_without_gaps(self):
        cues = build_timed_subtitles(script_subtitles("Hello world. Next story."), 6, speed_multiplier=1.5)
        words = [w for c in cues for w in c["words"]]
        self.assertEqual(words[0]["start_ms"], 0)
        self.assertEqual(words[-1]["end_ms"], 4000)
        self.assertTrue(all(a["end_ms"] == b["start_ms"] for a, b in zip(words, words[1:])))
        self.assertEqual(cues[0]["timing_source"], "estimated")

    def test_different_cue_lengths_receive_proportional_time(self):
        cues = build_timed_subtitles([{"text": "One two three"}, {"text": "Four"}], 4)
        self.assertEqual(cues[0]["end_ms"], 3000)
        self.assertEqual(cues[1]["start_ms"], 3000)

    def test_empty_script(self):
        self.assertEqual(build_timed_subtitles(script_subtitles(""), 90), [])

    def test_invalid_duration_uses_fallback(self):
        for duration in (None, "invalid", -1, float("nan")):
            with self.subTest(duration=duration):
                self.assertEqual(build_timed_subtitles([{"text": "Hola"}], duration)[0]["end_ms"], 90000)

    def test_invalid_speed_is_rejected(self):
        with self.assertRaises(ValueError):
            build_timed_subtitles([{"text": "Hello"}], 90, speed_multiplier=0)


if __name__ == "__main__":
    unittest.main()
