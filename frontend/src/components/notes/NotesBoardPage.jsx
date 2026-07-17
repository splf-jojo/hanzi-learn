import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Trash2, X } from 'lucide-react';
import { deleteNote, fetchNotes, saveNote } from '../../data/api.js';
import NotePaper from './NotePaper.jsx';
import { boardSize, formatFullDate, noteAppearance, todayIsoDate } from './boardLayout.js';
import { buildWordIndex } from './noteWordLinks.js';

const SAVE_DEBOUNCE_MS = 800;

export default function NotesBoardPage({ words, noteDate }) {
  const today = todayIsoDate();
  const [textByDate, setTextByDate] = useState(null);
  const [camera, setCamera] = useState({ mode: 'overview' });
  const didIntroRef = useRef(false);
  const [viewport, setViewport] = useState({ width: 0, height: 0 });
  const [saveState, setSaveState] = useState('idle');
  const viewportRef = useRef(null);
  const editorRef = useRef(null);
  const pendingSaveRef = useRef(null);
  const saveTimerRef = useRef(null);
  const savedLabelTimerRef = useRef(null);

  const wordIndex = useMemo(() => buildWordIndex(words), [words]);

  const flushPendingSave = useCallback(() => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
    }

    const pending = pendingSaveRef.current;

    if (!pending) {
      return;
    }

    pendingSaveRef.current = null;
    setSaveState('saving');

    saveNote(pending.date, pending.text)
      .then(() => {
        setSaveState('saved');
        clearTimeout(savedLabelTimerRef.current);
        savedLabelTimerRef.current = setTimeout(() => setSaveState('idle'), 1600);
      })
      .catch(() => {
        setSaveState('error');
      });
  }, []);

  useEffect(() => {
    let ignore = false;

    fetchNotes()
      .then((notes) => {
        if (ignore) {
          return;
        }

        const nextTextByDate = new Map();

        for (const note of notes) {
          nextTextByDate.set(note.note_date, note.text);
        }

        setTextByDate(nextTextByDate);
      })
      .catch(() => {
        if (!ignore) {
          setTextByDate(new Map());
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (noteDate) {
      setCamera({ mode: 'zoom', date: noteDate });
    }
  }, [noteDate]);

  const isLoading = textByDate === null;

  useEffect(() => {
    if (didIntroRef.current || isLoading || !viewport.width) {
      return undefined;
    }

    didIntroRef.current = true;
    let innerFrame = null;
    const outerFrame = requestAnimationFrame(() => {
      innerFrame = requestAnimationFrame(() => setCamera({ mode: 'zoom', date: noteDate || today }));
    });

    return () => {
      cancelAnimationFrame(outerFrame);
      if (innerFrame !== null) {
        cancelAnimationFrame(innerFrame);
      }
    };
  }, [isLoading, viewport.width, noteDate, today]);

  useEffect(() => {
    const element = viewportRef.current;

    if (!element) {
      return undefined;
    }

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];

      if (entry) {
        setViewport({ width: entry.contentRect.width, height: entry.contentRect.height });
      }
    });

    observer.observe(element);
    setViewport({ width: element.clientWidth, height: element.clientHeight });

    return () => observer.disconnect();
  }, []);

  useEffect(() => () => {
    flushPendingSave();
    clearTimeout(savedLabelTimerRef.current);
  }, [flushPendingSave]);

  const zoomDate = camera.mode === 'zoom' ? camera.date : null;
  const [editingDate, setEditingDate] = useState(zoomDate);

  useEffect(() => {
    if (zoomDate) {
      setEditingDate(zoomDate);
      return undefined;
    }

    const swapTimer = setTimeout(() => setEditingDate(null), 520);
    return () => clearTimeout(swapTimer);
  }, [zoomDate]);

  const boardDates = useMemo(() => {
    if (!textByDate) {
      return [];
    }

    const dates = new Set();

    for (const [date, text] of textByDate) {
      if (text.trim()) {
        dates.add(date);
      }
    }

    dates.add(today);

    if (zoomDate) {
      dates.add(zoomDate);
    }

    return [...dates].sort((left, right) => (left < right ? 1 : -1));
  }, [textByDate, today, zoomDate]);

  const appearanceByDate = useMemo(() => {
    const appearances = new Map();

    boardDates.forEach((date, index) => {
      appearances.set(date, noteAppearance(date, index));
    });

    return appearances;
  }, [boardDates]);

  const board = boardSize(boardDates.length);

  const selectNote = useCallback(
    (date) => {
      flushPendingSave();
      setCamera({ mode: 'zoom', date });
    },
    [flushPendingSave],
  );

  const showOverview = useCallback(() => {
    flushPendingSave();

    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }

    setCamera({ mode: 'overview' });
  }, [flushPendingSave]);

  const stepNote = useCallback(
    (step) => {
      if (!zoomDate || !boardDates.length) {
        return;
      }

      const currentIndex = boardDates.indexOf(zoomDate);
      const nextIndex = Math.min(boardDates.length - 1, Math.max(0, currentIndex + step));

      if (nextIndex !== currentIndex) {
        selectNote(boardDates[nextIndex]);
      }
    },
    [boardDates, selectNote, zoomDate],
  );

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        if (camera.mode === 'zoom') {
          event.preventDefault();
          showOverview();
        }

        return;
      }

      if (event.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (camera.mode === 'zoom' && event.key === 'ArrowLeft') {
        event.preventDefault();
        stepNote(-1);
      } else if (camera.mode === 'zoom' && event.key === 'ArrowRight') {
        event.preventDefault();
        stepNote(1);
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [camera.mode, showOverview, stepNote]);

  useEffect(() => {
    if (!zoomDate || !textByDate) {
      return undefined;
    }

    const focusTimer = setTimeout(() => {
      const editor = editorRef.current;

      if (editor) {
        editor.focus({ preventScroll: true });
        const length = editor.value.length;
        editor.setSelectionRange(length, length);
      }
    }, 500);

    return () => clearTimeout(focusTimer);
  }, [zoomDate, textByDate]);

  function handleChangeText(date, text) {
    setTextByDate((current) => {
      const next = new Map(current);
      next.set(date, text);
      return next;
    });

    pendingSaveRef.current = { date, text };
    clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(flushPendingSave, SAVE_DEBOUNCE_MS);
  }

  function handleDelete() {
    if (!zoomDate) {
      return;
    }

    const confirmed = window.confirm('Remove this note from the board?');

    if (!confirmed) {
      return;
    }

    if (pendingSaveRef.current?.date === zoomDate) {
      pendingSaveRef.current = null;
      clearTimeout(saveTimerRef.current);
    }

    deleteNote(zoomDate).catch(() => {});
    setTextByDate((current) => {
      const next = new Map(current);
      next.delete(zoomDate);
      return next;
    });
    setCamera({ mode: 'overview' });
  }

  const transform = useMemo(() => {
    if (!viewport.width || !viewport.height) {
      return null;
    }

    if (camera.mode === 'zoom') {
      const appearance = appearanceByDate.get(camera.date);

      if (appearance) {
        const scale = Math.min(
          2.4,
          Math.max(1.05, Math.min((viewport.width * 0.66) / appearance.width, (viewport.height * 0.8) / appearance.height)),
        );
        const translateX = viewport.width / 2 - appearance.centerX * scale;
        const translateY = viewport.height / 2 - appearance.centerY * scale;
        return `translate(${translateX}px, ${translateY}px) scale(${scale})`;
      }
    }

    const scale = Math.min((viewport.width * 0.94) / board.width, (viewport.height * 0.92) / board.height);
    const translateX = (viewport.width - board.width * scale) / 2;
    const translateY = (viewport.height - board.height * scale) / 2;
    return `translate(${translateX}px, ${translateY}px) scale(${scale})`;
  }, [appearanceByDate, board.height, board.width, camera, viewport]);

  return (
    <div className="notes-page">
      <div className="notes-viewport" onClick={showOverview} ref={viewportRef}>
        {!isLoading && transform && (
          <div className="notes-board" style={{ width: board.width, height: board.height, transform }}>
            <div className="notes-cork" />
            <span aria-hidden="true" className="notes-corner corner-tl" />
            <span aria-hidden="true" className="notes-corner corner-tr" />
            <span aria-hidden="true" className="notes-corner corner-br" />
            <span aria-hidden="true" className="notes-corner corner-bl" />
            <span className="notes-plaque" title="Study notes">
              学习笔记
            </span>
            {boardDates.map((date) => (
              <NotePaper
                appearance={appearanceByDate.get(date)}
                date={date}
                editorRef={date === zoomDate ? editorRef : null}
                isDimmed={Boolean(zoomDate) && date !== zoomDate}
                isEditing={date === editingDate}
                isToday={date === today}
                isZoomed={date === zoomDate}
                key={date}
                onChangeText={handleChangeText}
                onSelect={selectNote}
                text={textByDate.get(date) || ''}
                wordIndex={wordIndex}
              />
            ))}
          </div>
        )}
        {isLoading && <p className="notes-loading">Loading notes…</p>}
      </div>
      {editingDate && (
        <div
          className={`notes-toolbar ${camera.mode === 'zoom' ? '' : 'is-hidden'}`}
          onClick={(event) => event.stopPropagation()}
        >
          <button
            aria-label="Previous note"
            className="notes-toolbar-button"
            disabled={boardDates.indexOf(zoomDate || editingDate) <= 0}
            onClick={() => stepNote(-1)}
            type="button"
          >
            <ChevronLeft aria-hidden="true" size={16} />
          </button>
          <span className="notes-toolbar-date">
            {formatFullDate(zoomDate || editingDate)}
            {saveState === 'saving' && <em className="notes-save-state">Saving…</em>}
            {saveState === 'saved' && <em className="notes-save-state">Saved</em>}
            {saveState === 'error' && <em className="notes-save-state is-error">Save failed</em>}
          </span>
          <button
            aria-label="Next note"
            className="notes-toolbar-button"
            disabled={boardDates.indexOf(zoomDate || editingDate) >= boardDates.length - 1}
            onClick={() => stepNote(1)}
            type="button"
          >
            <ChevronRight aria-hidden="true" size={16} />
          </button>
          <button
            aria-label="Remove note from board"
            className="notes-toolbar-button is-danger"
            onClick={handleDelete}
            type="button"
          >
            <Trash2 aria-hidden="true" size={15} />
          </button>
          <button
            aria-label="Back to the board"
            className="notes-toolbar-button"
            onClick={showOverview}
            type="button"
          >
            <X aria-hidden="true" size={16} />
          </button>
        </div>
      )}
      {!isLoading && (
        <p className={`notes-hint ${camera.mode === 'overview' ? '' : 'is-hidden'}`}>
          Click a note to zoom in · today’s note is always waiting
        </p>
      )}
    </div>
  );
}
