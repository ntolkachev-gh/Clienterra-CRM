#!/usr/bin/env python3
"""
Скрипт для управления базой знаний в Qdrant
Позволяет добавлять, обновлять и удалять информацию о услугах
"""

import os
import sys
import json
import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

load_dotenv()

# Конфигурация
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
COLLECTION_NAME = "knowledge_base"

openai.api_key = OPENAI_API_KEY

class KnowledgeManager:
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL)
        
    def create_collection(self):
        """Создание коллекции в Qdrant"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if COLLECTION_NAME in collection_names:
                print(f"Коллекция {COLLECTION_NAME} уже существует")
                return
                
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            print(f"Коллекция {COLLECTION_NAME} создана успешно")
            
        except Exception as e:
            print(f"Ошибка создания коллекции: {e}")
            
    def add_knowledge(self, text, category, knowledge_id=None):
        """Добавление знания в базу"""
        try:
            # Получаем эмбеддинг от OpenAI
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-ada-002"
            )
            embedding = response['data'][0]['embedding']
            
            # Генерируем ID если не указан
            if knowledge_id is None:
                existing_points = self.client.scroll(
                    collection_name=COLLECTION_NAME,
                    limit=1000
                )[0]
                knowledge_id = len(existing_points) + 1
            
            # Добавляем в Qdrant
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=knowledge_id,
                        vector=embedding,
                        payload={
                            "text": text,
                            "category": category
                        }
                    )
                ]
            )
            
            print(f"Знание добавлено с ID: {knowledge_id}")
            return knowledge_id
            
        except Exception as e:
            print(f"Ошибка добавления знания: {e}")
            return None
    
    def search_knowledge(self, query, limit=5):
        """Поиск знаний по запросу"""
        try:
            # Получаем эмбеддинг запроса
            response = openai.Embedding.create(
                input=query,
                model="text-embedding-ada-002"
            )
            query_embedding = response['data'][0]['embedding']
            
            # Поиск в Qdrant
            search_result = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                limit=limit
            )
            
            results = []
            for hit in search_result:
                results.append({
                    'id': hit.id,
                    'score': hit.score,
                    'text': hit.payload['text'],
                    'category': hit.payload['category']
                })
            
            return results
            
        except Exception as e:
            print(f"Ошибка поиска: {e}")
            return []
    
    def list_all_knowledge(self):
        """Получение всех знаний из базы"""
        try:
            points, _ = self.client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000
            )
            
            knowledge_list = []
            for point in points:
                knowledge_list.append({
                    'id': point.id,
                    'text': point.payload['text'],
                    'category': point.payload['category']
                })
            
            return knowledge_list
            
        except Exception as e:
            print(f"Ошибка получения знаний: {e}")
            return []
    
    def delete_knowledge(self, knowledge_id):
        """Удаление знания по ID"""
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=[knowledge_id]
            )
            print(f"Знание с ID {knowledge_id} удалено")
            
        except Exception as e:
            print(f"Ошибка удаления знания: {e}")
    
    def load_from_file(self, filename):
        """Загрузка знаний из JSON файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                knowledge_data = json.load(f)
            
            for item in knowledge_data:
                self.add_knowledge(
                    text=item['text'],
                    category=item['category'],
                    knowledge_id=item.get('id')
                )
            
            print(f"Загружено {len(knowledge_data)} знаний из файла {filename}")
            
        except Exception as e:
            print(f"Ошибка загрузки из файла: {e}")
    
    def export_to_file(self, filename):
        """Экспорт всех знаний в JSON файл"""
        try:
            knowledge_list = self.list_all_knowledge()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(knowledge_list, f, ensure_ascii=False, indent=2)
            
            print(f"Экспортировано {len(knowledge_list)} знаний в файл {filename}")
            
        except Exception as e:
            print(f"Ошибка экспорта в файл: {e}")

def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python knowledge_manager.py create_collection")
        print("  python knowledge_manager.py add 'текст знания' 'категория'")
        print("  python knowledge_manager.py search 'поисковый запрос'")
        print("  python knowledge_manager.py list")
        print("  python knowledge_manager.py delete <id>")
        print("  python knowledge_manager.py load <filename.json>")
        print("  python knowledge_manager.py export <filename.json>")
        return
    
    manager = KnowledgeManager()
    command = sys.argv[1]
    
    if command == "create_collection":
        manager.create_collection()
        
    elif command == "add" and len(sys.argv) >= 4:
        text = sys.argv[2]
        category = sys.argv[3]
        manager.add_knowledge(text, category)
        
    elif command == "search" and len(sys.argv) >= 3:
        query = sys.argv[2]
        results = manager.search_knowledge(query)
        
        print(f"\nНайдено {len(results)} результатов:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. ID: {result['id']}, Score: {result['score']:.3f}")
            print(f"   Категория: {result['category']}")
            print(f"   Текст: {result['text']}")
            
    elif command == "list":
        knowledge_list = manager.list_all_knowledge()
        
        print(f"\nВсего знаний в базе: {len(knowledge_list)}")
        for item in knowledge_list:
            print(f"\nID: {item['id']}")
            print(f"Категория: {item['category']}")
            print(f"Текст: {item['text']}")
            
    elif command == "delete" and len(sys.argv) >= 3:
        knowledge_id = int(sys.argv[2])
        manager.delete_knowledge(knowledge_id)
        
    elif command == "load" and len(sys.argv) >= 3:
        filename = sys.argv[2]
        manager.load_from_file(filename)
        
    elif command == "export" and len(sys.argv) >= 3:
        filename = sys.argv[2]
        manager.export_to_file(filename)
        
    else:
        print("Неверная команда или недостаточно аргументов")

if __name__ == "__main__":
    main() 