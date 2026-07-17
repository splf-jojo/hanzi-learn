# Chinese Words

Локальное веб-приложение для изучения китайских слов и иероглифов.

![Страница слова](docs/screenshots/word-detail.png)

## Возможности

- словарь: 302 слова и выражения;
- pinyin и перевод для каждого слова;
- 300 примеров с подсветкой изучаемого слова;
- разбор слов на отдельные иероглифы;
- 19 тематических групп;
- шесть уровней знания слова от `New` до `Mastered`;
- карточки по тематическим группам;
- заметки по дням с распознаванием слов из словаря;
- хранение прогресса и заметок в PostgreSQL.

| Словарь | Карточки |
| --- | --- |
| ![Список слов](docs/screenshots/word-library.png) | ![Режим карточек](docs/screenshots/flashcards.png) |

## Стек

- React 18, Vite 5, Tailwind CSS 3;
- FastAPI, SQLAlchemy 2;
- PostgreSQL.

## Запуск

Требования: Python 3.11+, Node.js 20+ и PostgreSQL.

### Backend

```powershell
cd C:\work\chinese_app\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Создайте `backend\.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/chinese
```

Создайте базу, загрузите данные и запустите API:

```powershell
createdb -h localhost -U postgres chinese
python -m app.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Frontend

```powershell
cd C:\work\chinese_app\frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

Приложение: [http://127.0.0.1:5174](http://127.0.0.1:5174)

Подробная инструкция для Windows и WSL: [START_PROJECT.md](START_PROJECT.md).

## Управление

| Экран | Действие | Клавиши |
| --- | --- | --- |
| Страница слова | Предыдущее или следующее слово | `←` / `→` |
| Карточки | Предыдущая или следующая карточка | `A` / `D` или `←` / `→` |
| Карточки | Перевернуть карточку | `Space` или `↑` |
| Заметки | Вернуться к списку заметок | `Esc` |
| Заметки | Перейти между днями | `←` / `→` вне редактора |

## Структура

```text
frontend/
  src/components/    страницы и UI-компоненты
  src/data/api.js    запросы к backend

backend/
  app/main.py        FastAPI endpoints
  app/models.py      SQLAlchemy models
  app/seed.py        импорт данных в PostgreSQL
  data/*.md          слова, примеры и группы
  static/photos/     изображения слов
```

Frontend получает словарь через `/api/data`. Изменения уровней знания и заметок сохраняются отдельными API-запросами.

## Ограничения

- используется один локальный профиль `local`;
- нет авторизации и синхронизации;
- нет алгоритма интервальных повторений;
- страницы `Radicals` и `Progress` пока не реализованы;
- `backend/ai.py` не используется при обычном запуске приложения.
