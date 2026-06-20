from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from difflib import SequenceMatcher
from pathlib import Path
import csv
import json
import os
import re

import cv2
import imagehash
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR


ROOT = Path(r"D:\WPS_Share\立夏期末复习")
SRC = ROOT / "手机今晚原始照片"
OUT_CSV = ROOT / "手机照片分析.csv"
OUT_JSON = ROOT / "手机照片分析.json"

MATH_KWS = {
    "数学": 4,
    "竖式": 4,
    "验算": 4,
    "余数": 4,
    "时针": 4,
    "分针": 4,
    "秒针": 4,
    "钟面": 4,
    "计数器": 4,
    "算盘": 4,
    "平均分": 4,
    "除法": 4,
    "加法": 3,
    "减法": 3,
    "乘法": 3,
    "计算": 3,
    "算一算": 3,
    "近似数": 4,
    "千位": 4,
    "百位": 4,
    "个位": 4,
    "万位": 4,
    "分成": 2,
    "还剩": 2,
    "扎一束": 3,
    "装一盒": 3,
    "面包": 2,
    "矿泉水": 2,
    "借出本数": 3,
    "千克": 3,
    "厘米": 3,
    "米": 2,
    "元": 2,
    "角": 2,
    "分": 1,
    "秒": 2,
    "时": 2,
    "口算": 3,
    "估算": 3,
    "图形": 3,
    "周期": 3,
    "规律": 2,
    "数一数": 2,
    "读出下面各数": 5,
    "三位数": 4,
    "四位数": 4,
    "二年级下 小学数学": 8,
    "阳光同学 数学": 8,
}

CHINESE_KWS = {
    "语文": 5,
    "词语表": 5,
    "写字表": 5,
    "识字表": 5,
    "阅读提示": 5,
    "语文园地": 5,
    "口语交际": 5,
    "古诗": 4,
    "课文": 4,
    "默读课文": 5,
    "拼音": 4,
    "生字": 4,
    "默写": 5,
    "图书借阅公约": 6,
    "阅读": 2,
    "黄帝": 3,
    "喜鹊": 3,
    "雷雨": 3,
    "绝句": 3,
    "大禹治水": 4,
    "黄帝的传说": 4,
    "太空生活趣事多": 4,
    "要是你在野外迷了路": 4,
    "晓出净慈寺送林子方": 4,
    "二月春风似剪刀": 4,
    "羿射九日": 4,
    "硬笔书法纸": 4,
    "咏柳": 4,
    "目录": 4,
}

EXAM_STRONG = {
    "学校": 6,
    "班级": 6,
    "姓名": 6,
    "学号": 6,
    "密封线": 8,
    "封线": 6,
    "答题": 6,
    "试卷": 8,
    "第1页，共": 4,
    "共8页": 3,
    "共24分": 4,
    "共": 1,
    "通关": 6,
    "硬笔书法纸": 5,
    "阳光同学": 5,
    "扫描全能王创建": 5,
}

EXAM_MILD = {
    "填一填": 2,
    "选一选": 2,
    "判断": 2,
    "连一连": 2,
    "竖式": 2,
    "验算": 2,
    "默写": 2,
    "题": 1,
    "第5页，共8页": 4,
    "不 要 答 题": 6,
    "不要答题": 6,
}

BOOK_KWS = {
    "目录": 6,
    "课文": 5,
    "语文园地": 6,
    "词语表": 6,
    "写字表": 6,
    "识字表": 6,
    "阅读提示": 6,
    "口语交际": 6,
    "默读课文": 6,
    "已读": 5,
    "练一练": 4,
    "分析解答": 4,
    "读一读": 3,
    "想一想": 3,
    "观察": 2,
    "下面各数": 3,
    "图书借阅公约": 6,
    "故事": 3,
    "阅读理解": 3,
    "知识点": 4,
}

ENGINE = None


def get_engine() -> RapidOCR:
    global ENGINE
    if ENGINE is None:
        ENGINE = RapidOCR()
    return ENGINE


def norm_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    return re.sub(r"\s+", " ", text).strip()


