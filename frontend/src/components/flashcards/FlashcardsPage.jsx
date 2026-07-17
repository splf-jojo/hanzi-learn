import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const FLIP_TRANSITION_MS = 250;

function groupHref(groupName) {
  return `#/flashcards/${encodeURIComponent(groupName)}`;
}

function wordsForGroup(group, wordsById) {
  return group.words.map((id) => wordsById.get(id)).filter(Boolean);
}

function shuffleWords(words) {
  const shuffledWords = [...words];

  for (let index = shuffledWords.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    [shuffledWords[index], shuffledWords[randomIndex]] = [shuffledWords[randomIndex], shuffledWords[index]];
  }

  return shuffledWords;
}

function isEditableTarget(target) {
  if (!(target instanceof HTMLElement)) {
    return false;
  }

  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
}

function FlashcardGroups({ groups, words }) {
  const wordsById = useMemo(() => new Map(words.map((word) => [word.id, word])), [words]);

  return (
    <section className="min-h-full pr-2 pb-24">
      <div className="grid gap-3">
        {groups.map((group) => {
          const groupWords = wordsForGroup(group, wordsById);

          return (
            <a
              className="grid min-h-[112px] grid-cols-[minmax(190px,260px)_1fr] items-center gap-5 rounded border border-[rgba(39,40,38,0.09)] bg-[rgba(255,255,252,0.76)] px-5 py-4 shadow-[0_10px_28px_rgba(28,28,26,0.05)] transition hover:-translate-y-0.5 hover:border-[rgba(178,42,34,0.24)] hover:shadow-[0_16px_32px_rgba(28,28,26,0.08)] max-[760px]:grid-cols-1"
              href={groupHref(group.name)}
              key={group.id}
            >
              <h1 className="m-0 [font-family:Georgia,Times_New_Roman,serif] text-[clamp(22px,3vw,30px)] font-bold leading-tight text-[#20201e]">
                {group.name}
              </h1>
              <div className="flex flex-wrap justify-end gap-2 max-[760px]:justify-start">
                {groupWords.slice(0, 18).map((word) => (
                  <span
                    className="rounded border border-[rgba(52,52,49,0.1)] bg-white/70 px-3 py-2 font-hanzi text-2xl font-bold leading-none text-[#161615]"
                    key={word.id}
                  >
                    {word.hanzi}
                  </span>
                ))}
                {groupWords.length > 18 && (
                  <span className="rounded bg-[rgba(177,43,36,0.08)] px-3 py-2 text-sm font-bold leading-none text-[#b22a22]">
                    +{groupWords.length - 18}
                  </span>
                )}
              </div>
            </a>
          );
        })}
      </div>
    </section>
  );
}

