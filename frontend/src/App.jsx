import React, { useEffect, useMemo, useState } from 'react';
import CharacterDetail from './components/characters/CharacterDetail.jsx';
import FlashcardsPage from './components/flashcards/FlashcardsPage.jsx';
import GroupsPage from './components/groups/GroupsPage.jsx';
import NotesBoardPage from './components/notes/NotesBoardPage.jsx';
import PhotoDetailPage from './components/photos/PhotoDetailPage.jsx';
import PhotosPage from './components/photos/PhotosPage.jsx';
import Sidebar from './components/sidebar/Sidebar.jsx';
import WordDetail from './components/words/WordDetail.jsx';
import WordGrid from './components/words/WordGrid.jsx';
import { fetchLearningData, fetchWordPhoto, updateWordKnowledgeLevel } from './data/api.js';
import { readHashRoute } from './utils/hashRoute.js';

const knowledgeGroupDefinitions = [
  { id: 1000, level: 0, glyph: '生', name: '生 · Level 0' },
  { id: 1001, level: 1, glyph: '忘', name: '忘 · Level 1' },
  { id: 1002, level: 2, glyph: '疑', name: '疑 · Level 2' },
  { id: 1003, level: 3, glyph: '记', name: '记 · Level 3' },
  { id: 1004, level: 4, glyph: '熟', name: '熟 · Level 4' },
  { id: 1005, level: 5, glyph: '精', name: '精 · Level 5' },
];

function normalizeKnowledgeLevel(value) {
  if (value === null || value === undefined) {
    return 0;
  }

  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return 0;
  }

  return Math.min(5, Math.max(0, Math.round(numericValue)));
}

function applyWordKnowledgeLevel(words, wordId, knowledgeLevel) {
  return words.map((word) => (word.id === wordId ? { ...word, knowledge_level: knowledgeLevel } : word));
}

