#!/usr/bin/env python3
"""
YOLO детектор для сегментации полей в накладных
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import logging

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("ultralytics не установлен. YOLO детекция недоступна.")

logger = logging.getLogger(__name__)


class YoloFieldDetector:
    """Детектор полей документов на основе YOLO"""
    
    def __init__(self, model_path: str = None, confidence_threshold: float = 0.25):
        """
        Инициализация детектора
        
        Args:
            model_path: Путь к обученной модели YOLO
            confidence_threshold: Порог уверенности для детекции
        """
        self.model = None
        self.confidence_threshold = confidence_threshold
        
        # Классы полей
        self.field_classes = {
            0: "delivery-date",
            1: "order-date", 
            2: "carrier",
            3: "recipient",
            4: "payload",
            5: "price",
            6: "address"
        }
        
        # Русские названия полей
        self.field_names_ru = {
            "delivery-date": "Дата доставки",
            "order-date": "Дата заказа",
            "carrier": "Перевозчик", 
            "recipient": "Получатель",
            "payload": "Груз",
            "price": "Цена",
            "address": "Адрес"
        }
        
        if not YOLO_AVAILABLE:
            logger.warning("YOLO недоступен. Используйте 'pip install ultralytics'")
            return
            
        # Попытка загрузить модель
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        else:
            # Попытка найти обученную модель
            default_paths = [
                "src/best_invoice_model.pt",
                "yolo_training/overfit_models/best_overfit_model.pt",
                "yolo_training/models/best_invoice_model.pt"
            ]
            
            for path in default_paths:
                if Path(path).exists():
                    self.load_model(path)
                    break
    
    def load_model(self, model_path: str) -> bool:
        """Загрузка модели YOLO"""
        try:
            if not YOLO_AVAILABLE:
                logger.error("ultralytics не установлен")
                return False
                
            self.model = YOLO(model_path)
            logger.info(f"YOLO модель загружена: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели {model_path}: {e}")
            return False
    
    def is_available(self) -> bool:
        """Проверка доступности детектора"""
        return YOLO_AVAILABLE and self.model is not None
    
    def detect_fields(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Детекция полей на изображении
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Список обнаруженных полей с координатами и метаданными
        """
        if not self.is_available():
            logger.warning("YOLO детектор недоступен")
            return []
        
        try:
            # Предсказание
            results = self.model(
                image_path,
                conf=self.confidence_threshold,
                iou=0.6,
                verbose=False
            )
            
            if not results or not results[0].boxes:
                logger.info("Поля не обнаружены")
                return []
            
            # Обработка результатов
            fields = []
            boxes = results[0].boxes
            
            for box in boxes:
                field = self._process_detection(box, image_path)
                if field:
                    fields.append(field)
            
            # Сортировка по уверенности
            fields.sort(key=lambda x: x['confidence'], reverse=True)
            
            logger.info(f"Обнаружено полей: {len(fields)}")
            return fields
            
        except Exception as e:
            logger.error(f"Ошибка детекции полей: {e}")
            return []
    
    def _process_detection(self, box, image_path: str) -> Optional[Dict[str, Any]]:
        """Обработка одного обнаружения"""
        try:
            # Координаты
            coords = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            
            # Фильтрация по уверенности
            if confidence < self.confidence_threshold:
                return None
            
            # Название поля
            field_type = self.field_classes.get(class_id, f"unknown_{class_id}")
            field_name_ru = self.field_names_ru.get(field_type, field_type)
            
            # Размеры бокса
            x1, y1, x2, y2 = coords
            width = x2 - x1
            height = y2 - y1
            center_x = x1 + width / 2
            center_y = y1 + height / 2
            
            field = {
                "field_type": field_type,
                "field_name": field_name_ru,
                "confidence": confidence,
                "class_id": class_id,
                "bbox": {
                    "x1": x1,
                    "y1": y1, 
                    "x2": x2,
                    "y2": y2,
                    "width": width,
                    "height": height,
                    "center_x": center_x,
                    "center_y": center_y
                }
            }
            
            return field
            
        except Exception as e:
            logger.error(f"Ошибка обработки детекции: {e}")
            return None
    
    def extract_field_regions(self, image_path: str, fields: List[Dict] = None) -> Dict[str, Image.Image]:
        """
        Извлечение регионов полей как отдельных изображений
        
        Args:
            image_path: Путь к изображению
            fields: Список полей (если None, то детектируем автоматически)
            
        Returns:
            Словарь {field_type: PIL.Image} с вырезанными регионами
        """
        if fields is None:
            fields = self.detect_fields(image_path)
        
        if not fields:
            return {}
        
        try:
            # Загружаем изображение
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Не удалось загрузить изображение: {image_path}")
                return {}
            
            regions = {}
            
            for field in fields:
                bbox = field['bbox']
                field_type = field['field_type']
                
                # Вырезаем регион
                x1, y1 = int(bbox['x1']), int(bbox['y1'])
                x2, y2 = int(bbox['x2']), int(bbox['y2'])
                
                # Добавляем небольшой отступ
                padding = 5
                x1 = max(0, x1 - padding)
                y1 = max(0, y1 - padding)
                x2 = min(image.shape[1], x2 + padding)
                y2 = min(image.shape[0], y2 + padding)
                
                region = image[y1:y2, x1:x2]
                
                if region.size > 0:
                    # Конвертируем в PIL
                    region_rgb = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(region_rgb)
                    
                    # Используем уникальный ключ для дубликатов
                    key = field_type
                    counter = 1
                    while key in regions:
                        key = f"{field_type}_{counter}"
                        counter += 1
                    
                    regions[key] = pil_image
                    
            logger.info(f"Извлечено регионов: {len(regions)}")
            return regions
            
        except Exception as e:
            logger.error(f"Ошибка извлечения регионов: {e}")
            return {}
    
    def create_annotated_image(self, image_path: str, output_path: str = None) -> str:
        """
        Создание изображения с аннотациями
        
        Args:
            image_path: Путь к исходному изображению
            output_path: Путь для сохранения (если None, то рядом с исходным)
            
        Returns:
            Путь к сохраненному изображению
        """
        fields = self.detect_fields(image_path)
        
        if not fields:
            logger.info("Нет полей для аннотации")
            return image_path
        
        try:
            # Загружаем изображение
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Не удалось загрузить изображение: {image_path}")
                return image_path
            
            # Цвета для разных классов
            colors = [
                (255, 0, 0),    # delivery-date - красный
                (0, 255, 0),    # order-date - зеленый
                (0, 0, 255),    # carrier - синий
                (255, 255, 0),  # recipient - желтый
                (255, 0, 255),  # payload - фиолетовый
                (0, 255, 255),  # price - голубой
                (128, 128, 128) # address - серый
            ]
            
            # Рисуем боксы
            for field in fields:
                bbox = field['bbox']
                class_id = field['class_id']
                confidence = field['confidence']
                field_name = field['field_name']
                
                x1, y1 = int(bbox['x1']), int(bbox['y1'])
                x2, y2 = int(bbox['x2']), int(bbox['y2'])
                
                color = colors[class_id % len(colors)]
                
                # Рисуем прямоугольник
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                
                # Подпись
                label = f"{field_name}: {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                
                # Фон для текста
                cv2.rectangle(image, (x1, y1 - label_size[1] - 10), 
                             (x1 + label_size[0], y1), color, -1)
                
                # Текст
                cv2.putText(image, label, (x1, y1 - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Сохранение
            if output_path is None:
                base_path = Path(image_path)
                output_path = str(base_path.parent / f"{base_path.stem}_annotated{base_path.suffix}")
            
            cv2.imwrite(output_path, image)
            logger.info(f"Аннотированное изображение сохранено: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка создания аннотаций: {e}")
            return image_path
    
    def get_field_summary(self, image_path: str) -> Dict[str, Any]:
        """
        Получение сводки обнаруженных полей
        
        Returns:
            Сводная информация о полях
        """
        fields = self.detect_fields(image_path)
        
        summary = {
            "total_fields": len(fields),
            "fields_by_type": {},
            "average_confidence": 0.0,
            "high_confidence_fields": 0,
            "detected_types": []
        }
        
        if not fields:
            return summary
        
        # Статистика по типам
        for field in fields:
            field_type = field['field_type']
            if field_type not in summary["fields_by_type"]:
                summary["fields_by_type"][field_type] = {
                    "count": 0,
                    "max_confidence": 0.0,
                    "avg_confidence": 0.0,
                    "confidences": []
                }
            
            type_stats = summary["fields_by_type"][field_type]
            type_stats["count"] += 1
            type_stats["confidences"].append(field['confidence'])
            type_stats["max_confidence"] = max(type_stats["max_confidence"], field['confidence'])
        
        # Вычисление средних значений
        all_confidences = [f['confidence'] for f in fields]
        summary["average_confidence"] = sum(all_confidences) / len(all_confidences)
        summary["high_confidence_fields"] = len([c for c in all_confidences if c > 0.8])
        summary["detected_types"] = list(summary["fields_by_type"].keys())
        
        # Средняя уверенность по типам
        for type_stats in summary["fields_by_type"].values():
            if type_stats["confidences"]:
                type_stats["avg_confidence"] = sum(type_stats["confidences"]) / len(type_stats["confidences"])
        
        return summary
