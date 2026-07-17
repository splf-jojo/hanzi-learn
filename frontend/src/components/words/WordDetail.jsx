import React, { useEffect, useMemo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { normalizePinyinText, pinyinSyllablesForWord } from '../../utils/pinyin.js';
import CharacterPaper from './CharacterPaper.jsx';

const knowledgeLevels = [
  {
    level: 0,
    glyph: '生',
    label: 'New',
    color: '#2563eb',
    border: 'rgba(37, 99, 235, 0.34)',
    background: 'rgba(37, 99, 235, 0.08)',
  },
  {
    level: 1,
    glyph: '忘',
    label: 'Forgot',
    color: '#16803b',
    border: 'rgba(22, 128, 59, 0.32)',
    background: 'rgba(22, 128, 59, 0.08)',
  },
  {
    level: 2,
    glyph: '疑',
    label: 'Unsure',
    color: '#a56b00',
    border: 'rgba(165, 107, 0, 0.34)',
    background: 'rgba(165, 107, 0, 0.1)',
  },
  {
    level: 3,
    glyph: '记',
    label: 'Remember',
    color: '#c25512',
    border: 'rgba(194, 85, 18, 0.32)',
    background: 'rgba(194, 85, 18, 0.08)',
  },
  {
    level: 4,
    glyph: '熟',
    label: 'Familiar',
    color: '#b22a22',
    border: 'rgba(178, 42, 34, 0.34)',
    background: 'rgba(178, 42, 34, 0.08)',
  },
  {
    level: 5,
    glyph: '精',
    label: 'Mastered',
    color: '#151615',
    border: 'rgba(21, 22, 21, 0.28)',
    background: 'rgba(21, 22, 21, 0.06)',
  },
];

const hanRegex = /\p{Script=Han}/gu;
const pinyinTokenRegex = /\S+/g;
const hanziHighlightClass = 'word-highlight';
const pinyinHighlightClass = 'word-highlight';

function countHanCharacters(value) {
  return Array.from(value.matchAll(hanRegex)).length;
}

function findTextRanges(text, needle, { matchCase = true } = {}) {
  if (!text || !needle) {
    return [];
  }

  const source = matchCase ? text : text.toLocaleLowerCase();
  const target = matchCase ? needle : needle.toLocaleLowerCase();
  const ranges = [];
  let start = source.indexOf(target);

  while (start !== -1) {
    const end = start + needle.length;
    ranges.push([start, end]);
    start = source.indexOf(target, end);
  }

  return ranges;
}

function findTermTextRanges(text, term) {
  const exactRanges = findTextRanges(text, term);
  if (exactRanges.length || !term.includes('……')) {
    return exactRanges;
  }

  const parts = term.split('……').map((part) => part.trim()).filter(Boolean);
  const ranges = [];
  let cursor = 0;

  for (const part of parts) {
    const start = text.indexOf(part, cursor);

    if (start === -1) {
      return [];
    }

    const end = start + part.length;
    ranges.push([start, end]);
    cursor = end;
  }

  return ranges;
}

function sentenceMatchesWord(sentence, term) {
  return findTermTextRanges(sentence.hanzi, term).length > 0;
}

function isEditableTarget(target) {
  if (!(target instanceof HTMLElement)) {
    return false;
  }

  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
}

function mergeRanges(ranges) {
  return ranges
    .filter(Boolean)
    .sort(([startA], [startB]) => startA - startB)
    .reduce((merged, [start, end]) => {
      const previous = merged[merged.length - 1];

      if (!previous || start > previous[1]) {
        merged.push([start, end]);
        return merged;
      }

      previous[1] = Math.max(previous[1], end);
      return merged;
    }, []);
}

function renderHighlightedText(text, ranges, highlightClassName, keyPrefix) {
  if (!ranges.length) {
    return text;
  }

  const nodes = [];
  let cursor = 0;

  ranges.forEach(([start, end], index) => {
    if (start > cursor) {
      nodes.push(text.slice(cursor, start));
    }

    nodes.push(
      <mark className={highlightClassName} key={`${keyPrefix}-${index}`}>
        {text.slice(start, end)}
      </mark>,
    );
    cursor = end;
  });

  if (cursor < text.length) {
    nodes.push(text.slice(cursor));
  }

  return nodes;
}

function getPinyinTokenRanges(pinyin) {
  return Array.from(pinyin.matchAll(pinyinTokenRegex), (match) => ({
    start: match.index,
    end: match.index + match[0].length,
  }));
}

function getSentencePinyinHighlightRanges(sentence, word) {
  if (!sentence.pinyin || !word.hanzi) {
    return [];
  }

  const termRanges = findTermTextRanges(sentence.hanzi, word.hanzi);
  const pinyinTokens = getPinyinTokenRanges(sentence.pinyin);
  const mappedRanges = termRanges.map(([start, end]) => {
    const hanBeforeWord = countHanCharacters(sentence.hanzi.slice(0, start));
    const hanInWord = countHanCharacters(sentence.hanzi.slice(start, end));
    const firstToken = pinyinTokens[hanBeforeWord];
    const lastToken = pinyinTokens[hanBeforeWord + hanInWord - 1];

    if (!hanInWord || !firstToken || !lastToken) {
      return null;
    }

    return [firstToken.start, lastToken.end];
  });

  const mappedHighlights = mergeRanges(mappedRanges);
  if (mappedHighlights.length) {
    return mappedHighlights;
  }

  return mergeRanges(findTextRanges(sentence.pinyin, word.pinyin, { matchCase: false }));
}

function normalizeKnowledgeLevel(value) {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return 0;
  }

  return Math.min(5, Math.max(0, Math.round(numericValue)));
}

