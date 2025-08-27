#!/bin/bash
# Скрипт для запуска приложения через Docker с поддержкой CUDA

echo "🐳 Запуск приложения извлечения информации из накладных через Docker (CUDA)"
echo "======================================================================"

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установите Docker для продолжения."
    exit 1
fi

if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo "❌ Docker Compose не найден. Установите Docker Compose для продолжения."
    exit 1
fi

# Проверка NVIDIA Docker runtime
if ! nvidia-smi &> /dev/null; then
    echo "⚠️  NVIDIA GPU или NVIDIA Container Runtime не найден."
    echo "   Приложение будет запущено без поддержки GPU."
    echo "   Для включения CUDA установите NVIDIA Docker runtime."
    read -p "Продолжить без GPU? (y/n): " continue_without_gpu
    if [ "$continue_without_gpu" != "y" ]; then
        exit 1
    fi
else
    echo "✅ NVIDIA GPU поддержка обнаружена"
    nvidia-smi
fi

# Создание необходимых директорий
mkdir -p uploads temp data

# Выбор режима запуска
echo ""
echo "Выберите режим запуска:"
echo "1) Производственный режим (production)"
echo "2) Режим разработки (development)"
echo "3) Остановить контейнеры"
echo "4) Пересобрать образы"
echo "5) Просмотр логов"
read -p "Введите номер (1-5): " choice

case $choice in
    1)
        echo "🚀 Запуск в производственном режиме..."
        docker compose up -d
        ;;
    2)
        echo "🛠️  Запуск в режиме разработки..."
        if [ -f "docker-compose.dev.yml" ]; then
            docker compose -f docker-compose.dev.yml up -d
        else
            echo "❌ Файл docker-compose.dev.yml не найден. Запуск в обычном режиме..."
            docker compose up -d
        fi
        ;;
    3)
        echo "🛑 Остановка контейнеров..."
        docker compose down
        if [ -f "docker-compose.dev.yml" ]; then
            docker compose -f docker-compose.dev.yml down
        fi
        ;;
    4)
        echo "🔨 Пересборка образов..."
        docker compose down
        docker compose build
        docker compose up -d
        ;;
    5)
        echo "📊 Просмотр логов..."
        docker compose logs -f
        ;;
    *)
        echo "❌ Неверный выбор. Используйте 1, 2, 3, 4 или 5."
        exit 1
        ;;
esac

if [ "$choice" = "1" ] || [ "$choice" = "2" ]; then
    echo ""
    echo "✅ Приложение запущено!"
    echo "🌐 Откройте браузер по адресу: http://localhost:8501"
    echo "📊 Для просмотра логов: docker compose logs -f"
    echo "🛑 Для остановки: ./docker-run.sh (выберите опцию 3)"
    echo "🔍 Проверка GPU внутри контейнера:"
    echo "   docker exec nakladnaya-ocr-app nvidia-smi"
fi
