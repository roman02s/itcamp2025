#!/usr/bin/env python3
"""
Исправленное обучение YOLO для предотвращения слипания боксов
"""

import os
import sys
from pathlib import Path
import torch
from ultralytics import YOLO

def main():
    """Главная функция обучения с исправленными параметрами"""

    print("🚀 Исправленное обучение YOLO модели")
    print("=" * 50)

    # Проверяем устройство
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"📊 Используемое устройство: {device}")

    # Создаем директорию для результатов
    output_dir = Path("yolo_training/models/invoice_field_detection_fixed_v2")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Параметры обучения для предотвращения слипания боксов
    train_args = {
        'data': 'yolo_training/dataset/dataset.yaml',
        'epochs': 200,              # Умеренное количество эпох
        'batch': 8,                 # Размер батча
        'imgsz': 640,               # Размер изображения
        'device': device,
        'project': str(output_dir.parent),
        'name': 'invoice_field_detection_fixed_v2',
        'save_period': 20,          # Сохранять каждые 20 эпох
        'patience': 50,             # Раннее прекращение
        'save': True,
        'cache': True,
        'workers': 2,
        'verbose': True,
        'exist_ok': True,
        'pretrained': True,

        # Исправленные параметры для предотвращения слипания
        'lr0': 0.005,               # Начальная скорость обучения
        'lrf': 0.005,               # Финальная скорость обучения
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'warmup_epochs': 10,        # Дольше warmup
        'warmup_momentum': 0.8,
        'warmup_bias_lr': 0.05,

        # Параметры потерь для предотвращения слипания
        'box': 5.0,                 # Вес box loss
        'cls': 0.5,                 # Вес classification loss
        'dfl': 1.5,                 # Distribution Focal Loss

        # Параметры для NMS и предотвращения слипания
        'iou': 0.7,                 # IoU threshold для NMS
        'conf': 0.25,               # Confidence threshold

        # Отключаем аугментации, которые могут вызвать слипание
        'hsv_h': 0.1,               # Минимальная аугментация цвета
        'hsv_s': 0.1,
        'hsv_v': 0.1,
        'degrees': 5.0,             # Маленький поворот
        'translate': 0.1,           # Маленький сдвиг
        'scale': 0.1,               # Маленькое масштабирование
        'shear': 2.0,               # Маленькое искажение
        'perspective': 0.001,
        'flipud': 0.0,              # Отключаем вертикальное отражение
        'fliplr': 0.0,              # Отключаем горизонтальное отражение
        'mosaic': 0.0,              # Отключаем мозаику
        'mixup': 0.0,               # Отключаем mixup
        'copy_paste': 0.0,

        # Дополнительные параметры для стабильности
        'overlap_mask': False,      # Отключаем пересечения масок
        'mask_ratio': 1,
        'dropout': 0.1,             # Dropout для предотвращения переобучения
        'amp': True,                # Автоматическая смешанная точность
    }

    try:
        # Загружаем предобученную модель
        print("📥 Загружаем YOLO модель...")
        model = YOLO('yolov8n.pt')

        print("🏃 Начинаем обучение...")
        print("Параметры обучения:")
        for key, value in train_args.items():
            print(f"  {key}: {value}")

        # Запускаем обучение
        results = model.train(**train_args)

        print("\\n✅ Обучение завершено!")
        print(f"📁 Результаты сохранены в: {output_dir}")

        # Сохраняем лучшую модель
        best_model_path = output_dir / 'weights' / 'best.pt'
        if best_model_path.exists():
            print(f"🏆 Лучшая модель: {best_model_path}")

            # Копируем в удобное место
            final_model_path = Path("src/best_yolo_model_fixed.pt")
            import shutil
            shutil.copy2(best_model_path, final_model_path)
            print(f"📋 Финальная модель скопирована: {final_model_path}")

        return True

    except Exception as e:
        print(f"❌ Ошибка при обучении: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print("\\n" + "=" * 50)
    if success:
        print("🎯 Обучение завершено успешно!")
        print("Рекомендации:")
        print("1. Проверьте результаты на тестовых данных")
        print("2. Если боксы все еще слипаются, попробуйте увеличить IoU threshold")
        print("3. Рассмотрите возможность объединения близких полей")
    else:
        print("❌ Возникли ошибки при обучении")
