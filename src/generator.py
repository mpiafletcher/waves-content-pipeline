import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_story(item, category, output_language):
    prompt = f"""
You are generating a premium audio-news episode.

Language: {output_language}

Story title: {item['title']}
Story description: {item['description']}
Source: {item['url']}
Category: {category}

Write naturally for audio.

Guidelines:
- Focus on clarity and storytelling
- Include context ONLY if it adds value
- Do NOT force implications or analysis if not needed
- Keep it engaging but concise

Return JSON:
{{
  "title": "...",
  "title_internal": "...",
  "caption": "...",
  "subtopic": "...",
  "script": "...",
  "estimated_duration_sec": 120,
  "subtitles": []
}}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return res.choices[0].message.content
