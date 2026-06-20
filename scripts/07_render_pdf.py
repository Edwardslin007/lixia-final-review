from __future__ import annotations

from pathlib import Path
from shutil import copy2
import sys

import markdown
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from review_tool.site import sanitize_text


PDF_CSS = """
@page { size: A4; margin: 16mm 14mm; }
body { font-family: "Microsoft YaHei", "Noto Sans CJK SC", sans-serif; color: #17211b; line-height: 1.55; }
h1 { font-size: 28px; border-bottom: 2px solid #17211b; padding-bottom: 8px; }
h2 { font-size: 20px; break-after: avoid; margin-top: 22px; }
h3 { font-size: 15px; margin-top: 14px; }
pre { white-space: pre-wrap; word-break: break-word; background: #f4f1e7; border: 1px solid #d8d8ce; padding: 10px; border-radius: 4px; font-size: 11px; }
li { margin: 4px 0; }
code { white-space: pre-wrap; }
"""


def render_one(md_path: Path, pdf_path: Path) -> None:
    text = sanitize_text(md_path.read_text(encoding="utf-8"))
    body = markdown.markdown(text, extensions=["fenced_code", "tables"])
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{PDF_CSS}</style></head><body>{body}</body></html>"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri(), wait_until="load")
        page.pdf(path=str(pdf_path), format="A4", print_background=True)
        browser.close()


def main() -> None:
    sources = [
        ROOT / "wrongbook" / "语文错题集.md",
        ROOT / "wrongbook" / "数学错题集.md",
        ROOT / "wrongbook" / "语文错题集加强版.md",
        ROOT / "wrongbook" / "数学错题集加强版.md",
    ]
    for source in sources:
        target = ROOT / "wrongbook" / "pdf" / f"{source.stem}.pdf"
        render_one(source, target)
        public_dir = ROOT / "docs" / "downloads"
        public_dir.mkdir(parents=True, exist_ok=True)
        public_target = public_dir / target.name
        copy2(target, public_target)
        print(target)
    links = []
    for pdf_path in sorted((ROOT / "docs" / "downloads").glob("*.pdf")):
        links.append(f'<a class="tile" href="{pdf_path.name}">{pdf_path.stem}</a>')
    index = (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>打印 PDF</title><link rel='stylesheet' href='../assets/site.css'></head>"
        "<body><header class='topbar'><a href='../index.html'>首页</a><a href='../wrongbook/index.html'>错题集</a></header>"
        "<main class='layout'><section class='page-head'><p class='eyebrow'>Print</p><h1>打印 PDF</h1>"
        "<p>普通版适合孩子重做，加强版适合家长讲解。</p></section>"
        f"<section class='tile-grid'>{''.join(links)}</section></main></body></html>"
    )
    (ROOT / "docs" / "downloads" / "index.html").write_text(index, encoding="utf-8")


if __name__ == "__main__":
    main()
