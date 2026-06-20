from review_tool.knowledge import build_markdown_document, normalize_ocr_text


def test_normalize_ocr_text_removes_extra_spaces() -> None:
    assert normalize_ocr_text("  一、  填一填。\n\n  60分  ") == "一、 填一填。\n60分"


def test_build_markdown_document_groups_pages_by_bucket() -> None:
    rows = [
        {
            "bucket": "数学试题",
            "name": "page1.jpg",
            "rel_path": "数学试题拍照/page1.jpg",
            "ocr_text": "一、填一填。\n60分=1时",
            "ocr_conf": 0.88,
        }
    ]

    markdown = build_markdown_document("数学试题", rows)

    assert markdown.startswith("# 数学试题结构化知识库")
    assert "## page1.jpg" in markdown
    assert "60分=1时" in markdown
    assert "OCR 平均置信度" in markdown