function PanelHeader({ title, meta }) {
  return (
    <header className="detail-card-header">
      <div className="min-w-0">
        <h2 className="detail-card-title">{title}</h2>
      </div>
      {meta && <span className="detail-card-meta">{meta}</span>}
    </header>
  );
}

function KnowledgeLevelControl({ level = null, onChange }) {
  const hasSelection = level !== null && level !== undefined;
  const selectedLevel = hasSelection ? normalizeKnowledgeLevel(level) : null;

  return (
    <section
      aria-label="Word knowledge level"
      className="detail-card knowledge-card"
    >
      <div className="knowledge-options" role="radiogroup" aria-label="Set word knowledge level">
        {knowledgeLevels.map((rating) => {
          const isSelected = hasSelection && rating.level === selectedLevel;

          return (
            <button
              aria-checked={isSelected}
              aria-label={`Set knowledge level ${rating.level} of 5: ${rating.label}`}
              className={['knowledge-option', isSelected ? 'is-selected' : ''].filter(Boolean).join(' ')}
              key={rating.level}
              onClick={() => onChange(rating.level)}
              role="radio"
              style={{
                '--level-color': rating.color,
                '--level-border': rating.border,
                '--level-bg': rating.background,
              }}
              title={`Level ${rating.level}: ${rating.label}`}
              type="button"
            >
              <span className="knowledge-option-glyph">{rating.glyph}</span>
              <span className="knowledge-option-copy">
                <span className="knowledge-option-level">Level {rating.level}</span>
                <span className="knowledge-option-label">{rating.label}</span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function WordNavButton({ word, direction, href, onSelect }) {
  const Icon = direction === 'previous' ? ChevronLeft : ChevronRight;
  const sideClass = direction === 'previous' ? 'previous' : 'next';
  const label = direction === 'previous' ? `Previous word: ${word.hanzi}` : `Next word: ${word.hanzi}`;

  function handleClick(event) {
    event.preventDefault();
    onSelect();
  }

  return (
    <a
      className={['word-nav-button', sideClass].join(' ')}
      aria-label={label}
      href={href}
      onClick={handleClick}
      title={label}
    >
      <Icon aria-hidden="true" size={22} strokeWidth={2.2} />
    </a>
  );
}

function SentenceExamples({ sentences, word }) {
  if (!sentences.length) {
    return (
      <section className="detail-card examples-card">
        <PanelHeader title="Examples" meta="0 sentences" />
        <p className="examples-empty">No linked examples.</p>
      </section>
    );
  }

  return (
    <section className="detail-card examples-card">
      <PanelHeader title="Examples" meta={`${sentences.length} ${sentences.length === 1 ? 'sentence' : 'sentences'}`} />
      <div className="example-list">
        {sentences.map((sentence, index) => {
          const hanziRanges = mergeRanges(findTermTextRanges(sentence.hanzi, word.hanzi));
          const pinyinRanges = getSentencePinyinHighlightRanges(sentence, word);

          return (
            <article className="example-row" key={sentence.id}>
              <span className="example-index">{String(index + 1).padStart(2, '0')}</span>
              <div className="example-content">
                <p className="example-hanzi">
                  {renderHighlightedText(sentence.hanzi, hanziRanges, hanziHighlightClass, `hanzi-${sentence.id}`)}
                </p>
                {sentence.pinyin && (
                  <p className="example-pinyin">
                    {renderHighlightedText(sentence.pinyin, pinyinRanges, pinyinHighlightClass, `pinyin-${sentence.id}`)}
                  </p>
                )}
                {sentence.translation && <p className="example-translation">{sentence.translation}</p>}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function WordImagePanel({ word }) {
  if (!word.image) {
    return null;
  }

  return (
    <figure className="detail-card image-card">
      <div className="word-image-frame">
        <img src={word.image} alt={`${word.translation || word.hanzi} reference`} loading="lazy" />
      </div>
    </figure>
  );
}

export default function WordDetail({
  word,
  previousWord,
  nextWord,
  groupName = 'All words',
  previousHref,
  nextHref,
  sentences = [],
  knowledgeLevel = null,
  onKnowledgeLevelChange = () => {},
  onPrevious,
  onNext,
}) {
  const hanCharacters = Array.from(word.hanzi.matchAll(/\p{Script=Han}/gu), (match) => match[0]);
  const isMultiCharacterWord = hanCharacters.length > 1;
  const pinyinSyllables = pinyinSyllablesForWord(word, hanCharacters.length);
  const displayPinyin = normalizePinyinText(
    isMultiCharacterWord && pinyinSyllables.length === hanCharacters.length ? pinyinSyllables.join(' ') : word.pinyin,
  );
  const matchingSentences = useMemo(
    () =>
      sentences.filter((sentence) =>
        Array.isArray(sentence.words) && sentence.words.length
          ? sentence.words.includes(word.id)
          : sentenceMatchesWord(sentence, word.hanzi),
      ),
    [sentences, word.hanzi, word.id],
  );

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || isEditableTarget(event.target)) {
        return;
      }

      if (event.key === 'ArrowLeft' && previousWord) {
        event.preventDefault();
        onPrevious();
      }

      if (event.key === 'ArrowRight' && nextWord) {
        event.preventDefault();
        onNext();
      }
    }

    window.addEventListener('keydown', handleKeyDown);

    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [nextWord, onNext, onPrevious, previousWord]);

  return (
    <section className="word-detail-page">
      <nav aria-label="Word navigation" className="word-side-navigation">
        {previousWord ? (
          <WordNavButton
            word={previousWord}
            direction="previous"
            href={previousHref}
            onSelect={onPrevious}
          />
        ) : (
          <span />
        )}
        {nextWord ? (
          <WordNavButton
            word={nextWord}
            direction="next"
            href={nextHref}
            onSelect={onNext}
          />
        ) : (
          <span />
        )}
      </nav>

      <div className="word-detail-body">
        <div className="word-detail-container">
          <header className="word-detail-header">
            <span className="detail-chip">{groupName}</span>
          </header>

          <article className="word-detail-layout">
            <div className="word-detail-main">
              <section className="detail-card word-overview-card">
                <div className={['word-overview-grid', isMultiCharacterWord ? 'is-multi-character' : ''].filter(Boolean).join(' ')}>
                  <div className="word-paper-slot">
                    <CharacterPaper
                      term={word.hanzi}
                      characters={word.characters}
                      pinyinSyllables={pinyinSyllables}
                      showPinyin={isMultiCharacterWord}
                    />
                  </div>
                  <div className="word-summary">
                    {displayPinyin && (
                      <h1 className={['word-pinyin', isMultiCharacterWord ? 'is-multi-character' : ''].filter(Boolean).join(' ')}>
                        {displayPinyin}
                      </h1>
                    )}
                    {word.translation && <p className="word-translation">{word.translation}</p>}
                  </div>
                </div>
              </section>

              <SentenceExamples sentences={matchingSentences} word={word} />
            </div>

            <aside className="word-detail-aside">
              <WordImagePanel word={word} />
              <KnowledgeLevelControl level={knowledgeLevel} onChange={onKnowledgeLevelChange} />
            </aside>
          </article>
        </div>
      </div>
    </section>
  );
}
