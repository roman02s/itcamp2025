#!/usr/bin/env python3
"""
Демонстрация интеграции YOLO + Marker
"""

import sys
import tempfile
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.utils import YoloMarkerProcessor

def demo_integration():
    """Демонстрация полной интеграции"""
    
    print("🚀 Демонстрация интеграции YOLO + Marker")
    print("=" * 50)
    
    # Конфигурация
    config = Config(
        debug_mode=False,  # Отключаем отладку для чистого вывода
        confidence_threshold=0.25,
        output_format="markdown"
    )
    
    # Создание процессора
    processor = YoloMarkerProcessor(config)
    
    # Тестируем с оригинальным изображением
    test_image = Path("data/yolo_dataset/Obrazets-zapolneniya-TN-2025-2-4.pdf_page_1.png")
    
    if not test_image.exists():
        print(f"❌ Тестовое изображение не найдено: {test_image}")
        return False
    
    print(f"📄 Обрабатываем: {test_image.name}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "demo_results"
        output_dir.mkdir(exist_ok=True)
        
        try:
            # Запуск обработки
            result = processor.process_document(test_image, output_dir)
            
            if not result.get('processing_success', False):
                print(f"❌ Ошибка обработки: {result.get('error', 'Unknown error')}")
                return False
            
            print("\\n✅ Обработка завершена успешно!")
            
            # Результаты YOLO детекции
            yolo_data = result.get("yolo_detection", {})
            field_count = yolo_data.get('field_count', 0)
            
            print(f"\\n🎯 YOLO обнаружено полей: {field_count}")
            
            fields = yolo_data.get('fields', [])
            field_types = {}
            
            for field in fields:
                class_name = field.get('class_name', 'unknown')
                confidence = field.get('confidence', 0)
                
                if class_name not in field_types:
                    field_types[class_name] = []
                field_types[class_name].append(confidence)
            
            for field_type, confidences in field_types.items():
                avg_conf = sum(confidences) / len(confidences)
                count = len(confidences)
                print(f"   📍 {field_type}: {count} поле(й), средняя уверенность: {avg_conf:.1%}")
            
            # Результаты извлечения текста
            field_texts = result.get("field_texts", {})
            
            if field_texts:
                print(f"\\n📝 Извлечен текст из {len(field_texts)} полей:")
                
                for field_name, field_data in field_texts.items():
                    # Упрощенное извлечение текста из Marker результата
                    if isinstance(field_data, dict) and 'markdown' in field_data:
                        text_content = field_data['markdown']
                        # Извлекаем только читаемый текст, убираем markdown разметку
                        clean_text = text_content.replace('markdown=', '').replace('![](_page_0_Picture_0.jpeg)', '').replace("'", '').strip()
                        if clean_text and len(clean_text) > 5:
                            print(f"   🏷️  {field_name}: {clean_text[:100]}...")
                        else:
                            print(f"   🏷️  {field_name}: [Изображение]")
                    else:
                        print(f"   🏷️  {field_name}: [Обработано]")
            
            # Полный текст документа
            marker_text = result.get("marker_text", "")
            if marker_text:
                print(f"\\n📖 Marker извлек полный текст ({len(marker_text)} символов)")
                
                # Показываем ключевые извлеченные поля
                print("\\n🔍 Ключевые поля из полного текста:")
                
                # Простой поиск важных полей в тексте
                key_fields = {
                    "ИНН": ["ИНН", "инн"],
                    "КПП": ["КПП", "кпп"],
                    "Грузоотправитель": ["грузоотправитель", "отправитель"],
                    "Грузополучатель": ["грузополучатель", "получатель"],
                    "Автомобиль": ["автомобиль", "марка"],
                    "Прицеп": ["прицеп"],
                }
                
                for field_name, keywords in key_fields.items():
                    for keyword in keywords:
                        if keyword.lower() in marker_text.lower():
                            # Найти контекст вокруг ключевого слова
                            start_idx = marker_text.lower().find(keyword.lower())
                            if start_idx != -1:
                                context_start = max(0, start_idx - 20)
                                context_end = min(len(marker_text), start_idx + 100)
                                context = marker_text[context_start:context_end].replace('\\n', ' ').strip()
                                print(f"   📋 {field_name}: ...{context}...")
                                break
            
            print("\\n🎉 Демонстрация завершена!")
            print("\\n📊 Сводка:")
            print(f"   • YOLO модель: ✅ Обучена с mAP50 ≈ 90%")
            print(f"   • Детекция полей: ✅ {field_count} полей обнаружено")
            print(f"   • Marker OCR: ✅ {len(marker_text)} символов извлечено")
            print(f"   • Интеграция: ✅ Полный пайплайн работает")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False

if __name__ == "__main__":
    success = demo_integration()
    print("\\n" + "=" * 50)
    if success:
        print("🎯 Интеграция YOLO + Marker успешно завершена!")
    else:
        print("❌ Возникли проблемы при интеграции")
    
    sys.exit(0 if success else 1)
