from review_tool.site import render_textbook_map, sanitize_text, subject_outline


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


def test_render_textbook_map_includes_detailed_points(tmp_path) -> None:
    render_textbook_map(tmp_path)

    html = (tmp_path / "textbook-map" / "index.html").read_text(encoding="utf-8")

    assert "细化考点" in html
    assert "《村居》《咏柳》会背、会默写重点诗句" in html
    assert "1时=60分，1分=60秒" in html
    assert '<link rel="icon" href="data:,">' in html
