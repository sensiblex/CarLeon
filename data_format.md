# Формат данных

## 1. Блокчейн (собственная реализация, `backend/app/blockchain/`)

### 1.1. Запись (StatusChange) — событие смены статуса

```json
{
  "deal_id": "deal-1",
  "status": 4,
  "timestamp": 1727184600.123,
  "file_path": null,
  "file_hash": null,
  "content_hash": "3f4d04a7…64 hex"
}
```

- `status` — `DealStatus` 0–9 (см. ниже).
- `file_path` / `file_hash` — необязательная привязка внешнего файла
  (договор, ПТС): `file_hash` = SHA-256 содержимого файла.
- `content_hash` — SHA-256 от полей записи (без самого `content_hash`);
  пересчитывается при проверке, поэтому подмена полей обнаруживается.

### 1.2. Статусы сделки

| Код | Статус            | Код | Статус            |
|-----|-------------------|-----|-------------------|
| 0   | Опубликовано      | 5   | Таможня           |
| 1   | Заказ оформлен    | 6   | В пути (РФ)       |
| 2   | Депозит оплачен   | 7   | Доставлен в город |
| 3   | Выкуплен          | 8   | Готов к выдаче    |
| 4   | В пути (страна отправки) | 9 | Завершено  |

### 1.3. Блок

```json
{
  "index": 1,
  "timestamp": 1727184600.123,
  "previous_hash": "195c95a5…64 hex",
  "hash": "3b407d94…64 hex",
  "transactions": [ { "…StatusChange…" } ]
}
```

- `hash` = SHA-256 от `index + timestamp + previous_hash + transactions`
  (канонический JSON, `sort_keys`).
- `previous_hash` блока `i` = `hash` блока `i-1`; у генезиса (index 0)
  `previous_hash` = `"0"×64`, timestamp и запись фиксированы — поэтому
  чистые ноды одной сети имеют одинаковый хэш генезиса.

### 1.4. Файл цепочки (`CHAIN_JSON_PATH`)

```json
{ "chain": [ { "…Block…" }, … ] }
```

Пишется атомарно (tempfile + rename). При загрузке цепочка целиком
проверяется; повреждённый файл отклоняется с `ChainLoadError`.

## 2. REST API (`/api/v1`)

### 2.1. Конверт ответа

Успех:

```json
{ "success": true, "data": { /* … */ } }
```

Ошибка — стандартный FastAPI `detail`:

```json
{ "detail": "Invalid or missing X-API-Key" }
```

или объект для сетевых ошибок:

```json
{
  "detail": {
    "code": "invalid_block",
    "message": "Полученный блок не прошёл проверку",
    "errors": [
      { "type": "block_hash_mismatch", "message": "…",
        "block_index": 2, "tx_index": null,
        "expected": "…", "actual": "…" }
    ]
  }
}
```

Массив `detail[]` с `msg` — ошибки валидации Pydantic (HTTP 422).

### 2.2. Основные эндпоинты

```
GET    /api/v1/deals                          список сделок
POST   /api/v1/deals                          создать сделку          [key]
GET    /api/v1/deals/{track_code}             сделка по трек-коду
DELETE /api/v1/deals/{track_code}             удалить сделку          [key]

GET    /api/v1/deals/{track_code}/tracking    история точек
POST   /api/v1/deals/{track_code}/tracking    добавить статус        [key]
DELETE /api/v1/deals/{track_code}/tracking/{id}                  [key]

GET    /api/v1/blockchain                     дамп цепочки
GET    /api/v1/blockchain/validate            проверка целостности
GET    /api/v1/blockchain/files/verify        сверка хэшей файлов
GET    /api/v1/blockchain/deals/{deal_id}/history   история по сделке
POST   /api/v1/blockchain/status              запись в цепочку       [key]

GET    /api/v1/network/info                   сведения об узле       [key]
GET    /api/v1/network/peers                  статус известных peer  [key]
GET    /api/v1/network/peers/{id}/info        сведения о peer        [key]
GET    /api/v1/network/peers/{id}/blocks/{h}  блок у peer            [key]
POST   /api/v1/network/peers/{id}/blocks/{h}/send  передать блок     [key]
POST   /api/v1/network/peers/{id}/invalid-block-demo  демо отказа    [key, dev/demo]
POST   /api/v1/network/blocks                 приём блока            [key]
GET    /api/v1/network/blocks/{hash}          блок локальной цепочки [key]
GET    /health                                healthcheck (без ключа)
```

`[key]` — требуется заголовок `X-API-Key`. Чтение бизнес-каталога
открыто (режим «только просмотр»); все `/network/*` — только с ключом,
тем же ключом ноды обращаются друг к другу.

Полный контракт сетевого API — [network_protocol.md](network_protocol.md).

## 3. Сущности PostgreSQL

### 3.1. Deal (сделка)

```typescript
interface Deal {
  id: string            // uuid
  track_code: string    // 4–32 символа, уникальный
  title: string         // автомобиль, до 255
  supplier: string      // до 128
  buyer: string         // до 128
  status: number        // DealStatus 0–9
  created_at: string    // ISO datetime
}
```

### 3.2. TrackingPoint (точка трекинга)

```typescript
interface TrackingPoint {
  id: string
  deal_id: string       // → deals.id
  status: number        // 0–9
  comment: string | null
  tx_hash: string | null    // хэш блока цепочки
  block_index: number | null
  created_at: string
}
```

### 3.3. Блокчейн-записи (StatusChange / Block)

```typescript
interface StatusChange {
  deal_id: string
  status: number
  timestamp: number
  file_path: string | null
  file_hash: string | null
  content_hash: string     // 64 hex
}

interface Block {
  index: number
  timestamp: number
  previous_hash: string    // 64 hex
  hash: string             // 64 hex
  transactions: StatusChange[]
}
```
