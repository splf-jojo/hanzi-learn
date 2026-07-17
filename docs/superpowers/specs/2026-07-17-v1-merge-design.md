# v1: слияние chinese_app + chinese_ocr — дизайн

Дата: 2026-07-17. Статус: утверждён. Репозиторий-цель: `hanzi-learn` (бывш. chinese_app).

## Цель

Один репозиторий, который поднимается одной командой `docker compose up`:
учебный домен (words, sentences, groups, notes, progress) + OCR-домен
(галерея фото, загрузка, CLIP-поиск похожих, OCR-боксы). CI зелёный,
история из осмысленных коммитов.

## Утверждённые решения

- Репозиторий — этот (`chinese_app`); `chinese_ocr` остаётся архивом-донором
  (его рефакторинг закоммичен и запушен отдельно).
- Архитектура бэкенда — слои `api / services / repositories` из chinese_ocr.
- Единый SQLAlchemy ORM для обеих схем (pgvector — через `pgvector.sqlalchemy.Vector`);
  raw SQL из OCR-репозиториев переписывается на ORM.
- Alembic вместо самописных `ALTER TABLE`; одна базовая миграция `0001_initial`
  (включает `CREATE EXTENSION IF NOT EXISTS vector` и ivfflat-индекс).
- Pydantic-схемы на все тела запросов и ответы (уходят три `payload: dict`).
- Логика AI-карточек НЕ переносится: ни эндпоинта `/api/cards`, ни таблицы
  `learning_cards`, ни зависимости `openai`. `backend/ai.py` и `chroma_db/` удаляются.
- Фронт: весь на JS; порт OCR-компонентов TS→JS в стиле chinese_app.
- Чистая БД: новое имя по умолчанию `hanzi` (старая локальная БД `chinese`
  не трогается и не мигрируется). Сид из markdown.
- Опечатки чинятся: `/api/gropups` и ключ `gropups` в `/api/data` удаляются,
  маршрут `#/flaschcards` → `#/flashcards`; алиас
  `PATCH /api/words/{id}/knowledge-level` удаляется (канон —
  `/api/word-progress/{word_id}/knowledge-level`, фронт уже ходит туда).

## Структура бэкенда

```
backend/
  alembic.ini
  migrations/            env.py, versions/0001_initial.py
  requirements.txt       ядро (fastapi, sqlalchemy, psycopg, pgvector, pillow, numpy, ...)
  requirements-ml.txt    paddlepaddle, paddleocr, torch (CPU), open_clip_torch
  requirements-dev.txt   pytest, httpx
  app/
    main.py              create_app(): CORS, request-logging, статика, роутеры, lifespan(character_sync)
    config.py            Settings из env (python-dotenv), get_settings()
    database.py          engine, SessionLocal, Base, get_db
    dependencies.py      синглтоны: ocr_engine, clip_embedder, pending_uploads
    models/              learning.py, notes.py, progress.py, images.py (+ __init__ реэкспорт)
    schemas/             по доменам; формы ответов = текущие serialize_* (совместимость с фронтом)
    api/                 health.py, words.py, photos.py, notes.py, catalog.py, data.py, images.py, uploads.py
    services/            words.py, photos.py, notes.py, catalog.py, learning_data.py,
                         character_sync.py, seeding.py, image_search.py, image_gallery.py, upload_save.py
    repositories/        words.py, photos.py, notes.py, progress.py, catalog.py, images.py
    ocr/                 engine.py, parser.py, geometry.py, uploads.py (read_image_upload)
    clip_service.py
    pending_uploads.py
    request_logging.py
    logging_config.py
    parsers.py           markdown-парсеры (данные в backend/data/*.md)
    seed.py              CLI: python -m app.seed [--if-empty]
  tests/                 conftest.py + tests/services/*
```

Конвенции: сервисы — единственное место бизнес-логики и маппинга ошибок в
HTTPException; роутеры тонкие; репозитории не бросают HTTP-ошибок; блокирующая
работа в OCR-сервисах — через `asyncio.to_thread` (как в chinese_ocr);
ML-библиотеки импортируются лениво внутри engine/embedder (ядро без них
работает, тесты их мокают). `DEFAULT_USER_ID = "local"` сохраняется.

## Модель данных

Учебный домен — 10 таблиц chinese_app как есть (`words`, `photos`, `characters`,
`word_characters`, `sentences`, `word_sentences`, `groups`, `group_words`,
`notes` с `uq_notes_user_date`, `user_word_progress`, `user_character_progress`;
последняя остаётся в схеме под FSRS v2, но в API не выходит).

