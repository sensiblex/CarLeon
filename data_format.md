# Формат данных

## 1. Структура блока в блокчейне

### 1.1. Структура данных в блоке

```solidity
struct DealStatus {
    uint256 dealId;           // ID сделки
    uint8 status;             // Статус (0-9)
    uint256 timestamp;        // Время изменения
}
```

### 1.2. Статусы сделки

```solidity
enum DealStatus {
    Published,        // 0 - Опубликовано
    OrderCreated,     // 1 - Заказ оформлен
    DepositPaid,      // 2 - Депозит оплачен
    Purchased,        // 3 - Выкуплен
    InTransitOrigin,  // 4 - В пути (страна отправки)
    Customs,          // 5 - Таможня
    InTransitRF,      // 6 - В пути (РФ)
    DeliveredCity,    // 7 - Доставлен в город
    ReadyForPickup,   // 8 - Готов к выдаче
    Completed         // 9 - Завершено
}
```

---

## 2. Форматы передачи данных

### 2.1. Frontend ↔ Backend (REST API)

#### Формат успешного ответа
```json
{
  "success": true,
  "data": { /* данные */ }
}
```

#### Формат ошибки
```json
{
  "success": false,
  "error": "Описание ошибки"
}
```

### 2.2. Backend ↔ Blockchain

Транзакция смены статуса:
```json
{
  "dealId": "123",
  "newStatus": 4,
  "timestamp": 1727184600
}
```

### 2.3. Frontend ↔ Blockchain (чтение)

Frontend читает через viem:
```typescript
interface DealStatus {
  dealId: string;
  status: number;
  timestamp: number;
}
```

---

## 3. Основные сущности

### 3.1. Автомобиль
```typescript
interface Car {
  id: string;
  supplierId: string;
  brand: string;        // BMW, Mercedes
  model: string;        // X5, E-Class
  year: number;
  price: number;        // в RUB
  country: string;      // Германия
  photos: string[];     // URL фото
}
```

### 3.2. Сделка
```typescript
interface Deal {
  id: string;
  carId: string;
  customerId: string;
  supplierId: string;
  currentStatus: number;  // 0-9
  totalAmount: number;
  depositAmount: number;
  destinationCity: string;
}
```

### 3.3. Пользователь
```typescript
interface User {
  id: string;
  email: string;
  role: "customer" | "supplier" | "admin";
  firstName: string;
  lastName: string;
}
```

---

## 4. API эндпоинты

```
POST   /api/v1/auth/login
POST   /api/v1/auth/register
GET    /api/v1/cars
POST   /api/v1/cars
GET    /api/v1/deals
POST   /api/v1/deals
PUT    /api/v1/deals/{id}/status
GET    /api/v1/deals/{id}
```