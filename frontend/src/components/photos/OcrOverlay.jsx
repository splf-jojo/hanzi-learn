import React from 'react';
import { polygonClassName, polygonPoints } from '../../utils/ocrPolygon.js';

export default function OcrOverlay({ boxes, selectedBoxId, onBoxClick }) {
  if (!boxes || !boxes.length) {
    return null;
  }

  return (
    <svg className="ocr-overlay" viewBox="0 0 1 1" preserveAspectRatio="none">
      {boxes.map((box) => (
        <polygon
          key={box.id}
          className={polygonClassName(box, selectedBoxId)}
          points={polygonPoints(box)}
          vectorEffect="non-scaling-stroke"
          focusable="false"
          aria-hidden="true"
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => onBoxClick(box)}
        />
      ))}
    </svg>
  );
}
