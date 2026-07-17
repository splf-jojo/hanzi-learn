from __future__ import annotations

from typing import Any

from ..schemas.images import OcrBoxOut
from .geometry import (
    bbox_from_polygon,
    clamp01,
    normalize_polygon,
    polygon_from_axis_box,
    safe_float,
    to_plain_list,
)


def parse_paddle_result(raw_result: Any, width: int, height: int) -> list[OcrBoxOut]:
    boxes: list[OcrBoxOut] = []
    for result in iter_paddle_results(raw_result):
        if is_structured_paddle_result(result):
            parsed_lines = parse_structured_paddle_result(result)
        else:
            parsed = parse_legacy_paddle_line(result)
            parsed_lines = [parsed] if parsed is not None else []

        for parsed in parsed_lines:
            if parsed is None:
                continue
            points, text, confidence = parsed
            if not text.strip():
                continue
            polygon = normalize_polygon(points, width, height)
            if not polygon:
                continue
            boxes.append(
                OcrBoxOut(
                    id=f"box_{len(boxes) + 1}",
                    text=text.strip(),
                    confidence=clamp01(confidence),
                    bbox=bbox_from_polygon(polygon),
                    polygon=polygon,
                )
            )
    return boxes


def iter_paddle_results(raw_result: Any) -> list[Any]:
    if not raw_result:
        return []
    if is_structured_paddle_result(raw_result):
        return [raw_result]
    if len(raw_result) == 1 and isinstance(raw_result[0], list):
        inner = raw_result[0]
        if inner and is_structured_paddle_result(inner[0]):
            return inner
        return inner
    return raw_result


def is_structured_paddle_result(value: Any) -> bool:
    return isinstance(value, dict) and "rec_texts" in value


def parse_structured_paddle_result(result: dict[str, Any]) -> list[tuple[Any, str, float]]:
    texts = to_plain_list(result.get("rec_texts", []))
    scores = to_plain_list(result.get("rec_scores", []))
    polygons = to_plain_list(result.get("rec_polys", [])) or to_plain_list(result.get("dt_polys", []))
    axis_boxes = to_plain_list(result.get("rec_boxes", []))

    parsed: list[tuple[Any, str, float]] = []
    for index, text_value in enumerate(texts):
        points: Any | None = None
        if index < len(polygons):
            points = polygons[index]
        elif index < len(axis_boxes):
            points = polygon_from_axis_box(axis_boxes[index])
        if points is not None:
            confidence = safe_float(scores[index] if index < len(scores) else 0.0)
            parsed.append((points, str(text_value), confidence))
    return parsed


def parse_legacy_paddle_line(line: Any) -> tuple[Any, str, float] | None:
    if not isinstance(line, (list, tuple)) or len(line) < 2:
        return None

    points = line[0]
    text_confidence = line[1]
    if not isinstance(text_confidence, (list, tuple)) or len(text_confidence) < 2:
        return None

    text = str(text_confidence[0])
    confidence = safe_float(text_confidence[1])
    return points, text, confidence
