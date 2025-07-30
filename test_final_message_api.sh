#!/bin/bash

echo "🧪 Тестирование API endpoint для сохранения финального сообщения"
echo "================================================================"

# URL вашего приложения на Heroku
APP_URL="https://clienterra-crm.herokuapp.com"

# Тест 1: Первое сообщение пользователя
echo -e "\n1️⃣ Тест: Первое сообщение пользователя"
curl -X POST "$APP_URL/api/save_final_message" \
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
      "text": "Хочу создать бота для интернет-магазина с функциями каталога, корзины и оплаты",
      "message_type": "text",
      "timestamp": "2025-07-30T21:50:29+00:00",
      "message_id": 31
    },
    "metadata": {
      "is_first_message": true,
      "chat_id": 8099856341
    }
  }'

echo -e "\n\n2️⃣ Тест: Обычное сообщение пользователя"
curl -X POST "$APP_URL/api/save_final_message" \
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
      "text": "Также нужна интеграция с CRM системой",
      "message_type": "text",
      "timestamp": "2025-07-30T21:51:00+00:00",
      "message_id": 32
    },
    "metadata": {
      "is_first_message": false,
      "chat_id": 8099856341
    }
  }'

echo -e "\n\n3️⃣ Тест: Новый пользователь"
curl -X POST "$APP_URL/api/save_final_message" \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "telegram_id": 1234567890,
      "first_name": "Анна",
      "last_name": "Петрова",
      "username": "anna_pet",
      "language_code": "ru"
    },
    "message": {
      "text": "Нужен бот для записи клиентов в салон красоты",
      "message_type": "text",
      "timestamp": "2025-07-30T21:52:00+00:00",
      "message_id": 33
    },
    "metadata": {
      "is_first_message": true,
      "chat_id": 1234567890
    }
  }'

echo -e "\n\n✅ Тестирование завершено!"
echo "Проверьте веб-интерфейс для просмотра сохраненных данных" 