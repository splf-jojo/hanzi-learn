import { normalizePinyinText } from '../utils/pinyin.js';

const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
const apiBaseUrl = rawApiBaseUrl.replace(/\/$/, '');

function apiUrl(path) {
  return apiBaseUrl ? `${apiBaseUrl}${path}` : path;
}

function normalizeArray(value) {
  return Array.isArray(value) ? value : [];
}

function normalizeWordCharacter(character) {
  return {
    ...character,
    pinyin: normalizePinyinText(character.pinyin),
  };
}

function normalizeWord(word) {
  return {
    ...word,
    pinyin: normalizePinyinText(word.pinyin),
    characters: normalizeArray(word.characters).map(normalizeWordCharacter),
  };
}

function normalizeSentence(sentence) {
  return {
    ...sentence,
    pinyin: normalizePinyinText(sentence.pinyin),
  };
}

function normalizeCharacter(character) {
  return {
    ...character,
    pinyin: normalizePinyinText(character.pinyin),
  };
}

export async function fetchLearningData() {
  const response = await fetch(apiUrl('/api/data'));

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  const data = await response.json();

  return {
    words: normalizeArray(data.words).map(normalizeWord),
    sentences: normalizeArray(data.sentences).map(normalizeSentence),
    groups: normalizeArray(data.groups),
    characters: normalizeArray(data.characters).map(normalizeCharacter),
    wordCharacters: normalizeArray(data.word_characters).map(normalizeWordCharacter),
  };
}

export async function fetchWordPhoto(wordId) {
  const response = await fetch(apiUrl(`/api/words/${wordId}/photo`));

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Word photo request failed with status ${response.status}`);
  }

  const photo = await response.json();

  return {
    ...photo,
    url: photo.url ? apiUrl(photo.url) : '',
  };
}

export async function fetchNotes() {
  const response = await fetch(apiUrl('/api/notes'));

  if (!response.ok) {
    throw new Error(`Notes request failed with status ${response.status}`);
  }

  return response.json();
}

export async function saveNote(noteDate, text) {
  const response = await fetch(apiUrl(`/api/notes/${noteDate}`), {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`Note save failed with status ${response.status}`);
  }

  return response.json();
}

export async function deleteNote(noteDate) {
  const response = await fetch(apiUrl(`/api/notes/${noteDate}`), {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Note delete failed with status ${response.status}`);
  }

  return response.json();
}

export async function updateWordKnowledgeLevel(wordId, knowledgeLevel) {
  const response = await fetch(apiUrl(`/api/word-progress/${wordId}/knowledge-level`), {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ knowledge_level: knowledgeLevel }),
  });

  if (!response.ok) {
    throw new Error(`Knowledge level update failed with status ${response.status}`);
  }

  return response.json();
}
