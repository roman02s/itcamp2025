#!/bin/bash
# Скрипт для запуска сервиса извлечения информации из накладных

echo "🧾 Запуск сервиса извлечения информации из накладных"
echo "=================================================="

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+ для работы сервиса."
    exit 1
fi

# Проверка виртуального окружения
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Виртуальное окружение не активировано."
    echo "Рекомендуется создать и активировать venv:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
fi

# Проверка зависимостей
echo "🔍 Проверка зависимостей..."
python3 -c "import streamlit" 2>/dev/null || {
    echo "❌ Streamlit не установлен. Установите зависимости:"
    echo "  pip install -r requirements.txt"
    exit 1
}

# Проверка Marker (опционально)
if command -v marker_single &> /dev/null; then
    echo "✅ Marker CLI найден"
else
    echo "⚠️  marker_single не найден. OCR функциональность может быть ограничена."
    echo "Для установки Marker:"
    echo "  pip install marker-pdf"
fi

# Запуск приложения
echo ""
echo "🚀 Запуск веб-интерфейса..."
echo "Откройте браузер по адресу: http://localhost:8501"
echo ""

streamlit run streamlit_app.py
