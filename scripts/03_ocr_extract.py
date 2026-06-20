from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from review_tool.ocr import run_ocr, write_ocr_result


MANIFEST = ROOT / "data" / "manifest" / "photos_manifest.json"
OUT_DIR = ROOT / "data" / "ocr" / "by_hash"


def process_one(item: dict) -> str:
    sha = item["sha256"]
    out_path = OUT_DIR / f"{sha}.json"
    if out_path.exists():
        return f"SKIP {item['name']}"
    result = run_ocr(Path(item["path"]), max_side=900)
    write_ocr_result(result, out_path)
    return f"OK {item['name']} blocks={result.block_count} seconds={result.elapsed_seconds}"


def main() -> None:
    records = json.loads(MANIFEST.read_text(encoding="utf-8"))
    seen: set[str] = set()
    unique_records = []
    for record in records:
        if record["sha256"] in seen:
            continue
        seen.add(record["sha256"])
        unique_records.append(record)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    workers = max(1, min(2, os.cpu_count() or 1))
    print(f"unique_images={len(unique_records)} workers={workers}", flush=True)
    completed = 0
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_one, record) for record in unique_records]
        for future in as_completed(futures):
            completed += 1
            print(f"[{completed}/{len(futures)}] {future.result()}", flush=True)


if __name__ == "__main__":
    main()
