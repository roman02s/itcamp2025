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
from src.utils import TextProcessor, MarkerRunner, YoloMarkerProcessor
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
        
        # Настройки YOLO
        st.subheader("YOLO детекция")
        use_yolo = st.checkbox(
            "Использовать YOLO детекцию полей", 
            value=True,
            help="Автоматическое обнаружение полей с помощью обученной YOLO модели"
        )
        yolo_confidence = st.slider("Порог уверенности YOLO", 0.1, 1.0, 0.25)
    
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
                
                # Выбор обработчика
                if use_yolo:
                    processor = YoloMarkerProcessor(config)
                    use_enhanced_processing = processor.is_yolo_available()
                    if not use_enhanced_processing:
                        st.warning("⚠️ YOLO недоступен, используется стандартная обработка")
                else:
                    use_enhanced_processing = False
                
                if not use_enhanced_processing:
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
                    
                    if use_enhanced_processing:
                        # YOLO + Marker обработка
                        status_container.info("🎯 YOLO детекция полей...")
                        progress_bar.progress(20)
                        
                        status_container.info("🔍 Выполнение OCR...")
                        progress_bar.progress(50)
                        
                        status_container.info("📝 Извлечение текста из полей...")
                        progress_bar.progress(80)
                        
                        # Полная обработка через YOLO + Marker
                        enhanced_result = processor.process_document(input_path, tmpdir / "output")
                        
                        status_container.success("✅ Расширенная обработка завершена!")
                        progress_bar.progress(100)
                        
                        # Отображение результатов
                        display_enhanced_results(enhanced_result, debug_mode)
                        
                    else:
                        # Стандартная обработка
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


def display_enhanced_results(enhanced_result: Dict, debug_mode: bool):
    """Отображение результатов расширенной обработки (YOLO + Marker)"""
    
    st.subheader("🎯 Результаты YOLO + Marker обработки")
    
    # Проверяем успешность обработки
    if not enhanced_result.get("processing_success", False):
        st.error("❌ Ошибка при обработке документа")
        if "error" in enhanced_result:
            st.error(f"Детали ошибки: {enhanced_result['error']}")
        return
    
    # Статистика YOLO детекции
    yolo_data = enhanced_result.get("yolo_detection")
    if yolo_data:
        st.subheader("📊 Статистика детекции полей")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего полей", yolo_data["field_count"])
        
        with col2:
            summary = yolo_data.get("summary", {})
            st.metric("Высокая уверенность", summary.get("high_confidence_fields", 0))
        
        with col3:
            avg_conf = summary.get("average_confidence", 0)
            st.metric("Средняя уверенность", f"{avg_conf:.2f}")
        
        with col4:
            detected_types = len(summary.get("detected_types", []))
            st.metric("Типов полей", detected_types)
        
        # Детали по полям
        if yolo_data["fields"]:
            st.subheader("🔍 Обнаруженные поля")
            
            # Создаем таблицу полей
            fields_data = []
            for field in yolo_data["fields"]:
                fields_data.append({
                    "Тип поля": field["field_name"],
                    "Уверенность": f"{field['confidence']:.3f}",
                    "Координаты": f"({field['bbox']['x1']:.0f}, {field['bbox']['y1']:.0f}) - ({field['bbox']['x2']:.0f}, {field['bbox']['y2']:.0f})",
                    "Размер": f"{field['bbox']['width']:.0f} × {field['bbox']['height']:.0f}"
                })
            
            import pandas as pd
            df = pd.DataFrame(fields_data)
            st.dataframe(df, use_container_width=True)
    
    # Аннотированное изображение
    annotated_image = enhanced_result.get("annotated_image")
    if annotated_image and Path(annotated_image).exists():
        st.subheader("🖼️ Аннотированное изображение")
        st.image(annotated_image, caption="Обнаруженные поля", use_container_width=True)
    
    # Тексты полей
    field_texts = enhanced_result.get("field_texts", {})
    if field_texts:
        st.subheader("📝 Извлеченные тексты полей")
        
        # Создаем табы для разных полей
        tabs = st.tabs(list(field_texts.keys())[:6])  # Ограничиваем количество табов
        
        for i, (field_name, text) in enumerate(field_texts.items()):
            if i < len(tabs):
                with tabs[i]:
                    st.text_area(f"Текст поля {field_name}", text, height=100, disabled=True)
    
    # Полный текст документа
    full_text = enhanced_result.get("marker_text")
    if full_text:
        with st.expander("📄 Полный текст документа"):
            st.text_area("Marker OCR", full_text[:2000] + "..." if len(full_text) > 2000 else full_text, 
                        height=300, disabled=True)
    
    # Отладочная информация
    if debug_mode:
        with st.expander("🔧 Отладочная информация"):
            st.json(enhanced_result)
    
    # Экспорт результатов
    st.subheader("💾 Экспорт результатов")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # JSON экспорт
        json_str = json.dumps(enhanced_result, ensure_ascii=False, indent=2, default=str)
        st.download_button(
            label="📄 Скачать полные результаты (JSON)",
            data=json_str,
            file_name="yolo_marker_results.json",
            mime="application/json"
        )
    
    with col2:
        # Экспорт только текстов полей
        if field_texts:
            fields_json = json.dumps(field_texts, ensure_ascii=False, indent=2)
            st.download_button(
                label="📝 Скачать тексты полей (JSON)",
                data=fields_json,
                file_name="field_texts.json",
                mime="application/json"
            )
    
    with col3:
        # CSV экспорт полей
        if yolo_data and yolo_data["fields"]:
            csv_data = create_fields_csv_export(yolo_data["fields"], field_texts)
            st.download_button(
                label="📊 Скачать данные полей (CSV)",
                data=csv_data,
                file_name="detected_fields.csv",
                mime="text/csv"
            )


def create_fields_csv_export(fields: List[Dict], field_texts: Dict[str, str]) -> str:
    """Создание CSV экспорта для полей"""
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        "Тип поля", "Название", "Уверенность", "X1", "Y1", "X2", "Y2", 
        "Ширина", "Высота", "Извлеченный текст"
    ])
    
    # Данные полей
    for field in fields:
        bbox = field["bbox"]
        field_type = field["field_type"]
        
        # Ищем соответствующий текст
        extracted_text = ""
        for text_key, text_value in field_texts.items():
            if field_type in text_key:
                extracted_text = text_value
                break
        
        writer.writerow([
            field_type,
            field["field_name"],
            f"{field['confidence']:.3f}",
            f"{bbox['x1']:.0f}",
            f"{bbox['y1']:.0f}",
            f"{bbox['x2']:.0f}",
            f"{bbox['y2']:.0f}",
            f"{bbox['width']:.0f}",
            f"{bbox['height']:.0f}",
            extracted_text
        ])
    
    return output.getvalue()


if __name__ == "__main__":
    main()
