@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml
LAYOUT_WITH_LEGEND()
title НПЗ — C4 Level 1 (System Context)

' ==== Акторы ====
Person(emp, "Сотрудник офиса", "ERP, почта, документы")
Person(analyst, "Аналитик/Руководитель", "BI/дашборды")
Person(admin, "Администратор", "Мониторинг/безопасность")
Person(ext_partner, "Внешний партнёр", "B2B/API/порталы")

' ==== Главная система ====
System_Boundary(enterprise, "ИТ-система НПЗ") {
  System(npz_core, "Платформа приложений и данных НПЗ", "ERP/DMS/ESB/API, Data Platform (Lake/DWH/BI), AI/ML, SIEM/NMS")
}

' ==== Внешние системы/среды ====
System_Ext(otdmz, "Industrial DMZ (OT)", "SCADA/DCS/IIoT/СКУД/видео", "Телеметрия, видео, логи доступа")
System_Ext(partners, "Внешние порталы/каналы", "B2B/EDI, API, SFTP", "Документооборот и интеграции")
System_Ext(extdc, "Внешний ЦОД / DR", "S3-объектное хранилище, DWH-DR", "Реплика/аварийное восстановление")
System_Ext(internet, "Публичные/почтовые сервисы", "SMTP/IMAP, угрозы", "Внешняя почта, фишинг/вложения")

' ==== Связи (крупноблочно) ====
Rel(emp, npz_core, "Операционная работа")
Rel(analyst, npz_core, "Просмотр отчётов/аналитики")
Rel(admin, npz_core, "Администрирование, реагирование")
Rel(ext_partner, partners, "ЛК/API/EDI")

Rel(otdmz, npz_core, "Стрим телеметрии/видео/логи СКУД")
Rel(partners, npz_core, "Документы и файлы (B2B/SFTP/API)")
Rel(npz_core, extdc, "Реплика Lake/DWH/метаданных (DR)")
Rel(internet, npz_core, "Почтовый трафик/вложения → анализ угроз")

@enduml
