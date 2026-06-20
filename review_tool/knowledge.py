from __future__ import annotations

from pathlib import Path
import re


def normalize_ocr_text(text: str) -> str:
    lines = []
    for raw_line in text.replace("\u3000", " ").splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def build_markdown_document(bucket: str, rows: list[dict]) -> str:
    lines = [
        f"# {bucket}结构化知识库",
        "",
        "> 说明：本文档由照片 OCR 自动生成，保留原始图片编号和 OCR 置信度。手写文字、红笔批改、反光区域可能存在误识别，需要人工复核。",
        "",
    ]
    for row in rows:
        text = normalize_ocr_text(str(row.get("ocr_text", "")))
        lines.extend(
            [
                f"## {row.get('name', '')}",
                "",
                f"- 来源：`{row.get('rel_path', '')}`",
                f"- OCR 平均置信度：`{row.get('ocr_conf', 0)}`",
                "",
                "```text",
                text or "（未识别到文字）",
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def write_knowledge_documents(rows: list[dict], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for bucket in ["语文课本", "语文试题", "数学课本", "数学试题"]:
        bucket_rows = [row for row in rows if row.get("bucket") == bucket]
        markdown = build_markdown_document(bucket, bucket_rows)
        path = output_dir / f"{bucket}知识库.md"
        path.write_text(markdown, encoding="utf-8")
        paths.append(path)
    return paths