def classify(text: str) -> tuple[str, str, float, float, float, float, float]:
    lower = text.lower()
    math_score = 0.0
    chinese_score = 0.0
    exam_score = 0.0
    book_score = 0.0

    for key, value in MATH_KWS.items():
        if key.lower() in lower:
            math_score += value
    for key, value in CHINESE_KWS.items():
        if key.lower() in lower:
            chinese_score += value
    for key, value in EXAM_STRONG.items():
        if key.lower() in lower:
            exam_score += value
    for key, value in EXAM_MILD.items():
        if key.lower() in lower:
            exam_score += value
    for key, value in BOOK_KWS.items():
        if key.lower() in lower:
            book_score += value

    digit_count = len(re.findall(r"\d", text))
    operator_count = len(re.findall(r"[+\-×x÷=><]", text))
    pinyin_count = len(re.findall(r"\b[a-z]{2,}\b", lower))

    math_score += min(digit_count / 12.0, 8) + operator_count * 0.8
    chinese_score += min(pinyin_count / 6.0, 6)

    if "语文" in text and "数学" not in text:
        chinese_score += 6
    if "数学" in text and "语文" not in text:
        math_score += 6

    subject = "数学" if math_score >= chinese_score else "语文"
    if abs(math_score - chinese_score) < 3:
        if re.search(r"词语表|写字表|识字表|语文园地|口语交际|古诗|默读课文|拼音|生字|喜鹊|黄帝", text):
            subject = "语文"
        elif re.search(r"竖式|验算|余数|时针|分针|秒针|千位|百位|个位|计数器|算盘|规律|周期|近似数", text):
            subject = "数学"

    if exam_score >= book_score + 2:
        kind = "试题"
    elif book_score >= exam_score + 2:
        kind = "课本"
    else:
        if re.search(r"学校|班级|姓名|学号|通关|试卷|硬笔书法纸|阳光同学|不要答题", text):
            kind = "试题"
        elif re.search(r"目录|语文园地|词语表|写字表|识字表|阅读提示|口语交际|默读课文|已读|练一练|分析解答", text):
            kind = "课本"
        else:
            kind = "待定"

    confidence = abs(math_score - chinese_score) + abs(exam_score - book_score)
    return (
        subject,
        kind,
        round(math_score, 2),
        round(chinese_score, 2),
        round(exam_score, 2),
        round(book_score, 2),
        round(confidence, 2),
    )


def process_one(path_str: str) -> dict:
    path = Path(path_str)
    img_bgr = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise RuntimeError(f"无法读取图片: {path}")

    height, width = img_bgr.shape[:2]
    scale = 1000.0 / max(height, width)
    if scale < 1:
        resized = cv2.resize(img_bgr, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)
    else:
        resized = img_bgr

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    pil = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
    phash = str(imagehash.phash(pil, hash_size=16))

    engine = get_engine()
    result, _ = engine(resized)
    texts: list[str] = []
    confs: list[float] = []
    if result:
        for _box, txt, conf in result:
            txt = str(txt).strip()
            if txt:
                texts.append(txt)
                confs.append(float(conf))

    text = norm_text(" ".join(texts))
    avg_conf = round(sum(confs) / len(confs), 4) if confs else 0.0
    subject, kind, math_score, chinese_score, exam_score, book_score, confidence = classify(text)

    return {
        "name": path.name,
        "path": str(path),
        "text_len": len(text),
        "text": text,
        "ocr_conf": avg_conf,
        "blur": round(blur, 2),
        "phash": phash,
        "subject": subject,
        "kind": kind,
        "category": f"{subject}{kind}" if kind != "待定" else "待定",
        "math_score": math_score,
        "chinese_score": chinese_score,
        "exam_score": exam_score,
        "book_score": book_score,
        "confidence": confidence,
    }


def hamming(left: str, right: str) -> int:
    return sum(lch != rch for lch, rch in zip(left, right))


def seconds_from_name(name: str) -> int:
    match = re.search(r"IMG_\d{8}_(\d{6})", name)
    if not match:
        return 0
    hhmmss = match.group(1)
    return int(hhmmss[:2]) * 3600 + int(hhmmss[2:4]) * 60 + int(hhmmss[4:6])


