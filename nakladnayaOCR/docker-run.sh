#!/bin/bash
# Скрипт для запуска приложения через Docker

echo "🐳 Запуск приложения извлечения информации из накладных через Docker"
echo "=================================================================="

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установите Docker для продолжения."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo "❌ Docker Compose не найден. Установите Docker Compose для продолжения."
    exit 1
fi

# Создание необходимых директорий
mkdir -p uploads temp data

# Выбор режима запуска
echo "Выберите режим запуска:"
echo "1) Производственный режим (production)"
echo "2) Режим разработки (development)"
echo "3) Остановить контейнеры"
echo "4) Пересобрать образы"
read -p "Введите номер (1-4): " choice

case $choice in
    1)
        echo "🚀 Запуск в производственном режиме..."
        docker-compose up -d
        ;;
    2)
        echo "🛠️  Запуск в режиме разработки..."
        docker-compose -f docker-compose.dev.yml up -d
        ;;
    3)
        echo "🛑 Остановка контейнеров..."
        docker-compose down
        docker-compose -f docker-compose.dev.yml down
        ;;
    4)
        echo "🔨 Пересборка образов..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        ;;
    *)
        echo "❌ Неверный выбор. Используйте 1, 2, 3 или 4."
        exit 1
        ;;
esac

if [ "$choice" = "1" ] || [ "$choice" = "2" ]; then
    echo ""
    echo "✅ Приложение запущено!"
    echo "🌐 Откройте браузер по адресу: http://localhost:8501"
    echo "📊 Для просмотра логов: docker-compose logs -f"
    echo "🛑 Для остановки: ./docker-run.sh (выберите опцию 3)"
fi
