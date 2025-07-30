#!/usr/bin/env python3
"""
Миграция для добавления поля user_brief в таблицу client
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def migrate_add_user_brief():
    """Добавляет поле user_brief в таблицу client"""
    
    # Получаем URL базы данных
    database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/clienterra_crm')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print(f"🔗 Подключение к базе данных: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    try:
        # Создаем подключение к базе данных
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Проверяем, существует ли уже поле user_brief
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'client' AND column_name = 'user_brief'
            """))
            
            if result.fetchone():
                print("✅ Поле user_brief уже существует")
                return
            
            # Добавляем поле user_brief (очень большое)
            print("📝 Добавляем поле user_brief (очень большое)...")
            conn.execute(text("""
                ALTER TABLE client 
                ADD COLUMN user_brief TEXT
            """))
            
            # Переносим данные из project_description в user_brief для существующих записей
            print("🔄 Переносим существующие данные...")
            conn.execute(text("""
                UPDATE client 
                SET user_brief = project_description 
                WHERE project_description IS NOT NULL AND user_brief IS NULL
            """))
            
            conn.commit()
            print("✅ Миграция успешно завершена!")
            
            # Показываем статистику
            result = conn.execute(text("SELECT COUNT(*) FROM client WHERE user_brief IS NOT NULL"))
            count = result.fetchone()[0]
            print(f"📊 Обновлено записей: {count}")
            
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Запуск миграции для добавления поля user_brief")
    print("=" * 50)
    migrate_add_user_brief() 