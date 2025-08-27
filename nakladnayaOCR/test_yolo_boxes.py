#!/usr/bin/env python3
"""
Тест YOLO модели на слипание боксов
"""

import sys
from pathlib import Path
from ultralytics import YOLO
import cv2
import json

def test_yolo_boxes(model_path: str, test_image: str):
    """Тест модели на слипание боксов"""

    print("🧪 Тестирование YOLO модели на слипание боксов")
    print("=" * 50)

    # Загружаем модель
    try:
        model = YOLO(model_path)
        print(f"✅ Модель загружена: {model_path}")
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        return False

    # Загружаем тестовое изображение
    image_path = Path(test_image)
    if not image_path.exists():
        print(f"❌ Изображение не найдено: {test_image}")
        return False

    print(f"🖼️  Обрабатываем изображение: {image_path.name}")

    # Запускаем детекцию
    try:
        results = model.predict(
            str(image_path),
            conf=0.25,
            iou=0.7,  # Высокий IoU threshold для предотвращения слипания
            save=False,
            verbose=True
        )

        if not results or len(results) == 0:
            print("❌ Результаты детекции отсутствуют")
            return False

        result = results[0]

        # Анализируем результаты
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            print("❌ Боксы не обнаружены")
            return False

        print(f"\\n📊 Обнаружено {len(boxes)} боксов")

        # Выводим информацию о каждом боксе
        detections = []
        for i, box in enumerate(boxes):
            # Координаты
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = box.conf[0].cpu().numpy()
            cls = int(box.cls[0].cpu().numpy())

            # Получаем имя класса
            class_name = model.names[cls]

            width = x2 - x1
            height = y2 - y1
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            detection = {
                'id': i + 1,
                'class': class_name,
                'confidence': float(conf),
                'bbox': {
                    'x1': float(x1), 'y1': float(y1),
                    'x2': float(x2), 'y2': float(y2),
                    'width': float(width), 'height': float(height),
                    'center_x': float(center_x), 'center_y': float(center_y)
                }
            }

            detections.append(detection)

            print(f"  {i+1}. {class_name}: уверенность={conf:.3f}, "
                  f"позиция=({x1:.1f}, {y1:.1f}), "
                  f"размер={width:.1f}x{height:.1f}")

        # Проверяем на слипание боксов
        print("\\n🔍 АНАЛИЗ СЛИПАНИЯ БОКСОВ:")

        overlapping_pairs = []
        close_pairs = []

        for i in range(len(detections)):
            for j in range(i + 1, len(detections)):
                box1 = detections[i]
                box2 = detections[j]

                # Вычисляем IoU
                x1_1, y1_1, x2_1, y2_1 = box1['bbox']['x1'], box1['bbox']['y1'], box1['bbox']['x2'], box1['bbox']['y2']
                x1_2, y1_2, x2_2, y2_2 = box2['bbox']['x1'], box2['bbox']['y1'], box2['bbox']['x2'], box2['bbox']['y2']

                # Пересечение
                x1_inter = max(x1_1, x1_2)
                y1_inter = max(y1_1, y1_2)
                x2_inter = min(x2_1, x2_2)
                y2_inter = min(y2_1, y2_2)

                inter_width = max(0, x2_inter - x1_inter)
                inter_height = max(0, y2_inter - y1_inter)
                inter_area = inter_width * inter_height

                # Объединение
                box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
                box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
                union_area = box1_area + box2_area - inter_area

                iou = inter_area / union_area if union_area > 0 else 0

                # Расстояние между центрами
                center1_x, center1_y = box1['bbox']['center_x'], box1['bbox']['center_y']
                center2_x, center2_y = box2['bbox']['center_x'], box2['bbox']['center_y']

                distance = ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5

                if iou > 0.1:  # Значительное пересечение
                    overlapping_pairs.append((box1, box2, iou, distance))
                    print(f"  ❌ СЛИПАНИЕ: {box1['class']} и {box2['class']}")
                    print(f"     IoU: {iou:.3f}, Расстояние: {distance:.1f} пикселей")
                elif distance < 30:  # Близкие боксы
                    close_pairs.append((box1, box2, iou, distance))
                    print(f"  ⚠️  БЛИЗКИЕ: {box1['class']} и {box2['class']}")
                    print(f"     Расстояние: {distance:.1f} пикселей")

        # Выводим статистику
        print(f"\\n📈 СТАТИСТИКА:")
        print(f"   Всего боксов: {len(detections)}")
        print(f"   Слипшихся пар: {len(overlapping_pairs)}")
        print(f"   Близких пар: {len(close_pairs)}")

        # Сохраняем результаты
        output_data = {
            'model': model_path,
            'image': str(image_path),
            'detections': detections,
            'overlapping_pairs': len(overlapping_pairs),
            'close_pairs': len(close_pairs),
            'analysis': {
                'has_overlapping': len(overlapping_pairs) > 0,
                'has_close_pairs': len(close_pairs) > 0
            }
        }

        output_file = Path("yolo_test_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\\n💾 Результаты сохранены в: {output_file}")

        # Итоговая оценка
        if len(overlapping_pairs) == 0:
            print("\\n✅ ТЕСТ ПРОЙДЕН: Слипания боксов не обнаружено!")
            if len(close_pairs) == 0:
                print("🏆 ОТЛИЧНЫЙ РЕЗУЛЬТАТ: Все боксы хорошо разделены")
            else:
                print(f"⚠️  ВНИМАНИЕ: Есть {len(close_pairs)} близких пар, но без слипания")
            return True
        else:
            print(f"\\n❌ ТЕСТ ПРОВАЛЕН: Обнаружено {len(overlapping_pairs)} слипшихся пар")
            return False

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция"""

    if len(sys.argv) != 3:
        print("Использование: python test_yolo_boxes.py <model_path> <image_path>")
        print("Пример: python test_yolo_boxes.py src/best_yolo_model_fixed.pt data/yolo_dataset/Obrazets-zapolneniya-TN-2025-2-4.pdf_page_1.png")
        return

    model_path = sys.argv[1]
    image_path = sys.argv[2]

    success = test_yolo_boxes(model_path, image_path)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
