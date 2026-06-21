from __future__ import annotations

import json

from review_tool.sprint_system import build_sprint_review_data, summarize_wrong_topics


def test_summarize_wrong_topics_counts_subject_topics() -> None:
    items = [
        {"subject": "数学", "topic": "时间与钟面", "name": "m1.jpg", "excerpt": "9:50 到 10:20"},
        {"subject": "数学", "topic": "时间与钟面", "name": "m2.jpg", "excerpt": "75分"},
        {"subject": "语文", "topic": "阅读理解", "name": "c1.jpg", "excerpt": "为什么"},
    ]

    summary = summarize_wrong_topics(items)

    assert summary["数学"][0]["topic"] == "时间与钟面"
    assert summary["数学"][0]["count"] == 2
    assert summary["语文"][0]["topic"] == "阅读理解"


def test_build_sprint_review_data_turns_materials_into_training_system(tmp_path) -> None:
    wrongbook = tmp_path / "wrongbook"
    wrongbook.mkdir()
    (wrongbook / "wrong_items.json").write_text(
        json.dumps(
            [
                {
                    "subject": "数学",
                    "topic": "时间与钟面",
                    "name": "math-time.jpg",
                    "rel_path": "数学试题拍照\\math-time.jpg",
                    "excerpt": "姓名：小朋友\n9:50 到 10:20 经过多少分\n75分=多少时多少分",
                },
                {
                    "subject": "数学",
                    "topic": "计算与验算",
                    "name": "math-calc.jpg",
                    "rel_path": "数学试题拍照\\math-calc.jpg",
                    "excerpt": "306-128 列竖式计算并验算",
                },
                {
                    "subject": "语文",
                    "topic": "阅读理解",
                    "name": "chinese-reading.jpg",
                    "rel_path": "语文试题拍照\\chinese-reading.jpg",
                    "excerpt": "根据短文回答：从哪里看出春天来了？",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    (knowledge / "数学课本知识库.md").write_text(
        "## 时间\n1时=60分，1分=60秒。经过时间先算到整点。\n",
        encoding="utf-8",
    )
    (knowledge / "语文课本知识库.md").write_text(
        "## 阅读\n《找春天》小草、野花、嫩芽、小溪。\n",
        encoding="utf-8",
    )

    data = build_sprint_review_data(tmp_path)
    math_modules = data["subjects"][1]["modules"]
    chinese_modules = data["subjects"][0]["modules"]

    assert len(data["five_day_plan"]) == 5
    assert data["wrong_topic_summary"]["数学"][0]["topic"] == "时间与钟面"
    assert any("9:50 到 10:20" in example["steps"] for module in math_modules for example in module["worked_examples"])
    assert any("竖式草稿" in routine for module in math_modules for routine in module["routines"])
    assert any("回原文定位" in routine for module in chinese_modules for routine in module["routines"])
    assert "姓名" not in json.dumps(data, ensure_ascii=False)
