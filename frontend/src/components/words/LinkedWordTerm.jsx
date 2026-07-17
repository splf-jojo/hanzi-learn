import React from 'react';

function characterHref(characterId) {
  return `#/characters/${characterId}`;
}

function fallbackCharacters(term) {
  return Array.from(term).map((glyph, index) => ({
    glyph,
    position: index,
    character_id: null,
  }));
}

function wordCharacters(word) {
  const characters = Array.isArray(word.characters) && word.characters.length ? word.characters : fallbackCharacters(word.hanzi);

  return [...characters].sort((left, right) => left.position - right.position);
}

export default function LinkedWordTerm({
  word,
  wordHref,
  className = '',
  characterClassName = '',
  stopPropagation = false,
}) {
  function navigateToWord(event) {
    if (!wordHref || event.defaultPrevented) {
      return;
    }

    if (stopPropagation) {
      event.stopPropagation();
    }

    window.location.hash = wordHref;
  }

  function handleKeyDown(event) {
    if (event.key !== 'Enter' && event.key !== ' ') {
      return;
    }

    event.preventDefault();
    navigateToWord(event);
  }

  return (
    <span
      aria-label={wordHref ? `Open word ${word.hanzi}` : undefined}
      className={className}
      onClick={navigateToWord}
      onKeyDown={handleKeyDown}
      role={wordHref ? 'link' : undefined}
      tabIndex={wordHref ? 0 : undefined}
    >
      {wordCharacters(word).map((character) => {
        if (!character.character_id) {
          return (
            <span className={characterClassName} key={`${character.glyph}-${character.position}`}>
              {character.glyph}
            </span>
          );
        }

        return (
          <a
            aria-label={`Open character ${character.glyph}`}
            className={characterClassName}
            href={characterHref(character.character_id)}
            key={`${character.character_id}-${character.position}`}
            onClick={(event) => {
              event.stopPropagation();
            }}
          >
            {character.glyph}
          </a>
        );
      })}
    </span>
  );
}
