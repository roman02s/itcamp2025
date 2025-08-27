#!/usr/bin/env python3
"""
Скрипт для проверки пересекающихся боксов в данных
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple

def calculate_iou(box1: Dict, box2: Dict) -> float:
    """Вычисление IoU (Intersection over Union) двух боксов"""
    x1_1, y1_1 = float(box1['x']), float(box1['y'])
    x2_1, y2_1 = x1_1 + float(box1['width']), y1_1 + float(box1['height'])

    x1_2, y1_2 = float(box2['x']), float(box2['y'])
    x2_2, y2_2 = x1_2 + float(box2['width']), y1_2 + float(box2['height'])

    # Координаты пересечения
    x1_inter = max(x1_1, x1_2)
    y1_inter = max(y1_1, y1_2)
    x2_inter = min(x2_1, x2_2)
    y2_inter = min(y2_1, y2_2)

    # Площадь пересечения
    inter_width = max(0, x2_inter - x1_inter)
    inter_height = max(0, y2_inter - y1_inter)
    inter_area = inter_width * inter_height

    # Площади боксов
    box1_area = float(box1['width']) * float(box1['height'])
    box2_area = float(box2['width']) * float(box2['height'])

    # IoU
    union_area = box1_area + box2_area - inter_area
    if union_area == 0:
        return 0.0

    return inter_area / union_area

def check_overlapping_boxes(annotation_file: Path):
    """Проверка пересекающихся боксов в файле аннотаций"""

    print(f"🔍 Проверяем файл: {annotation_file.name}")

    with open(annotation_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    boxes = data['boxes']
    width = data['width']
    height = data['height']

    print(f"📊 Всего боксов: {len(boxes)}")
    print(f"📐 Размер изображения: {width}x{height}")

    # Список для хранения проблемных пар
    overlapping_pairs = []
    close_pairs = []

    # Проверяем все пары боксов
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            box1 = boxes[i]
            box2 = boxes[j]

            # Вычисляем расстояние между центрами
            center1_x = float(box1['x']) + float(box1['width']) / 2
            center1_y = float(box1['y']) + float(box1['height']) / 2

            center2_x = float(box2['x']) + float(box2['width']) / 2
            center2_y = float(box2['y']) + float(box2['height']) / 2

            distance = ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5

            # Вычисляем IoU
            iou = calculate_iou(box1, box2)

            if iou > 0:
                overlapping_pairs.append((box1, box2, iou, distance))
                print(f"⚠️  ПЕРЕСЕЧЕНИЕ: {box1['label']} и {box2['label']}")
                print(f"   IoU: {iou:.3f}, Расстояние между центрами: {distance:.1f} пикселей")
            elif distance < 50:  # Близкие боксы (меньше 50 пикселей)
                close_pairs.append((box1, box2, iou, distance))
                print(f"⚠️  БЛИЗКИЕ: {box1['label']} и {box2['label']}")
                print(f"   Расстояние: {distance:.1f} пикселей")

    # Вывод статистики
    print(f"\n📈 СТАТИСТИКА:")
    print(f"   Пересекающихся пар: {len(overlapping_pairs)}")
    print(f"   Близких пар: {len(close_pairs)}")

    # Детальный анализ каждого бокса
    print(f"\n🏷️  АНАЛИЗ БОКСОВ:")
    for i, box in enumerate(boxes):
        x, y = float(box['x']), float(box['y'])
        w, h = float(box['width']), float(box['height'])

        print(f"   {i+1}. {box['label']}: "
              f"позиция=({x:.1f}, {y:.1f}), "
              f"размер={w:.1f}x{h:.1f}, "
              f"соотношение={w/h:.2f}")

        # Проверяем, не слишком ли маленький бокс
        if h < 20 or w < 50:
            print(f"      ⚠️  МАЛЕНЬКИЙ БОКС!")

    return len(overlapping_pairs), len(close_pairs)

def main():
    """Главная функция"""
    annotation_file = Path("data/yolo_dataset/annotated_data.json")

    if not annotation_file.exists():
        print(f"❌ Файл аннотаций не найден: {annotation_file}")
        return

    print("🚀 Проверка пересекающихся боксов в данных")
    print("=" * 50)

    overlapping, close = check_overlapping_boxes(annotation_file)

    print("\n" + "=" * 50)
    if overlapping > 0:
        print(f"❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ: {overlapping} пересекающихся боксов")
        print("Рекомендации:")
        print("1. Исправьте пересекающиеся боксы в данных")
        print("2. Убедитесь, что между близкими полями есть достаточное расстояние")
        print("3. Рассмотрите увеличение минимального расстояния между боксами")
    else:
        print("✅ Пересекающихся боксов не найдено")

    if close > 0:
        print(f"⚠️  Найдено {close} близких пар боксов")
        print("Рекомендации:")
        print("1. Проверьте, что близкие боксы действительно должны быть отдельными")
        print("2. Рассмотрите объединение близких полей в одно")

if __name__ == "__main__":
    main()
