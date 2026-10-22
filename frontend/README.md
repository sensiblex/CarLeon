# CarLeon — фронтенд

React + TypeScript + Tailwind (Vite). Работает с REST API бэкенда (`/api/v1`).

## Запуск

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Бэкенд должен быть запущен на `http://localhost:8000` (`docker compose up`). В dev-режиме запросы `/api` проксируются на бэкенд; адрес меняется через `VITE_PROXY_TARGET` (см. `.env.example`).

Сборка: `npm run build` → `dist/`.

## Страницы

| Маршрут | Что делает |
|---|---|
| `/` | Поиск сделки по трек-коду |
| `/deals` | Список сделок, создание новой |
| `/deals/:trackCode` | Ход сделки, история статусов с номером блока, смена статуса, удаление |
| `/blockchain` | Журнал блоков и проверка целостности цепочки |

## Авторизация

В бэкенде пока нет `/auth`, запись защищена заголовком `X-API-Key`. Ключ вводится в правом верхнем углу (по умолчанию на бэкенде `change-me`) и хранится в localStorage. Чтение открыто.

## Структура

`src/pages` — страницы, `src/components` — UI, `src/services/api.ts` — API-клиент, `src/context` — API-ключ, `src/hooks` — `useAsync`, `src/types` — типы ответов, `src/utils` — статусы и форматирование.
