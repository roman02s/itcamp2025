@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
LAYOUT_WITH_LEGEND()
title НПЗ — C4 Level 2 (Containers)

' ==== Акторы ====
Person(emp, "Сотрудник офиса", "1С, почта, документы")
Person(analyst, "Аналитик/Руководитель", "BI/дашборды")
Person(admin, "Администратор", "NMS/SIEM/SOC")
Person(ext_partner, "Внешний партнёр", "B2B/API/порталы")

' ==== Внешняя производственная среда ====
System(otdmz, "Industrial DMZ (OT)", "Источники телеметрии/видео/СКУД")

' ==== Корпоративный прикладной контур ====
System_Boundary(it_core, "Корпоративный прикладной контур") {
  Container(erp1c, "1С ERP", "Прикладная система", "Учет/логистика/финансы")
  Container(mail, "Почтовый сервер", "SMTP/IMAP/POP3", "Корпоративная почта")
  Container(dms, "Документооборот", "Р7/ECM/DMS", "Файлы/договоры/заявки")
  Container(apps, "Бизнес-сервисы/CMMS", "Web/API", "Операционные приложения, заявки ТО")
  Container(db_apps, "БД приложений", "RDBMS", "Транзакционные данные")
  Container(esb, "ESB/Service Bus", "Шина", "Оркестрация/трансформация")
  Container(apigw, "API Gateway / WAF", "Reverse proxy", "Публикация API, защита L7")
  Container(iam, "IAM/AD/LDAP", "Каталог/SSO", "Аутентификация/авторизация")
}

' ==== Интеграция и внешние каналы ====
System_Boundary(ext_integ, "Интеграция и внешние каналы") {
  Container(b2b, "B2B/EDI шлюз", "AS2/EDIFACT", "Обмен с контрагентами")
  Container(sftp, "SFTP/FTPS шлюз", "Файловый обмен", "Импорт/экспорт")
  Container(vpn, "VPN/MPLS/SD-WAN", "Каналы", "Защищённые соединения")
  Container(ext_portal, "Внешние порталы/API", "Web/API", "ЛК поставщиков/клиентов")
}

' ==== Сбор, обработка данных и аналитика ====
System_Boundary(analytics, "Сбор/обработка/аналитика и AI/ML") {
  Container(kafka, "Message Bus", "Kafka/MQTT/AMQP", "Стриминг телеметрии/событий")
  Container(cdc, "CDC/Replication Ingest", "Debezium/Log-ship", "Захват изменений из БД")
  Container(stream, "Stream Processing", "Flink/Spark Streaming", "Онлайн-обработка")
  Container(etl, "Batch ETL / Оркестрация", "Airflow/DBT", "Пакетные пайплайны")
  Container(datalake, "Data Lake (RAW)", "Объектное хранилище", "Сырая/архивная зона")
  Container(dwh, "Локальное DWH", "Колонночное хранилище", "Модель предприятия")
  Container(marts, "Витрины данных", "Star/Snowflake", "Оптимизированные схемы")
  Container(bi, "BI/Дашборды", "Power BI/Tableau/Grafana", "Отчёты и визуализация")

  ' ==== AI/ML сервисы (добавленные сценарии) ====
  Container(video_ingest, "Видео-ингест/шлюз", "RTSP/ONVIF → Kafka", "Кадры/метаданные")
  Container(ai_anom_load, "AI: Аномалии налива", "Flink/Python/ONNX", "Аналитика эстакад/резервуаров, алерты")
  Container(ai_cv, "AI: Компьютерное зрение (терминал)", "CV Inference", "PPE/периметр/процедуры")
  Container(ai_access, "AI: Физический доступ", "FaceID/PPE", "FaceID, детекция отсутствия шлема, корреляция со СКУД")
  Container(ai_email, "AI: Кибербезопасность почты", "NLP/AV Sandbox", "Фишинг/малварь/вложения")
  Container(ai_pm, "AI: Предиктивное обслуживание", "Time-Series/Vibration ML", "RUL/рекомендации ТО")
}

' ==== Внешний ЦОД / DR ====
System_Boundary(ext_dc, "Внешний ЦОД / DR") {
  Container(ext_obj, "Объектное хранилище (реплика)", "S3-совместимое", "RAW/архивы")
  Container(ext_dwh, "DWH-DR (реплика)", "Колонночное", "Горячий/тёплый резерв")
  Container(ext_bi, "BI Gateway (RO)", "Read-only", "Отчёты при DR")
  Container(rep_mgr, "DR Replication Manager", "MirrorMaker/Snapshots", "Репликация Lake/DWH/метаданных")
}

