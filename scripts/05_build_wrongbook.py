from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from review_tool.wrongbook import build_wrong_items, build_wrongbook_markdown


def main() -> None:
    items = build_wrong_items(ROOT)
    out_dir = ROOT / "wrongbook"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "wrong_items.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    for subject in ["语文", "数学"]:
        (out_dir / f"{subject}错题集.md").write_text(
            build_wrongbook_markdown(subject, items, enhanced=False),
            encoding="utf-8",
        )
        (out_dir / f"{subject}错题集加强版.md").write_text(
            build_wrongbook_markdown(subject, items, enhanced=True),
            encoding="utf-8",
        )
    print(f"wrong_items={len(items)}")
    print(out_dir)


if __name__ == "__main__":
    main()
