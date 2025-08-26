@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
LAYOUT_WITH_LEGEND()
title C4 L2.5 — IT Core (simplified)

Person(analyst, "Аналитик", "BI/дашборды")
Person(emp, "Сотрудник офиса", "ERP, почта, документы")
Person(admin, "Администратор", "Управление ИТ-сервисами")

System_Boundary(it_core, "IT Core Boundary") {
  Container(erp1c, "1С ERP", "App", "Учет/закупки/склады")
  Container(cmms, "CMMS/ТОиР", "Web/API", "Work Orders/ремонты")
  Container(mail, "Почта", "SMTP/IMAP", "Корпоративная почта")
  Container(dms, "DMS/ECM", "ECM", "Договоры/файлы")
  Container(apps, "Опер. сервисы", "Web/API", "Тикеты/реестры")
  Container(db_apps, "RDBMS", "DB", "Транзакции")
  Container(esb, "ESB/iPaaS", "ESB", "Оркестрация/трансформация")
  Container(apigw, "API GW/WAF", "Proxy", "Публикация/защита L7")
  Container(iam, "IAM/AD/LDAP", "SSO", "Аутентификация/авторизация")
}

' внешние ключевые интеграции
System(analytics, "Платформа данных/AI", "Lake/DWH/AI", "Фичестор, модели, BI")
System(ops, "Эксплуатация и безопасность", "NMS/SIEM", "Мониторинг, корреляция")
System(ext_integ, "Интеграция/внешние каналы", "B2B/SFTP/VPN/Порталы", "")
System(ot, "Industrial DMZ (OT)", "SCADA/СКУД/Видео", "Телеметрия, доступ")

' связи внутри и наружу
Rel(emp, erp1c, "Бизнес-операции")
Rel(emp, mail, "Коммуникации")
Rel(analyst, analytics, "Отчёты/дашборды")
Rel(admin, ops, "Мониторинг/алерты")

Rel(erp1c, db_apps, "Транзакции")
Rel(apps, db_apps, "Чтение/запись")
Rel(cmms, db_apps, "Чтение/запись")
Rel(esb, apigw, "Публикация внутренних API")
Rel(iam, erp1c, "SSO/LDAP")
Rel(iam, apps, "SSO/LDAP")
Rel(iam, cmms, "SSO/LDAP")
Rel(esb, ext_integ, "Интеграции во внешние каналы")

' мосты в AI/эксплуатацию
Rel(erp1c, analytics, "DWH/CDC/витрины")
Rel(cmms, analytics, "История ремонтов/наработки")
Rel(mail, analytics, "Копии/метаданные писем → AI-почта")
Rel(it_core, ops, "Логи/алерты/аудит")
Rel(ot, analytics, "Производственные данные → Lake/Stream")

@enduml
