import { useEffect, useRef, useState } from 'react';

export function usePreviewUrl() {
  const [previewUrl, setPreviewUrl] = useState(null);
  const latestUrl = useRef(null);

  useEffect(() => () => revokeBlobUrl(latestUrl.current), []);

  function setPreview(nextUrl) {
    setPreviewUrl((current) => {
      revokeBlobUrl(current);
      latestUrl.current = nextUrl;
      return nextUrl;
    });
  }

  return { previewUrl, setPreview };
}

function revokeBlobUrl(url) {
  if (url && url.startsWith('blob:')) {
    URL.revokeObjectURL(url);
  }
}