' ==== Эксплуатация и безопасность ====
System_Boundary(ops, "Эксплуатация и безопасность") {
  Container(nms, "Monitoring/NMS", "Prometheus/Zabbix", "Метрики/алерты/трейсинг")
  Container(siem, "SIEM/SOC", "Корреляция событий", "Логи/инциденты/расследования")
  Container(backup, "Backup/Archive", "VTL/Snapshots", "Резервные копии/архив")
}

' ==== Взаимосвязи (ключевое) ====

' Акторы
Rel(emp, erp1c, "Операционная работа")
Rel(emp, mail, "Коммуникации")
Rel(analyst, bi, "Просмотр отчётов")
Rel(admin, nms, "Мониторинг")
Rel(admin, siem, "Инциденты/расследования")
Rel(ext_partner, ext_portal, "ЛК/API")
Rel(ext_partner, b2b, "EDI")
Rel(ext_partner, sftp, "Файловый обмен")

' Прикладной контур
Rel(erp1c, db_apps, "Транзакции")
Rel(apps, db_apps, "Чтение/запись")
Rel(erp1c, esb, "Интеграции")
Rel(apps, esb, "Оркестрация")
Rel(esb, apigw, "Публикация внутренних API")
Rel(iam, erp1c, "SSO/LDAP")
Rel(iam, apps, "SSO/LDAP")
Rel(iam, bi, "SSO/LDAP")
Rel(apigw, ext_portal, "Доступ внешним потребителям")

' Потоки данных/аналитика
Rel(otdmz, kafka, "Телеметрия/журналы")
Rel(otdmz, sftp, "Пакеты данных")
Rel(otdmz, video_ingest, "RTSP/ONVIF видеопотоки")
Rel(sftp, datalake, "Загрузка RAW")
Rel(esb, kafka, "События приложений")
Rel(db_apps, cdc, "CDC изменений")
Rel(cdc, kafka, "Публикация изменений")
Rel(kafka, stream, "Стрим-обработка")
Rel(stream, datalake, "ENRICHED/RAW")
Rel(etl, datalake, "Чтение RAW")
Rel(etl, dwh, "Модель данных")
Rel(dwh, marts, "Витрины")
Rel(marts, bi, "Отчёты/дашборды")

' AI/ML — видео/доступ
Rel(video_ingest, kafka, "Кадры/метаданные (topics)")
Rel(kafka, ai_cv, "Видео-метаданные/кадры")
Rel(kafka, ai_access, "Видео-метаданные/кадры")
Rel(otdmz, ai_access, "Логи СКУД/проходов")
Rel(ai_access, iam, "Сверка идентичности/прав")
Rel(ai_cv, nms, "Алерты PPE/периметр")
Rel(ai_cv, siem, "Инциденты безопасности")
Rel(ai_cv, bi, "KPI соблюдения процедур")
Rel(video_ingest, datalake, "Архив видео/меток")

' AI/ML — аномалии налива
Rel(kafka, ai_anom_load, "Телеметрия эстакад/резервуаров")
Rel(ai_anom_load, nms, "Алерты аномалий налива")
Rel(ai_anom_load, siem, "События безопасности процесса")
Rel(ai_anom_load, bi, "KPI/отчёты по отклонениям")
Rel(ai_anom_load, datalake, "Метки/события")

' AI/ML — кибербезопасность почты
Rel(mail, ai_email, "Письма/журналы/вложения (копии)")
Rel(ai_email, siem, "Фишинг/малварь — инциденты")
Rel(ai_email, mail, "Карантин/метки/DMARC")

' AI/ML — предиктивное обслуживание
Rel(kafka, ai_pm, "Вибрация/температура/давления (стрим)")
Rel(datalake, ai_pm, "История, ремонты, контекст")
Rel(ai_pm, nms, "Предиктивные алерты/RUL")
Rel(ai_pm, bi, "Дашборды надёжности/прогнозы")
Rel(ai_pm, erp1c, "Заявки ТО/заказ ЗИП")
Rel(ai_pm, apps, "CMMS/Work Orders")

' DR/резерв
Rel(datalake, rep_mgr, "Снимки/версии")
Rel(dwh, rep_mgr, "Реплика таблиц")
Rel(rep_mgr, ext_obj, "Реплика Lake/архив")
Rel(rep_mgr, ext_dwh, "Реплика DWH")
Rel(ext_dwh, ext_bi, "RO-отчёты при DR")

' Эксплуатация/безопасность
Rel(apigw, siem, "Логи доступа/WAF")
Rel(esb, siem, "Интеграционные логи")
Rel(kafka, siem, "Аудит событий")
Rel(mail, siem, "Почтовые логи")
Rel(nms, siem, "Корреляция событий")
Rel(db_apps, backup, "Резервные копии")
Rel(dwh, backup, "Бэкапы")
Rel(datalake, backup, "Архивы/снапшоты")

@enduml
