from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable
import csv
import json

from PIL import Image


BUCKET_DIRS: dict[str, str] = {
    "语文课本": "语文课本拍照",
    "语文试题": "语文试题拍照",
    "数学课本": "数学课本拍照",
    "数学试题": "数学试题拍照",
}


@dataclass(frozen=True)
class PhotoRecord:
    id: str
    bucket: str
    subject: str
    material_type: str
    name: str
    path: str
    rel_path: str
    extension: str
    size_bytes: int
    sha256: str
    width: int
    height: int


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def iter_photo_files(root: Path) -> Iterable[tuple[str, Path]]:
    for bucket, dirname in BUCKET_DIRS.items():
        bucket_root = root / dirname
        if not bucket_root.exists():
            continue
        for path in sorted(bucket_root.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                yield bucket, path


def scan_photo_roots(root: Path) -> list[PhotoRecord]:
    records: list[PhotoRecord] = []
    for index, (bucket, path) in enumerate(iter_photo_files(root), start=1):
        width, height = image_size(path)
        subject = bucket[:2]
        material_type = bucket[2:]
        digest = file_sha256(path)
        records.append(
            PhotoRecord(
                id=f"{index:04d}_{bucket}_{path.stem}",
                bucket=bucket,
                subject=subject,
                material_type=material_type,
                name=path.name,
                path=str(path),
                rel_path=str(path.relative_to(root)),
                extension=path.suffix.lower(),
                size_bytes=path.stat().st_size,
                sha256=digest,
                width=width,
                height=height,
            )
        )
    return records


def find_duplicate_groups(records: Iterable[PhotoRecord]) -> list[list[PhotoRecord]]:
    by_hash: dict[str, list[PhotoRecord]] = {}
    for record in records:
        by_hash.setdefault(record.sha256, []).append(record)
    return [group for group in by_hash.values() if len(group) > 1]


def write_manifest(records: list[PhotoRecord], csv_path: Path, json_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(record) for record in records]
    fieldnames = list(rows[0].keys()) if rows else list(PhotoRecord.__dataclass_fields__.keys())
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def write_duplicate_report(groups: list[list[PhotoRecord]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for group_index, group in enumerate(groups, start=1):
        for record in group:
            rows.append(
                {
                    "duplicate_group": group_index,
                    "bucket": record.bucket,
                    "name": record.name,
                    "path": record.path,
                    "sha256": record.sha256,
                }
            )
    fieldnames = ["duplicate_group", "bucket", "name", "path", "sha256"]
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
