# src/config.py
"""
Конфигурационные настройки для парсера накладных
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Конфигурация для парсера накладных"""
    
    # Настройки Marker
    output_format: str = "markdown"  # markdown, json, html
    force_ocr: bool = True
    torch_device: str = "cpu"  # cpu, cuda
    
    # Настройки парсинга текста
    max_lines_section: int = 8
    confidence_threshold: float = 0.7
    
    # Отладка
    debug_mode: bool = False
    
    # Регулярные выражения для поиска
    money_pattern: str = r"([0-9][0-9\s.,]*)"
    date_pattern: str = r"([0-3]?\d[.\-/][01]?\d[.\-/]\d{2,4})"
    inn_pattern: str = r"ИНН[:\s]*([0-9]{10,12})"
    kpp_pattern: str = r"КПП[:\s]*([0-9]{9})"
    
    # Лейблы для поиска секций
    supplier_labels = [r"Поставщик", r"Продавец", r"Грузоотправитель"]
    buyer_labels = [r"Покупатель", r"Плательщик", r"Грузополучатель"]
    
    # Паттерны для поиска номера документа
    number_patterns = [
        r"(?:Товарная\s+накладная|Накладная|ТН)[^\n]{0,50}?(?:№|N|No)\s*([A-Za-zА-Яа-я0-9/\-]+)",
        r"(?:№|N|No)\s*([A-Za-zА-Яа-я0-9/\-]+)\s*(?:от|дата)"
    ]
    
    # Паттерны для поиска даты
    date_patterns = [
        r"(?:от|дата)\s*([0-3]?\d[.\-/][01]?\d[.\-/]\d{2,4})",
        r"Дата[:\s]+([0-3]?\d[.\-/][01]?\d[.\-/]\d{2,4})"
    ]
    
    # Паттерны для поиска сумм
    total_with_vat_patterns = [
        r"(?:Всего\s*к\s*оплате|Итого\s*с\s*НДС|Всего\s*с\s*НДС)\s*[:\-]?\s*([0-9][0-9\s.,]*)"
    ]
    
    vat_patterns = [
        r"(?:НДС\s*(?:\d+%)?|Налог\s*на\s*добавленную\s*стоимость)\s*[:\-]?\s*([0-9][0-9\s.,]*)"
    ]
    
    total_without_vat_patterns = [
        r"(?:Сумма\s*без\s*НДС|Итого\s*без\s*НДС|Итого\s*(?:без\s*НДС)?)\s*[:\-]?\s*([0-9][0-9\s.,]*)"
    ]
