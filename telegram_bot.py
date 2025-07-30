import os
import openai
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import asyncio
import asyncpg
from typing import List, Dict, Any
import aiohttp
import json

# Try to import Qdrant, but don't fail if it's not available
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("Qdrant client недоступен")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')

# Set OpenAI API key
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

class TelegramBot:
    def __init__(self):
        self.qdrant_client = None
        self.collection_name = "knowledge_base"
        self.db_pool = None
        self.qdrant_available = False
        
        # Initialize Qdrant if available and configured
        if QDRANT_AVAILABLE and QDRANT_URL:
            try:
                if QDRANT_API_KEY:
                    self.qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
                else:
                    self.qdrant_client = QdrantClient(url=QDRANT_URL)
                logger.info("Qdrant client инициализирован")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать Qdrant: {e}")
        
    async def init_db_pool(self):
        """Инициализация пула подключений к базе данных"""
        if DATABASE_URL:
            try:
                self.db_pool = await asyncpg.create_pool(DATABASE_URL)
                logger.info("Подключение к базе данных установлено")
            except Exception as e:
                logger.error(f"Ошибка подключения к БД: {e}")
        
    async def setup_qdrant_collection(self):
        """Настройка коллекции в Qdrant"""
        if not self.qdrant_client:
            logger.warning("Qdrant недоступен")
            return
            
        try:
            collections = await asyncio.to_thread(self.qdrant_client.get_collections)
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                await asyncio.to_thread(
                    self.qdrant_client.create_collection,
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
                logger.info(f"Создана коллекция {self.collection_name}")
                await self.populate_knowledge_base()
            else:
                logger.info(f"Коллекция {self.collection_name} уже существует")
                
            self.qdrant_available = True
                
        except Exception as e:
            logger.error(f"Ошибка настройки Qdrant: {e}")
            logger.warning("Бот будет работать без базы знаний Qdrant")
            self.qdrant_available = False
    
    async def populate_knowledge_base(self):
        """Заполнение базы знаний информацией об услугах"""
        if not OPENAI_API_KEY or not self.qdrant_client:
            return
            
        knowledge_items = [
            {
                "id": 1,
                "text": "Мы создаем Telegram-ботов для автоматизации бизнес-процессов: прием заказов, консультации клиентов, запись на услуги, уведомления о статусе заказов.",
                "category": "automation"
            },
            {
                "id": 2,
                "text": "Интеграция с CRM системами, базами данных, платежными системами (Stripe, ЮKassa), API сторонних сервисов для полной автоматизации бизнеса.",
                "category": "integrations"
            },
            {
                "id": 3,
                "text": "Боты для интернет-магазинов: каталог товаров, корзина, оформление заказов, отслеживание доставки, система лояльности и скидок.",
                "category": "ecommerce"
            },
            {
                "id": 4,
                "text": "Обучающие боты и боты-помощники: курсы, тесты, напоминания, персональные рекомендации, чат-боты с ИИ для консультаций.",
                "category": "education"
            },
            {
                "id": 5,
                "text": "Боты для управления сообществами: модерация, автоответы, опросы, розыгрыши, система ролей и прав доступа.",
                "category": "community"
            },
            {
                "id": 6,
                "text": "Аналитика и отчетность: сбор статистики использования бота, анализ поведения пользователей, A/B тестирование функций.",
                "category": "analytics"
            }
        ]
        
        for item in knowledge_items:
            try:
                # Получаем эмбеддинг от OpenAI (старый API)
                response = await asyncio.to_thread(
                    openai.Embedding.create,
                    input=item["text"],
                    model="text-embedding-ada-002"
                )
                embedding = response['data'][0]['embedding']
                
                # Добавляем в Qdrant
                await asyncio.to_thread(
                    self.qdrant_client.upsert,
                    collection_name=self.collection_name,
                    points=[
                        PointStruct(
                            id=item["id"],
                            vector=embedding,
                            payload={
                                "text": item["text"],
                                "category": item["category"]
                            }
                        )
                    ]
                )
                logger.info(f"Добавлен элемент знаний: {item['category']}")
                
            except Exception as e:
                logger.error(f"Ошибка добавления знаний: {e}")
    
    async def search_knowledge(self, query: str, limit: int = 3) -> List[str]:
        """Поиск релевантной информации в базе знаний"""
        # Fallback knowledge base
        fallback_knowledge = [
            "Мы создаем Telegram-ботов для автоматизации бизнес-процессов: прием заказов, консультации клиентов, запись на услуги, уведомления о статусе заказов.",
            "Интеграция с CRM системами, базами данных, платежными системами (Stripe, ЮKassa), API сторонних сервисов для полной автоматизации бизнеса.",
            "Боты для интернет-магазинов: каталог товаров, корзина, оформление заказов, отслеживание доставки, система лояльности и скидок."
        ]
        
        if not self.qdrant_available or not OPENAI_API_KEY:
            logger.warning("Qdrant или OpenAI недоступен, возвращаем базовую информацию")
            return fallback_knowledge
        
        try:
            # Получаем эмбеддинг запроса (старый API)
            response = await asyncio.to_thread(
                openai.Embedding.create,
                input=query,
                model="text-embedding-ada-002"
            )
            query_embedding = response['data'][0]['embedding']
            
            # Поиск в Qdrant
            search_result = await asyncio.to_thread(
                self.qdrant_client.search,
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            return [hit.payload["text"] for hit in search_result]
            
        except Exception as e:
            logger.error(f"Ошибка поиска в базе знаний: {e}")
            return fallback_knowledge
    
    async def get_openai_response(self, user_message: str, context: List[str]) -> str:
        """Генерация ответа через OpenAI с контекстом из базы знаний"""
        if not OPENAI_API_KEY:
            return "Извините, сервис временно недоступен. Пожалуйста, свяжитесь с нашим менеджером напрямую."
            
        try:
            context_text = "\n".join(context) if context else "Информация о наших услугах недоступна."
            
            system_prompt = """Ты помощник по продажам агентства по разработке Telegram-ботов. 
            Твоя задача - помочь клиенту понять, какие функции могут быть полезны в его боте.
            
            Веди диалог вежливо и профессионально. Задавай уточняющие вопросы о:
            - Названии компании/организации
            - Сфере деятельности
            - Какие задачи должен решать бот
            - Целевой аудитории
            - Бюджете проекта
            
            Используй информацию из контекста для предложения подходящих решений."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Контекст о наших услугах:\n{context_text}\n\nСообщение клиента: {user_message}"}
            ]
            
            # Используем старый API OpenAI
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка OpenAI: {e}")
            return "Извините, произошла ошибка. Попробуйте еще раз или свяжитесь с нашим менеджером."
    
    async def save_message_to_db(self, telegram_id: int, message_text: str, is_from_bot: bool = False):
        """Сохранение сообщения в базу данных"""
        if not self.db_pool:
            logger.warning("База данных недоступна")
            return
            
        try:
            async with self.db_pool.acquire() as conn:
                # Проверяем, существует ли клиент
                client = await conn.fetchrow(
                    "SELECT id FROM client WHERE telegram_id = $1", telegram_id
                )
                
                if not client:
                    # Создаем нового клиента
                    client_id = await conn.fetchval(
                        """INSERT INTO client (telegram_id, created_at, updated_at) 
                           VALUES ($1, $2, $2) RETURNING id""",
                        telegram_id, datetime.utcnow()
                    )
                else:
                    client_id = client['id']
                    # Обновляем время последней активности
                    await conn.execute(
                        "UPDATE client SET updated_at = $1 WHERE id = $2",
                        datetime.utcnow(), client_id
                    )
                
                # Сохраняем сообщение
                await conn.execute(
                    """INSERT INTO message (client_id, message_text, is_from_bot, timestamp)
                       VALUES ($1, $2, $3, $4)""",
                    client_id, message_text, is_from_bot, datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Ошибка сохранения в БД: {e}")
    
    async def get_welcome_message(self, user_info: dict = None) -> str:
        """Получение приветственного сообщения из настроек"""
        if not self.db_pool:
            message = "Привет! Я помогу вам создать идеального Telegram-бота для вашего бизнеса. Расскажите, что вас интересует?"
        else:
            try:
                async with self.db_pool.acquire() as conn:
                    result = await conn.fetchrow("SELECT welcome_message FROM bot_settings LIMIT 1")
                    if result:
                        message = result['welcome_message']
                    else:
                        message = "Привет! Я помогу вам создать идеального Telegram-бота для вашего бизнеса. Расскажите, что вас интересует?"
            except Exception as e:
                logger.error(f"Ошибка получения настроек: {e}")
                message = "Привет! Я помогу вам создать идеального Telegram-бота для вашего бизнеса. Расскажите, что вас интересует?"
        
        # Заменяем плейсхолдеры на реальные данные пользователя
        if user_info:
            if user_info.get('first_name'):
                message = message.replace('{name}', user_info['first_name'])
            else:
                message = message.replace('{name}', 'пользователь')
                
            if user_info.get('username'):
                message = message.replace('{username}', f"@{user_info['username']}")
            else:
                message = message.replace('{username}', 'пользователь')
        else:
            # Если нет информации о пользователе, заменяем на общие значения
            message = message.replace('{name}', 'пользователь')
            message = message.replace('{username}', 'пользователь')
        
        return message

    async def send_welcome_if_new_user(self, update: Update) -> bool:
        """Отправляет приветствие если пользователь новый"""
        user_id = update.effective_user.id
        user = update.effective_user
        
        # Проверяем, новый ли пользователь
        is_new = await self.is_new_user(user_id)
        
        if is_new:
            # Получаем информацию о пользователе для персонализации
            user_info = {
                'first_name': user.first_name,
                'username': user.username
            }
            
            # Получаем персонализированное приветственное сообщение
            welcome_message = await self.get_welcome_message(user_info)
            
            # Отправляем приветствие
            await update.message.reply_text(welcome_message)
            
            # Сохраняем приветствие в БД
            await self.save_message_to_db(user_id, welcome_message, is_from_bot=True)
            
            logger.info(f"Отправлено автоматическое приветствие пользователю {user_id}")
            return True
        
        return False

    async def send_n8n_webhook(self, user_info: dict, message_data: dict) -> bool:
        """Отправка webhook на n8n с данными пользователя и сообщения"""
        if not N8N_WEBHOOK_URL:
            logger.warning("N8N_WEBHOOK_URL не настроен")
            return False
            
        try:
            # Подготавливаем данные для отправки
            webhook_data = {
                "user": {
                    "telegram_id": user_info.get("telegram_id"),
                    "first_name": user_info.get("first_name"),
                    "last_name": user_info.get("last_name"),
                    "username": user_info.get("username"),
                    "language_code": user_info.get("language_code")
                },
                "message": {
                    "text": message_data.get("text"),
                    "message_type": message_data.get("message_type", "text"),
                    "timestamp": message_data.get("timestamp"),
                    "message_id": message_data.get("message_id")
                },
                "metadata": {
                    "is_first_message": message_data.get("is_first_message", False),
                    "chat_id": user_info.get("telegram_id")
                }
            }
            
            # Если это аудио сообщение, добавляем информацию о файле
            if message_data.get("audio_file_id"):
                webhook_data["message"]["audio_file_id"] = message_data["audio_file_id"]
                webhook_data["message"]["audio_duration"] = message_data.get("audio_duration")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    N8N_WEBHOOK_URL,
                    json=webhook_data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook успешно отправлен на n8n для пользователя {user_info.get('telegram_id')}")
                        return True
                    else:
                        logger.error(f"Ошибка отправки webhook на n8n: {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error("Таймаут при отправке webhook на n8n")
            return False
        except Exception as e:
            logger.error(f"Ошибка отправки webhook на n8n: {e}")
            return False

    async def is_new_user(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь новым (нет записей в БД)"""
        if not self.db_pool:
            return True
            
        try:
            async with self.db_pool.acquire() as conn:
                # Проверяем, есть ли клиент с таким telegram_id
                client = await conn.fetchrow(
                    "SELECT id FROM client WHERE telegram_id = $1",
                    user_id
                )
                return client is None
                
        except Exception as e:
            logger.error(f"Ошибка проверки нового пользователя: {e}")
            return True

    async def is_first_message_after_welcome(self, user_id: int) -> bool:
        """Проверяет, является ли это первым сообщением пользователя после приветствия"""
        if not self.db_pool:
            return False
            
        try:
            async with self.db_pool.acquire() as conn:
                # Получаем все сообщения пользователя
                messages = await conn.fetch(
                    """
                    SELECT message_text, is_from_bot 
                    FROM message m
                    JOIN client c ON m.client_id = c.id
                    WHERE c.telegram_id = $1
                    ORDER BY m.timestamp ASC
                    """,
                    user_id
                )
                
                # Если сообщений нет, это не первое сообщение после приветствия
                if len(messages) == 0:
                    return False
                
                # Ищем паттерн: первое сообщение от бота (приветствие), 
                # затем первое сообщение от пользователя
                if len(messages) == 2:
                    first_message = messages[0]
                    second_message = messages[1]
                    
                    # Первое должно быть от бота, второе от пользователя
                    if (first_message['is_from_bot'] and 
                        not second_message['is_from_bot']):
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"Ошибка проверки первого сообщения после приветствия: {e}")
            return False

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    # Получаем информацию о пользователе
    user = update.effective_user
    user_info = {
        'first_name': user.first_name,
        'username': user.username
    }
    
    welcome_message = await bot_instance.get_welcome_message(user_info)
    await update.message.reply_text(welcome_message)
    
    # Сохраняем команду в БД
    await bot_instance.save_message_to_db(
        update.effective_user.id, 
        "/start", 
        is_from_bot=False
    )
    await bot_instance.save_message_to_db(
        update.effective_user.id, 
        welcome_message, 
        is_from_bot=True
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Проверяем, нужно ли отправить автоматическое приветствие
    welcome_sent = await bot_instance.send_welcome_if_new_user(update)
    
    # Сохраняем сообщение пользователя
    await bot_instance.save_message_to_db(user_id, user_message, is_from_bot=False)
    
    # Если приветствие было отправлено, это означает что текущее сообщение - первое после приветствия
    # Также проверяем обычным способом для случаев когда пользователь уже существует
    is_first_message = welcome_sent or await bot_instance.is_first_message_after_welcome(user_id)
    
    # Если это первое сообщение после приветствия, отправляем webhook на n8n
    if is_first_message:
        user_info = {
            "telegram_id": user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "language_code": user.language_code
        }
        
        message_data = {
            "text": user_message,
            "message_type": "text",
            "timestamp": update.message.date.isoformat(),
            "message_id": update.message.message_id,
            "is_first_message": True
        }
        
        # Отправляем webhook на n8n
        webhook_sent = await bot_instance.send_n8n_webhook(user_info, message_data)
        
        if webhook_sent:
            logger.info(f"Первое сообщение пользователя {user_id} отправлено в n8n")
        else:
            logger.warning(f"Не удалось отправить первое сообщение пользователя {user_id} в n8n")
        
        # Если это первое сообщение, не отвечаем стандартным способом
        # n8n workflow будет обрабатывать это сообщение
        return
    
    # Для всех остальных сообщений - стандартная обработка
    # Ищем релевантную информацию в базе знаний
    context_info = await bot_instance.search_knowledge(user_message)
    
    # Генерируем ответ через OpenAI
    bot_response = await bot_instance.get_openai_response(user_message, context_info)
    
    # Отправляем ответ пользователю
    await update.message.reply_text(bot_response)
    
    # Сохраняем ответ бота
    await bot_instance.save_message_to_db(user_id, bot_response, is_from_bot=True)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик голосовых сообщений"""
    user_id = update.effective_user.id
    user = update.effective_user
    voice = update.message.voice
    
    # Проверяем, нужно ли отправить автоматическое приветствие
    welcome_sent = await bot_instance.send_welcome_if_new_user(update)
    
    # Сохраняем информацию об аудио сообщении в БД
    audio_message_text = f"[Голосовое сообщение: {voice.duration}с]"
    await bot_instance.save_message_to_db(user_id, audio_message_text, is_from_bot=False)
    
    # Если приветствие было отправлено, это означает что текущее сообщение - первое после приветствия
    # Также проверяем обычным способом для случаев когда пользователь уже существует
    is_first_message = welcome_sent or await bot_instance.is_first_message_after_welcome(user_id)
    
    # Если это первое сообщение после приветствия, отправляем webhook на n8n
    if is_first_message:
        user_info = {
            "telegram_id": user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "language_code": user.language_code
        }
        
        message_data = {
            "text": None,  # Для аудио сообщений текста нет
            "message_type": "voice",
            "timestamp": update.message.date.isoformat(),
            "message_id": update.message.message_id,
            "is_first_message": True,
            "audio_file_id": voice.file_id,
            "audio_duration": voice.duration
        }
        
        # Отправляем webhook на n8n
        webhook_sent = await bot_instance.send_n8n_webhook(user_info, message_data)
        
        if webhook_sent:
            logger.info(f"Первое аудио сообщение пользователя {user_id} отправлено в n8n")
        else:
            logger.warning(f"Не удалось отправить первое аудио сообщение пользователя {user_id} в n8n")
        
        # Если это первое сообщение, не отвечаем стандартным способом
        # n8n workflow будет обрабатывать это сообщение
        return
    
    # Для всех остальных аудио сообщений - стандартный ответ
    await update.message.reply_text("Спасибо за голосовое сообщение! Я получил его и передал для обработки.")
    
    # Сохраняем ответ бота
    await bot_instance.save_message_to_db(user_id, "Спасибо за голосовое сообщение! Я получил его и передал для обработки.", is_from_bot=True)

def main():
    """Основная функция запуска бота"""
    global bot_instance
    bot_instance = TelegramBot()
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    logger.info("Бот запущен!")
    
    # Запуск бота с инициализацией
    async def initialize_and_run():
        try:
            await bot_instance.init_db_pool()
            await bot_instance.setup_qdrant_collection()
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            
            # Ждем бесконечно
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
        finally:
            try:
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
                if bot_instance.db_pool:
                    await bot_instance.db_pool.close()
            except Exception as e:
                logger.error(f"Ошибка при остановке: {e}")
    
    # Используем простой event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(initialize_and_run())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
    finally:
        try:
            # Закрываем loop только если он не закрыт
            if not loop.is_closed():
                loop.close()
        except Exception:
            pass

if __name__ == '__main__':
    main() 