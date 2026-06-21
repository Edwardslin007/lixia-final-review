from __future__ import annotations

import json

from review_tool.site import render_site, render_sprint_system, sanitize_text, subject_outline


def test_sanitize_text_removes_student_identity_lines() -> None:
    text = "学校：Q\n班级：二（6）\n姓名：小朋友\n学号：30\n一、填一填。"

    sanitized = sanitize_text(text)

    assert "学校" not in sanitized
    assert "姓名" not in sanitized
    assert "学号" not in sanitized
    assert "一、填一填。" in sanitized


def test_subject_outline_contains_math_draft_requirement() -> None:
    outline = subject_outline("数学")

    assert "竖式" in "\n".join(outline["must_do"])


def test_render_sprint_system_includes_training_closure(tmp_path) -> None:
    wrongbook = tmp_path / "wrongbook"
    wrongbook.mkdir()
    (wrongbook / "wrong_items.json").write_text(
        json.dumps(
            [
                {
                    "subject": "数学",
                    "topic": "时间与钟面",
                    "name": "m.jpg",
                    "rel_path": "数学试题拍照\\m.jpg",
                    "excerpt": "9:50 到 10:20",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / "knowledge").mkdir()

    render_sprint_system(tmp_path, tmp_path / "docs")

    html = (tmp_path / "docs" / "sprint" / "index.html").read_text(encoding="utf-8")

    assert "错题优先，课本兜底" in html
    assert "9:50 到 10:20" in html
    assert "竖式草稿" in html
    assert "回原文定位" in html
    assert '<link rel="icon" href="data:,">' in html


def test_render_site_removes_legacy_public_routes(tmp_path) -> None:
    docs = tmp_path / "docs"
    for route in ["textbook-map", "wrongbook", "outline", "knowledge", "downloads"]:
        path = docs / route
        path.mkdir(parents=True)
        (path / "index.html").write_text("legacy", encoding="utf-8")
    (tmp_path / "wrongbook").mkdir()
    (tmp_path / "wrongbook" / "wrong_items.json").write_text("[]", encoding="utf-8")
    (tmp_path / "knowledge").mkdir()

    render_site(tmp_path)

    assert (docs / "sprint" / "index.html").exists()
    assert not (docs / "textbook-map").exists()
    assert not (docs / "wrongbook").exists()
    assert not (docs / "outline").exists()
    assert not (docs / "knowledge").exists()
    assert not (docs / "downloads").exists()
