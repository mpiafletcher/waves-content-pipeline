import json
from datetime import datetime


def sql_escape(value: str) -> str:
    return value.replace("'", "''")


def build_subtitles_update_sql(episodes_with_subtitles):
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    filename = f"subtitles_updates_{timestamp}.sql"

    lines = ["BEGIN;", ""]

    for ep in episodes_with_subtitles:
        dedupe_key = ep["dedupe_key"]
        subtitles_json = json.dumps(ep["subtitles_json"], ensure_ascii=False)

        lines.append(
            f"UPDATE episodes\n"
            f"SET subtitles_json = '{sql_escape(subtitles_json)}'::jsonb\n"
            f"WHERE dedupe_key = '{sql_escape(dedupe_key)}';\n"
        )

    lines.append("COMMIT;")
    lines.append("")

    return filename, "\n".join(lines)
