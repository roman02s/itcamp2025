# src/parser.py
"""
Основной модуль для парсинга накладных и извлечения ключевой информации
"""
import re
import logging
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime

from .config import Config
from .utils import TextProcessor

logger = logging.getLogger(__name__)


class InvoiceParser:
    """Парсер для извлечения информации из накладных"""
    
    def __init__(self, config: Config, text_processor: TextProcessor):
        self.config = config
        self.text_processor = text_processor
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Основной метод парсинга накладной"""
        if not text:
            return self._empty_result("Пустой текст")
        
        try:
            # Нормализация текста
            normalized_text = self.text_processor.normalize_text(text)
            lines = [line.strip() for line in text.splitlines()]
            
            logger.info("Начинаем парсинг накладной...")
            
            # Извлечение основной информации
            document_info = self._extract_document_info(normalized_text)
            parties_info = self._extract_parties_info(normalized_text, lines)
            amounts_info = self._extract_amounts_info(normalized_text)
            logistics_info = self._extract_logistics_info(lines)
            
            # Сборка результата
            result = {
                "document_type": self._determine_document_type(normalized_text),
                "extraction_timestamp": datetime.now().isoformat(),
                "confidence_score": self._calculate_confidence_score(document_info, parties_info, amounts_info),
                **document_info,
                **parties_info,
                **amounts_info,
                **logistics_info
            }
            
            # Добавление отладочной информации
            if self.config.debug_mode:
                result["debug_info"] = {
                    "text_length": len(text),
                    "lines_count": len(lines),
                    "first_100_chars": text[:100],
                    "extraction_patterns_used": self._get_used_patterns()
                }
            
            logger.info(f"Парсинг завершен. Уверенность: {result.get('confidence_score', 0):.2f}")
            return result
            
        except Exception as e:
            logger.exception("Ошибка при парсинге накладной")
            return self._empty_result(f"Ошибка парсинга: {str(e)}")
    
    def _extract_document_info(self, text: str) -> Dict[str, Any]:
        """Извлечение основной информации о документе"""
        # Номер документа
        number = self.text_processor.find_first_match(
            self.config.number_patterns, text
        )
        
        # Дата документа
        date = self.text_processor.find_first_match(
            self.config.date_patterns, text
        )
        
        # Нормализация даты
        normalized_date = self._normalize_date(date) if date else None
        
        return {
            "number": number,
            "date": normalized_date,
            "original_date": date
        }
    
    def _extract_parties_info(self, text: str, lines: List[str]) -> Dict[str, Any]:
        """Извлечение информации о сторонах сделки"""
        # Поставщик
        supplier_name = self._extract_company_name(lines, self.config.supplier_labels)
        
        # Покупатель  
        buyer_name = self._extract_company_name(lines, self.config.buyer_labels)
        
        # ИНН/КПП поставщика
        supplier_inn, supplier_kpp = self._extract_inn_kpp_for_party(
            lines, self.config.supplier_labels
        )
        
        # ИНН/КПП покупателя  
        buyer_inn, buyer_kpp = self._extract_inn_kpp_for_party(
            lines, self.config.buyer_labels
        )
        
        return {
            "supplier": {
                "name": supplier_name or None,
                "INN": supplier_inn,
                "KPP": supplier_kpp
            },
            "buyer": {
                "name": buyer_name or None,
                "INN": buyer_inn,
                "KPP": buyer_kpp
            }
        }
    
    def _extract_amounts_info(self, text: str) -> Dict[str, Any]:
        """Извлечение финансовой информации"""
        # Отладочный вывод паттернов поиска
        if self.config.debug_mode:
            logger.info("Паттерны для поиска сумм:")
            logger.info(f"НДС: {self.config.vat_patterns}")
        
        # Сумма с НДС
        total_with_vat_str = self.text_processor.find_first_match(
            self.config.total_with_vat_patterns, text
        )
        total_with_vat = self.text_processor.parse_money(total_with_vat_str)
        
        # НДС - особый поиск чтобы не захватить сумму без НДС
        vat_str = self._extract_vat_amount(text)
        vat = self.text_processor.parse_money(vat_str)
        
        # Сумма без НДС  
        total_without_vat_str = self.text_processor.find_first_match(
            self.config.total_without_vat_patterns, text
        )
        total_without_vat = self.text_processor.parse_money(total_without_vat_str)
        
        # Отладочный вывод
        if self.config.debug_mode:
            logger.info(f"Найденные строки: без НДС='{total_without_vat_str}', НДС='{vat_str}', с НДС='{total_with_vat_str}'")
            logger.info(f"Парсинг: без НДС={total_without_vat}, НДС={vat}, с НДС={total_with_vat}")
        
        # Вычисление недостающих сумм
        if total_without_vat is None and total_with_vat is not None and vat is not None:
            total_without_vat = round(total_with_vat - vat, 2)
        
        if total_with_vat is None and total_without_vat is not None and vat is not None:
            total_with_vat = round(total_without_vat + vat, 2)
        
        if vat is None and total_with_vat is not None and total_without_vat is not None:
            vat = round(total_with_vat - total_without_vat, 2)
        
        return {
            "amounts": {
                "total_without_vat": total_without_vat,
                "vat": vat,
                "total_with_vat": total_with_vat,
                "original_strings": {
                    "total_without_vat": total_without_vat_str,
                    "vat": vat_str,
                    "total_with_vat": total_with_vat_str
                }
            }
        }
    
    def _extract_logistics_info(self, lines: List[str]) -> Dict[str, Any]:
        """Извлечение логистической информации"""
        # Грузоотправитель
        shipper = self._extract_company_name(lines, [r"Грузоотправитель"])
        
        # Грузополучатель  
        consignee = self._extract_company_name(lines, [r"Грузополучатель"])
        
        return {
            "shipper": shipper or None,
            "consignee": consignee or None
        }
    
    def _determine_document_type(self, text: str) -> str:
        """Определение типа документа"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ["товарная накладная", "торг-12"]):
            return "Товарная накладная (ТОРГ-12)"
        elif "накладная" in text_lower:
            return "Накладная"
        elif any(keyword in text_lower for keyword in ["счет-фактура", "счёт-фактура"]):
            return "Счет-фактура"
        elif "акт" in text_lower:
            return "Акт"
        else:
            return "Неопределенный документ"
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Нормализация даты в стандартный формат"""
        if not date_str:
            return None
        
        # Список возможных форматов
        date_formats = [
            "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y",
            "%d.%m.%y", "%d/%m/%y", "%d-%m-%y"
        ]
        
        # Очистка строки
        cleaned_date = re.sub(r"[^\d./-]", "", date_str.strip())
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(cleaned_date, fmt)
                # Если год двузначный и меньше 50, считаем это 20xx
                if parsed_date.year < 1950:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                return parsed_date.strftime("%d.%m.%Y")
            except ValueError:
                continue
        
        logger.warning(f"Не удалось распарсить дату: {date_str}")
        return date_str
    
    def _calculate_confidence_score(self, document_info: Dict, parties_info: Dict, amounts_info: Dict) -> float:
        """Расчет оценки уверенности в извлеченных данных"""
        score = 0.0
        max_score = 10.0
        
        # Основная информация документа (3 балла)
        if document_info.get("number"):
            score += 1.5
        if document_info.get("date"):
            score += 1.5
        
        # Информация о сторонах (4 балла)
        supplier = parties_info.get("supplier", {})
        buyer = parties_info.get("buyer", {})
        
        if supplier.get("name"):
            score += 1.0
        if supplier.get("INN"):
            score += 0.5
        if buyer.get("name"):
            score += 1.0
        if buyer.get("INN"):
            score += 0.5
        if supplier.get("KPP"):
            score += 0.5
        if buyer.get("KPP"):
            score += 0.5
        
        # Финансовая информация (3 балла)
        amounts = amounts_info.get("amounts", {})
        if amounts.get("total_with_vat") or amounts.get("total_without_vat"):
            score += 2.0
        if amounts.get("vat"):
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def _extract_company_name(self, lines: List[str], labels: List[str]) -> Optional[str]:
        """Извлечение названия компании после указанной метки"""
        for i, line in enumerate(lines):
            # Ищем строку с меткой
            if any(re.search(label, line, re.IGNORECASE) for label in labels):
                # Проверяем, есть ли название на той же строке
                for label in labels:
                    pattern = rf"{label}[:\s]*(.+?)(?:ИНН|КПП|$)"
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        name = match.group(1).strip()
                        if name and not re.match(r"^\d+$", name):  # Не только цифры
                            return name
                
                # Если не найдено на той же строке, ищем в следующих строках
                for j in range(i + 1, min(i + 3, len(lines))):
                    if j < len(lines):
                        line_content = lines[j].strip()
                        # Пропускаем строки с ИНН/КПП или пустые
                        if (line_content and 
                            not re.search(r"(ИНН|КПП|^\d+$)", line_content, re.IGNORECASE)):
                            return line_content
                break
        return None
    
    def _extract_vat_amount(self, text: str) -> Optional[str]:
        """Специальный метод для извлечения суммы НДС"""
        lines = text.splitlines()
        
        for line in lines:
            # Ищем строки с НДС, но избегаем строк с "без НДС" и "к оплате"
            if (re.search(r"НДС\s*\d+%?", line, re.IGNORECASE) and 
                not re.search(r"без\s*НДС|к\s*оплате|итого|всего", line, re.IGNORECASE)):
                
                # Извлекаем число после НДС
                match = re.search(r"НДС\s*\d+%?\s*[:\-]?\s*([0-9][0-9\s.,]*)", line, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        # Fallback к обычному поиску
        return self.text_processor.find_first_match(self.config.vat_patterns, text)
    
    def _extract_inn_kpp_for_party(self, lines: List[str], labels: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """Извлечение ИНН и КПП для конкретной стороны"""
        # Находим секцию стороны
        start_idx = None
        for i, line in enumerate(lines):
            if any(re.search(label, line, re.IGNORECASE) for label in labels):
                start_idx = i
                break
        
        if start_idx is None:
            return None, None
        
        # Ищем до следующей секции или конца окна
        end_idx = min(start_idx + 8, len(lines))
        
        # Ищем следующую секцию контрагента
        for j in range(start_idx + 1, len(lines)):
            line = lines[j]
            if any(re.search(other_label, line, re.IGNORECASE) 
                   for other_label in (self.config.supplier_labels + self.config.buyer_labels)
                   if not any(re.search(label, line, re.IGNORECASE) for label in labels)):
                end_idx = j
                break
        
        # Поиск ИНН и КПП в найденной секции
        inn = None
        kpp = None
        
        for i in range(start_idx, end_idx):
            if i < len(lines):
                line = lines[i]
                
                if inn is None:
                    inn_match = re.search(self.config.inn_pattern, line, re.IGNORECASE)
                    if inn_match:
                        inn = inn_match.group(1)
                
                if kpp is None:
                    kpp_match = re.search(self.config.kpp_pattern, line, re.IGNORECASE)
                    if kpp_match:
                        kpp = kpp_match.group(1)
                
                if inn and kpp:
                    break
        
        return inn, kpp
    
    def _get_used_patterns(self) -> List[str]:
        """Получение списка использованных паттернов для отладки"""
        return [
            "number_patterns", "date_patterns", "total_with_vat_patterns",
            "vat_patterns", "total_without_vat_patterns", "inn_pattern", "kpp_pattern"
        ]
    
    def _empty_result(self, reason: str) -> Dict[str, Any]:
        """Создание пустого результата с указанием причины"""
        return {
            "document_type": "Неопределенный",
            "extraction_timestamp": datetime.now().isoformat(),
            "confidence_score": 0.0,
            "error": reason,
            "number": None,
            "date": None,
            "supplier": {"name": None, "INN": None, "KPP": None},
            "buyer": {"name": None, "INN": None, "KPP": None},
            "shipper": None,
            "consignee": None,
            "amounts": {
                "total_without_vat": None,
                "vat": None,
                "total_with_vat": None
            }
        }
