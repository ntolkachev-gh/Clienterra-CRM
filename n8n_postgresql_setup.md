# Настройка PostgreSQL ноды в n8n

## 1. Создание ноды PostgreSQL

1. Добавьте ноду **"PostgreSQL"** в ваш workflow
2. Подключите её после **Webhook** ноды

## 2. Настройка подключения к базе данных

### Параметры подключения:
```
Host: your-postgresql-host.com
Database: your_database_name
User: your_username
Password: your_password
Port: 5432
SSL: Require (для Heroku)
```

### Пример URL для Heroku:
```
postgresql://username:password@host:5432/database_name
```

## 3. Настройка SQL запроса

### Создание таблицы (выполнить один раз):
```sql
CREATE TABLE IF NOT EXISTS telegram_messages (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    username VARCHAR(100),
    language_code VARCHAR(10),
    message_text TEXT,
    message_type VARCHAR(20),
    message_timestamp TIMESTAMP,
    message_id INTEGER,
    is_first_message BOOLEAN,
    chat_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### SQL запрос для вставки данных:
```sql
INSERT INTO telegram_messages (
    telegram_id,
    first_name,
    last_name,
    username,
    language_code,
    message_text,
    message_type,
    message_timestamp,
    message_id,
    is_first_message,
    chat_id
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
);
```

## 4. Настройка параметров в n8n

### Параметры запроса:
```
$1: {{ $json.user.telegram_id }}
$2: {{ $json.user.first_name }}
$3: {{ $json.user.last_name }}
$4: {{ $json.user.username }}
$5: {{ $json.user.language_code }}
$6: {{ $json.message.text }}
$7: {{ $json.message.message_type }}
$8: {{ $json.message.timestamp }}
$9: {{ $json.message.message_id }}
$10: {{ $json.metadata.is_first_message }}
$11: {{ $json.metadata.chat_id }}
```

## 5. Дополнительные настройки

### Опции ноды:
- **Operation**: Execute Query
- **Query**: (вставить SQL запрос выше)
- **Options**: 
  - Return Fields: `*`
  - Query Replacement: `{{ $json.user.telegram_id }}, {{ $json.user.first_name }}, {{ $json.user.last_name }}, {{ $json.user.username }}, {{ $json.user.language_code }}, {{ $json.message.text }}, {{ $json.message.message_type }}, {{ $json.message.timestamp }}, {{ $json.message.message_id }}, {{ $json.metadata.is_first_message }}, {{ $json.metadata.chat_id }}`

## 6. Тестирование

Запустите скрипт `test_n8n_webhook.sh` для тестирования:
```bash
chmod +x test_n8n_webhook.sh
./test_n8n_webhook.sh
```

## 7. Проверка данных

После выполнения workflow проверьте таблицу:
```sql
SELECT * FROM telegram_messages ORDER BY created_at DESC LIMIT 10;
``` 