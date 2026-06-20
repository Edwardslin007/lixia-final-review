from review_tool.textbook_map import textbook_map_data


def test_textbook_map_has_chinese_and_math_units_in_order() -> None:
    data = textbook_map_data()

    assert [subject["name"] for subject in data["subjects"]] == ["语文", "数学"]
    assert data["subjects"][0]["units"][0]["title"] == "第一单元 阅读：春天与成长"
    assert data["subjects"][1]["units"][0]["title"] == "第一单元 有余数的除法"


def test_textbook_map_math_includes_vertical_calculation_habit() -> None:
    data = textbook_map_data()
    math = data["subjects"][1]
    joined = " ".join(math["exam_moves"] + math["risk_points"])

    assert "竖式" in joined
    assert "验算" in joined


def test_textbook_map_units_include_detailed_sections() -> None:
    data = textbook_map_data()
    units = [unit for subject in data["subjects"] for unit in subject["units"]]

    assert all(len(unit["details"]) >= 3 for unit in units)
    assert "《村居》《咏柳》会背、会默写重点诗句" in units[0]["details"][0]["items"]
    assert "1时=60分，1分=60秒" in units[9]["details"][0]["items"]