export default function App() {
  const [route, setRoute] = useState(readHashRoute);
  const [learningData, setLearningData] = useState({
    words: [],
    sentences: [],
    groups: [],
    characters: [],
    wordCharacters: [],
  });
  const [loadingState, setLoadingState] = useState({ isLoading: true, error: null });
  const [selectedWordPhoto, setSelectedWordPhoto] = useState({ wordId: null, photo: null });
  const { words, sentences, groups, characters } = learningData;
  const allWordIndexes = useMemo(() => words.map((_, index) => index), [words]);
  const wordIndexById = useMemo(() => new Map(words.map((word, index) => [word.id, index])), [words]);
  const characterById = useMemo(() => new Map(characters.map((character) => [character.id, character])), [characters]);
  const selectedIndex = useMemo(() => {
    if (route.page !== 'word') {
      return null;
    }

    if (Number.isInteger(route.wordId)) {
      return wordIndexById.get(route.wordId) ?? null;
    }

    return route.wordIndex;
  }, [route.page, route.wordId, route.wordIndex, wordIndexById]);
  const knowledgeGroups = useMemo(
    () =>
      knowledgeGroupDefinitions.map((group) => ({
        id: group.id,
        name: group.name,
        badge: group.glyph,
        isKnowledgeGroup: true,
        words: words
          .filter((word) => normalizeKnowledgeLevel(word.knowledge_level) === group.level)
          .map((word) => word.id),
      })),
    [words],
  );
  const navigationGroups = useMemo(() => [...knowledgeGroups, ...groups], [knowledgeGroups, groups]);
  const selectedGroup = useMemo(
    () => (Number.isInteger(route.groupId) ? navigationGroups.find((group) => group.id === route.groupId) || null : null),
    [navigationGroups, route.groupId],
  );
  const selectedGroupIndexes = useMemo(() => {
    if (!selectedGroup) {
      return [];
    }

    return selectedGroup.words.map((id) => wordIndexById.get(id)).filter(Number.isInteger);
  }, [selectedGroup, wordIndexById]);
  const selectedWord = useMemo(
    () => (Number.isInteger(selectedIndex) ? words[selectedIndex] : null),
    [selectedIndex, words],
  );
  const selectedWordForDetail = useMemo(
    () =>
      selectedWord
        ? {
            ...selectedWord,
            image: selectedWordPhoto.wordId === selectedWord.id ? selectedWordPhoto.photo?.url || '' : '',
          }
        : null,
    [selectedWord, selectedWordPhoto],
  );
  const isGroupWord = Boolean(selectedGroup && selectedGroupIndexes.includes(selectedIndex));
  const navigationIndexes = isGroupWord ? selectedGroupIndexes : allWordIndexes;
  const groupName = isGroupWord ? selectedGroup.name : 'All words';
  const sidebarPage = isGroupWord ? 'groups' : route.page === 'photo' ? 'photos' : route.page;
  const selectedPosition = selectedWord ? navigationIndexes.indexOf(selectedIndex) : -1;
  const previousIndex =
    selectedPosition >= 0 && navigationIndexes.length
      ? navigationIndexes[(selectedPosition - 1 + navigationIndexes.length) % navigationIndexes.length]
      : null;
  const nextIndex =
    selectedPosition >= 0 && navigationIndexes.length ? navigationIndexes[(selectedPosition + 1) % navigationIndexes.length] : null;
  const previousWord = Number.isInteger(previousIndex) ? words[previousIndex] : null;
  const nextWord = Number.isInteger(nextIndex) ? words[nextIndex] : null;
  const selectedKnowledgeLevel = selectedWord ? normalizeKnowledgeLevel(selectedWord.knowledge_level) : 0;
  const selectedCharacter = route.page === 'character' ? characterById.get(route.characterId) || null : null;

  function selectWord(index) {
    if (!words.length) {
      return;
    }

    const nextIndex = (index + words.length) % words.length;
    const nextHash = getWordHref(nextIndex);
    window.location.hash = nextHash;
    setRoute({
      page: 'word',
      groupId: isGroupWord ? selectedGroup.id : null,
      wordIndex: nextIndex,
    });
  }

  function getWordHref(index) {
    const word = words[index];
    if (!word) {
      return '#/';
    }

    return isGroupWord ? `#/groups/${selectedGroup.id}/words/${word.id}` : `#/words/${word.id}`;
  }

  async function setWordKnowledgeLevel(wordId, level) {
    const nextLevel = normalizeKnowledgeLevel(level);

    setLearningData((currentData) => ({
      ...currentData,
      words: applyWordKnowledgeLevel(currentData.words, wordId, nextLevel),
    }));

    try {
      const updatedWord = await updateWordKnowledgeLevel(wordId, nextLevel);
      const confirmedLevel = normalizeKnowledgeLevel(updatedWord.knowledge_level);

      setLearningData((currentData) => ({
        ...currentData,
        words: applyWordKnowledgeLevel(currentData.words, wordId, confirmedLevel),
      }));
    } catch (error) {
      setLoadingState({ isLoading: false, error });
    }
  }

  useEffect(() => {
    const syncFromHash = () => setRoute(readHashRoute());
    window.addEventListener('hashchange', syncFromHash);
    syncFromHash();

    return () => window.removeEventListener('hashchange', syncFromHash);
  }, []);

  useEffect(() => {
    let ignore = false;

    fetchLearningData()
      .then((nextLearningData) => {
        if (ignore) {
          return;
        }

        setLearningData(nextLearningData);
        setLoadingState({ isLoading: false, error: null });
      })
      .catch((error) => {
        if (ignore) {
          return;
        }

        setLoadingState({ isLoading: false, error });
      });

    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedWord) {
      setSelectedWordPhoto({ wordId: null, photo: null });
      return undefined;
    }

    let ignore = false;
    setSelectedWordPhoto({ wordId: selectedWord.id, photo: null });

    fetchWordPhoto(selectedWord.id)
      .then((photo) => {
        if (!ignore) {
          setSelectedWordPhoto({ wordId: selectedWord.id, photo });
        }
      })
      .catch(() => {
        if (!ignore) {
          setSelectedWordPhoto({ wordId: selectedWord.id, photo: null });
        }
      });

    return () => {
      ignore = true;
    };
  }, [selectedWord]);

  function renderStatus(message, details = null) {
    return (
      <section className="grid h-full place-items-center px-6 text-center">
        <div>
          <p className="m-0 [font-family:Georgia,Times_New_Roman,serif] text-3xl font-bold text-[#20201e]">
            {message}
          </p>
          {details && <p className="mt-2 mb-0 text-sm text-[#5a5b55]">{details}</p>}
        </div>
      </section>
    );
  }

  return (
    <div className="app-shell min-h-screen">
      <Sidebar currentPage={sidebarPage} />
      <main className="content">
        {route.page === 'photos' ? (
          <PhotosPage />
        ) : route.page === 'photo' ? (
          <PhotoDetailPage photoId={route.photoId} />
        ) : loadingState.isLoading ? (
          renderStatus('Loading...')
        ) : loadingState.error ? (
          renderStatus('Data unavailable', loadingState.error.message)
        ) : route.page === 'notes' ? (
          <NotesBoardPage words={words} noteDate={route.noteDate} />
        ) : route.page === 'flashcards' ? (
          <FlashcardsPage groups={groups} words={words} selectedGroupName={route.flashcardsGroupName} />
        ) : route.page === 'groups' ? (
          <GroupsPage groups={navigationGroups} words={words} />
        ) : selectedCharacter ? (
          <CharacterDetail character={selectedCharacter} words={words} />
        ) : selectedWordForDetail ? (
          <WordDetail
            word={selectedWordForDetail}
            previousWord={previousWord}
            nextWord={nextWord}
            previousIndex={previousIndex}
            nextIndex={nextIndex}
            groupName={groupName}
            previousHref={Number.isInteger(previousIndex) ? getWordHref(previousIndex) : null}
            nextHref={Number.isInteger(nextIndex) ? getWordHref(nextIndex) : null}
            sentences={sentences}
            knowledgeLevel={selectedKnowledgeLevel}
            onKnowledgeLevelChange={(level) => setWordKnowledgeLevel(selectedWord.id, level)}
            onPrevious={() => selectWord(previousIndex)}
            onNext={() => selectWord(nextIndex)}
          />
        ) : (
          <WordGrid list={words} />
        )}
      </main>
    </div>
  );
}
