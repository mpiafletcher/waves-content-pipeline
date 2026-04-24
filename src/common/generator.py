from openai import OpenAI
import os
import json
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "story"


def generate_story(item, category, source_language, output_language):
    description = item.get("summary") or item.get("description") or ""

    prompt = f"""
You are writing a short audio news script for a mobile news app.

Source language: {source_language}
Output language: {output_language}

You are given a news item that may be written in a different language than the final output.
Read and understand the source in its original language, then write the final script fully in the output language.

Rules:
- Start directly with the news. No greetings.
- Do NOT say things like:
  - "Welcome to today's episode"
  - "In today's episode"
  - "Today we're diving into"
  - "Let's take a look"
- The opening line must be specific and centered on the actual news.
- Sound sharp, natural, informed, and concise.
- Explain the news clearly, but do not over-explain.
- Add context only if it truly helps.
- Do not force big-picture analysis if the story does not need it.
- Do not use bullet points in the script.
- Keep it fluid for audio.
- Aim for roughly 60 to 120 seconds.
- Return ONLY valid JSON.
- The final title, caption, subtopic, script and subtitles must all be in the output language.
For free-tier episodes, the subtopic must be a short, highly informative label that helps a user instantly understand what the episode is about.

Prefer:
1. Country or place name if central to the story
2. Company or organization name if central
3. Sector + event if more useful

Good examples:
- Iran Oil
- Tesla Earnings
- Google Workspace AI
- Spain Markets
- Mexico Startups
- France Football

Avoid vague labels like:
- General News
- Current Affairs
- Market Update
- Technology Trends

Return a subtopic with 2 to 4 words max.

Story title: {item.get('title', '')}
Story description: {description}
Source URL: {item.get('url', '')}
Category: {category}

Return JSON with exactly these fields:
{{
  "title": "short user-facing title",
  "title_internal": "short internal title",
  "caption": "1 short teaser sentence",
  "subtopic": "specific_subtopic",
  "script": "full audio script",
  "estimated_duration_sec": 90,
  "subtitles": [
    {{ "text": "subtitle chunk 1" }},
    {{ "text": "subtitle chunk 2" }}
  ]
}}

Subtitle rules:
- subtitles must use the exact wording of the script
- no paraphrasing
- split naturally for pacing
- 6 to 10 chunks
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
        )

        content = res.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        data = json.loads(content)

        if not data.get("title_internal"):
            data["title_internal"] = slugify(data.get("title", item.get("title", "story")))

        if not data.get("subtopic"):
            data["subtopic"] = "general"

        if not data.get("estimated_duration_sec"):
            data["estimated_duration_sec"] = 90

        if not isinstance(data.get("subtitles"), list):
            data["subtitles"] = []

        return data

    except Exception as e:
        print("OpenAI error:", str(e))
        return None