function FlashcardStudy({ group, words }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const pendingMoveTimeoutRef = useRef(null);
  const pendingMoveDeltaRef = useRef(0);
  const shuffledWords = useMemo(() => shuffleWords(words), [group.id, words]);
  const boundedActiveIndex = shuffledWords.length ? activeIndex % shuffledWords.length : 0;
  const activeWord = shuffledWords[boundedActiveIndex] || null;

  const clearPendingMove = useCallback(() => {
    if (pendingMoveTimeoutRef.current) {
      window.clearTimeout(pendingMoveTimeoutRef.current);
      pendingMoveTimeoutRef.current = null;
    }

    pendingMoveDeltaRef.current = 0;
  }, []);

  const applyMove = useCallback((delta) => {
    setActiveIndex((currentIndex) => (currentIndex + delta + shuffledWords.length) % shuffledWords.length);
    setIsFlipped(false);
  }, [shuffledWords.length]);

  useEffect(() => {
    clearPendingMove();
    setActiveIndex(0);
    setIsFlipped(false);
  }, [clearPendingMove, group.id, words]);

  useEffect(() => clearPendingMove, [clearPendingMove]);

  const move = useCallback((delta) => {
    if (!shuffledWords.length) {
      return;
    }

    if (pendingMoveTimeoutRef.current) {
      pendingMoveDeltaRef.current += delta;
      return;
    }

    if (!isFlipped) {
      applyMove(delta);
      return;
    }

    pendingMoveDeltaRef.current = delta;
    setIsFlipped(false);
    pendingMoveTimeoutRef.current = window.setTimeout(() => {
      const nextDelta = pendingMoveDeltaRef.current;
      pendingMoveTimeoutRef.current = null;
      pendingMoveDeltaRef.current = 0;

      if (nextDelta !== 0) {
        applyMove(nextDelta);
      }
    }, FLIP_TRANSITION_MS);
  }, [applyMove, isFlipped, shuffledWords.length]);

  const flipCard = useCallback(() => {
    if (pendingMoveTimeoutRef.current) {
      return;
    }

    setIsFlipped((value) => !value);
  }, []);

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || isEditableTarget(event.target)) {
        return;
      }

      if (event.code === 'KeyA' || event.key === 'a' || event.key === 'A' || event.key === 'ArrowLeft') {
        event.preventDefault();
        move(-1);
        return;
      }

      if (event.code === 'KeyD' || event.key === 'd' || event.key === 'D' || event.key === 'ArrowRight') {
        event.preventDefault();
        move(1);
        return;
      }

      if (event.code === 'Space' || event.key === ' ' || event.key === 'ArrowUp') {
        event.preventDefault();
        flipCard();
      }
    }

    window.addEventListener('keydown', handleKeyDown);

    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [flipCard, move]);

  if (!activeWord) {
    return null;
  }

  return (
    <section className="relative h-full min-h-0">
      <div className="absolute inset-x-0 top-0 z-10 flex w-full items-center justify-between gap-4">
        <a className="rounded-sm bg-[rgba(177,43,36,0.08)] px-3 py-2 text-sm font-bold text-[#b22a22]" href="#/flashcards">
          {group.name}
        </a>
        <span className="text-sm font-bold text-[#5a5b55]">
          {boundedActiveIndex + 1} / {shuffledWords.length}
        </span>
      </div>

      <div className="grid h-full min-h-0 place-items-center">
        <button
          className="relative aspect-square w-[min(560px,calc(100dvh-220px),100%)] cursor-pointer [perspective:1200px]"
          onClick={flipCard}
          type="button"
        >
          <div
            className={[
              'relative h-full w-full transition-transform duration-[250ms] [transform-style:preserve-3d]',
              isFlipped ? '[transform:rotateY(180deg)]' : '',
            ]
              .filter(Boolean)
              .join(' ')}
          >
            <div className="absolute inset-0 grid place-items-center bg-[#b22a22] shadow-[0_22px_44px_rgba(38,38,35,0.12)] [backface-visibility:hidden] [clip-path:polygon(25%_0,75%_0,100%_25%,100%_75%,75%_100%,25%_100%,0_75%,0_25%)]">
              <span className="max-w-[92%] text-center font-hanzi text-[clamp(96px,16vw,190px)] font-extrabold leading-none text-white [overflow-wrap:anywhere]">
                {activeWord.hanzi}
              </span>
            </div>
            <div className="absolute inset-0 grid place-items-center bg-[rgba(255,255,252,0.9)] px-8 text-center shadow-[0_22px_44px_rgba(38,38,35,0.06)] [backface-visibility:hidden] [clip-path:polygon(25%_0,75%_0,100%_25%,100%_75%,75%_100%,25%_100%,0_75%,0_25%)] [transform:rotateY(180deg)]">
              <div>
                <p className="m-0 whitespace-nowrap [font-family:Times_New_Roman,Georgia,serif] text-[clamp(38px,6vw,64px)] font-bold leading-tight text-[#b22a22]">
                  {activeWord.pinyin}
                </p>
                {activeWord.translation && (
                  <p className="mt-4 mb-0 [font-family:Georgia,Times_New_Roman,serif] text-[clamp(24px,4vw,36px)] leading-tight text-[#20201e]">
                    {activeWord.translation}
                  </p>
                )}
              </div>
            </div>
          </div>
        </button>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-0 mx-auto flex w-full items-center justify-between">
        <button
          aria-label="Previous card"
          className="pointer-events-auto grid aspect-square w-[clamp(76px,9vw,96px)] place-items-center rounded-xl border border-[rgba(67,92,72,0.08)] bg-[#dde8df] text-[#151715] shadow-[0_10px_28px_rgba(31,39,33,0.08)]"
          onClick={() => move(-1)}
          type="button"
        >
          <ChevronLeft aria-hidden="true" size={34} strokeWidth={2.2} />
        </button>
        <button
          aria-label="Next card"
          className="pointer-events-auto grid aspect-square w-[clamp(76px,9vw,96px)] place-items-center rounded-xl border border-[rgba(67,92,72,0.08)] bg-[#dde8df] text-[#151715] shadow-[0_10px_28px_rgba(31,39,33,0.08)]"
          onClick={() => move(1)}
          type="button"
        >
          <ChevronRight aria-hidden="true" size={34} strokeWidth={2.2} />
        </button>
      </div>
    </section>
  );
}

export default function FlashcardsPage({ groups, words, selectedGroupName }) {
  const selectedGroup = selectedGroupName ? groups.find((group) => group.name === selectedGroupName) || null : null;
  const wordsById = useMemo(() => new Map(words.map((word) => [word.id, word])), [words]);
  const selectedGroupWords = useMemo(
    () => (selectedGroup ? wordsForGroup(selectedGroup, wordsById) : []),
    [selectedGroup, wordsById],
  );

  if (selectedGroup) {
    return <FlashcardStudy group={selectedGroup} words={selectedGroupWords} />;
  }

  return <FlashcardGroups groups={groups} words={words} />;
}
