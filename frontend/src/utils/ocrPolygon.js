export function polygonClassName(box, selectedBoxId) {
  const names = ['ocr-polygon'];

  if (box.id === selectedBoxId) {
    names.push('is-selected');
  }

  return names.join(' ');
}

export function polygonPoints(box) {
  return polygonOrBoundingBox(box)
    .map(([x, y]) => `${x},${y}`)
    .join(' ');
}

function polygonOrBoundingBox(box) {
  if (Array.isArray(box.polygon) && box.polygon.length >= 3) {
    return box.polygon;
  }

  const { x, y, width, height } = box.bbox;

  return [
    [x, y],
    [x + width, y],
    [x + width, y + height],
    [x, y + height],
  ];
}
