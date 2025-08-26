# 🧾 Сервис извлечения информации из накладных

Современный сервис для автоматического извлечения ключевой информации из товарных накладных, счетов-фактур и других документов с использованием OCR технологии Marker.

## 🚀 Возможности

- **Автоматическое OCR**: Использует Marker для высококачественного распознавания текста из PDF и изображений
- **Извлечение ключевых полей**: Автоматически находит номер, дату, контрагентов, суммы и другую важную информацию
- **Поддержка форматов**: PDF, PNG, JPG, JPEG, TIFF, BMP
- **Веб-интерфейс**: Удобный интерфейс на Streamlit с возможностью экспорта результатов
- **Отладочный режим**: Детальная информация о процессе извлечения
- **Экспорт данных**: Сохранение результатов в JSON и CSV форматах

## 📋 Извлекаемые поля

### Основная информация
- Тип документа
- Номер документа
- Дата документа

### Контрагенты
- **Поставщик**: название, ИНН, КПП
- **Покупатель**: название, ИНН, КПП
- **Грузоотправитель** (если отличается)
- **Грузополучатель** (если отличается)

### Финансовые данные
- Сумма без НДС
- Сумма НДС
- Общая сумма с НДС

## 🛠 Установка

### Требования
- Python 3.8+
- marker-pdf (устанавливается отдельно)

### Пошаговая установка

1. **Клонирование репозитория**
```bash
git clone <repository-url>
cd nakladnayaOCR
```

2. **Создание виртуального окружения**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

4. **Установка Marker**

Marker требует отдельной установки. Выберите один из вариантов:

**Вариант A: Установка через pip**
```bash
pip install marker-pdf
```

**Вариант B: Установка из исходников**
```bash
git clone https://github.com/VikParuchuri/marker.git
cd marker
pip install -e .
```

5. **Проверка установки**
```bash
marker_single --help
```

## 🚀 Запуск

### Запуск веб-интерфейса
```bash
streamlit run streamlit_app.py
```

Откройте браузер и перейдите по адресу `http://localhost:8501`

### Настройки окружения

Для оптимальной работы можно настроить переменные окружения:

```bash
# Принудительное использование CPU (если нет GPU)
export CUDA_VISIBLE_DEVICES=""
export TORCH_DEVICE="cpu"

# Для работы с GPU
export CUDA_VISIBLE_DEVICES="0"
export TORCH_DEVICE="cuda"
```

## 📖 Использование

### Веб-интерфейс

1. Откройте веб-интерфейс
2. Загрузите файл накладной или выберите образец
3. Настройте параметры в боковой панели:
   - Формат вывода Marker
   - Принудительное OCR
   - Режим отладки
4. Нажмите "Обработать документ"
5. Просмотрите результаты в удобном формате
6. Экспортируйте данные в JSON или CSV

### Программное использование

```python
from src.config import Config
from src.utils import MarkerRunner, TextProcessor
from src.parser import InvoiceParser

# Настройка
config = Config(output_format="markdown", force_ocr=True)
marker_runner = MarkerRunner(config)
text_processor = TextProcessor(config)
parser = InvoiceParser(config, text_processor)

# Обработка файла
output_path = marker_runner.run(pdf_path, output_dir)
text = text_processor.extract_text_from_marker_output(output_path)
result = parser.parse(text)

print(result)
```

## ⚙️ Конфигурация

Основные настройки находятся в `src/config.py`:

```python
@dataclass
class Config:
    output_format: str = "markdown"  # markdown, json, html
    force_ocr: bool = True
    torch_device: str = "cpu"
    max_lines_section: int = 8
    confidence_threshold: float = 0.7
    debug_mode: bool = False
```

## 🧪 Тестирование

Протестируйте сервис с образцом накладной:

```bash
# Запустите Streamlit и используйте кнопку "Использовать образец ТН-2025"
streamlit run streamlit_app.py
```

## 📁 Структура проекта

```
nakladnayaOCR/
├── streamlit_app.py          # Основное приложение
├── requirements.txt          # Зависимости
├── README.md                # Документация
├── data/                    # Образцы документов
│   └── Obrazets-zapolneniya-TN-2025-2.pdf
└── src/                     # Исходный код
    ├── __init__.py
    ├── config.py            # Конфигурация
    ├── utils.py            # Утилиты обработки
    └── parser.py           # Основной парсер
```

## 🔧 Устранение неполадок

### Проблемы с Marker

**Ошибка: "marker_single not found"**
```bash
# Убедитесь, что Marker установлен
pip install marker-pdf
marker_single --help
```

**Проблемы с GPU**
```bash
# Принудительное использование CPU
export CUDA_VISIBLE_DEVICES=""
export TORCH_DEVICE="cpu"
```

### Проблемы с зависимостями

**Конфликты версий**
```bash
# Создайте чистое окружение
python -m venv fresh_venv
source fresh_venv/bin/activate
pip install -r requirements.txt
```

### Проблемы с качеством распознавания

1. Попробуйте разные форматы вывода (`markdown`, `json`)
2. Убедитесь, что включено принудительное OCR
3. Проверьте качество исходного изображения
4. Используйте режим отладки для анализа

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для фичи (`git checkout -b feature/amazing-feature`)
3. Внесите изменения и протестируйте
4. Создайте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для деталей.

## 🆘 Поддержка

Если у вас возникли проблемы:

1. Проверьте раздел "Устранение неполадок"
2. Создайте Issue с подробным описанием проблемы
3. Приложите логи и образцы документов (без конфиденциальных данных)

## 🔮 Планы развития

- [ ] Поддержка дополнительных типов документов
- [ ] Интеграция с базами данных
- [ ] API для массовой обработки
- [ ] Улучшение точности извлечения
- [ ] Поддержка многоязычных документов
