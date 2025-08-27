#!/usr/bin/env python3
"""
Обучение YOLO модели для детекции полей в накладных
"""

import os
import sys
from pathlib import Path
import yaml
import torch
from ultralytics import YOLO

class YoloTrainer:
    """Класс для обучения YOLO модели"""
    
    def __init__(self, dataset_path: str, model_output_dir: str):
        self.dataset_path = Path(dataset_path)
        self.model_output_dir = Path(model_output_dir)
        self.model_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Проверяем доступность CUDA
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Используемое устройство: {self.device}")
        
    def load_dataset_config(self):
        """Загрузка конфигурации датасета"""
        config_path = self.dataset_path / 'dataset.yaml'
        
        if not config_path.exists():
            raise FileNotFoundError(f"Конфигурация датасета не найдена: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"Загружена конфигурация датасета:")
        print(f"  Классы: {config['nc']}")
        print(f"  Названия классов: {list(config['names'].values())}")
        
        return config
    
    def train_model(self, epochs: int = 100, batch_size: int = 16, imgsz: int = 640):
        """Обучение модели YOLO"""
        
        # Загружаем предобученную модель YOLOv8
        model = YOLO('yolov8n.pt')  # nano версия для быстрого обучения
        
        # Параметры обучения
        train_args = {
            'data': str(self.dataset_path / 'dataset.yaml'),
            'epochs': epochs,
            'batch': batch_size,
            'imgsz': imgsz,
            'device': self.device,
            'project': str(self.model_output_dir),
            'name': 'invoice_field_detection',
            'save_period': 10,  # Сохранять каждые 10 эпох
            'patience': 50,     # Остановка при отсутствии улучшений
            'save': True,
            'cache': True,      # Кэширование для ускорения
            'workers': 1,       # Количество воркеров для загрузки данных
            'verbose': True,
            
            # Аугментации для лучшего качества
            # 'hsv_h': 0.015,     # Изменение оттенка
            # 'hsv_s': 0.7,       # Изменение насыщенности  
            # 'hsv_v': 0.4,       # Изменение яркости
            'degrees': 0.0,     # Поворот (отключен для документов)
            'translate': 0.0,   # Сдвиг
            'scale': 0.0,       # Масштабирование
            'shear': 0.0,       # Сдвиг (отключен)
            'perspective': 0.0, # Перспектива (отключена)
            'flipud': 0.0,      # Вертикальный поворот (отключен)
            'fliplr': 0.0,      # Горизонтальный поворот
            'mosaic': 0.0,      # Мозаика
            'mixup': 0.0,       # Смешивание изображений
            'copy_paste': 0.0,  # Копирование объектов
        }
        
        print("Начинаем обучение модели...")
        print(f"Параметры обучения: {train_args}")
        
        try:
            # Запускаем обучение
            results = model.train(**train_args)
            
            print(f"Обучение завершено!")
            print(f"Результаты сохранены в: {self.model_output_dir}")
            
            # Сохраняем лучшую модель в корень директории
            best_model_path = self.model_output_dir / 'invoice_field_detection' / 'weights' / 'best.pt'
            if best_model_path.exists():
                final_model_path = self.model_output_dir / 'best_invoice_model.pt'
                import shutil
                shutil.copy2(best_model_path, final_model_path)
                print(f"Лучшая модель скопирована в: {final_model_path}")
            
            return results
            
        except Exception as e:
            print(f"Ошибка при обучении: {e}")
            raise
    
    def validate_model(self, model_path: str = None):
        """Валидация обученной модели"""
        if model_path is None:
            model_path = self.model_output_dir / 'best_invoice_model.pt'
        
        if not Path(model_path).exists():
            print(f"Модель не найдена: {model_path}")
            return None
        
        model = YOLO(model_path)
        
        # Запускаем валидацию
        results = model.val(
            data=str(self.dataset_path / 'dataset.yaml'),
            device=self.device
        )
        
        print(f"Результаты валидации:")
        print(f"  mAP50: {results.box.map50:.4f}")
        print(f"  mAP50-95: {results.box.map:.4f}")
        
        return results
    
    def test_inference(self, image_path: str, model_path: str = None):
        """Тестовое предсказание на изображении"""
        if model_path is None:
            model_path = self.model_output_dir / 'best_invoice_model.pt'
        
        if not Path(model_path).exists():
            print(f"Модель не найдена: {model_path}")
            return None
        
        model = YOLO(model_path)
        
        # Делаем предсказание
        results = model(image_path)
        
        # Сохраняем результат с визуализацией
        output_path = self.model_output_dir / 'test_prediction.jpg'
        results[0].save(str(output_path))
        
        print(f"Тестовое предсказание сохранено: {output_path}")
        
        # Выводим детекции
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    coords = box.xyxy[0].tolist()
                    
                    print(f"Класс: {class_id}, Уверенность: {confidence:.3f}, Координаты: {coords}")
        
        return results

def main():
    """Главная функция"""
    # Пути
    dataset_path = "/home/rsim/itcamp2025/nakladnayaOCR/yolo_training/dataset"
    model_output_dir = "/home/rsim/itcamp2025/nakladnayaOCR/yolo_training/models"
    
    # Проверяем существование датасета
    if not Path(dataset_path).exists():
        print(f"❌ Датасет не найден: {dataset_path}")
        print("Сначала запустите prepare_yolo_data.py")
        sys.exit(1)
    
    # Создаем тренер
    trainer = YoloTrainer(dataset_path, model_output_dir)
    
    try:
        # Загружаем конфигурацию
        config = trainer.load_dataset_config()
        
        # Обучаем модель (много эпох для высокого качества)
        print("\n🚀 Начинаем обучение модели...")
        results = trainer.train_model(
            epochs=40,     # Много эпох для переобучения на одном примере
            batch_size=1,   # Маленький батч из-за одного изображения  
            imgsz=1200       # Размер изображения
        )
        
        # Валидируем модель
        print("\n📊 Валидация модели...")
        val_results = trainer.validate_model()
        
        # Тестируем на обучающем изображении
        test_image = Path(dataset_path) / 'train' / 'images' / 'Obrazets-zapolneniya-TN-2025-2-4.pdf_page_1.png'
        if test_image.exists():
            print("\n🔍 Тестовое предсказание...")
            trainer.test_inference(str(test_image))
        
        print("\n✅ Обучение модели завершено успешно!")
        print(f"Модель сохранена в: {model_output_dir}/best_invoice_model.pt")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
