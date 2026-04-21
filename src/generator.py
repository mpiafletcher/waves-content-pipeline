from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_story(item, category, output_language):
    # ✅ safe description fallback
    description = item.get("summary") or item.get("description") or ""

    # ✅ CLEAN prompt (single, no duplicates, no code inside)
    prompt = f"""
You are a news editor generating a premium audio-news episode.

Language: {output_language}

Create a short podcast script based on:

Title: {item.get('title', '')}
Description: {description}

Return ONLY valid JSON with:
- title
- title_internal
- caption
- script
- subtitles

Source: {item.get('url', '')}
Category: {category}

Write naturally for audio.
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        content = res.choices[0].message.content.strip()

        # 🔥 clean markdown if model wraps JSON
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        data = json.loads(content)

        return data

    except Exception as e:
        print("❌ OpenAI error:", str(e))
        return None
