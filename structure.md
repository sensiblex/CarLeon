# CarLeon

## Структура проекта

```
CarLeon/
├── backend/                  # FastAPI бэкенд (один Docker-образ = одна нода)
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/           # REST-эндпоинты v1
│   │   │   │   ├── deals.py          # сделки (CRUD)
│   │   │   │   ├── tracking.py       # точки трекинга + запись в цепочку
│   │   │   │   ├── blockchain.py     # чтение/проверка цепочки
│   │   │   │   └── network.py        # узел↔узел: info, peers, блоки
│   │   │   ├── deps.py        # зависимости FastAPI (сервисы)
│   │   │   └── router.py      # сборка /api/v1
│   │   ├── blockchain/        # Собственный блокчейн
│   │   │   ├── block.py       # Block: хэш, сериализация
│   │   │   ├── chain.py       # Blockchain: валидация, добавление блоков
│   │   │   ├── storage.py     # JSON-хранилище (атомарная запись, загрузка)
│   │   │   └── transaction.py # StatusChange, DealStatus, хэши файлов
│   │   ├── core/              # config (env), security (X-API-Key)
│   │   ├── models/            # SQLAlchemy ORM: Deal, TrackingPoint
│   │   ├── schemas/           # Pydantic-схемы запросов/ответов
│   │   ├── services/          # бизнес-логика
│   │   │   ├── blockchain_service.py  # записи в цепочку, приём peer-блоков
│   │   │   ├── network_service.py     # HTTP-клиент пиров, проверка совместимости
│   │   │   ├── deal_service.py
│   │   │   └── tracking_service.py
│   │   ├── db/                # engine, сессии, Base
│   │   └── main.py            # FastAPI app, lifespan
│   ├── tests/                 # pytest: chain, API, сеть (10 тестов), трекинг
│   ├── alembic/               # миграции БД (сейчас create_all на старте)
│   ├── demo.py                # консольное демо блокчейна (одна нода)
│   ├── data/                  # runtime JSON-цепочки (gitignored)
│   ├── Dockerfile             # python:3.13-slim + uvicorn
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                  # React SPA (Vite + Tailwind)
│   ├── src/
│   │   ├── components/        # Layout, StatusBadge, StatusProgress, ui
│   │   ├── pages/             # TrackPage, DealsPage, DealPage,
│   │   │                      # ChainPage, NetworkPage (демо обмена блоками)
│   │   ├── hooks/             # useAsync
│   │   ├── services/api.ts    # API-клиент
│   │   ├── utils/             # статусы, форматирование
│   │   ├── context/           # ApiKeyContext (X-API-Key)
│   │   └── types/             # TypeScript-типы ответов API
│   ├── Dockerfile             # multi-stage: vite build → nginx
│   ├── nginx.conf             # статика + прокси /api → node-a:8000
│   └── package.json
│
├── docker-compose.yml         # node-a :8000, node-b :8001, frontend :3001, postgres
├── architecture.md            # общая архитектура
├── network_architecture.md    # сетевое взаимодействие нод (спринт 4)
├── network_protocol.md        # контракт peer-API
├── network_test_scenarios.md  # позитивные/негативные сценарии
├── data_format.md             # форматы блоков, записей, API
├── analytics.md               # целевые метрики и отчёты
├── structure.md               # этот файл
└── README.md
```

## Ключевые потоки

- **Смена статуса**: `POST /deals/{track}/tracking` → запись `TrackingPoint`
  в PostgreSQL + `StatusChange` в новый блок JSON-цепочки (`tx_hash`,
  `block_index` проставляются в точку трекинга).
- Обмен блоками между нодами и модель доступа — см.
  [network_architecture.md](network_architecture.md) и
  [network_protocol.md](network_protocol.md).
