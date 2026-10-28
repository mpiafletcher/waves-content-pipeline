
# Waves content pipeline

## Caption testing

Free and premium episodes include caption text derived locally from the generated
script, with estimated word timings. No additional model request is made. Cues are
marked `timing_source: estimated`; these support UI testing, not accurate audio
alignment. The current duration/speed estimate can drift from actual speech.
Audio-worker captions take precedence in the free-tier SQL artifact when returned.
The audio worker/Make integration must persist `episode.subtitles_json` for the
app to display captions; verify this after the scheduled run. Existing episodes
are not backfilled.

Run offline checks with `PYTHONPATH=src python3 -m unittest discover -s tests`.
