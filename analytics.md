# Аналитика

## 1. Основные метрики

### 1.1. Метрики платформы
- **Active Users** - количество активных пользователей
- **Total Deals** - общее количество сделок
- **Deals by Status** - распределение сделок по статусам

### 1.2. Метрики сделок
- **Average Deal Value** - средняя стоимость сделки
- **Average Deal Duration** - средняя длительность сделки (в днях)
- **Deal Success Rate** - процент завершенных сделок

### 1.3. Метрики поставщиков
- **Active Suppliers** - количество активных поставщиков
- **Top Suppliers** - топ-5 поставщиков по количеству сделок

---

## 2. Базовые отчёты

### 2.1. Отчёт по сделкам
```
GET /api/v1/analytics/deals
```

Ответ:
```json
{
  "totalDeals": 150,
  "byStatus": {
    "published": 20,
    "orderCreated": 30,
    "completed": 50
  },
  "averageValue": 2500000,
  "successRate": 85
}
```

### 2.2. Отчёт по пользователям
```
GET /api/v1/analytics/users
```

Ответ:
```json
{
  "activeUsers": 320,
  "suppliers": 45,
  "customers": 275
}
```

---

## 3. Сбор данных

### 3.1. Источники
- **PostgreSQL** - данные о пользователях, сделках, авто
- **Blockchain** - история статусов сделок

### 3.2. Формат события
```typescript
interface AnalyticsEvent {
  eventType: string;      // "deal_created", "status_changed"
  userId?: string;
  dealId?: string;
  timestamp: string;
}
```
