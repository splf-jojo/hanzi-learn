export function readHashRoute(hash = window.location.hash || window.location.pathname) {
  const routeValue = hash.startsWith('#') ? hash : `#${hash}`;

  function route(fields) {
    return {
      flashcardsGroupName: null,
      groupId: null,
      wordId: null,
      wordIndex: null,
      characterId: null,
      noteDate: null,
      photoId: null,
      ...fields,
    };
  }

  const noteDateMatch = routeValue.match(/^#\/notes\/(\d{4}-\d{2}-\d{2})$/);
  if (noteDateMatch) {
    return route({
      page: 'notes',
      noteDate: noteDateMatch[1],
    });
  }

  if (routeValue === '#/notes') {
    return route({
      page: 'notes',
    });
  }

  // "flaschcards" — легаси-опечатка, старые ссылки продолжают работать.
  const flashcardsGroupMatch = routeValue.match(/^#\/(?:flashcards|flaschcards)\/(.+)$/);
  if (flashcardsGroupMatch) {
    return route({
      page: 'flashcards',
      flashcardsGroupName: decodeURIComponent(flashcardsGroupMatch[1]),
    });
  }

  if (routeValue === '#/flashcards' || routeValue === '#/flaschcards') {
    return route({
      page: 'flashcards',
    });
  }

  const photoMatch = routeValue.match(/^#\/photos\/([0-9a-fA-F-]+)$/);
  if (photoMatch) {
    return route({
      page: 'photo',
      photoId: photoMatch[1],
    });
  }

  if (routeValue === '#/photos') {
    return route({
      page: 'photos',
    });
  }

  const groupWordIdMatch = routeValue.match(/^#\/(?:groups|gropups)\/(\d+)\/words\/(\d+)$/);
  if (groupWordIdMatch) {
    return route({
      page: 'word',
      groupId: Number(groupWordIdMatch[1]),
      wordId: Number(groupWordIdMatch[2]),
    });
  }

  const groupWordMatch = routeValue.match(/^#\/(?:groups|gropups)\/(\d+)\/word\/(\d+)$/);
  if (groupWordMatch) {
    return route({
      page: 'word',
      groupId: Number(groupWordMatch[1]),
      wordIndex: Number(groupWordMatch[2]),
    });
  }

  const wordIdMatch = routeValue.match(/^#\/words\/(\d+)$/);
  if (wordIdMatch) {
    return route({
      page: 'word',
      wordId: Number(wordIdMatch[1]),
    });
  }

  const wordMatch = routeValue.match(/^#\/word\/(\d+)$/);
  if (wordMatch) {
    return route({
      page: 'word',
      wordIndex: Number(wordMatch[1]),
    });
  }

  const characterMatch = routeValue.match(/^#\/characters\/(\d+)$/);
  if (characterMatch) {
    return route({
      page: 'character',
      characterId: Number(characterMatch[1]),
    });
  }

  if (routeValue === '#/groups' || routeValue === '#/gropups') {
    return route({
      page: 'groups',
    });
  }

  return route({
    page: 'home',
  });
}

export function readHashIndex() {
  const route = readHashRoute();
  return route.page === 'word' ? route.wordIndex : null;
}