def smooth_categories(rows: list[dict]) -> None:
    for index, row in enumerate(rows):
        if row["kind"] != "待定" and row["confidence"] >= 5:
            continue

        neighbors: list[str] = []
        for candidate in rows[max(0, index - 2) : min(len(rows), index + 3)]:
            if candidate is row:
                continue
            if candidate["category"] != "待定":
                neighbors.append(candidate["category"])
        if not neighbors:
            continue

        top = max(set(neighbors), key=neighbors.count)
        if neighbors.count(top) >= 2:
            row["category"] = top
            row["subject"] = top[:2]
            row["kind"] = top[2:]


def mark_duplicates(rows: list[dict]) -> None:
    keep = [True] * len(rows)
    dup_reason = [""] * len(rows)

    seen_burst: set[str] = set()
    for index, row in enumerate(rows):
        if "_BURST" not in row["name"]:
            continue
        base = row["name"].split("_BURST")[0]
        if base in seen_burst:
            continue
        seen_burst.add(base)
        same = [pos for pos, candidate in enumerate(rows) if candidate["name"].startswith(base + "_BURST")]
        best = max(same, key=lambda pos: (rows[pos]["blur"], rows[pos]["ocr_conf"], rows[pos]["text_len"]))
        for pos in same:
            if pos == best:
                continue
            keep[pos] = False
            dup_reason[pos] = f"burst_duplicate_keep_{rows[best]['name']}"

    for index in range(1, len(rows)):
        if not keep[index] or not keep[index - 1]:
            continue

        previous = rows[index - 1]
        current = rows[index]
        if previous["category"] != current["category"] or previous["category"] == "待定":
            continue

        similarity = 0.0
        if previous["text"] and current["text"]:
            similarity = SequenceMatcher(None, previous["text"][:1500], current["text"][:1500]).ratio()
        distance = hamming(previous["phash"], current["phash"])
        gap = seconds_from_name(current["name"]) - seconds_from_name(previous["name"])

        if gap > 20:
            continue
        if not (similarity >= 0.97 or (similarity >= 0.94 and distance <= 14)):
            continue

        winner = index - 1 if (
            previous["blur"],
            previous["ocr_conf"],
            previous["text_len"],
        ) >= (
            current["blur"],
            current["ocr_conf"],
            current["text_len"],
        ) else index
        loser = index if winner == index - 1 else index - 1
        keep[loser] = False
        dup_reason[loser] = (
            f"near_duplicate_keep_{rows[winner]['name']}_"
            f"sim_{similarity:.3f}_dist_{distance}"
        )

    for index, row in enumerate(rows):
        row["keep"] = keep[index]
        row["dup_reason"] = dup_reason[index]


def main() -> None:
    files = sorted(SRC.glob("IMG_20260620_*.jpg"))
    rows: list[dict] = []

    with ProcessPoolExecutor(max_workers=min(4, os.cpu_count() or 1)) as executor:
        futures = {executor.submit(process_one, str(path)): path for path in files}
        completed = 0
        for future in as_completed(futures):
            rows.append(future.result())
            completed += 1
            if completed % 20 == 0 or completed == len(futures):
                print(f"PROGRESS {completed}/{len(futures)}", flush=True)

    rows.sort(key=lambda row: row["name"])
    smooth_categories(rows)
    mark_duplicates(rows)

    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    all_counts = Counter(row["category"] for row in rows)
    keep_counts = Counter(row["category"] for row in rows if row["keep"])
    print("ALL_COUNTS", dict(all_counts))
    print("KEEP_COUNTS", dict(keep_counts))
    print("DUP_COUNT", sum(1 for row in rows if not row["keep"]))
    print("UNCERTAIN", sum(1 for row in rows if row["category"] == "待定"))

    low_conf = [row for row in rows if row["category"] == "待定" or row["confidence"] < 5][:20]
    for row in low_conf:
        print("LOW", row["name"], row["category"], row["confidence"], row["text"][:120])


if __name__ == "__main__":
    main()
