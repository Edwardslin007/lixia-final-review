from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from review_tool.classify import classify_bucket_from_text
from review_tool.knowledge import write_knowledge_documents


MANIFEST = ROOT / "data" / "manifest" / "photos_manifest.json"
OCR_DIR = ROOT / "data" / "ocr" / "by_hash"


def main() -> None:
    records = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_hash: dict[str, list[dict]] = {}
    for record in records:
        by_hash.setdefault(record["sha256"], []).append(record)

    rows = []
    for sha, group in by_hash.items():
        ocr_path = OCR_DIR / f"{sha}.json"
        if not ocr_path.exists():
            continue
        ocr = json.loads(ocr_path.read_text(encoding="utf-8"))
        text = ocr.get("text", "")
        inferred_bucket = classify_bucket_from_text(text, group[0]["bucket"])
        record = next((candidate for candidate in group if candidate["bucket"] == inferred_bucket), group[0])
        rows.append(
            {
                **record,
                "bucket": inferred_bucket,
                "original_bucket": record["bucket"],
                "ocr_text": text,
                "ocr_conf": ocr.get("avg_confidence", 0),
                "block_count": ocr.get("block_count", 0),
            }
        )

    paths = write_knowledge_documents(rows, ROOT / "knowledge")
    print(f"rows={len(rows)}")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
