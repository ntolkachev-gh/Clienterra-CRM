# 🧠 Clienterra CRM - Telegram-бот для сбора информации о клиентах

## 🎯 Описание проекта

Полнофункциональная CRM-система с Telegram-ботом для агентства по разработке ботов. Система автоматически собирает информацию от клиентов, использует ИИ для генерации персонализированных ответов и предоставляет удобный веб-интерфейс для управления лидами.

### ✨ Ключевые возможности

- 🤖 **Умный Telegram-бот** с интеграцией OpenAI GPT-4
- 🔍 **Векторный поиск знаний** через Qdrant для релевантных ответов
- 📊 **Современная CRM-панель** с аналитикой и фильтрацией
- 💬 **Полная история диалогов** с каждым клиентом
- 🎨 **Адаптивный веб-интерфейс** с темной темой
- 🔐 **Безопасная авторизация** и управление пользователями
- ☁️ **Готовность к деплою** на Heroku

---

## 🏗️ Архитектура системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │────│   OpenAI API    │────│   Qdrant DB     │
│                 │    │                 │    │                 │
│ • Обработка     │    │ • GPT-4 ответы  │    │ • База знаний   │
│   сообщений     │    │ • Эмбеддинги    │    │ • Векторный     │
│ • Сбор данных   │    │ • Контекст      │    │   поиск         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         │              ┌─────────────────┐             │
         └──────────────│  PostgreSQL DB  │─────────────┘
                        │                 │
                        │ • Клиенты       │
                        │ • Сообщения     │
                        │ • Настройки     │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   Flask CRM     │
                        │                 │
                        │ • Дашборд       │
                        │ • Аналитика     │
                        │ • Управление    │
                        └─────────────────┘
```

---

## 🚀 Быстрый старт

### 1. Клонирование и установка

```bash
git clone <repository-url>
cd Clienterra-CRM
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` на основе `env_example.txt`:

```bash
cp env_example.txt .env
```

Заполните необходимые переменные:

```env
# База данных
DATABASE_URL=postgresql://username:password@localhost:5432/clienterra_crm

# API ключи
TELEGRAM_BOT_TOKEN=your-bot-token-here
OPENAI_API_KEY=your-openai-api-key-here

# Qdrant
QDRANT_URL=http://localhost:6333

# Безопасность
SECRET_KEY=your-very-secret-key-here
```

### 3. Настройка базы данных

```bash
# Создайте базу данных PostgreSQL
createdb clienterra_crm

# Запустите приложение для создания таблиц
python app.py
```

### 4. Настройка Qdrant и загрузка знаний

```bash
# Запустите Qdrant (через Docker)
docker run -p 6333:6333 qdrant/qdrant

# Создайте коллекцию и загрузите базовые знания
python knowledge_manager.py create_collection
python knowledge_manager.py load knowledge_base.json
```

### 5. Запуск системы

```bash
# Запуск веб-приложения
python app.py

# В отдельном терминале - запуск бота
python telegram_bot.py
```

---

## 📱 Использование

### Веб-интерфейс CRM

1. **Авторизация**: Откройте http://localhost:5000, войдите как `admin`/`admin123`
2. **Дашборд**: Просматривайте статистику и список клиентов
3. **Детали клиента**: Изучайте полную историю диалогов
4. **Настройки**: Редактируйте приветственное сообщение бота

### Telegram-бот

1. Найдите вашего бота в Telegram
2. Отправьте `/start` для начала диалога
3. Бот автоматически будет собирать информацию о ваших потребностях
4. Все диалоги сохраняются в CRM-системе

### Управление базой знаний

```bash
# Просмотр всех знаний
python knowledge_manager.py list

# Добавление нового знания
python knowledge_manager.py add "Новая информация об услуге" "категория"

# Поиск по базе знаний
python knowledge_manager.py search "запрос для поиска"

