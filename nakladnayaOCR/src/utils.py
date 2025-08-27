# src/utils.py
"""
Утилиты для обработки текста и работы с Marker
"""
import os
import re
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
import logging

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser

from .config import Config

logger = logging.getLogger(__name__)


class TextProcessor:
    """Класс для обработки и нормализации текста"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def normalize_text(self, text: str) -> str:
        """Нормализация текста: удаление лишних пробелов и символов"""
        if not text:
            return ""
        
        # Замена неразрывных пробелов
        text = text.replace("\xa0", " ")
        text = text.replace("\u202f", " ")
        
        # Удаление множественных пробелов и табуляций
        text = re.sub(r"[ \t]+", " ", text)
        
        return text.strip()
    
    def parse_money(self, text: Optional[str]) -> Optional[float]:
        """Парсинг денежных сумм из текста"""
        if not text:
            return None
        
        # Очистка от пробелов и замена запятых на точки
        cleaned = text.replace(" ", "").replace("\u202f", "").replace(",", ".")
        
        # Оставляем только цифры и точку
        cleaned = re.sub(r"[^0-9.]", "", cleaned)
        
        if not cleaned:
            return None
        
        try:
            return float(cleaned)
        except ValueError:
            logger.warning(f"Не удалось распарсить сумму: {text}")
            return None
    
    def find_first_match(self, patterns: List[str], text: str, 
                        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) -> Optional[str]:
        """Поиск первого совпадения среди списка паттернов"""
        for pattern in patterns:
            match = re.search(pattern, text, flags)
            if match:
                # Возвращаем первую захватывающую группу, если есть
                groups = match.groups()
                if groups:
                    return next((g for g in groups if g is not None), match.group(0))
                return match.group(0)
        return None
    
    def extract_section(self, lines: List[str], start_labels: List[str], 
                       next_labels: List[str], max_lines: Optional[int] = None) -> str:
        """Извлечение секции текста между указанными метками"""
        max_lines = max_lines or self.config.max_lines_section
        
        # Поиск начальной позиции
        start_idx = None
        for i, line in enumerate(lines):
            if any(re.search(label, line, re.IGNORECASE) for label in start_labels):
                start_idx = i
                break
        
        if start_idx is None:
            return ""
        
        # Поиск конечной позиции
        end_idx = min(start_idx + max_lines, len(lines))
        for j in range(start_idx + 1, min(start_idx + max_lines, len(lines))):
            if j < len(lines) and any(re.search(label, lines[j], re.IGNORECASE) for label in next_labels):
                end_idx = j
                break
        
        # Склеивание строк
        section_lines = []
        for line in lines[start_idx + 1:end_idx]:
            normalized = self.normalize_text(line)
            if normalized:
                section_lines.append(normalized)
        
        return " ".join(section_lines)
    
    def extract_inn_kpp(self, text: str, near_patterns: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """Извлечение ИНН и КПП из текста вблизи указанных паттернов"""
        lines = text.splitlines()
        
        # Поиск области вокруг метки
        target_idx = None
        for i, line in enumerate(lines):
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in near_patterns):
                target_idx = i
                break
        
        # Определение окна поиска
        if target_idx is not None:
            start_idx = max(0, target_idx)
            end_idx = min(len(lines), target_idx + 8)  # Увеличим окно поиска
            search_lines = lines[start_idx:end_idx]
        else:
            search_lines = lines
        
        # Поиск ИНН и КПП в окне
        inn = None
        kpp = None
        
        for line in search_lines:
            if inn is None:
                inn_match = re.search(self.config.inn_pattern, line, re.IGNORECASE)
                if inn_match:
                    inn = inn_match.group(1)
            
            if kpp is None:
                kpp_match = re.search(self.config.kpp_pattern, line, re.IGNORECASE)
                if kpp_match:
                    kpp = kpp_match.group(1)
            
            # Если нашли оба, можем прекратить поиск
            if inn and kpp:
                break
        
        return inn, kpp
    
    def extract_text_from_marker_output(self, path: Path) -> str:
        """Извлечение текста из вывода Marker в зависимости от формата"""
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")
        
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Ошибка чтения файла {path}: {e}")
            raise
        
        if path.suffix.lower() == ".md":
            return content
        
        elif path.suffix.lower() == ".json":
            try:
                data = json.loads(content)
                
                # Обработка различных форматов JSON от Marker
                if isinstance(data, dict):
                    # Прямое поле markdown
                    if "markdown" in data and isinstance(data["markdown"], str):
                        return data["markdown"]
                    
                    # Поле pages с массивом страниц
                    if "pages" in data and isinstance(data["pages"], list):
                        pages_text = []
                        for page in data["pages"]:
                            if isinstance(page, dict):
                                page_text = page.get("markdown") or page.get("text", "")
                                if page_text:
                                    pages_text.append(page_text)
                            else:
                                pages_text.append(str(page))
                        return "\n\n".join(pages_text)
                
                # Fallback - конвертация в строку
                return str(data)
                
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                return content
        
        elif path.suffix.lower() == ".html":
            # Простое удаление HTML тегов
            return re.sub(r"<[^>]+>", "", content)
        
        else:
            logger.warning(f"Неизвестный формат файла: {path.suffix}")
            return content


class MarkerRunner:
    """Класс для запуска Marker OCR"""
    
    def __init__(self, config: Config):
        self.config = config
        self._setup_converter()
    
    def _setup_converter(self):
        """Настройка конвертера Marker"""
        # Создание конфигурации для Marker
        marker_config = {
            "output_format": self.config.output_format,
        }
        
        # Добавляем дополнительные настройки если они есть
        if hasattr(self.config, 'force_ocr') and self.config.force_ocr:
            marker_config["FORCE_OCR"] = True
        
        # Создание парсера конфигурации
        self.config_parser = ConfigParser(marker_config)
        
        # Создание конвертера
        self.converter = PdfConverter(
            config=self.config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=self.config_parser.get_processors(),
            renderer=self.config_parser.get_renderer(),
            llm_service=self.config_parser.get_llm_service()
        )
        
        logger.info("Marker конвертер инициализирован")
    
    def run(self, input_path: Path, output_dir: Path) -> Path:
        """Запуск Marker для обработки документа"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Запуск Marker для файла: {input_path}")
        
        try:
            # Запуск конвертации через новый API
            result = self.converter(str(input_path))
            
            # Определение выходного файла
            output_file = self._get_output_path(input_path, output_dir)
            
            # Сохранение результата в зависимости от формата
            self._save_result(result, output_file)
            
            logger.info(f"Marker создал файл: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Ошибка при работе с Marker: {e}")
            raise RuntimeError(f"Marker завершился с ошибкой: {str(e)}")
    
    def _get_output_path(self, input_path: Path, output_dir: Path) -> Path:
        """Определение пути для выходного файла"""
        # Определение расширения по формату
        suffix_map = {
            "markdown": ".md",
            "json": ".json", 
            "html": ".html",
            "chunks": ".json"
        }
        
        suffix = suffix_map.get(self.config.output_format, ".md")
        return (output_dir / input_path.name).with_suffix(suffix)
    
    def _save_result(self, result, output_file: Path):
        """Сохранение результата в файл"""
        try:
            if self.config.output_format == "json":
                # Для JSON формата сохраняем как JSON
                if hasattr(result, '__dict__'):
                    # Если result это объект, конвертируем в словарь
                    data = result.__dict__ if hasattr(result, '__dict__') else result
                else:
                    # Если result это уже словарь или строка
                    data = result
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                # Для других форматов сохраняем как текст
                content = str(result)
                output_file.write_text(content, encoding='utf-8')
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении результата: {e}")
            # Fallback - сохраняем как строку
            output_file.write_text(str(result), encoding='utf-8')


