from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
import json

import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR


ENGINE: RapidOCR | None = None

QUALITY_KEYWORDS = {
    "小学": 5,
    "二年级": 5,
    "语文": 5,
    "数学": 5,
    "课文": 4,
    "生字": 4,
    "词语表": 4,
    "填一填": 4,
    "选一选": 4,
    "时间": 3,
    "钟面": 3,
    "竖式": 3,
    "阅读": 3,
    "题": 2,
}


@dataclass(frozen=True)
class OcrBlock:
    text: str
    confidence: float
    box: list[list[float]]


@dataclass(frozen=True)
class OcrResult:
    image_path: str
    width: int
    height: int
    scaled_width: int
    scaled_height: int
    elapsed_seconds: float
    block_count: int
    avg_confidence: float
    text: str
    blocks: list[OcrBlock]


def get_engine() -> RapidOCR:
    global ENGINE
    if ENGINE is None:
        ENGINE = RapidOCR()
    return ENGINE


def choose_best_ocr_candidate(candidates: list[dict]) -> dict:
    def score(candidate: dict) -> float:
        text = str(candidate.get("text", ""))
        avg_conf = float(candidate.get("avg_conf", candidate.get("avg_confidence", 0.0)) or 0.0)
        keyword_score = sum(value for key, value in QUALITY_KEYWORDS.items() if key in text)
        length_score = min(len(text) / 80.0, 20.0)
        return keyword_score * 2.0 + length_score + avg_conf * 4.0

    if not candidates:
        raise ValueError("candidates cannot be empty")
    return max(candidates, key=score)


def load_image(path: Path, max_side: int = 900) -> tuple[np.ndarray, int, int]:
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"无法读取图片: {path}")
    height, width = image.shape[:2]
    scale = max_side / max(height, width)
    if scale < 1:
        image = cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)
    return image, width, height


def run_ocr(path: Path, max_side: int = 900) -> OcrResult:
    image, original_width, original_height = load_image(path, max_side=max_side)
    started = perf_counter()
    raw_result, _ = get_engine()(image)
    elapsed = perf_counter() - started

    blocks: list[OcrBlock] = []
    confidences: list[float] = []
    texts: list[str] = []
    if raw_result:
        for box, text, confidence in raw_result:
            clean_text = str(text).strip()
            if not clean_text:
                continue
            conf = float(confidence)
            blocks.append(OcrBlock(text=clean_text, confidence=conf, box=[[float(x), float(y)] for x, y in box]))
            confidences.append(conf)
            texts.append(clean_text)

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    scaled_height, scaled_width = image.shape[:2]
    return OcrResult(
        image_path=str(path),
        width=original_width,
        height=original_height,
        scaled_width=scaled_width,
        scaled_height=scaled_height,
        elapsed_seconds=round(elapsed, 3),
        block_count=len(blocks),
        avg_confidence=round(avg_conf, 4),
        text="\n".join(texts),
        blocks=blocks,
    )


def write_ocr_result(result: OcrResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(result)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
