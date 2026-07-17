import React, { useMemo } from 'react';
import CharacterPaper from '../words/CharacterPaper.jsx';
import LinkedWordTerm from '../words/LinkedWordTerm.jsx';
import { splitPinyinSyllables } from '../../utils/pinyin.js';

function wordsForCharacter(character, words) {
  return words
    .map((word) => ({
      word,
      link: Array.isArray(word.characters)
        ? word.characters.find((characterLink) => characterLink.character_id === character.id)
        : null,
    }))
    .filter((entry) => entry.link);
}

function pinyinForCharacterLink(word, link) {
  if (link.pinyin) {
    return link.pinyin;
  }

  if (!word.pinyin || !Array.isArray(word.characters)) {
    return '';
  }

  const syllables = splitPinyinSyllables(word.pinyin, word.characters.length);
  return syllables[link.position] || '';
}

export default function CharacterDetail({ character, words }) {
  const relatedWords = useMemo(() => wordsForCharacter(character, words), [character, words]);
  const characterPinyin =
    character.pinyin || relatedWords.map(({ word, link }) => pinyinForCharacterLink(word, link)).find(Boolean) || '';
  const characterTranslation =
    character.translation || relatedWords.map(({ word }) => word.translation).find(Boolean) || '';
  const characterDescription = character.description || '';

  return (
    <section className="min-h-full">
      <div className="w-full pr-2 pl-[clamp(14px,2vw,28px)] max-[760px]:pl-0">
        <div className="mb-3 flex items-center gap-2">
          <a className="rounded-sm bg-[rgba(177,43,36,0.08)] px-2 py-1 text-xs font-bold uppercase tracking-wide text-[#b22a22]" href="#/">
            Characters
          </a>
        </div>

        <article className="grid w-full grid-cols-[minmax(176px,232px)_minmax(260px,360px)_minmax(260px,1fr)] items-center gap-[clamp(18px,3vw,34px)] max-[1180px]:grid-cols-1 max-[1180px]:items-start">
          <CharacterPaper term={character.glyph} />

          <section className="min-w-0">
            <div className="flex items-center overflow-visible">
              {characterPinyin && (
                <h1 className="m-0 overflow-visible whitespace-nowrap pt-[0.1em] pb-[0.04em] [font-family:Times_New_Roman,Georgia,serif] text-[clamp(42px,7vw,62px)] font-bold leading-[1.22] text-[#b22a22]">
                  {characterPinyin}
                </h1>
              )}
            </div>
            {characterTranslation && (
              <p className="mt-2 mb-0 [font-family:Georgia,Times_New_Roman,serif] text-[clamp(24px,4vw,34px)] leading-[1.28] text-[#20201e]">
                {characterTranslation}
              </p>
            )}
            {characterDescription && (
              <p className="mt-3 mb-0 max-w-[42rem] text-sm leading-relaxed text-[#5a5b55]">
                {characterDescription}
              </p>
            )}
          </section>

          <section className="min-w-0">
            <h2 className="m-0 [font-family:Georgia,Times_New_Roman,serif] text-[clamp(22px,3vw,30px)] font-bold leading-tight text-[#20201e]">
              Words
            </h2>
            <div className="mt-4 grid grid-cols-[repeat(auto-fit,minmax(136px,1fr))] gap-3">
              {relatedWords.map(({ word }) => (
                <article
                  className="grid min-h-[96px] gap-2 rounded border border-[rgba(39,40,38,0.09)] bg-[rgba(255,255,252,0.72)] px-4 py-3 shadow-[0_10px_28px_rgba(28,28,26,0.05)]"
                  key={word.id}
                >
                  <LinkedWordTerm
                    characterClassName="transition hover:text-[#b22a22] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#b22a22]"
                    className="font-hanzi text-3xl font-bold leading-none text-[#161615] [overflow-wrap:anywhere]"
                    word={word}
                    wordHref={`#/words/${word.id}`}
                  />
                  {word.pinyin && <a className="truncate text-xs font-bold leading-tight text-[#b22a22]" href={`#/words/${word.id}`}>{word.pinyin}</a>}
                  {word.translation && <a className="truncate text-xs leading-tight text-[#5a5b55]" href={`#/words/${word.id}`}>{word.translation}</a>}
                </article>
              ))}
            </div>
          </section>
        </article>
      </div>
    </section>
  );
}
