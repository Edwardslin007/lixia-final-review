from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from review_tool.scan import find_duplicate_groups, scan_photo_roots, write_duplicate_report, write_manifest



def main() -> None:
    records = scan_photo_roots(ROOT)
    groups = find_duplicate_groups(records)

    manifest_dir = ROOT / "data" / "manifest"
    write_manifest(
        records,
        manifest_dir / "photos_manifest.csv",
        manifest_dir / "photos_manifest.json",
    )
    write_duplicate_report(groups, manifest_dir / "duplicate_photos.csv")

    print(f"photos={len(records)}")
    print(f"duplicate_groups={len(groups)}")
    print(f"duplicate_files={sum(len(group) for group in groups)}")
    print(f"manifest={manifest_dir / 'photos_manifest.csv'}")
    print(f"duplicates={manifest_dir / 'duplicate_photos.csv'}")


if __name__ == "__main__":
    main()
