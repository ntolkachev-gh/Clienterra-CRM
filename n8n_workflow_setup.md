# Настройка n8n Workflow с API Endpoint

## 🎯 Архитектура решения

```
Telegram Bot → n8n Webhook → HTTP Request → Flask API → PostgreSQL
```

## 1. Создание n8n Workflow

### Шаг 1: Webhook Node
- **Node Type**: Webhook
- **HTTP Method**: POST
- **Path**: `text-from-user`
- **Response Mode**: Last Node

### Шаг 2: HTTP Request Node (для сохранения в базу)
- **Node Type**: HTTP Request
- **Method**: POST
- **URL**: `https://clienterra-crm.herokuapp.com/api/save_final_message`
- **Headers**: 
  ```
  Content-Type: application/json
  ```
- **Body**: JSON
  ```json
  {
    "user": {
      "telegram_id": "{{ $json.user.telegram_id }}",
      "first_name": "{{ $json.user.first_name }}",
      "last_name": "{{ $json.user.last_name }}",
      "username": "{{ $json.user.username }}",
      "language_code": "{{ $json.user.language_code }}"
    },
    "message": {
      "text": "{{ $json.message.text }}",
      "message_type": "{{ $json.message.message_type }}",
      "timestamp": "{{ $json.message.timestamp }}",
      "message_id": "{{ $json.message.message_id }}"
    },
    "metadata": {
      "is_first_message": "{{ $json.metadata.is_first_message }}",
      "chat_id": "{{ $json.metadata.chat_id }}"
    }
  }
  ```

### Шаг 3: Telegram Node (для ответа пользователю)
- **Node Type**: Telegram
- **Operation**: Send Message
- **Chat ID**: `{{ $json.metadata.chat_id }}`
- **Text**: Ваш кастомный ответ

## 2. Логика обработки

### Для первого сообщения:
1. Сохраняется в `user_brief` клиента (сырой бриф)
2. Статус клиента меняется на "в работе"
3. Отправляется специальный ответ

### Для обычных сообщений:
1. Сохраняется в таблицу `messages`
2. Отправляется стандартный ответ

## 3. Пример ответов

### Первое сообщение:
```
Спасибо за описание проекта! 🎯

Я понял, что вам нужно: {{ $json.message.text }}

Наш менеджер свяжется с вами в ближайшее время для уточнения деталей.

А пока расскажите подробнее:
• Какой у вас бюджет?
• Когда планируете запуск?
• Есть ли особые требования?
```

### Обычное сообщение:
```
Понял! 📝 Сохранил вашу информацию.

Продолжайте рассказывать о проекте, а я соберу все детали для наших специалистов.
```

## 4. Тестирование

### Запустите тестовый скрипт:
```bash
chmod +x test_final_message_api.sh
./test_final_message_api.sh
```

### Проверьте веб-интерфейс:
- Откройте `https://clienterra-crm.herokuapp.com`
- Войдите в систему
- Проверьте список клиентов

## 5. Преимущества этого подхода

✅ **Централизованное хранение** - все данные в одной базе
✅ **Автоматическое создание клиентов** - не нужно вручную добавлять
✅ **Гибкая логика** - можно настроить разные ответы
✅ **Простота интеграции** - один HTTP запрос
✅ **Масштабируемость** - легко добавить новые поля

## 6. Структура данных в базе

### Таблица `client`:
- `telegram_id` - ID пользователя в Telegram
- `name` - полное имя
- `user_brief` - сырой бриф от пользователя (первое сообщение)
- `project_description` - обработанное описание проекта
- `status` - статус (новый → в работе → завершён)

### Таблица `message`:
- `client_id` - связь с клиентом
- `message_text` - текст сообщения
- `is_from_bot` - от бота или пользователя
- `timestamp` - время отправки 