# How to start the project on Windows

This repo currently has two runtime parts:

- `backend/` - FastAPI API with SQLAlchemy and PostgreSQL.
- `frontend/` - React/Vite app. During local dev it calls `/api/data`; Vite proxies `/api` to the backend at `http://127.0.0.1:8000`.

The backend is no longer an empty placeholder. The live backend entrypoint is `backend/app/main.py`.

## Requirements

- Windows terminal: PowerShell is preferred.
- Python 3.11+ available through `py`.
- Node.js 20+.
- PostgreSQL running locally.

Expected local ports:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5174`

## Backend

Open PowerShell:

```powershell
cd C:\work\chinese_app\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks venv activation, run this in the same terminal and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Create `backend\.env` if it does not exist:

```env
DATABASE_URL=postgresql+psycopg://postgres:123@localhost:5432/chinese
```

Adjust the user, password, host, port, or database name if your local PostgreSQL uses different settings.

Create the database once if it does not exist:

```powershell
createdb -h localhost -U postgres chinese
```

If `createdb` is not in PATH, run it from PostgreSQL's `bin` directory or create the `chinese` database through pgAdmin.

Create tables and import the app data from:

- `backend/data/words.md`
- `backend/data/sentence.md`
- `backend/data/groups.md`

```powershell
python -m app.seed
```

Start the backend:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check it in the browser:

- API health: `http://127.0.0.1:8000/api/health`
- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- All app data: `http://127.0.0.1:8000/api/data`

Current backend endpoints:

- `GET /`
- `GET /api/health`
- `GET /api/words`
- `GET /api/photos/{photo_id}`
- `GET /api/words/{word_id}/photo`
- `PATCH /api/words/{word_id}/photo`
- `GET /api/sentences`
- `GET /api/characters`
- `GET /api/word-characters`
- `GET /api/groups`
- `GET /api/gropups` (legacy alias)
- `PATCH /api/word-progress/{word_id}/knowledge-level`
- `GET /api/data`

Backend startup calls `init_db()`, so missing tables are created automatically. It does not seed data automatically; run `python -m app.seed` after creating the DB or after changing the markdown files.

The normalized learning schema is:

- `words` for full words and phrases (`hanzi`, `pinyin`, `translation`, `description`, `photo_id`).
- `photos` for stored photo metadata (`slug`, `filename`, `content_type`, `alt`, `source`); files are served from `backend/static/photos` through `/api/photo-files/{filename}`.
- `characters` for individual Hanzi glyphs (`glyph`, `pinyin`, `translation`, `description`).
- `word_characters` for ordered links from words to characters, with per-word character pinyin.
- `sentences` plus `word_sentences` for example sentences and the words they demonstrate.
- `groups` plus `group_words` for ordered word groups.
- `user_word_progress` and `user_character_progress` for local learning state.

## Frontend

Open a second PowerShell terminal:

```powershell
cd C:\work\chinese_app\frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

Open:

```text
http://127.0.0.1:5174
```

The current `frontend/vite.config.js` keeps port `5174` strict and proxies `/api` to `http://127.0.0.1:8000`, so start the backend first.

## WSL alternative

Use this only if you intentionally run the project from WSL:

```bash
cd /mnt/c/work/chinese_app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then start the frontend:

```bash
cd /mnt/c/work/chinese_app/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

## Optional AI script

`backend/ai.py` uses OpenAI embeddings and ChromaDB. It is not part of the normal FastAPI startup and is not required for the frontend/backend app.

To run it, add this to `backend\.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Then run:

```powershell
cd C:\work\chinese_app\backend
.\.venv\Scripts\Activate.ps1
python ai.py 我
```

## Common issues

- `connection refused` or database errors: PostgreSQL is not running, the `chinese` database does not exist, or `DATABASE_URL` is wrong.
- Frontend loads but data requests fail: backend is not running on `127.0.0.1:8000`.
- Port `8000` is busy: stop the other process, or change the backend port and update the proxy in `frontend/vite.config.js`.
- Port `5174` is busy: Vite uses `strictPort: true`, so free the port or pass another port and update CORS in `backend/app/main.py`.
- Empty data: run `python -m app.seed` from the `backend` directory.
