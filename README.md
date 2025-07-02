# 🐾 Hundesystem – Home Assistant Integration

Das **Hundesystem** für Home Assistant bietet eine intelligente Verwaltung für Gassi, Fütterung, Geschäft, Besuchshunde und mehr – 100 % UI-basiert, YAML-frei und optimal für Mehrhundehaushalte.

---

## 🚀 Features

- 🐶 Tages- und Wochenstatistiken für Gassi, Fütterung, Geschäft
- 🧠 Automatisches Setup aller Helper und Sensoren
- 📲 Push-Benachrichtigungen mit Rückfragen und Aktionen (Android/iOS)
- 🧑‍💼 Besuchshund-Modus mit visueller Unterscheidung im Dashboard
- 🗂️ Mushroom-Dashboard für jeden Hund – optimiert für Mobilgeräte
- 📅 Automatisierungen per Service generierbar (z. B. „Kein Gassi bis 18 Uhr“)
- ⏱️ Timeline & letzte Aktivität pro Hund

---

## 🔧 Einrichtung

### 1. Installation über HACS

1. Füge das Repository in HACS als benutzerdefinierte Integration hinzu.
2. Installiere **Hundesystem**.
3. Starte Home Assistant neu.
4. Gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen → Hundesystem**.

### 2. Hund hinzufügen

- Gib den Namen deines Hundes ein (z. B. „Rex“).
- Optional: Aktiviere „Besuchshund-Modus“.
- Aktiviere „Dashboard automatisch erstellen“.

Das Setup erstellt automatisch:

- `input_datetime`, `input_text`, `counter`, `sensor`, `utility_meter`
- Mushroom-Dashboard mit Titel, Buttons, Status
- Besuchsmodus-Elemente (optisch hervorgehoben)

---

## 🐾 Beispiel-Services

```yaml
# Logge eine Aktivität
service: hundesystem.log_activity
data:
  dog_name: Rex
  activity_type: walk
```

```yaml
# Versende eine Rückfrage
service: hundesystem.send_notification
data:
  dog_name: Bella
  message: War Bella draußen?
```

```yaml
# Setup für Statistik-Sensoren
service: hundesystem.generate_stat_sensors
data:
  dog_name: Rex
```

```yaml
# Automatisierungen generieren
service: hundesystem.generate_automations
data:
  dog_name: Rex
  notify_target: mobile_app_deinename
```

---

## 🧩 Dashboard

Die Integration erstellt automatisch ein Dashboard mit:

- 📊 Tagesstatistiken
- 🧠 Letzter Aktivitätsstatus
- 🔘 Buttons für Aktionen (Füttern, Rückmelden)
- 🧑‍💼 Besuchshunde farblich hervorgehoben

Optional: Integration der Timeline-Karte (logbook-card empfohlen).

---

## 📎 Beispiel-Timeline-Karte (optional)

```yaml
type: custom:logbook-card
title: Aktivitäten – Rex
entities:
  - input_text.last_activity_rex
  - sensor.walks_today_rex
  - counter.walk_rex
hours_to_show: 24
```

---

## 🛠️ Erweiterung

- Unterstützt mehrere Hunde gleichzeitig
- Unterstützt Mushroom UI + mobile Nutzung
- Erweiterbar über Services, Dashboard oder Automatisierungen

---

## 🤝 Mithelfen & Feedback

Dieses Projekt ist offen für Feedback und Erweiterung.  
Pull Requests & Issues jederzeit willkommen!

---
