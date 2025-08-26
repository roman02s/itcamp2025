#!/usr/bin/env python3
"""
Простой тест для проверки функциональности парсера без Marker
"""
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

from src.config import Config
from src.utils import TextProcessor
from src.parser import InvoiceParser


def test_text_parsing():
    """Тест парсинга образца текста накладной"""
    
    # Образец текста накладной для тестирования
    sample_text = """
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
    
    # Инициализация компонентов
    config = Config(debug_mode=True)
    text_processor = TextProcessor(config)
    parser = InvoiceParser(config, text_processor)
    
    print("🧾 Тестирование парсера накладных")
    print("=" * 50)
    
    # Парсинг
    result = parser.parse(sample_text)
    
    # Вывод результатов
    print(f"Тип документа: {result.get('document_type')}")
    print(f"Номер: {result.get('number')}")
    print(f"Дата: {result.get('date')}")
    print(f"Уверенность: {result.get('confidence_score', 0):.2f}")
    
    print("\n👥 Контрагенты:")
    supplier = result.get('supplier', {})
    print(f"  Поставщик: {supplier.get('name')}")
    print(f"  ИНН: {supplier.get('INN')}")
    print(f"  КПП: {supplier.get('KPP')}")
    
    buyer = result.get('buyer', {})
    print(f"  Покупатель: {buyer.get('name')}")
    print(f"  ИНН: {buyer.get('INN')}")
    print(f"  КПП: {buyer.get('KPP')}")
    
    print(f"\n🚚 Логистика:")
    print(f"  Грузоотправитель: {result.get('shipper')}")
    print(f"  Грузополучатель: {result.get('consignee')}")
    
    print(f"\n💰 Суммы:")
    amounts = result.get('amounts', {})
    print(f"  Без НДС: {amounts.get('total_without_vat')}")
    print(f"  НДС: {amounts.get('vat')}")
    print(f"  С НДС: {amounts.get('total_with_vat')}")
    
    # Проверка качества извлечения
    success_indicators = [
        result.get('number') is not None,
        result.get('date') is not None,
        supplier.get('name') is not None,
        supplier.get('INN') is not None,
        buyer.get('name') is not None,
        buyer.get('INN') is not None,
        amounts.get('total_with_vat') is not None
    ]
    
    success_rate = sum(success_indicators) / len(success_indicators)
    
    print(f"\n📊 Результат теста:")
    print(f"  Извлечено полей: {sum(success_indicators)}/{len(success_indicators)}")
    print(f"  Успешность: {success_rate:.1%}")
    print(f"  Оценка уверенности: {result.get('confidence_score', 0):.1%}")
    
    if success_rate >= 0.7:
        print("✅ Тест пройден успешно!")
    else:
        print("❌ Тест не пройден. Требуется доработка.")
    
    return result


if __name__ == "__main__":
    test_text_parsing()
