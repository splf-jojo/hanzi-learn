import React from 'react';
import LinkedWordTerm from './LinkedWordTerm.jsx';

function countHanCharacters(term) {
  return Array.from(term.matchAll(/\p{Script=Han}/gu)).length;
}

export default function WordGrid({ list }) {
  function openWord(word) {
    window.location.hash = `#/words/${word.id}`;
  }

  return (
    <section className="min-h-full pr-2 pb-24">
      <div className="word-grid">
        {list.map((word) => {
          const isMultiCharacter = countHanCharacters(word.hanzi) > 1;
          const wordHref = `#/words/${word.id}`;

          return (
            <article
              key={word.id}
              className={['word-tile', isMultiCharacter ? 'col-span-2 max-[760px]:col-span-1' : ''].filter(Boolean).join(' ')}
              onClick={() => openWord(word)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  openWord(word);
                }
              }}
              role="link"
              tabIndex={0}
            >
              <LinkedWordTerm
                characterClassName="transition hover:text-[#b22a22] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#b22a22]"
                className="word-tile-term"
                stopPropagation
                word={word}
                wordHref={wordHref}
              />
              {word.pinyin && (
                <a className="word-tile-pinyin" href={wordHref} onClick={(event) => event.stopPropagation()}>
                  {word.pinyin}
                </a>
              )}
              {word.translation && (
                <a className="word-tile-meaning" href={wordHref} onClick={(event) => event.stopPropagation()}>
                  {word.translation}
                </a>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
