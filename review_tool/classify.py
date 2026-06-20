from __future__ import annotations


MATH_KEYWORDS = {
    "数学": 6,
    "填一填": 2,
    "选一选": 2,
    "竖式": 5,
    "验算": 5,
    "时针": 5,
    "分针": 5,
    "秒针": 5,
    "钟面": 5,
    "厘米": 3,
    "千米": 3,
    "千克": 3,
    "余数": 4,
    "除法": 4,
    "加法": 3,
    "减法": 3,
    "乘法": 3,
    "计算": 3,
    "应用题": 3,
}

CHINESE_KEYWORDS = {
    "语文": 8,
    "课文": 5,
    "识字": 5,
    "词语表": 7,
    "写字表": 7,
    "生字": 5,
    "拼音": 4,
    "阅读": 4,
    "古诗": 5,
    "语文园地": 8,
    "口语交际": 6,
    "看图写话": 5,
}

TEST_KEYWORDS = {
    "学校": 4,
    "班级": 4,
    "姓名": 4,
    "学号": 4,
    "答题": 5,
    "试卷": 6,
    "共": 1,
    "分）": 2,
    "填一填": 2,
    "选一选": 2,
    "判断": 2,
    "连一连": 2,
}

BOOK_KEYWORDS = {
    "目录": 6,
    "课文": 5,
    "练一练": 4,
    "语文园地": 6,
    "词语表": 6,
    "写字表": 6,
    "识字表": 6,
    "阅读提示": 5,
    "教材": 3,
    "第": 1,
}


def keyword_score(text: str, weights: dict[str, int]) -> int:
    return sum(value for key, value in weights.items() if key in text)


def classify_bucket_from_text(text: str, fallback_bucket: str) -> str:
    math_score = keyword_score(text, MATH_KEYWORDS)
    chinese_score = keyword_score(text, CHINESE_KEYWORDS)
    test_score = keyword_score(text, TEST_KEYWORDS)
    book_score = keyword_score(text, BOOK_KEYWORDS)

    subject = "数学" if math_score > chinese_score else "语文"
    if abs(math_score - chinese_score) <= 2:
        subject = fallback_bucket[:2]

    material_type = "试题" if test_score > book_score + 1 else "课本"
    if abs(test_score - book_score) <= 1:
        material_type = fallback_bucket[2:]

    return subject + material_type
