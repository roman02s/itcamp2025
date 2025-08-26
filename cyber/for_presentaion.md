flowchart LR
  %% ---------- Blue & White palette ----------
  classDef kas fill:#DBEAFE,stroke:#60A5FA,color:#0F172A,stroke-width:1.5px;
  classDef ch  fill:#EFF6FF,stroke:#3B82F6,color:#0F172A,stroke-width:1.5px;
  classDef obs fill:#EEF2FF,stroke:#1D4ED8,color:#0F172A,stroke-width:1.5px;
  classDef core fill:#FFFFFF,stroke:#60A5FA,color:#0F172A,stroke-width:1.5px;
  classDef ext fill:#FFFFFF,stroke:#93C5FD,color:#0F172A,stroke-width:1.5px;

  %% ---------- Actors / External ----------
  users["Рабочие станции и серверы"]:::ext
  admin["Команда безопасности"]:::ext
  internet["Интернет"]:::ext

  %% ---------- Core services ----------
  subgraph coreZone["Критичные сервисы"]
    bus["Бизнес-сервисы и API"]:::core
    mail["Почтовый сервер"]:::core
    data["Данные и резервные копии"]:::core
  end
  style coreZone fill:#FFFFFF,stroke:#60A5FA,stroke-width:1.5px

  %% ---------- Kaspersky ----------
  subgraph kasZone["Kaspersky"]
    kes["Антивирус на рабочих местах"]:::kas
    edr["Обнаружение и реагирование"]:::kas
    ksm["Защита почты"]:::kas
    kwts["Веб-шлюз"]:::kas
  end
  style kasZone fill:#DBEAFE,stroke:#60A5FA,color:#0F172A,stroke-width:1.5px

  %% ---------- Channels & Encryption ----------
  subgraph chZone["Каналы и шифрование"]
    vpn["Защищённые каналы связи"]:::ch
    tls["Сертификаты и ротация ключей"]:::ch
    enc["Шифрование по умолчанию"]:::ch
  end
  style chZone fill:#EFF6FF,stroke:#3B82F6,stroke-width:1.5px

  %% ---------- Monitoring & Access ----------
  subgraph obsZone["Мониторинг и доступ"]
    siem["Центр мониторинга"]:::obs
    iam["Управление доступом"]:::obs
  end
  style obsZone fill:#EEF2FF,stroke:#1D4ED8,stroke-width:1.5px

  %% ---------- Policies & Drills ----------
  subgraph policyZone["Процессы безопасности"]
    policies["Политики безопасности"]:::core
    drills["Киберучения и обучение"]:::core
  end
  style policyZone fill:#FFFFFF,stroke:#60A5FA,stroke-width:1.5px

  %% ---------- Relations ----------
  users --> kes
  kes --> edr

  internet <--> kwts
  kwts --> bus

  internet <--> ksm
  ksm --> mail

  bus --> tls
  data --> enc
  vpn --- internet

  edr --> siem
  kwts --> siem
  ksm --> siem
  iam --> siem
  siem --> admin

  policies --> iam
  policies --> kes
  drills --> siem
  drills --> admin
