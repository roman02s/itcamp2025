@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
LAYOUT_WITH_LEGEND()
title C4 L2.5 — Data & AI/ML Platform (simplified)

Person(analyst, "Аналитик/Бизнес", "BI/дашборды")
Person(ml, "ML/DS", "Эксперименты/обучение")
System(itcore, "IT Core", "ERP/CMMS/Почта", "Операционные данные")
System(ot, "OT/IDMZ", "SCADA/СКУД/Видео", "Телеметрия/события")

System_Boundary(ai, "Boundary: Data & AI Platform") {
  Container(kafka, "Streaming Ingest", "Kafka/MQTT", "Онлайн-события")
  Container(stream, "Stream Processing", "Flink/Spark", "Обработка/агрегации")
  Container(etl, "Batch Orchestration", "Airflow/DBT", "Пакетные пайплайны")
  Container(lake_raw, "Data Lake RAW", "Object Store", "Сырые данные")
  Container(lake_cur, "Lake CURATED", "Object Store", "Очищенные наборы")
  Container(dwh, "DWH/Витрины", "Columnar", "Модель предприятия")
  Container(fs, "Feature Store", "Online/Offline", "Признаки для моделей")
  Container(reg, "Model Registry", "Registry", "Версии/артефакты")
  Container(train, "Training/Tracking", "Notebooks/Train", "Эксперименты/обучение")
  Container(serve, "Model Serving", "REST/gRPC/Batch", "Инференс/скоры")
  Container(bi, "BI/Analytics", "BI", "Отчёты/дашборды")
  Container(mon, "Monitoring", "Metrics/Drift", "Метрики/дрифт/логи")
}

Rel(ot, kafka, "События/телеметрия")
Rel(itcore, etl, "CDC/батч-выгрузки")
Rel(kafka, stream, "Топики")
Rel(stream, lake_raw, "ENRICHED/RAW")
Rel(etl, lake_cur, "Трансформации")
Rel(lake_cur, dwh, "Модель/витрины")
Rel(dwh, bi, "Отчёты")
Rel(lake_cur, fs, "Offline признаки")
Rel(stream, fs, "Online признаки")
Rel(train, reg, "Регистр моделей")
Rel(reg, serve, "Деплой модели")
Rel(serve, mon, "Метрики/качество")
Rel(stream, mon, "Latency/SLI")
Rel(etl, mon, "Джобы/SLA")
Rel(ml, train, "Эксперименты")
Rel(analyst, bi, "Просмотр/анализ")

@enduml
