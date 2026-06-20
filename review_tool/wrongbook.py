from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json
import re

from review_tool.classify import classify_bucket_from_text
from review_tool.red_marks import red_mark_regions, red_mark_score


def infer_topic(subject: str, text: str) -> str:
    if subject == "数学":
        topic_rules = [
            ("时间与钟面", r"时针|分针|秒针|钟面|分钟|小时|时间"),
            ("有余数除法", r"余数|除法|平均分|每份|最多|至少"),
            ("万以内数与近似数", r"千位|百位|个位|近似数|读作|写作"),
            ("长度、质量和单位", r"厘米|分米|米|千米|克|千克"),
            ("计算与验算", r"竖式|验算|计算|加法|减法|乘法"),
            ("应用题审题", r"一共|还剩|需要|可以|大约|买|卖"),
        ]
    else:
        topic_rules = [
            ("生字词与形近字", r"生字|词语|组词|写字|形近字"),
            ("拼音与多音字", r"拼音|读音|多音字|声调"),
            ("句子与标点", r"句子|标点|连词成句|把字句|被字句"),
            ("阅读理解", r"阅读|短文|自然段|根据短文"),
            ("看图写话", r"写话|看图|图画"),
        ]
    for topic, pattern in topic_rules:
        if re.search(pattern, text):
            return topic
    return "综合易错题"


def infer_reason(subject: str, topic: str, text: str) -> str:
    if subject == "数学":
        if topic == "时间与钟面":
            return "时间单位和钟面读数容易混淆，特别是分针走几大格、几小格与经过时间的关系。"
        if topic == "计算与验算":
            return "会算但步骤不完整，容易心算跳步；需要固定写列式、竖式和验算。"
        if topic == "应用题审题":
            return "题目信息多，容易漏看关键词或没有先判断求什么。"
        return "知识点会做但细节检查不足，容易在单位、数量关系或题目条件上丢分。"
    if topic == "阅读理解":
        return "可能没有回到原文定位答案，或答题句式不完整。"
    if topic == "生字词与形近字":
        return "字词掌握基本可以，但形近字、易错笔画和词语搭配需要反复回看。"
    return "语文题容易在审题、书写、标点或答题格式上失分。"


def detailed_solution(subject: str, topic: str) -> str:
    if subject == "数学":
        return "\n".join(
            [
                "1. 读题：先圈出题目中的数字、单位和关键词，例如“一共、还剩、经过、每份、最多、至少”。",
                "2. 判断：用一句话说清楚这道题要求什么，避免只看数字就计算。",
                "3. 列式：把数量关系写成算式，不允许只在脑子里算。",
                "4. 竖式草稿：需要计算时必须在草稿区列竖式。",
                "   ```text",
                "   列式：__________",
                "   竖式：",
                "       ______",
                "   验算：__________",
                "   答：__________",
                "   ```",
                "5. 检查：看单位是否一致，答案是否回答了问题，钟面题要再看一次时针和分针的位置。",
                "6. 下次提醒：宁愿多写一步，也不要心算跳步；期末考试里会做的题最怕因为省草稿丢分。",
            ]
        )
    return "\n".join(
        [
            "1. 读题：先用手指读完整题目，圈出“选正确、选错误、填序号、用原文回答”等要求。",
            "2. 定位：阅读题必须回到原文找句子，不凭印象答。",
            "3. 书写：生字词题先想结构和易错笔画，再下笔。",
            "4. 格式：需要完整句子的题，要写成通顺的一句话；需要标点时检查句号、问号、感叹号。",
            "5. 检查：最后默读一遍答案，看有没有漏字、错别字、拼音声调或标点错误。",
        ]
    )