OCR-домен (UUID PK, как в chinese_ocr):
- `images`: id UUID, filename, content_type, image_bytes BYTEA (deferred),
  image_width/height (CHECK > 0), embedding Vector(512) NOT NULL, created_at TIMESTAMPTZ.
- `ocr_boxes`: id UUID, image_id FK CASCADE, box_order INT, text, confidence FLOAT,
  bbox JSONB, polygon JSONB (координаты нормированы 0..1).
- Индексы: ivfflat cosine на embedding, (image_id, box_order).

## Контракт API (совместимость с текущим фронтом)

Учебный домен — формы ответов в точности как сейчас (см. serialize_* в старом
main.py, включая дублирование `character_id`/`id` в word-character):
`GET /`, `GET /api/health`, `GET /api/words`, `GET /api/photos/{id}`,
`GET|PATCH /api/words/{id}/photo`, `PATCH /api/word-progress/{word_id}/knowledge-level`
(тело `{knowledge_level | knowledgeLevel: 0..5}`, ответ — сериализованное слово),
`GET /api/notes`, `PUT /api/notes/{date}` (пустой/пробельный text ⇒ удаление,
ответ `{note_date, text: "", deleted: true}` — инвариант доски заметок),
`DELETE /api/notes/{date}`, `GET /api/sentences`, `GET /api/characters`,
`GET /api/word-characters`, `GET /api/groups`, `GET /api/data` (без ключа `gropups`).
PATCH photo: поддерживаемые ключи тела `photo_id|photoId`, `photo_slug|photoSlug|slug`,
оба отсутствуют ⇒ отвязка (`{"word_id": id, "photo": null}`).
Статика: `/api/photo-files/*` из `backend/static/photos`.

OCR-домен — как в chinese_ocr, без карточек:
`POST /api/images/search` (multipart file ⇒ CLIP-поиск топ-5 похожих, upload_id
в pending store), `GET /api/images?limit&offset` (`has_more`),
`GET /api/images/{id}`, `GET /api/images/{id}/content` (байты),
`POST /api/uploads/{upload_id}/save` (OCR + сохранение фото/боксов/эмбеддинга).

## Фронтенд

Вкладка **Photo** в сайдбаре → `#/photos` (галерея: сетка превью + плитка
загрузки + «ещё»). Загрузка: превью → похожие изображения (проценты) →
«Добавить фото в базу» → сохранение с OCR → переход к фото. `#/photos/{id}`:
фото с SVG-оверлеем полигонов боксов; клик по боксу — боковая панель просто
со словом (текст бокса), без карточки. Файлы: `src/components/photos/*`
(JS), функции API — в существующий `src/data/api.js`. Стилистика —
существующая (бумага/чернила, Georgia; без акцентных плашек), НЕ тёмная
тема chinese_ocr.

## Docker / CI

- `docker-compose.yml`: `db` (pgvector/pgvector:pg17, healthcheck), `backend`
  (entrypoint: `alembic upgrade head` → `python -m app.seed --if-empty` →
  uvicorn :8000; образ тяжёлый из-за CPU-torch/Paddle — осознанная цена),
  `frontend` (node build → nginx: статика + proxy `/api` и `/api/photo-files` → backend).
- GitHub Actions: job backend — pgvector service container, `pip install -r
  requirements.txt -r requirements-dev.txt` (без ML), alembic upgrade, pytest;
  job frontend — `npm ci && npm run build`.
- Тесты: pytest, сервисный слой обоих доменов против реального Postgres
  (`TEST_DATABASE_URL`, по умолчанию БД `hanzi_test`); OCR-движок и
  CLIP-эмбеддер — моки (fake engine/embedder, подмена синглтонов).

## Конфигурация

`Settings`: `DATABASE_URL` (умолч. `postgresql+psycopg://postgres:123@localhost:5432/hanzi`),
`CORS_ORIGINS` (умолч. localhost:5174), `USE_PADDLEOCR` (умолч. true),
`MAX_IMAGE_MB` (10) / max pixels, CLIP: `ViT-B-32` / `laion2b_s34b_b79k` / cpu / 512,
`LOG_LEVEL`. Никаких OpenAI-переменных в v1. `.env.example` коммитится.

## Гигиена

- `backend/.env` и `chroma_db` в истории git НЕ светились (проверено);
  утёкший ранее артефакт — только отпечаток ключа в истории chinese_ocr
  (`logs.txt`), сам ключ не публиковался. Ротация ключа — рекомендованный
  ручной шаг владельца (ключ в v1 больше не используется кодом).
- Из индекса убраны: `ai.py`, `START_PROJECT.md`, `photo_promt.txt`; с диска —
  `chroma_db/`.

## Готово когда

`docker compose up` на чистой машине поднимает оба домена; CI зелёный;
история — осмысленные мелкие коммиты.
