from __future__ import annotations

from typing import Any

from ..schemas.images import BoundingBox


def normalize_polygon(points: Any, width: int, height: int) -> list[list[float]]:
    plain_points = to_plain_list(points)
    if is_axis_box(plain_points):
        plain_points = polygon_from_axis_box(plain_points)

    polygon: list[list[float]] = []
    for point in plain_points:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        x, y = safe_float(point[0]), safe_float(point[1])
        polygon.append([clamp01(x / width), clamp01(y / height)])
    return polygon


def bbox_from_polygon(polygon: list[list[float]]) -> BoundingBox:
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    left = min(xs)
    top = min(ys)
    right = max(xs)
    bottom = max(ys)
    return BoundingBox(x=left, y=top, width=max(0.0, right - left), height=max(0.0, bottom - top))


def polygon_from_axis_box(box: Any) -> list[list[float]]:
    plain_box = to_plain_list(box)
    if not is_axis_box(plain_box):
        return []
    left, top, right, bottom = [safe_float(value) for value in plain_box[:4]]
    return [[left, top], [right, top], [right, bottom], [left, bottom]]


def is_axis_box(value: Any) -> bool:
    return (
        isinstance(value, (list, tuple))
        and len(value) >= 4
        and all(isinstance(item, (int, float)) for item in value[:4])
    )


def to_plain_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return value
    return [value]


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
