# Hanzi Learn

Локальное веб-приложение для изучения китайских слов и иероглифов —
теперь вместе с фото-режимом: галерея снимков, поиск похожих изображений
(CLIP) и распознавание иероглифов на фото (PaddleOCR).

![Страница слова](docs/screenshots/word-detail.png)

## Возможности

- словарь: 302 слова и выражения, pinyin, перевод, разбор на иероглифы;
- 300 примеров с подсветкой изучаемого слова, 19 тематических групп;
- шесть уровней знания слова от `New` до `Mastered`, карточки по группам;
- заметки по дням с распознаванием слов из словаря;
- **Photo**: загрузка фото, топ-5 похожих снимков из базы (CLIP + pgvector),
  OCR-боксы поверх фото (PaddleOCR), клик по боксу показывает распознанное слово;
- всё в PostgreSQL (включая изображения и эмбеддинги).

| Словарь | Карточки |
| --- | --- |
| ![Список слов](docs/screenshots/word-library.png) | ![Режим карточек](docs/screenshots/flashcards.png) |

## Стек

- React 18, Vite 5, Tailwind CSS 3;
- FastAPI, SQLAlchemy 2, Alembic, Pydantic 2;
- PostgreSQL + pgvector;
- PaddleOCR, open_clip (CPU).

## Запуск в Docker (одна команда)

Требуется только Docker:

```bash
docker compose up
```

- приложение: http://localhost:8080
- API/Swagger: http://localhost:8000/docs

Первый запуск долгий: образ бэкенда содержит CPU-сборки torch и Paddle,
а веса CLIP/OCR докачиваются при первом использовании (кэшируются в volume).
Схема накатывается Alembic'ом, словарь сеется из markdown автоматически.

## Локальная разработка

Требования: Python 3.12+, Node.js 20+, PostgreSQL 16+ с расширением pgvector.

### Backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
# OCR/CLIP по желанию (тяжёлые): pip install -r requirements-ml.txt
```

Создайте `backend\.env` (см. `.env.example`):

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/hanzi
USE_PADDLEOCR=false
```

Создайте базу, накатите схему, загрузите данные, запустите API:

```powershell
createdb -h localhost -U postgres hanzi
python -m alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Приложение: http://localhost:5174 (запросы `/api` проксируются на бэкенд).

## Тесты

Сервисный слой обоих доменов, OCR и CLIP замоканы; нужна тестовая БД
(`hanzi_test` по умолчанию, см. `TEST_DATABASE_URL`):

```powershell
cd backend
python -m pytest
```

## Архитектура

```
backend/app/
  api/           тонкие роутеры FastAPI
  services/      бизнес-логика, маппинг в Pydantic-схемы
  repositories/  запросы SQLAlchemy ORM
  models/        таблицы (учебный домен + images/ocr_boxes c pgvector)
  schemas/       контракты запросов/ответов
  ocr/           PaddleOCR: движок, парсер, геометрия (ленивая загрузка)
backend/migrations/   Alembic
backend/data/         словарь в markdown (источник истины, python -m app.seed)
frontend/src/         React, hash-роутинг, вкладки Home/Groups/Notes/Flashcards/Photo
```

Дизайн слияния: `docs/superpowers/specs/2026-07-17-v1-merge-design.md`,
план развития: `ROADMAP.md`.

## Ограничения

- один пользователь (`local`), авторизации нет;
- интервальные повторения (FSRS) — в планах (v2), сейчас только уровни знания;
- страницы `Radicals`/`Progress` из навигации пока не реализованы.
