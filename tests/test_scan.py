from pathlib import Path

from PIL import Image

from review_tool.scan import BUCKET_DIRS, find_duplicate_groups, scan_photo_roots


def make_image(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (12, 8), color).save(path)


def test_scan_photo_roots_maps_four_required_buckets(tmp_path: Path) -> None:
    for bucket_name, dirname in BUCKET_DIRS.items():
        make_image(tmp_path / dirname / f"{bucket_name}.jpg", (10, 20, 30))

    records = scan_photo_roots(tmp_path)

    assert {record.bucket for record in records} == set(BUCKET_DIRS)
    assert {record.subject for record in records} == {"语文", "数学"}
    assert {record.material_type for record in records} == {"课本", "试题"}
    assert all(record.width == 12 and record.height == 8 for record in records)
    assert all(record.sha256 for record in records)


def test_find_duplicate_groups_uses_file_hash(tmp_path: Path) -> None:
    make_image(tmp_path / BUCKET_DIRS["数学试题"] / "a.jpg", (255, 255, 255))
    duplicate_bytes = (tmp_path / BUCKET_DIRS["数学试题"] / "a.jpg").read_bytes()
    target = tmp_path / BUCKET_DIRS["语文课本"] / "b.jpg"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(duplicate_bytes)
    make_image(tmp_path / BUCKET_DIRS["语文试题"] / "c.jpg", (1, 2, 3))

    records = scan_photo_roots(tmp_path)
    groups = find_duplicate_groups(records)

    assert len(groups) == 1
    assert {record.name for record in groups[0]} == {"a.jpg", "b.jpg"}