def load_canonical_records(root: Path) -> list[dict]:
    manifest = json.loads((root / "data" / "manifest" / "photos_manifest.json").read_text(encoding="utf-8"))
    by_hash: dict[str, list[dict]] = {}
    for record in manifest:
        by_hash.setdefault(record["sha256"], []).append(record)

    rows = []
    for sha, group in by_hash.items():
        ocr_path = root / "data" / "ocr" / "by_hash" / f"{sha}.json"
        if not ocr_path.exists():
            continue
        ocr = json.loads(ocr_path.read_text(encoding="utf-8"))
        text = ocr.get("text", "")
        bucket = classify_bucket_from_text(text, group[0]["bucket"])
        record = next((candidate for candidate in group if candidate["bucket"] == bucket), group[0])
        rows.append({**record, "bucket": bucket, "original_bucket": record["bucket"], "ocr": ocr})
    return rows


def build_wrong_items(root: Path, min_ratio: float = 0.0012) -> list[dict]:
    items = []
    for record in load_canonical_records(root):
        if not str(record.get("original_bucket", record["bucket"])).endswith("试题"):
            continue
        path = Path(record["path"])
        score = red_mark_score(path, min_ratio=min_ratio, min_pixels=9000)
        if not score.has_red_mark:
            continue
        subject = record["bucket"][:2]
        text = str(record["ocr"].get("text", ""))
        topic = infer_topic(subject, text)
        regions = [asdict(region) for region in red_mark_regions(path)]
        excerpt = "\n".join(text.splitlines()[:80])
        items.append(
            {
                "id": f"{subject}-{len(items)+1:03d}",
                "subject": subject,
                "bucket": record["bucket"],
                "name": record["name"],
                "path": record["path"],
                "rel_path": record["rel_path"],
                "red_ratio": round(score.red_ratio, 6),
                "red_pixel_count": score.red_pixel_count,
                "regions": regions[:8],
                "topic": topic,
                "reason": infer_reason(subject, topic, text),
                "excerpt": excerpt,
                "solution": detailed_solution(subject, topic),
            }
        )
    return items


def build_wrongbook_markdown(subject: str, items: list[dict], enhanced: bool = False) -> str:
    subject_items = [item for item in items if item["subject"] == subject]
    topic_counts: dict[str, int] = {}
    for item in subject_items:
        topic_counts[item["topic"]] = topic_counts.get(item["topic"], 0) + 1

    lines = [
        f"# {subject}错题集{'加强版' if enhanced else ''}",
        "",
        "## 错题分析报告",
        "",
        f"- 候选错题页/片段数量：{len(subject_items)}",
        f"- 高频错题类型：{', '.join(f'{k} {v}题' for k, v in sorted(topic_counts.items(), key=lambda kv: kv[1], reverse=True)) or '暂无'}",
        "- 识别依据：红色问号、红叉、红圈、红色订正痕迹和红笔批改区域。",
        "- 重要说明：自动识别结果已尽量保守，仍建议打印后人工确认具体小题。",
        "",
        "## 期末考试一定要注意",
        "",
    ]
    if subject == "数学":
        lines.extend(
            [
                "1. 每道应用题先圈关键词，再列式，不要直接心算。",
                "2. 计算题必须写竖式或草稿，尤其是进位、退位、带余数和时间换算。",
                "3. 答案要带单位，应用题最后写“答”。",
                "4. 做完后用验算或估算检查一次，防止会做但写错。",
            ]
        )
    else:
        lines.extend(
            [
                "1. 看清题目是写汉字、拼音、序号还是完整句子。",
                "2. 阅读题必须回原文定位，不凭感觉写。",
                "3. 检查错别字、标点和漏字。",
                "4. 看图写话要有时间、地点、人物、事情，句子要完整。",
            ]
        )
    lines.append("")

    for item in subject_items:
        lines.extend(
            [
                f"## {item['id']} {item['topic']} - {item['name']}",
                "",
                f"- 来源：`{item['rel_path']}`",
                f"- 红笔比例：`{item['red_ratio']}`",
                f"- 错因归纳：{item['reason']}",
                "",
                "### OCR 识别片段",
                "",
                "```text",
                item["excerpt"],
                "```",
                "",
            ]
        )
        if enhanced:
            lines.extend(["### 详细解题过程", "", item["solution"], ""])
    return "\n".join(lines)
