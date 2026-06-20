from pathlib import Path

from PIL import Image, ImageDraw

from review_tool.red_marks import red_mark_regions, red_mark_score


def test_red_mark_score_detects_red_teacher_marks(tmp_path: Path) -> None:
    path = tmp_path / "marked.jpg"
    image = Image.new("RGB", (100, 100), "white")
    draw = ImageDraw.Draw(image)
    draw.line((10, 10, 90, 90), fill=(230, 0, 0), width=6)
    image.save(path)

    score = red_mark_score(path)

    assert score.red_pixel_count > 400
    assert score.red_ratio > 0.04
    assert score.has_red_mark is True


def test_red_mark_score_ignores_black_printed_text(tmp_path: Path) -> None:
    path = tmp_path / "clean.jpg"
    image = Image.new("RGB", (100, 100), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 10, 90, 30), fill=(0, 0, 0))
    image.save(path)

    score = red_mark_score(path)

    assert score.red_pixel_count == 0
    assert score.has_red_mark is False


def test_red_mark_regions_returns_bounding_boxes(tmp_path: Path) -> None:
    path = tmp_path / "circle.jpg"
    image = Image.new("RGB", (120, 120), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((25, 30, 90, 95), outline=(240, 0, 0), width=8)
    image.save(path)

    regions = red_mark_regions(path)

    assert regions
    region = regions[0]
    assert region.x <= 30
    assert region.y <= 35
    assert region.width >= 55
    assert region.height >= 55
