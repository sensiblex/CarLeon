# Архитектура
## 1. Общая архитектура

```mermaid
flowchart TB
    UI[React Frontend<br/>TypeScript + Tailwind]
    API[FastAPI Backend<br/>Python]
    DB[(PostgreSQL<br/>База данных)]
    SC[Smart Contract<br/>Solidity]
    HH[Hardhat<br/>Локальный блокчейн]

    UI -->|REST API| API
    UI -->|Чтение статусов| SC
    API -->|SQLAlchemy| DB
    API -->|Подпись транзакций| SC
    SC --- HH
```

**Описание:**
- Frontend обращается к Backend через REST API
- Frontend читает статусы напрямую из блокчейна через viem
- Backend хранит данные в PostgreSQL
- Backend подписывает транзакции смены статуса сервисным кошельком

---

## 2. Жизненный цикл сделки

```mermaid
stateDiagram-v2
    [*] --> Published: Поставщик публикует авто
    Published --> OrderCreated: Заказ оформлен
    OrderCreated --> DepositPaid: Депозит оплачен
    DepositPaid --> Purchased: Авто выкуплен
    Purchased --> InTransitOrigin: В пути (страна отправки)
    InTransitOrigin --> Customs: Таможня
    Customs --> InTransitRF: В пути (РФ)
    InTransitRF --> DeliveredCity: Доставлен в город
    DeliveredCity --> ReadyForPickup: Готов к выдаче
    ReadyForPickup --> Completed: Завершено
    Completed --> [*]
```

**Статусы в блокчейне:** 0-9

---

## 3. Структура базы данных

```mermaid
erDiagram
    USERS ||--o{ CARS : publishes
    USERS ||--o{ DEALS : creates
    CARS ||--o{ DEALS : included_in
    
    USERS {
        uuid id PK
        string email
        string password_hash
        string role
        string first_name
        string last_name
    }
    
    CARS {
        uuid id PK
        uuid supplier_id FK
        string brand
        string model
        integer year
        decimal price
        string country
        string photos
    }
    
    DEALS {
        uuid id PK
        uuid car_id FK
        uuid customer_id FK
        uuid supplier_id FK
        integer current_status
        decimal total_amount
        string destination_city
    }
```

---

## 4. Смена статуса сделки

```mermaid
sequenceDiagram
    participant S as Поставщик
    participant UI as Frontend
    participant API as Backend
    participant DB as PostgreSQL
    participant BC as Blockchain
    
    S->>UI: Обновляет статус
    UI->>API: PUT /deals/{id}/status
    API->>DB: Обновление в БД
    API->>BC: Транзакция смены статуса
    BC->>BC: Запись в блок
    BC-->>API: Подтверждение
    API-->>UI: Успех
```