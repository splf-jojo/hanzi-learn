import React, { useMemo } from 'react';
import LinkedWordTerm from '../words/LinkedWordTerm.jsx';

const GROUP_WORD_PREVIEW_LIMIT = 24;

export default function GroupsPage({ groups, words }) {
  const wordsById = useMemo(() => new Map(words.map((word, index) => [word.id, { ...word, index }])), [words]);

  function openGroup(groupWords, groupId) {
    if (!groupWords.length) {
      return;
    }

    window.location.hash = `#/groups/${groupId}/words/${groupWords[0].id}`;
  }

  return (
    <section className="min-h-full pr-2">
      <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4 pb-24">
        {groups.map((group) => {
          const groupWords = group.words.map((id) => wordsById.get(id)).filter(Boolean);
          const previewWords = groupWords.slice(0, GROUP_WORD_PREVIEW_LIMIT);
          const hiddenWordCount = Math.max(0, groupWords.length - previewWords.length);

          return (
            <article
              className="min-h-[172px] cursor-pointer overflow-hidden rounded border border-[rgba(39,40,38,0.09)] bg-[rgba(255,255,252,0.76)] p-5 shadow-[0_10px_28px_rgba(28,28,26,0.05)] transition hover:-translate-y-0.5 hover:border-[rgba(178,42,34,0.24)] hover:shadow-[0_16px_32px_rgba(28,28,26,0.08)]"
              key={group.id}
              onClick={() => openGroup(groupWords, group.id)}
              onKeyDown={(event) => {
                if (event.target !== event.currentTarget) {
                  return;
                }

                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  openGroup(groupWords, group.id);
                }
              }}
              role="link"
              tabIndex={0}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <h1 className="m-0 [font-family:Georgia,Times_New_Roman,serif] text-[clamp(22px,3vw,30px)] font-bold leading-tight text-[#20201e]">
                    {group.name}
                  </h1>
                  <p className="mt-1 mb-0 text-xs font-bold leading-none text-[#6b6b64]">
                    {groupWords.length} words
                  </p>
                </div>
                <span className="grid h-8 min-w-8 shrink-0 place-items-center rounded-sm bg-[rgba(177,43,36,0.08)] px-2 text-sm font-bold leading-none text-[#b22a22]">
                  {group.badge ?? group.id}
                </span>
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                {previewWords.map((word) => (
                  <span
                    className="grid min-w-[76px] grid-cols-1 gap-1 rounded border border-[rgba(52,52,49,0.1)] bg-white/70 px-3 py-2 transition hover:-translate-y-0.5 hover:border-[rgba(178,42,34,0.24)] hover:shadow-[0_10px_22px_rgba(28,28,26,0.07)]"
                    key={word.id}
                  >
                    <LinkedWordTerm
                      characterClassName="transition hover:text-[#b22a22] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#b22a22]"
                      className="font-hanzi text-2xl font-bold leading-none text-[#161615] [overflow-wrap:anywhere]"
                      stopPropagation
                      word={word}
                      wordHref={`#/groups/${group.id}/words/${word.id}`}
                    />
                    {word.pinyin && (
                      <a
                        className="truncate text-xs font-bold leading-tight text-[#b22a22]"
                        href={`#/groups/${group.id}/words/${word.id}`}
                        onClick={(event) => event.stopPropagation()}
                      >
                        {word.pinyin}
                      </a>
                    )}
                  </span>
                ))}
                {hiddenWordCount > 0 && (
                  <span className="grid min-w-[76px] place-items-center rounded border border-[rgba(52,52,49,0.1)] bg-white/50 px-3 py-2 text-sm font-bold text-[#6b6b64]">
                    +{hiddenWordCount}
                  </span>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
