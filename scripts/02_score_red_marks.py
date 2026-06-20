from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from review_tool.red_marks import red_mark_score
from review_tool.scan import scan_photo_roots


TEST_BUCKETS = {"语文试题", "数学试题"}


def main() -> None:
    rows = []
    for record in scan_photo_roots(ROOT):
        if record.bucket not in TEST_BUCKETS:
            continue
        score = red_mark_score(Path(record.path))
        rows.append(
            {
                **asdict(record),
                "red_pixel_count": score.red_pixel_count,
                "red_ratio": round(score.red_ratio, 6),
                "has_red_mark": score.has_red_mark,
            }
        )

    out_dir = ROOT / "data" / "manifest"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "red_mark_scores.csv"
    json_path = out_dir / "red_mark_scores.json"
    fieldnames = list(rows[0].keys()) if rows else []
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    marked = sum(1 for row in rows if row["has_red_mark"])
    print(f"scored={len(rows)}")
    print(f"has_red_mark={marked}")
    print(f"csv={csv_path}")
    print(f"json={json_path}")


if __name__ == "__main__":
    main()
