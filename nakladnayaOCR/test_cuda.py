#!/usr/bin/env python3
"""
Скрипт для проверки доступности CUDA в контейнере
"""

import torch
import sys

def test_cuda():
    """Тестирование CUDA доступности"""
    print("🔍 Проверка поддержки CUDA...")
    print(f"PyTorch версия: {torch.__version__}")
    
    # Проверка доступности CUDA
    cuda_available = torch.cuda.is_available()
    print(f"CUDA доступна: {cuda_available}")
    
    if cuda_available:
        print(f"Количество GPU: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"  Память: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")
        
        # Тест простых операций на GPU
        try:
            print("\n🧪 Тестирование операций на GPU...")
            device = torch.device('cuda:0')
            x = torch.randn(1000, 1000, device=device)
            y = torch.randn(1000, 1000, device=device)
            z = torch.matmul(x, y)
            print("✅ Матричное умножение на GPU успешно!")
            
            # Проверка памяти GPU
            print(f"Использовано GPU памяти: {torch.cuda.memory_allocated() / 1024**2:.1f} MB")
            print(f"Зарезервировано GPU памяти: {torch.cuda.memory_reserved() / 1024**2:.1f} MB")
            
        except Exception as e:
            print(f"❌ Ошибка при работе с GPU: {e}")
            return False
    else:
        print("❌ CUDA недоступна. Проверьте:")
        print("  1. Установлен ли NVIDIA драйвер")
        print("  2. Установлен ли NVIDIA Container Runtime")
        print("  3. Запущен ли контейнер с флагом --gpus")
        return False
    
    return True

if __name__ == "__main__":
    success = test_cuda()
    sys.exit(0 if success else 1)
