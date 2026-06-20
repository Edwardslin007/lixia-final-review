from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from review_tool.site import render_site


def main() -> None:
    render_site(ROOT)
    print(ROOT / "docs" / "index.html")
    print(ROOT / "docs" / "wrongbook" / "index.html")
    print(ROOT / "docs" / "outline" / "index.html")


if __name__ == "__main__":
    main()
