#!/usr/bin/env python3
"""
Демонстрационный скрипт для сервиса извлечения информации из накладных
"""
import json
from pathlib import Path
from src.config import Config
from src.utils import TextProcessor
from src.parser import InvoiceParser


def demo_text_parsing():
    """Демонстрация парсинга текста накладной"""
    
    print("🧾 Демонстрация сервиса извлечения информации из накладных")
    print("=" * 60)
    
    # Различные образцы для тестирования
    samples = [
        {
            "name": "Товарная накладная ТОРГ-12",
            "text": """
            ТОВАРНАЯ НАКЛАДНАЯ № ТН-2025-001 от 15.01.2025
            
            Поставщик: ООО "Альфа Торг"
            ИНН: 1234567890
            КПП: 123456789
            
            Покупатель: ЗАО "Бета Снаб"  
            ИНН: 0987654321
            КПП: 987654321
            
            Грузоотправитель: ООО "Альфа Торг", г. Москва
            
            Грузополучатель: ЗАО "Бета Снаб", г. Санкт-Петербург
            
            Итого без НДС: 100 000,00
            НДС 20%: 20 000,00
            Всего к оплате: 120 000,00
            """
        },
        {
            "name": "Счет-фактура",
            "text": """
            СЧЕТ-ФАКТУРА № СФ-456 от 20.01.2025
            
            Продавец: ИП Петров Петр Петрович
            ИНН: 123456789012
            
            Покупатель: ООО "Гамма Плюс"
            ИНН: 5555666677
            КПП: 555566667
            
            Сумма без НДС: 50 000,00
            НДС 18%: 9 000,00
            Итого с НДС: 59 000,00
            """
        }
    ]
    
    # Инициализация
    config = Config(debug_mode=False)
    text_processor = TextProcessor(config)
    parser = InvoiceParser(config, text_processor)
    
    for i, sample in enumerate(samples, 1):
        print(f"\n📄 Образец {i}: {sample['name']}")
        print("-" * 50)
        
        # Парсинг
        result = parser.parse(sample['text'])
        
        # Вывод результатов
        print(f"Тип документа: {result.get('document_type')}")
        print(f"Номер: {result.get('number')}")
        print(f"Дата: {result.get('date')}")
        
        # Контрагенты
        supplier = result.get('supplier', {})
        buyer = result.get('buyer', {})
        
        print(f"\nПоставщик: {supplier.get('name')}")
        print(f"  ИНН: {supplier.get('INN')}")
        print(f"  КПП: {supplier.get('KPP')}")
        
        print(f"\nПокупатель: {buyer.get('name')}")
        print(f"  ИНН: {buyer.get('INN')}")
        print(f"  КПП: {buyer.get('KPP')}")
        
        # Суммы
        amounts = result.get('amounts', {})
        print(f"\nСуммы:")
        if amounts.get('total_without_vat'):
            print(f"  Без НДС: {amounts['total_without_vat']:,.2f} ₽")
        if amounts.get('vat'):
            print(f"  НДС: {amounts['vat']:,.2f} ₽")
        if amounts.get('total_with_vat'):
            print(f"  С НДС: {amounts['total_with_vat']:,.2f} ₽")
        
        print(f"\nУверенность: {result.get('confidence_score', 0):.1%}")


def demo_json_output():
    """Демонстрация JSON вывода"""
    
    print("\n\n📊 Демонстрация JSON API")
    print("=" * 40)
    
    sample_text = """
    ТОВАРНАЯ НАКЛАДНАЯ № ТН-2025-003 от 25.01.2025
    
    Поставщик: ООО "Дельта Логистик"
    ИНН: 7777888899
    КПП: 777788889
    
    Покупатель: АО "Эпсилон Трейд"
    ИНН: 1111222233
    КПП: 111122223
    
    Сумма без НДС: 250 000,00
    НДС 20%: 50 000,00
    Всего к оплате: 300 000,00
    """
    
    # Инициализация и парсинг
    config = Config()
    text_processor = TextProcessor(config)
    parser = InvoiceParser(config, text_processor)
    
    result = parser.parse(sample_text)
    
    # Красивый JSON вывод
    print(json.dumps(result, ensure_ascii=False, indent=2))


def demo_file_structure():
    """Демонстрация структуры проекта"""
    
    print("\n\n📁 Структура проекта")
    print("=" * 30)
    
    def print_tree(path, prefix="", max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return
            
        items = sorted(path.iterdir()) if path.is_dir() else []
        dirs = [item for item in items if item.is_dir() and not item.name.startswith('.')]
        files = [item for item in items if item.is_file() and not item.name.startswith('.')]
        
        # Выводим папки
        for i, item in enumerate(dirs):
            is_last_dir = (i == len(dirs) - 1) and len(files) == 0
            current_prefix = "└── " if is_last_dir else "├── "
            print(f"{prefix}{current_prefix}{item.name}/")
            
            next_prefix = prefix + ("    " if is_last_dir else "│   ")
            print_tree(item, next_prefix, max_depth, current_depth + 1)
        
        # Выводим файлы
        for i, item in enumerate(files):
            is_last = i == len(files) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")
    
    project_root = Path(".")
    print(f"{project_root.name}/")
    print_tree(project_root, max_depth=2)


if __name__ == "__main__":
    try:
        demo_text_parsing()
        demo_json_output()
        demo_file_structure()
        
        print("\n\n🚀 Для запуска веб-интерфейса выполните:")
        print("   ./run.sh")
        print("   или")
        print("   streamlit run streamlit_app.py")
        
    except Exception as e:
        print(f"\n❌ Ошибка демонстрации: {e}")
        import traceback
        traceback.print_exc()
