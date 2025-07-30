#!/bin/bash

# Тестовый curl для n8n webhook
curl -X POST https://n8n.tech.ai-community.com/webhook/text-from-user \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "telegram_id": 8099856341,
      "first_name": "Nikita",
      "last_name": "Tolkachev",
      "username": "ntolkachev_zennedge",
      "language_code": "ru"
    },
    "message": {
      "text": "Тестовое сообщение для сохранения в PostgreSQL",
      "message_type": "text",
      "timestamp": "2025-07-30T21:50:29+00:00",
      "message_id": 31
    },
    "metadata": {
      "is_first_message": false,
      "chat_id": 8099856341
    }
  }'

echo -e "\n\n--- Пример данных для PostgreSQL ноды ---"
echo "Данные которые приходят в n8n:"
echo "{
  \"user\": {
    \"telegram_id\": 8099856341,
    \"first_name\": \"Nikita\",
    \"last_name\": \"Tolkachev\",
    \"username\": \"ntolkachev_zennedge\",
    \"language_code\": \"ru\"
  },
  \"message\": {
    \"text\": \"Текст сообщения\",
    \"message_type\": \"text\",
    \"timestamp\": \"2025-07-30T21:50:29+00:00\",
    \"message_id\": 31
  },
  \"metadata\": {
    \"is_first_message\": false,
    \"chat_id\": 8099856341
  }
}" 