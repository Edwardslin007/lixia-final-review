from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class RedMarkScore:
    red_pixel_count: int
    red_ratio: float
    has_red_mark: bool


@dataclass(frozen=True)
class RedMarkRegion:
    x: int
    y: int
    width: int
    height: int
    area: int


def load_red_mask(path: Path, max_side: int | None = None) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"无法读取图片: {path}")
    if max_side:
        height, width = image.shape[:2]
        scale = max_side / max(height, width)
        if scale < 1:
            image = cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red_a = np.array([0, 70, 55])
    upper_red_a = np.array([12, 255, 255])
    lower_red_b = np.array([165, 70, 55])
    upper_red_b = np.array([180, 255, 255])
    mask = cv2.inRange(hsv, lower_red_a, upper_red_a) | cv2.inRange(hsv, lower_red_b, upper_red_b)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


def red_mark_score(path: Path, min_ratio: float = 0.003, min_pixels: int = 120) -> RedMarkScore:
    mask = load_red_mask(path)
    red_pixels = int(np.count_nonzero(mask))
    total_pixels = int(mask.shape[0] * mask.shape[1])
    ratio = red_pixels / total_pixels if total_pixels else 0.0
    return RedMarkScore(
        red_pixel_count=red_pixels,
        red_ratio=ratio,
        has_red_mark=red_pixels >= min_pixels and ratio >= min_ratio,
    )


def red_mark_regions(path: Path, max_side: int = 900, min_area: int = 60) -> list[RedMarkRegion]:
    mask = load_red_mask(path, max_side=max_side)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions: list[RedMarkRegion] = []
    for contour in contours:
        area = int(cv2.contourArea(contour))
        if area < min_area:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        regions.append(RedMarkRegion(x=x, y=y, width=width, height=height, area=area))
    return sorted(regions, key=lambda region: region.area, reverse=True)
