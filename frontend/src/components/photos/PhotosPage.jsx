import React, { useEffect, useRef, useState } from 'react';
import { ImagePlus, LoaderCircle, X } from 'lucide-react';
import { imageContentUrl, listImages, savePendingUpload, searchSimilarImages } from '../../data/api.js';
import { usePreviewUrl } from './usePreviewUrl.js';

const GALLERY_PAGE_SIZE = 12;
const ACCEPTED_IMAGE_TYPES = 'image/png,image/jpeg,image/webp';

export default function PhotosPage() {
  const [images, setImages] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [loadingGallery, setLoadingGallery] = useState(false);
  const [galleryError, setGalleryError] = useState(null);
  const [searchResult, setSearchResult] = useState(null);
  const [searching, setSearching] = useState(false);
  const [saving, setSaving] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const { previewUrl, setPreview } = usePreviewUrl();
  const fileInputRef = useRef(null);

  async function loadGalleryPage(offset, append) {
    setGalleryError(null);
    setLoadingGallery(true);

    try {
      const response = await listImages({ limit: GALLERY_PAGE_SIZE, offset });
      setImages((current) => (append ? [...current, ...response.images] : response.images));
      setHasMore(response.has_more);
    } catch (error) {
      setGalleryError(error.message);
    } finally {
      setLoadingGallery(false);
    }
  }

  useEffect(() => {
    loadGalleryPage(0, false);
  }, []);

  async function handleFileChange(event) {
    const file = event.target.files && event.target.files[0];
    event.target.value = '';

    if (!file) {
      return;
    }

    setUploadError(null);
    setSearchResult(null);
    setPreview(URL.createObjectURL(file));
    setSearching(true);

    try {
      const result = await searchSimilarImages(file);
      setSearchResult(result);
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setSearching(false);
    }
  }

  async function handleSaveUpload() {
    if (!searchResult) {
      return;
    }

    setUploadError(null);
    setSaving(true);

    try {
      const saved = await savePendingUpload(searchResult.upload_id);
      setPreview(null);
      setSearchResult(null);
      window.location.hash = `#/photos/${saved.image_id}`;
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setSaving(false);
    }
  }

  function handleCancelUpload() {
    setPreview(null);
    setSearchResult(null);
    setUploadError(null);
  }

  const matches = searchResult ? searchResult.matches || [] : [];

  return (
    <section className="min-h-full pr-2 pb-24">
      <input
        ref={fileInputRef}
        accept={ACCEPTED_IMAGE_TYPES}
        className="hidden"
        onChange={handleFileChange}
        type="file"
      />

      {previewUrl && (
        <article className="mb-5 overflow-hidden rounded border border-[rgba(39,40,38,0.09)] bg-[rgba(255,253,248,0.94)] shadow-[0_10px_28px_rgba(28,28,26,0.05)]">
          <div className="flex items-center justify-between gap-4 border-b border-[rgba(53,50,44,0.12)] bg-[rgba(251,248,242,0.7)] px-5 py-4">
            <h1 className="m-0 [font-family:Georgia,Times_New_Roman,serif] text-xl font-bold leading-tight text-[#20201e]">
              Новое фото
            </h1>
            <button
              aria-label="Отменить загрузку"
              className="grid h-8 w-8 place-items-center rounded border border-[rgba(53,50,44,0.12)] bg-[#fffdf8] text-[#646058] transition hover:border-[rgba(178,42,34,0.32)] hover:text-[#b22a22]"
              onClick={handleCancelUpload}
              type="button"
            >
              <X aria-hidden="true" size={15} />
            </button>
          </div>

          <div className="grid grid-cols-[minmax(200px,320px)_minmax(0,1fr)] items-start gap-6 p-5 max-[760px]:grid-cols-1">
            <div className="overflow-hidden rounded border border-[rgba(53,50,44,0.12)] bg-[#fbf8f2]">
              <img alt="" className="block h-auto w-full" draggable={false} src={previewUrl} />
            </div>

            <div className="min-w-0">
              <p className="m-0 text-[11px] font-extrabold uppercase leading-none text-[#8a867d]">
                Похожие{!searching && ` · ${matches.length}`}
              </p>

              {searching ? (
                <p className="mt-4 mb-0 flex items-center gap-2 text-sm font-semibold text-[#646058]">
                  <LoaderCircle aria-hidden="true" className="animate-spin" size={15} />
                  Ищем похожие фото...
                </p>
              ) : matches.length ? (
                <div className="mt-4 flex flex-wrap gap-3">
                  {matches.map((match) => (
                    <a
                      className="w-24 overflow-hidden rounded border border-[rgba(52,52,49,0.1)] bg-white/70 transition hover:-translate-y-0.5 hover:border-[rgba(178,42,34,0.24)] hover:shadow-[0_10px_22px_rgba(28,28,26,0.07)]"
                      href={`#/photos/${match.image_id}`}
                      key={match.image_id}
                      title={match.filename || match.image_id}
                    >
                      <img
                        alt=""
                        className="block aspect-square w-full object-cover"
                        draggable={false}
                        src={imageContentUrl(match.image_id)}
                      />
                      <span className="block px-2 py-1.5 text-center text-xs font-bold leading-none text-[#6b6b64]">
                        {Math.round(match.similarity * 100)}%
                      </span>
                    </a>
                  ))}
                </div>
              ) : (
                searchResult && <p className="mt-4 mb-0 text-sm font-semibold text-[#8a867d]">Похожих фото нет</p>
              )}

              {searchResult && (
                <button
                  className="mt-5 inline-flex items-center gap-2 rounded border border-[rgba(53,50,44,0.18)] bg-[#fffdf8] px-4 py-2.5 text-sm font-bold leading-none text-[#20201e] transition hover:border-[rgba(178,42,34,0.32)] hover:text-[#b22a22] disabled:cursor-default disabled:opacity-40"
                  disabled={saving}
                  onClick={handleSaveUpload}
                  type="button"
                >
                  {saving && <LoaderCircle aria-hidden="true" className="animate-spin" size={15} />}
                  Добавить фото в базу
                </button>
              )}

              {uploadError && <p className="mt-4 mb-0 text-sm font-semibold text-[#8a867d]">{uploadError}</p>}
            </div>
          </div>
        </article>
      )}

      <div className="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-3">
        <button
          className="grid aspect-square place-items-center rounded border border-dashed border-[rgba(53,50,44,0.28)] bg-[rgba(255,255,252,0.55)] text-[#8a867d] transition hover:-translate-y-0.5 hover:border-[rgba(178,42,34,0.32)] hover:text-[#b22a22]"
          onClick={() => fileInputRef.current && fileInputRef.current.click()}
          type="button"
        >
          <ImagePlus aria-hidden="true" size={30} strokeWidth={1.6} />
          <span className="sr-only">Загрузить фото</span>
        </button>

        {images.map((image) => (
          <a
            className="block aspect-square overflow-hidden rounded border border-[rgba(39,40,38,0.09)] bg-[rgba(255,255,252,0.72)] shadow-[0_10px_28px_rgba(28,28,26,0.05)] transition hover:-translate-y-0.5 hover:border-[rgba(178,42,34,0.24)] hover:shadow-[0_18px_36px_rgba(28,28,26,0.08)]"
            href={`#/photos/${image.image_id}`}
            key={image.image_id}
            title={image.filename || undefined}
          >
            <img
              alt={image.filename || ''}
              className="h-full w-full object-cover"
              draggable={false}
              loading="lazy"
              src={imageContentUrl(image.image_id)}
            />
          </a>
        ))}
      </div>

      <div className="mt-5 flex items-center gap-3">
        {hasMore && (
          <button
            className="inline-flex items-center gap-2 rounded border border-[rgba(53,50,44,0.18)] bg-[rgba(255,253,248,0.9)] px-4 py-2.5 text-sm font-bold leading-none text-[#5a5b55] transition hover:border-[rgba(178,42,34,0.32)] hover:text-[#b22a22] disabled:cursor-default disabled:opacity-40"
            disabled={loadingGallery}
            onClick={() => loadGalleryPage(images.length, true)}
            type="button"
          >
            {loadingGallery && <LoaderCircle aria-hidden="true" className="animate-spin" size={15} />}
            Загрузить больше фото
          </button>
        )}
        {loadingGallery && !images.length && (
          <p className="m-0 text-sm font-semibold text-[#646058]">Loading...</p>
        )}
        {galleryError && <p className="m-0 text-sm font-semibold text-[#8a867d]">{galleryError}</p>}
      </div>
    </section>
  );
}
