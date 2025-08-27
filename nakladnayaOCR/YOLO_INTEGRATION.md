# Интеграция YOLO + Marker

## Обзор

Успешно интегрирована система автоматической детекции полей документов на основе YOLOv8 с последующей обработкой через Marker OCR.

## Результаты обучения

- **Модель**: YOLOv8n (nano)
- **Качество**: mAP50 ≈ 90%
- **Детектируемые поля**: 7 типов
  - delivery-date (дата доставки)
  - order-date (дата заказа) 
  - carrier (перевозчик)
  - recipient (получатель)
  - payload (груз)
  - price (цена)
  - address (адрес)

## Архитектура системы

```
PDF/Изображение → YOLO детекция → Извлечение полей → Marker OCR → Структурированный результат
```

## Ключевые компоненты

### 1. YoloFieldDetector (`src/yolo_detector.py`)
- Детекция полей с использованием обученной модели
- Создание аннотированных изображений
- Извлечение регионов полей

### 2. YoloMarkerProcessor (`src/utils.py`)
- Интеграция YOLO + Marker
- Конвертация PDF в изображения
- Полный пайплайн обработки документов

### 3. Обученная модель
- Расположение: `src/best_invoice_model.pt`
- Обучена на аугментированных данных
- Высокая точность на накладных

## Использование

### Через Streamlit интерфейс
```bash
source yolo_env/bin/activate
streamlit run streamlit_app.py
```

### Программный интерфейс
```python
from src.config import Config
from src.utils import YoloMarkerProcessor

config = Config()
processor = YoloMarkerProcessor(config)
result = processor.process_document(image_path, output_dir)
```

## Структура результата

```python
{
    "processing_success": True,
    "yolo_detection": {
        "fields": [...],           # Обнаруженные поля
        "field_count": 7,          # Количество полей
        "summary": {...}           # Сводка
    },
    "marker_text": "...",         # Полный текст документа
    "field_texts": {              # Текст из каждого поля
        "carrier": "...",
        "recipient": "...",
        # ...
    }
}
```

## Демонстрация

Запустите `demo_yolo_integration.py` для полной демонстрации:

```bash
source yolo_env/bin/activate
python demo_yolo_integration.py
```

## Зависимости

- ultralytics (YOLOv8)
- PyMuPDF (конвертация PDF)
- marker-pdf (OCR)
- torch/torchvision

## Производительность

- **YOLO детекция**: ~1-2 сек
- **Marker OCR**: ~15-20 сек  
- **Общее время**: ~20-25 сек на документ

## Масштабируемость

Система готова для:
- Пакетной обработки документов
- Добавления новых типов полей
- Интеграции с API
- Docker развертывания
