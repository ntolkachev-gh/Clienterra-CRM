#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
Создает все необходимые таблицы и добавляет админ-пользователя
"""

import os
from app import app, db, User, BotSettings
from werkzeug.security import generate_password_hash

def init_database():
    """Инициализация базы данных"""
    with app.app_context():
        print("Создание таблиц...")
        db.create_all()
        
        # Создание админ-пользователя
        if not User.query.first():
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            print("Создан пользователь admin с паролем admin123")
        
        # Создание настроек бота
        if not BotSettings.query.first():
            settings = BotSettings(
                welcome_message="Привет! Я помогу вам создать идеального Telegram-бота для вашего бизнеса. Расскажите, что вас интересует?"
            )
            db.session.add(settings)
            print("Созданы настройки бота по умолчанию")
        
        db.session.commit()
        print("База данных успешно инициализирована!")

if __name__ == '__main__':
    init_database() 