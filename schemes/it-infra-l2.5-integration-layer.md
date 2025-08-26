@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
LAYOUT_WITH_LEGEND()
title C4 L2.5 — Интеграция и внешние каналы (simplified)

Person(partner, "Внешний партнёр", "ЛК, EDI, файлы")
System(apigw, "API Gateway/WAF (из IT Core)", "Reverse proxy", "Паблишинг внутренних API")

System_Boundary(ext_integ, "Boundary: Интеграция и внешние каналы") {
  Container(b2b, "B2B/EDI шлюз", "AS2/EDIFACT", "Трансляции/валидации")
  Container(sftp, "File Gateway", "SFTP/FTPS", "Приём/выдача, AV/PGP")
  Container(ext_portal, "Портал/API", "Web/API", "ЛК/партнёрские API")
  Container(vpn, "VPN/MPLS/SD-WAN", "Net", "Защищённые каналы")
  Container(policy, "Политики и аудит", "Rate/Registry/Audit", "Квоты/ограничения/логи")
}

System(esb, "ESB/Service Bus (IT Core)", "Orchestration", "")
System(analytics, "Платформа данных/AI", "Lake/Stream", "Ингест событий")
System(ops, "Эксплуатация и безопасность", "NMS/SIEM/SOAR", "")

Rel(partner, ext_portal, "ЛК, загрузка/скачивание")
Rel(partner, b2b, "EDI сообщения")
Rel(partner, sftp, "Файлы (батчи)")
Rel(partner, vpn, "Защищённый канал")

Rel(ext_portal, apigw, "Вызов внутренних API")
Rel(b2b, esb, "EDI сообщения/события")
Rel(sftp, analytics, "Landing → RAW")
Rel(policy, apigw, "Rate-limit/токены")
Rel(policy, b2b, "Профили/сертификаты")
Rel(policy, ops, "Аудит → SIEM")
Rel(vpn, ops, "Статусы туннелей")

@enduml
