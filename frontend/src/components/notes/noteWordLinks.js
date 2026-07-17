export function buildWordIndex(words) {
  const byFirstGlyph = new Map();

  for (const word of words) {
    const hanzi = (word.hanzi || '').trim();

    if (!hanzi) {
      continue;
    }

    const firstGlyph = hanzi[0];

    if (!byFirstGlyph.has(firstGlyph)) {
      byFirstGlyph.set(firstGlyph, []);
    }

    byFirstGlyph.get(firstGlyph).push(word);
  }

  for (const candidates of byFirstGlyph.values()) {
    candidates.sort((left, right) => right.hanzi.length - left.hanzi.length);
  }

  return byFirstGlyph;
}

export function segmentNoteText(text, wordIndex) {
  const segments = [];
  let plainText = '';
  let position = 0;

  while (position < text.length) {
    const candidates = wordIndex.get(text[position]);
    let matched = null;

    if (candidates) {
      for (const candidate of candidates) {
        if (text.startsWith(candidate.hanzi, position)) {
          matched = candidate;
          break;
        }
      }
    }

    if (matched) {
      if (plainText) {
        segments.push({ type: 'text', value: plainText });
        plainText = '';
      }

      segments.push({ type: 'word', value: matched.hanzi, word: matched });
      position += matched.hanzi.length;
    } else {
      plainText += text[position];
      position += 1;
    }
  }

  if (plainText) {
    segments.push({ type: 'text', value: plainText });
  }

  return segments;
}

export function collectNoteWords(text, wordIndex) {
  const uniqueWords = new Map();

  for (const segment of segmentNoteText(text, wordIndex)) {
    if (segment.type === 'word' && !uniqueWords.has(segment.word.id)) {
      uniqueWords.set(segment.word.id, segment.word);
    }
  }

  return [...uniqueWords.values()];
}
