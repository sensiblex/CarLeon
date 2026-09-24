# CarLeon 

## Структура проекта

```
CarLeon/
├── backend/                 # FastAPI бэкенд
│   ├── app/
│   │   ├── api/            # API роуты
│   │   │   └── v1/         # API версия 1
│   │   ├── core/           # Основная конфигурация (безопасность, настройки)
│   │   ├── models/         # SQLAlchemy ORM модели
│   │   ├── schemas/        # Pydantic схемы (request/response)
│   │   ├── services/       # Слой бизнес-логики
│   │   ├── db/             # Управление сессиями БД
│   │   └── main.py         # Точка входа FastAPI приложения
│   ├── tests/              # Тесты бэкенда
│   ├── alembic/            # Миграции БД
│   ├── requirements.txt    # Python зависимости
│   └── .env                # Переменные окружения
│
├── frontend/               # React фронтенд
│   ├── src/
│   │   ├── components/     # Переиспользуемые UI компоненты
│   │   ├── pages/          # Компоненты страниц
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API вызовы
│   │   ├── utils/          # Утилитные функции
│   │   ├── context/        # React context провайдеры
│   │   ├── types/          # TypeScript типы
│   │   └── App.tsx         # Главный React компонент
│   ├── public/             # Статические файлы
│   ├── package.json        # Node зависимости
│   └── .env                # Переменные окружения
│
└── README.md              # Документация проекта
```

## Структура бэкенда (FastAPI)

### `app/api/v1/`
- Определения API endpoints
- Обработчики роутов
- Валидация request/response

### `app/core/`
- Настройки конфигурации
- Безопасность (JWT, хеширование паролей)
- CORS настройки
- Подключение к БД

### `app/models/`
- SQLAlchemy ORM модели
- Определения таблиц БД

### `app/schemas/`
- Pydantic модели для валидации
- Схемы request/response

### `app/services/`
- Бизнес-логика
- Обработка данных
- Интеграции с внешними API

### `app/db/`
- Управление сессиями БД
- Инициализация подключения

## Структура фронтенда (React)

### `src/components/`
- Переиспользуемые UI компоненты
- Atomic design паттерн
- Презентационные компоненты

### `src/pages/`
- Компоненты уровня страниц
- Обработчики роутов
- Сложные UI сборки

### `src/hooks/`
- Custom React hooks
- Управление состоянием
- Hooks для интеграции с API

### `src/services/`
- Функции API клиента
- HTTP запросы к бэкенду
- Логика получения данных

### `src/utils/`
- Helper функции
- Константы
- Форматтеры

### `src/context/`
- React Context провайдеры
- Глобальное управление состоянием
- Контекст аутентификации

### `src/types/`
- Определения TypeScript типов
- Интерфейсы
- Type guards
