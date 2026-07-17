const pinyinInitials = ['zh', 'ch', 'sh', 'b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'r', 'z', 'c', 's', 'y', 'w'];
const pinyinFinals = [
  'uang',
  'iang',
  'iong',
  'ueng',
  'ang',
  'eng',
  'ing',
  'ong',
  'iao',
  'ian',
  'uai',
  'uan',
  'van',
  'ai',
  'ei',
  'ao',
  'ou',
  'an',
  'en',
  'in',
  'un',
  'ia',
  'ie',
  'iu',
  'ua',
  'uo',
  'ui',
  'ue',
  've',
  'er',
  'ar',
  'a',
  'o',
  'e',
  'i',
  'u',
  'v',
  'm',
  'n',
  'r',
];

export function normalizePinyinText(value = '') {
  return typeof value === 'string' ? value.normalize('NFC') : '';
}

function normalizePinyinCharacter(character) {
  return character
    .toLocaleLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace('ü', 'v');
}

function compactPinyin(pinyin) {
  return Array.from(normalizePinyinText(pinyin)).reduce(
    (result, character) => {
      if (/[\s'’.-]/.test(character)) {
        return result;
      }

      const normalizedCharacter = normalizePinyinCharacter(character);
      if (!/^[a-zv]$/.test(normalizedCharacter)) {
        return result;
      }

      result.normalized += normalizedCharacter;
      result.originalCharacters.push(character);
      return result;
    },
    { normalized: '', originalCharacters: [] },
  );
}

function pinyinSyllableLengthAt(source, cursor) {
  const initial = pinyinInitials.find((value) => source.startsWith(value, cursor)) || '';
  const finalCursor = cursor + initial.length;
  const final = pinyinFinals.find((value) => source.startsWith(value, finalCursor));

  return final ? initial.length + final.length : 1;
}

export function splitPinyinSyllables(pinyin = '', expectedCount = 0) {
  const normalizedPinyin = normalizePinyinText(pinyin);

  if (!normalizedPinyin || expectedCount < 1) {
    return [];
  }

  const spacedTokens = normalizedPinyin.trim().split(/\s+/).filter(Boolean);
  if (spacedTokens.length === expectedCount) {
    return spacedTokens;
  }

  const { normalized, originalCharacters } = compactPinyin(normalizedPinyin);
  const syllables = [];
  let cursor = 0;

  while (cursor < normalized.length && syllables.length < expectedCount) {
    const syllableLength = pinyinSyllableLengthAt(normalized, cursor);
    syllables.push(normalizePinyinText(originalCharacters.slice(cursor, cursor + syllableLength).join('')));
    cursor += syllableLength;
  }

  return syllables.length === expectedCount ? syllables : spacedTokens;
}

export function pinyinSyllablesForWord(word, expectedCount) {
  const sortedCharacters = Array.isArray(word.characters) ? [...word.characters].sort((left, right) => left.position - right.position) : [];
  const linkedSyllables = sortedCharacters.map((character) => normalizePinyinText(character.pinyin || ''));

  if (expectedCount > 0 && linkedSyllables.length === expectedCount && linkedSyllables.every(Boolean)) {
    return linkedSyllables;
  }

  return splitPinyinSyllables(normalizePinyinText(word.pinyin), expectedCount);
}
