import React, { useEffect, useState } from 'react';
import { ArrowLeft, X } from 'lucide-react';
import { getSavedImage, imageContentUrl } from '../../data/api.js';
import OcrOverlay from './OcrOverlay.jsx';

export default function PhotoDetailPage({ photoId }) {
  const [image, setImage] = useState(null);
  const [error, setError] = useState(null);
  const [selectedBox, setSelectedBox] = useState(null);

  useEffect(() => {
    let ignore = false;

    setImage(null);
    setError(null);
    setSelectedBox(null);

    getSavedImage(photoId)
      .then((nextImage) => {
        if (!ignore) {
          setImage(nextImage);
        }
      })
      .catch((caught) => {
        if (!ignore) {
          setError(caught.message);
        }
      });

    return () => {
      ignore = true;
    };
  }, [photoId]);

  function toggleBox(box) {
    setSelectedBox((current) => (current && current.id === box.id ? null : box));
  }

  return (
    <section className="min-h-full pr-2 pb-24">
      <div className="mb-4 flex min-h-8 items-center justify-between gap-4">
        <a
          className="inline-flex items-center gap-1.5 text-sm font-bold leading-none text-[#5a5b55] transition hover:text-[#b22a22]"
          href="#/photos"
        >
          <ArrowLeft aria-hidden="true" size={15} />
          Photos
        </a>
        {image && image.filename && (
          <span className="truncate text-xs font-semibold text-[#8a867d]">{image.filename}</span>
        )}
      </div>

      {error ? (
        <p className="m-0 text-sm font-semibold text-[#8a867d]">{error}</p>
      ) : !image ? (
        <p className="m-0 text-sm font-semibold text-[#646058]">Loading...</p>
      ) : (
        <div className="flex items-start gap-4 max-[900px]:flex-col">
          <div className="min-w-0 flex-1">
            <div className="relative inline-block max-w-full">
              <img
                alt={image.filename || ''}
                className="block max-h-[78dvh] max-w-full rounded border border-[rgba(39,40,38,0.09)] bg-[#fbf8f2] shadow-[0_10px_28px_rgba(28,28,26,0.05)]"
                draggable={false}
                src={imageContentUrl(photoId)}
              />
              <OcrOverlay
                boxes={image.boxes}
                onBoxClick={toggleBox}
                selectedBoxId={selectedBox ? selectedBox.id : null}
              />
            </div>
            {!(image.boxes && image.boxes.length) && (
              <p className="mt-3 mb-0 text-xs font-semibold text-[#8a867d]">No recognized text</p>
            )}
          </div>

          {selectedBox && (
            <aside className="w-[300px] shrink-0 self-start rounded border border-[rgba(39,40,38,0.09)] bg-[rgba(255,253,248,0.94)] p-5 shadow-[0_10px_28px_rgba(28,28,26,0.05)] max-[900px]:w-full min-[901px]:sticky min-[901px]:top-4">
              <div className="flex items-center justify-between gap-3">
                <p className="m-0 text-[11px] font-extrabold uppercase leading-none text-[#8a867d]">Word</p>
                <button
                  aria-label="Close panel"
                  className="grid h-7 w-7 place-items-center rounded border border-[rgba(53,50,44,0.12)] bg-[#fffdf8] text-[#646058] transition hover:border-[rgba(178,42,34,0.32)] hover:text-[#b22a22]"
                  onClick={() => setSelectedBox(null)}
                  type="button"
                >
                  <X aria-hidden="true" size={13} />
                </button>
              </div>
              <p className="mt-4 mb-0 font-hanzi text-[clamp(34px,4vw,52px)] font-bold leading-tight text-[#161615] [overflow-wrap:anywhere]">
                {selectedBox.text}
              </p>
              <p className="mt-4 mb-0 text-xs font-semibold text-[#8a867d]">
                confidence {Math.round(selectedBox.confidence * 100)}%
              </p>
            </aside>
          )}
        </div>
      )}
    </section>
  );
}