# Экспорт знаний
python knowledge_manager.py export backup_knowledge.json
```

---

## 🛠️ Технологический стек

### Backend
- **Flask** - веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **PostgreSQL** - основная база данных
- **python-telegram-bot** - API для Telegram

### AI & ML
- **OpenAI GPT-4** - генерация ответов
- **Qdrant** - векторная база данных
- **text-embedding-ada-002** - создание эмбеддингов

### Frontend
- **Bootstrap 5** - UI фреймворк
- **Font Awesome** - иконки
- **Vanilla JavaScript** - интерактивность

### Деплой
- **Heroku** - облачная платформа
- **Gunicorn** - WSGI сервер
- **Docker** - контейнеризация (опционально)

---

## 🌐 Деплой на Heroku

### 1. Подготовка

```bash
# Установите Heroku CLI
# Войдите в аккаунт
heroku login

# Создайте приложение
heroku create your-app-name
```

### 2. Настройка переменных окружения

```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set OPENAI_API_KEY=your-openai-key
heroku config:set TELEGRAM_BOT_TOKEN=your-bot-token
heroku config:set QDRANT_URL=your-qdrant-url
```

### 3. Настройка базы данных

```bash
# Добавьте PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# База данных будет автоматически настроена
```

### 4. Деплой

```bash
git add .
git commit -m "Initial deployment"
git push heroku main

# Масштабирование
heroku ps:scale web=1 worker=1
```

---

## 📊 Структура базы данных

### Таблица `client`
- `id` - уникальный идентификатор
- `telegram_id` - ID пользователя в Telegram
- `name` - имя клиента
- `organization` - организация
- `project_description` - описание проекта
- `required_functions` - требуемые функции
- `traffic_source` - источник трафика
- `status` - статус (новый/в работе/завершён)
- `created_at`, `updated_at` - временные метки

### Таблица `message`
- `id` - уникальный идентификатор
- `client_id` - связь с клиентом
- `message_text` - текст сообщения
- `is_from_bot` - флаг сообщения от бота
- `timestamp` - время отправки
- `attachment_path` - путь к вложению

### Таблица `user`
- `id` - уникальный идентификатор
- `username` - логин пользователя
- `password_hash` - хеш пароля
- `created_at` - время создания

### Таблица `bot_settings`
- `id` - уникальный идентификатор
- `welcome_message` - приветственное сообщение
- `updated_at` - время обновления

---

## 🔧 Настройка и кастомизация

### Изменение системного промпта

Отредактируйте файл `telegram_bot.py`, найдите переменную `system_prompt`:

```python
system_prompt = """Ваш кастомный промпт здесь..."""
```

### Добавление новых функций в CRM

1. Создайте новый маршрут в `app.py`
2. Добавьте соответствующий HTML-шаблон
3. Обновите навигацию в `base.html`

### Расширение базы знаний

```bash
# Добавьте новые знания через JSON
python knowledge_manager.py load new_knowledge.json

# Или добавьте индивидуально
python knowledge_manager.py add "Текст знания" "категория"
```

---

## 🐛 Отладка и мониторинг

### Логи приложения

```bash
# Локальные логи
tail -f app.log

# Логи Heroku
heroku logs --tail
```

### Проверка состояния Qdrant

```bash
curl http://localhost:6333/collections
```

### Мониторинг бота

Бот автоматически логирует все ошибки. Проверьте логи в случае проблем с обработкой сообщений.

---

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

---

## 📄 Лицензия

MIT License - см. файл LICENSE для подробностей.

---

## 📞 Поддержка

При возникновении вопросов или проблем:

1. Проверьте раздел FAQ
2. Создайте Issue в репозитории
3. Свяжитесь с командой разработки

---

## 🎯 Roadmap

- [ ] Интеграция с дополнительными мессенджерами (WhatsApp, Viber)
- [ ] Система уведомлений и напоминаний
- [ ] Расширенная аналитика и отчеты
- [ ] API для интеграции с внешними системами
- [ ] Мобильное приложение для CRM
- [ ] Многопользовательский режим с ролями
