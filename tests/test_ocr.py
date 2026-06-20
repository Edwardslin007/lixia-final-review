from review_tool.ocr import choose_best_ocr_candidate


def test_choose_best_ocr_candidate_prefers_keyword_rich_text() -> None:
    candidates = [
        {"rotation": 0, "text": "姓名 班级 一些零散文字", "avg_conf": 0.95, "items": []},
        {"rotation": 270, "text": "小学数学 二年级下 时间在哪里 填一填 选一选", "avg_conf": 0.88, "items": []},
    ]

    selected = choose_best_ocr_candidate(candidates)

    assert selected["rotation"] == 270


def test_choose_best_ocr_candidate_uses_text_length_when_quality_close() -> None:
    candidates = [
        {"rotation": 0, "text": "语文 生字", "avg_conf": 0.9, "items": []},
        {"rotation": 270, "text": "语文 生字 词语表 课文 阅读 复习", "avg_conf": 0.85, "items": []},
    ]

    selected = choose_best_ocr_candidate(candidates)

    assert selected["rotation"] == 270
