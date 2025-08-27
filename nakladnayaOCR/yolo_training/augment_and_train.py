#!/usr/bin/env python3
"""
Улучшенное обучение YOLO с аугментацией данных для достижения 100% качества
"""

import os
import json
import random
import shutil
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import yaml
from ultralytics import YOLO
import torch

class DataAugmentator:
    """Класс для аугментации данных"""
    
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.classes = [
            "delivery-date",    # 0
            "order-date",       # 1  
            "carrier",          # 2
            "recipient",        # 3
            "payload",          # 4
            "price",            # 5
            "address"           # 6
        ]
        
    def create_augmented_dataset(self, num_augmentations=50):
        """Создание аугментированного датасета"""
        print(f"Создаем аугментированный датасет с {num_augmentations} вариациями...")
        
        # Очищаем выходную директорию
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        
        # Создаем структуру
        for split in ['train', 'val']:
            (self.output_dir / split / 'images').mkdir(parents=True, exist_ok=True)
            (self.output_dir / split / 'labels').mkdir(parents=True, exist_ok=True)
        
        # Загружаем исходные данные
        annotation_file = self.source_dir / 'annotated_data.json'
        with open(annotation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        image_path = self.source_dir / data['key']
        image = cv2.imread(str(image_path))
        height, width = image.shape[:2]
        
        # Оригинальное изображение (train)
        self._save_sample(image, data['boxes'], 0, 'train', width, height)
        
        # Создаем аугментации
        for i in range(1, num_augmentations + 1):
            aug_image, aug_boxes = self._augment_image_and_boxes(
                image.copy(), data['boxes'], width, height
            )
            
            # 80% в train, 20% в val
            split = 'train' if i <= num_augmentations * 0.8 else 'val'
            self._save_sample(aug_image, aug_boxes, i, split, width, height)
        
        # Создаем dataset.yaml
        self._create_dataset_yaml()
        
        print(f"Создано {num_augmentations + 1} изображений")
        train_count = len(list((self.output_dir / 'train' / 'images').glob('*.png')))
        val_count = len(list((self.output_dir / 'val' / 'images').glob('*.png')))
        print(f"Train: {train_count}, Val: {val_count}")
    
    def _augment_image_and_boxes(self, image, boxes, orig_width, orig_height):
        """Аугментация изображения и соответствующих боксов"""
        
        # Конвертируем в PIL для некоторых операций
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Случайные аугментации
        augmentations = []
        
        # 1. Изменение яркости (более консервативное)
        if random.random() < 0.5:
            factor = random.uniform(0.9, 1.1)
            enhancer = ImageEnhance.Brightness(pil_image)
            pil_image = enhancer.enhance(factor)
            augmentations.append(f"brightness_{factor:.2f}")

        # 2. Изменение контраста (более консервативное)
        if random.random() < 0.5:
            factor = random.uniform(0.9, 1.1)
            enhancer = ImageEnhance.Contrast(pil_image)
            pil_image = enhancer.enhance(factor)
            augmentations.append(f"contrast_{factor:.2f}")

        # 3. Очень легкое размытие
        if random.random() < 0.2:
            radius = random.uniform(0.3, 0.8)
            pil_image = pil_image.filter(ImageFilter.GaussianBlur(radius=radius))
            augmentations.append(f"blur_{radius:.2f}")

        # 4. Шум (меньше интенсивности)
        if random.random() < 0.3:
            np_image = np.array(pil_image)
            noise = np.random.normal(0, random.uniform(3, 8), np_image.shape).astype(np.uint8)
            np_image = np.clip(np_image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            pil_image = Image.fromarray(np_image)
            augmentations.append("noise")

        # Конвертируем обратно в OpenCV
        aug_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        # 5. Легкое геометрическое преобразование (только сдвиг)
        if random.random() < 0.4:
            h, w = aug_image.shape[:2]

            # Маленький случайный сдвиг
            max_shift = 5  # пикселей (уменьшили)
            shift_x = random.randint(-max_shift, max_shift)
            shift_y = random.randint(-max_shift, max_shift)

            # Создаем матрицу трансформации
            M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
            aug_image = cv2.warpAffine(aug_image, M, (w, h),
                                     borderMode=cv2.BORDER_REFLECT)

            # Сдвигаем координаты боксов
            boxes = [self._shift_box(box, shift_x, shift_y, w, h) for box in boxes]
            augmentations.append(f"shift_{shift_x}_{shift_y}")
        
        return aug_image, boxes

    def _shift_box(self, box, shift_x, shift_y, img_w, img_h):
        """Сдвиг координат бокса"""
        x = float(box['x']) + shift_x
        y = float(box['y']) + shift_y
        width = float(box['width'])
        height = float(box['height'])

        # Убеждаемся, что бокс остается в пределах изображения
        x = max(0, min(x, img_w - width))
        y = max(0, min(y, img_h - height))
        width = min(width, img_w - x)
        height = min(height, img_h - y)

        return {
            'id': box['id'],
            'label': box['label'],
            'x': str(x),
            'y': str(y),
            'width': str(width),
            'height': str(height),
            'confidence': box.get('confidence', 1.0)
        }

    def _scale_box(self, box, scale, orig_w, orig_h):
        """Масштабирование координат бокса"""
        x = float(box['x']) * scale
        y = float(box['y']) * scale
        width = float(box['width']) * scale
        height = float(box['height']) * scale
        
        # Убеждаемся, что бокс остается в пределах изображения
        x = max(0, min(x, orig_w - width))
        y = max(0, min(y, orig_h - height))
        width = min(width, orig_w - x)
        height = min(height, orig_h - y)
        
        return {
            'id': box['id'],
            'label': box['label'],
            'x': str(x),
            'y': str(y),
            'width': str(width),
            'height': str(height),
            'confidence': box.get('confidence')
        }
    
    def _save_sample(self, image, boxes, index, split, orig_width, orig_height):
        """Сохранение образца изображения и аннотаций"""
        # Сохраняем изображение
        image_filename = f"sample_{index:03d}.png"
        image_path = self.output_dir / split / 'images' / image_filename
        cv2.imwrite(str(image_path), image)
        
        # Создаем YOLO аннотации
        yolo_annotations = []
        for box in boxes:
            yolo_line = self._convert_box_to_yolo(box, orig_width, orig_height)
            if yolo_line:
                yolo_annotations.append(yolo_line)
        
        # Сохраняем аннотации
        label_filename = f"sample_{index:03d}.txt"
        label_path = self.output_dir / split / 'labels' / label_filename
        
        with open(label_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(yolo_annotations))
    
    def _convert_box_to_yolo(self, box, image_width, image_height):
        """Конвертация бокса в формат YOLO"""
        x = float(box['x'])
        y = float(box['y'])
        width = float(box['width'])
        height = float(box['height'])
        
        # Центр бокса
        center_x = x + width / 2
        center_y = y + height / 2
        
        # Нормализация
        norm_center_x = center_x / image_width
        norm_center_y = center_y / image_height
        norm_width = width / image_width
        norm_height = height / image_height
        
        # Проверяем границы
        norm_center_x = max(0, min(1, norm_center_x))
        norm_center_y = max(0, min(1, norm_center_y))
        norm_width = max(0, min(1, norm_width))
        norm_height = max(0, min(1, norm_height))
        
        class_name = box['label']
        if class_name not in self.classes:
            return None
        
        class_idx = self.classes.index(class_name)
        return f"{class_idx} {norm_center_x:.6f} {norm_center_y:.6f} {norm_width:.6f} {norm_height:.6f}"
    
    def _create_dataset_yaml(self):
        """Создание конфигурации датасета"""
        dataset_config = {
            'path': str(self.output_dir.absolute()),
            'train': 'train/images',
            'val': 'val/images',
            'nc': len(self.classes),
            'names': {i: name for i, name in enumerate(self.classes)}
        }
        
        yaml_path = self.output_dir / 'dataset.yaml'
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(dataset_config, f, default_flow_style=False, allow_unicode=True)

class EnhancedYoloTrainer:
    """Улучшенный тренер YOLO для переобучения"""
    
    def __init__(self, dataset_path: str, model_output_dir: str):
        self.dataset_path = Path(dataset_path)
        self.model_output_dir = Path(model_output_dir)
        self.model_output_dir.mkdir(parents=True, exist_ok=True)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
    def train_overfit_model(self):
        """Обучение с переобучением для 100% качества на данных"""
        
        # Используем YOLOv8s для лучшего качества
        model = YOLO('yolov8s.pt')
        
        # Параметры для переобучения
        train_args = {
            'data': str(self.dataset_path / 'dataset.yaml'),
            'epochs': 300,           # Много эпох
            'batch': 8,              # Увеличиваем батч для стабильности
            'imgsz': 640,
            'device': self.device,
            'project': str(self.model_output_dir),
            'name': 'overfit_model',
            'save_period': 50,
            'patience': 0,           # Отключаем early stopping
            'save': True,
            'cache': True,
            'workers': 2,
            'verbose': True,
            'exist_ok': True,
            
            # Отключаем большинство аугментаций для переобучения
            'hsv_h': 0.0,
            'hsv_s': 0.0,
            'hsv_v': 0.0,
            'degrees': 0.0,
            'translate': 0.0,
            'scale': 0.0,
            'shear': 0.0,
            'perspective': 0.0,
            'flipud': 0.0,
            'fliplr': 0.0,
            'mosaic': 0.0,          # Отключаем мозаику
            'mixup': 0.0,
            'copy_paste': 0.0,
            
            # Настройки для переобучения (исправлены для предотвращения слипания)
            'lr0': 0.0005,          # Еще меньший learning rate
            'lrf': 0.0005,          # Финальный learning rate
            'weight_decay': 0.0001, # Меньший weight decay
            'momentum': 0.937,
            'warmup_epochs': 5,       # Больше warmup эпох
            'warmup_momentum': 0.8,
            'warmup_bias_lr': 0.05,   # Меньший bias lr

            # Параметры для предотвращения слипания боксов
            'box': 5.0,              # Вес боксов
            'cls': 0.5,              # Вес классификации
            'dfl': 1.5,              # Distribution Focal Loss
            'overlap_mask': False,   # Отключаем пересечения
            'mask_ratio': 1,
            'dropout': 0.1,          # Dropout для предотвращения переобучения
            'iou': 0.7,              # IoU threshold
            'conf': 0.25             # Confidence threshold
        }
        
        print("Начинаем интенсивное обучение для переобучения...")
        print(f"Параметры: {train_args}")
        
        try:
            results = model.train(**train_args)
            
            # Сохраняем лучшую модель
            best_model_path = self.model_output_dir / 'overfit_model' / 'weights' / 'best.pt'
            if best_model_path.exists():
                final_model_path = self.model_output_dir / 'best_overfit_model.pt'
                shutil.copy2(best_model_path, final_model_path)
                print(f"Модель сохранена: {final_model_path}")
            
            return results
            
        except Exception as e:
            print(f"Ошибка при обучении: {e}")
            raise
    
    def validate_and_test(self):
        """Валидация и тестирование модели"""
        model_path = self.model_output_dir / 'best_overfit_model.pt'
        
        if not model_path.exists():
            print("Модель не найдена!")
            return
        
        model = YOLO(model_path)
        
        # Валидация
        print("Валидация модели...")
        val_results = model.val(
            data=str(self.dataset_path / 'dataset.yaml'),
            device=self.device,
            conf=0.001,  # Очень низкий порог
            iou=0.6,
            save_json=True
        )
        
        print(f"mAP50: {val_results.box.map50:.4f}")
        print(f"mAP50-95: {val_results.box.map:.4f}")
        
        # Тест на всех изображениях
        test_images = list((self.dataset_path / 'train' / 'images').glob('*.png'))
        print(f"\nТестирование на {len(test_images)} изображениях...")
        
        for i, img_path in enumerate(test_images[:5]):  # Тестируем первые 5
            results = model(str(img_path), conf=0.001, iou=0.6)
            
            output_path = self.model_output_dir / f'test_result_{i}.jpg'
            results[0].save(str(output_path))
            
            print(f"Изображение {i}: {len(results[0].boxes) if results[0].boxes else 0} обнаружений")
            
            if results[0].boxes:
                for box in results[0].boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    print(f"  Класс: {class_id}, Уверенность: {confidence:.3f}")

def main():
    """Главная функция"""
    source_dir = "/home/rsim/itcamp2025/nakladnayaOCR/data/yolo_dataset"
    aug_dataset_dir = "/home/rsim/itcamp2025/nakladnayaOCR/yolo_training/augmented_dataset"
    model_output_dir = "/home/rsim/itcamp2025/nakladnayaOCR/yolo_training/overfit_models"
    
    print("🔄 Создание аугментированного датасета...")
    augmentator = DataAugmentator(source_dir, aug_dataset_dir)
    augmentator.create_augmented_dataset(num_augmentations=100)
    
    print("\n🚀 Обучение модели с переобучением...")
    trainer = EnhancedYoloTrainer(aug_dataset_dir, model_output_dir)
    results = trainer.train_overfit_model()
    
    print("\n📊 Валидация и тестирование...")
    trainer.validate_and_test()
    
    print("\n✅ Готово! Модель должна показать высокое качество на данных.")

if __name__ == "__main__":
    main()
