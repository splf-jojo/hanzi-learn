import React from 'react';
import { formatStamp } from './boardLayout.js';
import { collectNoteWords, segmentNoteText } from './noteWordLinks.js';

function Fastener({ appearance }) {
  if (appearance.fastener === 'pin') {
    return <span aria-hidden="true" className={`note-pin ${appearance.pinTint}`} />;
  }

  if (appearance.fastener === 'clip') {
    return <span aria-hidden="true" className="note-clip" />;
  }

  return <span aria-hidden="true" className="note-tape" />;
}

export default function NotePaper({
  date,
  text,
  appearance,
  isToday,
  isZoomed,
  isEditing,
  isDimmed,
  wordIndex,
  onSelect,
  onChangeText,
  editorRef,
}) {
  const className = [
    'note-paper',
    appearance.paper,
    isZoomed ? 'is-zoomed' : '',
    isDimmed ? 'is-dimmed' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const linkedWords = isEditing ? collectNoteWords(text, wordIndex) : [];

  function handleClick(event) {
    event.stopPropagation();

    if (!isZoomed) {
      onSelect(date);
    }
  }

  function handleKeyDown(event) {
    if (isZoomed || (event.key !== 'Enter' && event.key !== ' ')) {
      return;
    }

    event.preventDefault();
    onSelect(date);
  }

  return (
    <div
      aria-label={`Note for ${date}`}
      className={className}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role="button"
      style={{
        left: appearance.left,
        top: appearance.top,
        width: appearance.width,
        height: appearance.height,
        transform: `rotate(${appearance.rotation}deg)`,
        zIndex: isZoomed ? 5 : 1,
      }}
      tabIndex={isZoomed ? -1 : 0}
    >
      <Fastener appearance={appearance} />
      <span className="note-stamp">
        {formatStamp(date)}
        {isToday ? ' · 今' : ''}
      </span>
      {isEditing ? (
        <textarea
          className="note-editor"
          onChange={(event) => onChangeText(date, event.target.value)}
          onClick={(event) => event.stopPropagation()}
          placeholder={isToday ? 'What did you learn today?' : 'Write a note for this day…'}
          ref={editorRef}
          value={text}
        />
      ) : (
        <div className="note-text">
          {segmentNoteText(text, wordIndex).map((segment, index) =>
            segment.type === 'word' ? (
              <span className="note-text-word" key={`${segment.value}-${index}`}>
                {segment.value}
              </span>
            ) : (
              <React.Fragment key={index}>{segment.value}</React.Fragment>
            ),
          )}
        </div>
      )}
      {isEditing && linkedWords.length > 0 && (
        <div className="note-word-chips" onClick={(event) => event.stopPropagation()}>
          {linkedWords.map((word) => (
            <a className="note-word-chip" href={`#/words/${word.id}`} key={word.id}>
              <span className="note-word-chip-hanzi">{word.hanzi}</span>
              <span className="note-word-chip-pinyin">{word.pinyin}</span>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