class YoloMarkerProcessor:
    """Класс для совместной обработки YOLO + Marker"""
    
    def __init__(self, config: Config):
        self.config = config
        self.text_processor = TextProcessor(config)
        self.marker_runner = MarkerRunner(config)
        
        # Инициализация YOLO детектора
        try:
            from .yolo_detector import YoloFieldDetector
            self.yolo_detector = YoloFieldDetector()
            self.yolo_available = self.yolo_detector.is_available()
        except ImportError:
            logger.warning("YOLO детектор недоступен")
            self.yolo_detector = None
            self.yolo_available = False
    
    def process_document(self, input_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Полная обработка документа: YOLO детекция + Marker OCR
        
        Returns:
            Словарь с результатами обработки
        """
        results = {
            "input_path": str(input_path),
            "yolo_detection": None,
            "marker_text": None,
            "field_texts": {},
            "annotated_image": None,
            "processing_success": False
        }
        
        try:
            # 1. Конвертация PDF в изображения для YOLO (если это PDF)
            yolo_images = []
            if input_path.suffix.lower() == '.pdf':
                yolo_images = self._convert_pdf_to_images(input_path, output_dir / "pdf_pages")
            else:
                yolo_images = [input_path]  # Если уже изображение
            
            # 2. YOLO детекция полей (если доступна)
            if self.yolo_available and yolo_images:
                logger.info("Запуск YOLO детекции полей...")
                # Обрабатываем первую страницу для начала
                first_image = yolo_images[0] if yolo_images else None
                if first_image and first_image.exists():
                    fields = self.yolo_detector.detect_fields(str(first_image))
                    results["yolo_detection"] = {
                        "fields": fields,
                        "field_count": len(fields),
                        "summary": self.yolo_detector.get_field_summary(str(first_image))
                    }
                    
                    # Создание аннотированного изображения
                    annotated_path = self.yolo_detector.create_annotated_image(
                        str(first_image), 
                        str(output_dir / f"{first_image.stem}_annotated{first_image.suffix}")
                    )
                    results["annotated_image"] = annotated_path
                
            # 2. Marker OCR для полного документа
            logger.info("Запуск Marker OCR...")
            marker_output = self.marker_runner.run(input_path, output_dir)
            full_text = self.text_processor.extract_text_from_marker_output(marker_output)
            results["marker_text"] = full_text
            
            # 3. Извлечение текста из регионов полей (если YOLO доступна)
            if self.yolo_available and results.get("yolo_detection", {}).get("fields"):
                # Используем первое изображение для извлечения полей
                field_image = yolo_images[0] if yolo_images else input_path
                results["field_texts"] = self._extract_field_texts(
                    field_image, results["yolo_detection"]["fields"], output_dir
                )
            
            results["processing_success"] = True
            logger.info("Обработка документа завершена успешно")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке документа: {e}")
            results["error"] = str(e)
        
        return results
    
    def _extract_field_texts(self, input_path: Path, fields: List[Dict], output_dir: Path) -> Dict[str, str]:
        """Извлечение текста из регионов полей через Marker"""
        field_texts = {}
        
        if not self.yolo_available:
            return field_texts
        
        try:
            # Извлекаем регионы полей как изображения
            regions = self.yolo_detector.extract_field_regions(str(input_path), fields)
            
            for field_key, region_image in regions.items():
                try:
                    # Сохраняем регион как временное изображение
                    region_path = output_dir / f"field_{field_key}.png"
                    region_image.save(region_path)
                    
                    # Обрабатываем регион через Marker
                    region_output = self.marker_runner.run(region_path, output_dir / "regions")
                    region_text = self.text_processor.extract_text_from_marker_output(region_output)
                    
                    # Очистка и нормализация текста
                    clean_text = self.text_processor.normalize_text(region_text)
                    if clean_text:
                        field_texts[field_key] = clean_text
                    
                    # Удаляем временный файл
                    region_path.unlink(missing_ok=True)
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки региона {field_key}: {e}")
                    continue
            
            logger.info(f"Извлечен текст из {len(field_texts)} полей")
            
        except Exception as e:
            logger.error(f"Ошибка извлечения текстов полей: {e}")
        
        return field_texts
    
    def is_yolo_available(self) -> bool:
        """Проверка доступности YOLO"""
        return self.yolo_available
    
    def get_field_summary(self, input_path: Path) -> Dict[str, Any]:
        """Получение сводки по полям"""
        if not self.yolo_available:
            return {"error": "YOLO недоступен"}
        
        return self.yolo_detector.get_field_summary(str(input_path))
    
    def _convert_pdf_to_images(self, pdf_path: Path, output_dir: Path) -> List[Path]:
        """
        Конвертация PDF в изображения для YOLO обработки
        
        Args:
            pdf_path: Путь к PDF файлу
            output_dir: Директория для сохранения изображений
            
        Returns:
            Список путей к созданным изображениям
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        image_paths = []
        
        try:
            import fitz  # PyMuPDF
            
            # Открываем PDF
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                
                # Конвертируем в изображение с высоким разрешением
                mat = fitz.Matrix(2.0, 2.0)  # Увеличиваем разрешение в 2 раза
                pix = page.get_pixmap(matrix=mat)
                
                # Сохраняем изображение
                image_path = output_dir / f"page_{page_num + 1}.png"
                pix.save(str(image_path))
                image_paths.append(image_path)
                
                logger.info(f"Создано изображение: {image_path}")
            
            pdf_document.close()
            
        except ImportError:
            logger.warning("PyMuPDF не установлен, используем альтернативный метод")
            
            try:
                import pdf2image
                
                # Конвертация с помощью pdf2image
                images = pdf2image.convert_from_path(pdf_path, dpi=200)
                
                for i, image in enumerate(images):
                    image_path = output_dir / f"page_{i + 1}.png"
                    image.save(image_path, 'PNG')
                    image_paths.append(image_path)
                    logger.info(f"Создано изображение: {image_path}")
                    
            except ImportError:
                logger.error("Не установлены библиотеки для конвертации PDF: PyMuPDF или pdf2image")
                return []
        
        except Exception as e:
            logger.error(f"Ошибка при конвертации PDF в изображения: {e}")
            return []
        
        return image_paths
