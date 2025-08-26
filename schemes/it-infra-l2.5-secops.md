@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
LAYOUT_WITH_LEGEND()
title C4 L2.5 — Эксплуатация и безопасность (simplified)

Person(sre, "SRE/Мониторинг", "Поддержка SLO/SLA")
Person(soc, "SOC/IB", "Инциденты/расследования")

System_Boundary(ops, "Boundary: Ops/Sec") {
  Container(prom, "Monitoring", "Prometheus", "Метрики/алерты")
  Container(logs, "Log Pipeline", "Vector/Fluentd", "Сбор/нормализация")
  Container(siem, "SIEM/SOC", "SIEM", "Корреляция/UEBA")
  Container(soar, "SOAR/IR", "SOAR", "Авто-реакции")
  Container(vault, "Vault/PKI", "Secrets", "Секреты/сертификаты")
  Container(backup, "Backup/Archive", "Snapshots", "Иммутабельные копии")
  Container(edr, "EDR/XDR", "Agent/Cloud", "Хостовая защита")
}

System(it, "ИТ Core", "ERP/CMMS/Почта/ESB", "")
System(da, "Data/AI", "Kafka/Lake/Models", "")
System(ot, "OT/IDMZ", "SCADA/Видео/СКУД", "")

Rel(logs, siem, "Логи/события")
Rel(siem, soar, "Инциденты → плейбуки")
Rel(soar, it, "Аккаунты/блокировки")
Rel(soar, da, "Карантин топиков/пайплайнов")
Rel(soar, ot, "Оповещения/блокировки")
Rel(vault, it, "Секреты/сертификаты")
Rel(vault, da, "Секреты/ключи моделей/доступ к Lake")
Rel(backup, it, "Бэкапы приложений/БД")
Rel(backup, da, "Снапшоты Lake/DWH/регистры")
Rel(edr, siem, "Телееметрия/алерты")
Rel(it, logs, "App/sys логи")
Rel(da, logs, "Пайплайны/модели/инференс логи")
Rel(ot, logs, "Прокси логи/шлюзы/СКУД")
Rel(da, prom, "Экспортеры моделей/пайплайнов")
Rel(it, prom, "Экспортеры сервисов")
Rel(ot, prom, "Экспортеры шлюзов/каналов")

@enduml
