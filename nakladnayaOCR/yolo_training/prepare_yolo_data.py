#!/usr/bin/env python3
"""
Подготовка данных для обучения YOLO модели
Конвертация аннотаций из формата JSON в формат YOLO
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import yaml

class YoloDataPreparator:
    """Класс для подготовки данных YOLO"""
    
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        
        # Классы для детекции (на основе размеченных данных)
        self.classes = [
            "delivery-date",    # 0
            "order-date",       # 1  
            "carrier",          # 2
            "recipient",        # 3
            "payload",          # 4
            "price",            # 5
            "address"           # 6
        ]
        
        # Создаем структуру директорий
        self.setup_directories()
    
    def setup_directories(self):
        """Создание структуры директорий для YOLO"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Структура YOLOv8
        for split in ['train', 'val']:
            (self.output_dir / split / 'images').mkdir(parents=True, exist_ok=True)
            (self.output_dir / split / 'labels').mkdir(parents=True, exist_ok=True)
    
    def convert_box_to_yolo(self, box: Dict, image_width: int, image_height: int) -> str:
        """Конвертация бокса из формата JSON в формат YOLO"""
        
        # Извлекаем координаты
        x = float(box['x'])
        y = float(box['y'])
        width = float(box['width'])
        height = float(box['height'])
        
        # Конвертируем в центр + размеры
        center_x = x + width / 2
        center_y = y + height / 2
        
        # Нормализуем к размерам изображения
        norm_center_x = center_x / image_width
        norm_center_y = center_y / image_height
        norm_width = width / image_width
        norm_height = height / image_height
        
        # Получаем индекс класса
        class_name = box['label']
        if class_name not in self.classes:
            print(f"Предупреждение: неизвестный класс {class_name}")
            return None
        
        class_idx = self.classes.index(class_name)
        
        # Формат YOLO: class_id center_x center_y width height
        return f"{class_idx} {norm_center_x:.6f} {norm_center_y:.6f} {norm_width:.6f} {norm_height:.6f}"
    
    def process_annotation_file(self, annotation_path: Path) -> bool:
        """Обработка файла аннотаций"""
        try:
            with open(annotation_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Извлекаем информацию об изображении
            image_filename = data['key']
            image_width = data['width']
            image_height = data['height']
            boxes = data['boxes']
            
            # Путь к изображению
            image_path = self.source_dir / image_filename
            if not image_path.exists():
                print(f"Изображение не найдено: {image_path}")
                return False
            
            # Конвертируем боксы в формат YOLO
            yolo_annotations = []
            for box in boxes:
                yolo_line = self.convert_box_to_yolo(box, image_width, image_height)
                if yolo_line:
                    yolo_annotations.append(yolo_line)
            
            if not yolo_annotations:
                print(f"Нет валидных аннотаций для {image_filename}")
                return False
            
            # Разделяем данные (пока все в train, так как у нас один пример)
            split = 'train'
            
            # Копируем изображение
            target_image_path = self.output_dir / split / 'images' / image_filename
            shutil.copy2(image_path, target_image_path)
            
            # Создаем файл аннотаций
            annotation_filename = Path(image_filename).stem + '.txt'
            target_annotation_path = self.output_dir / split / 'labels' / annotation_filename
            
            with open(target_annotation_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(yolo_annotations))
            
            print(f"Обработано: {image_filename} -> {len(yolo_annotations)} объектов")
            return True
            
        except Exception as e:
            print(f"Ошибка при обработке {annotation_path}: {e}")
            return False
    
    def create_dataset_yaml(self):
        """Создание конфигурационного файла датасета"""
        dataset_config = {
            'path': str(self.output_dir.absolute()),
            'train': 'train/images',
            'val': 'train/images',  # Используем тот же набор для валидации
            'nc': len(self.classes),
            'names': {i: name for i, name in enumerate(self.classes)}
        }
        
        yaml_path = self.output_dir / 'dataset.yaml'
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(dataset_config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"Конфигурация датасета создана: {yaml_path}")
    
    def prepare_data(self):
        """Основной метод подготовки данных"""
        print("Начинаем подготовку данных для YOLO...")
        
        # Ищем файлы аннотаций
        annotation_files = list(self.source_dir.glob('*.json'))
        
        if not annotation_files:
            print(f"Файлы аннотаций не найдены в {self.source_dir}")
            return False
        
        print(f"Найдено файлов аннотаций: {len(annotation_files)}")
        
        # Обрабатываем каждый файл
        processed_count = 0
        for ann_file in annotation_files:
            if self.process_annotation_file(ann_file):
                processed_count += 1
        
        # Создаем конфигурацию датасета
        self.create_dataset_yaml()
        
        print(f"Подготовка завершена. Обработано файлов: {processed_count}/{len(annotation_files)}")
        print(f"Данные сохранены в: {self.output_dir}")
        
        return processed_count > 0

def main():
    """Главная функция"""
    source_dir = "/home/rsim/itcamp2025/nakladnayaOCR/data/yolo_dataset"
    output_dir = "/home/rsim/itcamp2025/nakladnayaOCR/yolo_training/dataset"
    
    preparator = YoloDataPreparator(source_dir, output_dir)
    success = preparator.prepare_data()
    
    if success:
        print("\n✅ Данные успешно подготовлены для обучения YOLO!")
        print(f"Структура данных:")
        print(f"  📁 {output_dir}/")
        print(f"    📁 train/")
        print(f"      📁 images/  - изображения для обучения")
        print(f"      📁 labels/  - аннотации в формате YOLO")
        print(f"    📄 dataset.yaml - конфигурация датасета")
    else:
        print("\n❌ Ошибка при подготовке данных")

if __name__ == "__main__":
    main()
