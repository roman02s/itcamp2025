# streamlit_app.py
# ── Основная логика: загрузка файла → OCR/парсинг через Marker → извлечение ключевых полей ──
import os
import re
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import logging

import streamlit as st

from src.parser import InvoiceParser
from src.utils import TextProcessor, MarkerRunner
from src.config import Config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация страницы
st.set_page_config(
    page_title="Парсер накладной (Marker OCR)", 
    page_icon="🧾", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Основная функция приложения"""
    
    # Заголовок и описание
    st.title("🧾 Сервис извлечения информации из накладных")
    st.markdown("""
    Этот сервис использует OCR технологию Marker для извлечения ключевой информации 
    из товарных накладных, счетов-фактур и других документов.
    """)
    
    # Боковая панель с настройками
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        # Выбор формата вывода Marker
        output_format = st.selectbox(
            "Формат вывода Marker:",
            ["markdown", "json", "html"],
            help="markdown - лучше для извлечения текста, json - содержит координаты"
        )
        
        # Принудительное OCR
        force_ocr = st.checkbox(
            "Принудительное OCR", 
            value=True,
            help="Использовать OCR даже для PDF с текстовым слоем"
        )
        
        # Отладочный режим
        debug_mode = st.checkbox(
            "Режим отладки",
            help="Показывать дополнительную информацию для отладки"
        )
        
        # Настройки обработки
        st.subheader("Обработка текста")
        max_lines_section = st.slider("Макс. строк для секции", 5, 20, 8)
        confidence_threshold = st.slider("Порог уверенности", 0.1, 1.0, 0.7)
    
    # Основная область
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📁 Загрузка документа")
        
        # Загрузка файла
        uploaded_file = st.file_uploader(
            "Выберите файл накладной",
            type=["pdf", "png", "jpg", "jpeg", "tiff", "bmp"],
            help="Поддерживаются PDF и изображения"
        )
        
        # Или выбор из примеров
        st.markdown("**Или выберите пример:**")
        use_sample = st.button("📋 Использовать образец ТН-2025")
        
        if use_sample:
            sample_path = Path("data/Obrazets-zapolneniya-TN-2025-2.pdf")
            if sample_path.exists():
                with open(sample_path, "rb") as f:
                    uploaded_file = type('MockFile', (), {
                        'read': lambda: f.read(),
                        'name': sample_path.name
                    })()
            else:
                st.error("Образец файла не найден")
    
    with col2:
        st.subheader("🔧 Статус обработки")
        status_container = st.empty()
        progress_bar = st.progress(0)
    
    # Обработка файла
    if uploaded_file is not None:
        if st.button("🚀 Обработать документ", type="primary"):
            try:
                # Инициализация компонентов
                config = Config(
                    output_format=output_format,
                    force_ocr=force_ocr,
                    max_lines_section=max_lines_section,
                    confidence_threshold=confidence_threshold,
                    debug_mode=debug_mode
                )
                
                marker_runner = MarkerRunner(config)
                text_processor = TextProcessor(config)
                invoice_parser = InvoiceParser(config, text_processor)
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmpdir = Path(tmpdir)
                    
                    # Сохранение загруженного файла
                    status_container.info("📥 Сохранение файла...")
                    progress_bar.progress(10)
                    
                    input_path = tmpdir / uploaded_file.name
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.read())
                    
                    # Запуск Marker OCR
                    status_container.info("🔍 Выполнение OCR...")
                    progress_bar.progress(30)
                    
                    try:
                        output_path = marker_runner.run(input_path, tmpdir / "marker_out")
                        
                        # Извлечение текста
                        status_container.info("📝 Извлечение текста...")
                        progress_bar.progress(60)
                        
                        text = text_processor.extract_text_from_marker_output(output_path)
                        
                        if debug_mode:
                            st.expander("🔍 Извлеченный текст (первые 2000 символов)").text(text[:2000])
                        
                        # Парсинг информации
                        status_container.info("🧠 Извлечение информации...")
                        progress_bar.progress(80)
                        
                        result = invoice_parser.parse(text)
                        
                        status_container.success("✅ Обработка завершена!")
                        progress_bar.progress(100)
                        
                        # Отображение результатов
                        display_results(result, debug_mode, text if debug_mode else None)
                        
                    except subprocess.CalledProcessError as e:
                        status_container.error("❌ Ошибка при запуске Marker OCR")
                        st.error(f"Команда завершилась с ошибкой: {e}")
                        if e.stderr:
                            st.code(e.stderr, language="bash")
                        
            except Exception as e:
                status_container.error("❌ Произошла ошибка")
                st.error(f"Ошибка обработки: {str(e)}")
                logger.exception("Ошибка при обработке файла")
                
                if debug_mode:
                    st.exception(e)

def display_results(result: Dict, debug_mode: bool, raw_text: Optional[str] = None):
    """Отображение результатов парсинга"""
    
    st.subheader("📊 Результаты извлечения")
    
    # Основная информация в метриках
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Тип документа", result.get("document_type", "Неизвестно"))
    
    with col2:
        st.metric("Номер", result.get("number") or "Не найден")
    
    with col3:
        st.metric("Дата", result.get("date") or "Не найдена")
    
    with col4:
        amounts = result.get("amounts", {})
        total = amounts.get("total_with_vat") or amounts.get("total_without_vat")
        st.metric("Сумма", f"{total:,.2f} ₽" if total else "Не найдена")
    
    # Детальная информация в табах
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Контрагенты", "💰 Суммы", "🚚 Логистика", "🔧 Техническая"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Поставщик")
            supplier = result.get("supplier", {})
            st.write(f"**Название:** {supplier.get('name') or 'Не указано'}")
            st.write(f"**ИНН:** {supplier.get('INN') or 'Не найден'}")
            st.write(f"**КПП:** {supplier.get('KPP') or 'Не найден'}")
        
        with col2:
            st.subheader("Покупатель")
            buyer = result.get("buyer", {})
            st.write(f"**Название:** {buyer.get('name') or 'Не указано'}")
            st.write(f"**ИНН:** {buyer.get('INN') or 'Не найден'}")
            st.write(f"**КПП:** {buyer.get('KPP') or 'Не найден'}")
    
    with tab2:
        amounts = result.get("amounts", {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Сумма без НДС", 
                f"{amounts.get('total_without_vat'):,.2f} ₽" if amounts.get('total_without_vat') else "Не найдена"
            )
        
        with col2:
            st.metric(
                "НДС",
                f"{amounts.get('vat'):,.2f} ₽" if amounts.get('vat') else "Не найден"
            )
        
        with col3:
            st.metric(
                "Сумма с НДС",
                f"{amounts.get('total_with_vat'):,.2f} ₽" if amounts.get('total_with_vat') else "Не найдена"
            )
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Грузоотправитель")
            shipper = result.get("shipper")
            st.write(shipper if shipper else "Не указан")
        
        with col2:
            st.subheader("Грузополучатель") 
            consignee = result.get("consignee")
            st.write(consignee if consignee else "Не указан")
    
    with tab4:
        if debug_mode:
            st.subheader("Отладочная информация")
            
            # JSON результат
            st.subheader("Полный результат (JSON)")
            st.json(result)
            
            # Сырой текст (если передан)
            if raw_text:
                st.subheader("Извлеченный текст")
                st.text_area("Полный текст", raw_text, height=300)
        else:
            st.info("Включите режим отладки в боковой панели для просмотра технической информации")
    
    # Кнопки для скачивания
    st.subheader("💾 Экспорт результатов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON экспорт
        json_str = json.dumps(result, ensure_ascii=False, indent=2)
        st.download_button(
            label="📄 Скачать JSON",
            data=json_str,
            file_name=f"invoice_data_{result.get('number', 'unknown')}.json",
            mime="application/json"
        )
    
    with col2:
        # CSV экспорт (упрощенный)
        csv_data = create_csv_export(result)
        st.download_button(
            label="📊 Скачать CSV", 
            data=csv_data,
            file_name=f"invoice_data_{result.get('number', 'unknown')}.csv",
            mime="text/csv"
        )

def create_csv_export(result: Dict) -> str:
    """Создание CSV экспорта"""
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        "Тип документа", "Номер", "Дата",
        "Поставщик", "ИНН поставщика", "КПП поставщика",
        "Покупатель", "ИНН покупателя", "КПП покупателя", 
        "Сумма без НДС", "НДС", "Сумма с НДС"
    ])
    
    # Данные
    supplier = result.get("supplier", {})
    buyer = result.get("buyer", {})
    amounts = result.get("amounts", {})
    
    writer.writerow([
        result.get("document_type", ""),
        result.get("number", ""),
        result.get("date", ""),
        supplier.get("name", ""),
        supplier.get("INN", ""),
        supplier.get("KPP", ""),
        buyer.get("name", ""),
        buyer.get("INN", ""),
        buyer.get("KPP", ""),
        amounts.get("total_without_vat", ""),
        amounts.get("vat", ""),
        amounts.get("total_with_vat", "")
    ])
    
    return output.getvalue()

if __name__ == "__main__":
    main()
