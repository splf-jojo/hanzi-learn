import React from 'react';
import { normalizePinyinText } from '../../utils/pinyin.js';

function fallbackCharacters(term) {
  const characters = Array.from(term.matchAll(/\p{Script=Han}/gu), (match) => match[0]);
  return (characters.length ? characters : Array.from(term)).map((glyph, index) => ({
    glyph,
    position: index,
    character_id: null,
  }));
}

function normalizeCharacters(term, characters) {
  if (!Array.isArray(characters) || !characters.length) {
    return fallbackCharacters(term);
  }

  return [...characters].sort((left, right) => left.position - right.position);
}

export default function CharacterPaper({ term, characters, pinyinSyllables = [], showPinyin = false }) {
  const visibleCharacters = normalizeCharacters(term, characters).map((character, index) => ({
    ...character,
    pinyin: normalizePinyinText(character.pinyin || pinyinSyllables[index] || ''),
  }));
  const characterCount = visibleCharacters.length;
  const gridClassByCount = {
    1: 'grid-cols-1',
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
  };
  const setSizeClass = (() => {
    if (characterCount === 1) {
      return 'max-w-[232px] max-[760px]:max-w-[210px]';
    }

    if (characterCount === 3) {
      return 'max-w-[420px] max-[760px]:max-w-[340px]';
    }

    if (characterCount >= 4) {
      return 'max-w-[520px]';
    }

    return 'max-w-[360px]';
  })();
  const characterTextClass =
    characterCount === 3
      ? 'text-[92px] max-[760px]:text-[64px] max-[430px]:text-[48px]'
      : 'text-[clamp(68px,11vw,158px)]';

  return (
    <div
      className={[
        'grid w-full gap-2',
        gridClassByCount[characterCount] || 'grid-cols-[repeat(auto-fit,minmax(0,1fr))]',
        setSizeClass,
      ].join(' ')}
    >
      {visibleCharacters.map((character) => {
        const tileClassName = [
          'group grid min-w-0 gap-2',
          character.character_id
            ? 'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#b22a22]'
            : '',
        ]
          .filter(Boolean)
          .join(' ');
        const cellClassName = [
          'relative grid aspect-square w-full place-items-center overflow-hidden rounded-[4px]',
          'border border-[rgba(52,52,49,0.14)] shadow-[0_1px_2px_rgba(38,38,35,0.05)]',
          'bg-white',
          "before:pointer-events-none before:absolute before:inset-0 before:bg-[linear-gradient(45deg,transparent_calc(50%_-_0.5px),rgba(90,90,84,0.18)_50%,transparent_calc(50%_+_0.5px)),linear-gradient(-45deg,transparent_calc(50%_-_0.5px),rgba(90,90,84,0.18)_50%,transparent_calc(50%_+_0.5px)),linear-gradient(90deg,transparent_calc(50%_-_0.5px),rgba(90,90,84,0.12)_50%,transparent_calc(50%_+_0.5px)),linear-gradient(0deg,transparent_calc(50%_-_0.5px),rgba(90,90,84,0.12)_50%,transparent_calc(50%_+_0.5px)),repeating-linear-gradient(0deg,transparent_0_49.5%,rgba(80,80,74,0.06)_50%,transparent_50.5%_100%),repeating-linear-gradient(90deg,transparent_0_49.5%,rgba(80,80,74,0.06)_50%,transparent_50.5%_100%)] before:content-['']",
          character.character_id
            ? 'transition group-hover:border-[rgba(178,42,34,0.28)]'
            : '',
        ]
          .filter(Boolean)
          .join(' ');
        const content = (
          <span
            className={[
              'max-w-[92%] text-center font-hanzi font-extrabold leading-[0.96] tracking-normal text-[#070707] [overflow-wrap:anywhere]',
              characterTextClass,
            ].join(' ')}
          >
            {character.glyph}
          </span>
        );
        const tileContent = (
          <>
            <span className={cellClassName}>{content}</span>
            {showPinyin && character.pinyin && (
              <span className="truncate text-center text-sm font-bold leading-none text-[#b22a22]">
                {character.pinyin}
              </span>
            )}
          </>
        );

        if (character.character_id) {
          return (
            <a
              aria-label={`Open character ${character.glyph}`}
              className={tileClassName}
              href={`#/characters/${character.character_id}`}
              key={`${character.character_id}-${character.position}`}
            >
              {tileContent}
            </a>
          );
        }

        return (
          <div className={tileClassName} key={`${character.glyph}-${character.position}`}>
            {tileContent}
          </div>
        );
      })}
    </div>
  );
}
