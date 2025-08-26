# src/utils.py
"""
Утилиты для обработки текста и работы с Marker
"""
import os
import re
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple
import logging

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
    
    def run(self, input_path: Path, output_dir: Path) -> Path:
        """Запуск Marker для обработки документа"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Формирование команды
        cmd = [
            "marker_single",
            str(input_path),
            "--output_format", self.config.output_format,
            "--output_dir", str(output_dir),
        ]
        
        if self.config.force_ocr:
            cmd.append("--force_ocr")
        
        # Настройка окружения
        env = os.environ.copy()
        env.setdefault("CUDA_VISIBLE_DEVICES", "")
        env.setdefault("TORCH_DEVICE", self.config.torch_device)
        
        logger.info(f"Запуск команды: {' '.join(cmd)}")
        
        try:
            # Запуск процесса
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=300  # 5 минут таймаут
            )
            
            if self.config.debug_mode:
                logger.info(f"Marker stdout: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Marker stderr: {result.stderr}")
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Marker превысил время ожидания (5 минут)")
        except subprocess.CalledProcessError as e:
            logger.error(f"Marker завершился с ошибкой: {e}")
            logger.error(f"Stderr: {e.stderr}")
            raise
        
        # Поиск выходного файла
        output_file = self._find_output_file(input_path, output_dir)
        
        if not output_file.exists():
            raise FileNotFoundError(f"Marker не создал ожидаемый выходной файл: {output_file}")
        
        logger.info(f"Marker создал файл: {output_file}")
        return output_file
    
    def _find_output_file(self, input_path: Path, output_dir: Path) -> Path:
        """Поиск выходного файла Marker"""
        # Определение расширения по формату
        suffix_map = {
            "markdown": ".md",
            "json": ".json", 
            "html": ".html",
            "chunks": ".json"
        }
        
        suffix = suffix_map.get(self.config.output_format, ".md")
        
        # Основной ожидаемый путь
        expected_file = (output_dir / input_path.name).with_suffix(suffix)
        
        if expected_file.exists():
            return expected_file
        
        # Fallback: поиск любого файла с нужным расширением
        candidates = sorted(output_dir.glob(f"*{suffix}"))
        if candidates:
            logger.warning(f"Ожидаемый файл {expected_file} не найден, используем {candidates[0]}")
            return candidates[0]
        
        # Если ничего не найдено, возвращаем ожидаемый путь для лучшего сообщения об ошибке
        return expected_file
