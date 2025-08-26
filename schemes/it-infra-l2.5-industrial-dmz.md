@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
LAYOUT_WITH_LEGEND()
title C4 L2.5 — Industrial DMZ (simplified)

Person(ops, "Операторы", "SCADA/HMI, дежурные")
System(it, "IT/Data/AI", "Kafka/Lake/AI", "Потребители OT-данных")

System_Boundary(ot, "Boundary: OT/IDMZ") {
  Boundary(src, "OT источники") {
    Container(scada, "SCADA/DCS", "HMI/Servers", "Управление/телеметрия")
    Container(plc, "PLC/RTU/SIS", "Контроллеры", "Полевые сигналы/интерлоки")
    Container(vms, "VMS/Камеры", "RTSP/ONVIF", "Видеопотоки")
    Container(acs, "СКУД/Периметр", "Controllers/Readers", "Проходы/события")
    Container(gas, "Газоанализ/Пожарка", "Sensors", "События ПБ")
  }
  Container(hist, "Process Historian", "TimeSeries DB", "Исторические ряды")
  Container(gw, "OT/DMZ Gateway", "OPC-UA/MQTT", "Агрегация/нормализация")
  Container(dmz_buf, "DMZ Buffer/Proxy", "Broker/Cache", "Буферизация/шиппинг")
  Container(otfw, "OT FW/Diode", "FW/Diode", "Фильтрация/односторонне")
}

Rel(ops, scada, "Мониторинг/управление")
Rel(plc, scada, "Телеметрия/алярмы")
Rel(scada, hist, "Архивация")
Rel(scada, gw, "OPC-UA/телеметрия")
Rel(src, dmz_buf, "Видео/СКУД/ПБ события")
Rel(gw, dmz_buf, "MQTT/AMQP телеметрия")

' безопасная передача в IT
Rel(otfw, dmz_buf, "Фильтрация/белые списки")
Rel(dmz_buf, it, "→ Kafka/Видео-ингест (односторонне)")

@enduml
