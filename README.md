# 🐶 Hundesystem - Umfassendes Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Bigdaddy1990/hundesystem)](https://github.com/Bigdaddy1990/hundesystem/releases)
[![GitHub](https://img.shields.io/github/license/Bigdaddy1990/hundesystem)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/Bigdaddy1990/hundesystem)](https://github.com/Bigdaddy1990/hundesystem/issues)
[![GitHub stars](https://img.shields.io/github/stars/Bigdaddy1990/hundesystem)](https://github.com/Bigdaddy1990/hundesystem/stargazers)
[![Buy me a coffee](https://img.shields.io/static/v1.svg?label=%20&message=Buy%20me%20a%20coffee&color=6f4e37&logo=buy%20me%20a%20coffee&logoColor=white)](https://ko-fi.com/bigdaddy1990)

**Das ultimative Smart Home System für Hundebesitzer** - Eine vollständige Home Assistant Integration zur intelligenten Verwaltung und Überwachung von Hundeaktivitäten, Gesundheit, Fütterung und täglichen Routinen.

## 🌟 Highlights

- **🧠 Intelligente Automationen** - Automatische Erinnerungen, Türsensor-Integration und KI-basierte Empfehlungen
- **📱 Mobile-First Design** - Optimiert für Smartphone-Nutzung mit ansprechenden Dashboards
- **🔔 Smart Notifications** - Personenbasierte Benachrichtigungen mit interaktiven Aktionen
- **📊 Umfassende Statistiken** - Detaillierte Analysen und Gesundheitstrends
- **🐕‍🦺 Multi-Hund Support** - Verwaltung mehrerer Hunde mit individuellen Profilen
- **🏥 Gesundheitsmonitoring** - Tierarzttermine, Medikamente und Gesundheitsbewertungen
- **🌦️ Wetter-Integration** - Wetterbasierte Empfehlungen für Aktivitäten
- **🚨 Notfall-System** - Sofortige Benachrichtigungen und Kontakte

---

## 🎯 Funktionsübersicht

### 🍽️ **Intelligentes Fütterungsmanagement**
- **Automatische Erinnerungen** für alle Mahlzeiten (Frühstück, Mittag, Abend, Leckerli)
- **Flexible Fütterungszeiten** mit benutzerdefinierten Zeitplänen
- **Überfütterungs-Schutz** mit Warnungen bei zu häufiger Fütterung
- **Fütterungsstatistiken** mit täglichen, wöchentlichen und monatlichen Trends
- **Interaktive Rückfragen** - "Wurde Rex schon gefüttert?"

### 🚶 **Umfassendes Aktivitäts-Tracking**
- **Türsensor-Integration** für automatische Erkennung von Gartengängen
- **Aktivitätsprotokollierung** - Gassi, Spielen, Training, Geschäfte
- **Inaktivitätswarnungen** bei zu wenig Bewegung
- **GPS-Ready** für zukünftige Standort-Features
- **Dauer-Tracking** für alle Aktivitäten

### ❤️ **Erweiterte Gesundheitsüberwachung**
- **Gesundheits-Score** mit automatischer Berechnung
- **Medikamenten-Management** mit Erinnerungen und Dosierung
- **Tierarzttermine** mit automatischen Erinnerungen
- **Gewichts-Tracking** und BMI-Berechnung
- **Symptom-Protokollierung** mit Trend-Analyse
- **Impfungs-Kalender** mit Auffrischungs-Erinnerungen

### 🏠 **Besuchsmodus & Betreuung**
- **Hundesitter-Modus** mit reduzierten Benachrichtigungen
- **Besucherinformationen** mit Kontaktdaten und Anweisungen
- **Temporäre Einstellungen** die sich automatisch zurücksetzen
- **Gäste-Dashboard** mit vereinfachter Bedienung

### 🚨 **Notfall-System**
- **Ein-Klick-Notfall** Button für sofortige Hilfe
- **Automatische Kontaktierung** aller eingetragenen Notfallkontakte
- **GPS-Standort** in Notfallbenachrichtigungen
- **Tierarzt-Integration** für medizinische Notfälle
- **Notfall-Historie** für bessere Vorbereitung

### 🌦️ **Wetter-Integration**
- **Wetterbasierte Empfehlungen** für Spaziergänge
- **Temperatur-Warnungen** (zu heiß/kalt für den Hund)
- **Regen-Alerts** mit Alternativvorschlägen
- **Saisonale Anpassungen** der Aktivitäts-Empfehlungen

---

## 📦 Installation

### Über HACS (Empfohlen)

1. **HACS öffnen** in Home Assistant
2. **Integrationen** → Menü (⋮) → **Benutzerdefinierte Repositories**
3. **Repository hinzufügen**: `https://github.com/Bigdaddy1990/hundesystem`
4. **Kategorie**: Integration
5. **"Hundesystem"** installieren
6. **Home Assistant neustarten**

### Manuelle Installation

```bash
# In Ihr Home Assistant config Verzeichnis
cd /config
git clone https://github.com/Bigdaddy1990/hundesystem.git
cp -r hundesystem/custom_components/hundesystem custom_components/
# Restart Home Assistant
```

---

## ⚙️ Einrichtung

### 🔧 **Grundkonfiguration**

1. **Integration hinzufügen**: Einstellungen → Geräte & Dienste → Integration hinzufügen
2. **"Hundesystem"** suchen und auswählen
3. **Setup-Wizard** durchlaufen:

#### Schritt 1: Grunddaten
- **Hundename**: Eindeutiger Name (z.B. "rex", "bella")
- **Push-Geräte**: Mobile Apps für Benachrichtigungen
- **Personen-Tracking**: Automatische Erkennung anwesender Personen
- **Dashboard**: Automatische Erstellung eines Mushroom-Dashboards

#### Schritt 2: Erweiterte Einstellungen
- **Türsensor**: Automatische Erkennung von Türbewegungen
- **Reset-Zeit**: Täglicher Reset der Statistiken (Standard: 23:59)
- **Gesundheitsmonitoring**: Erweiterte Gesundheitsfeatures
- **Wetter-Integration**: Wetterbasierte Empfehlungen
- **Notfall-Features**: Notfallkontakte und -funktionen

#### Schritt 3: Fütterungsplan
- **Frühstück**: 07:00 (anpassbar)
- **Mittagessen**: 12:00 (anpassbar)
- **Abendessen**: 18:00 (anpassbar)
- **Leckerli**: 15:00 (anpassbar)
- **Automatische Erinnerungen**: Ein/Aus

#### Schritt 4: Notfallkontakte
- **Tierarzt**: Name, Telefon, Adresse
- **Notfallkontakt**: Name und Telefon
- **Ersatzkontakt**: Backup-Person
- **Hundeinfos**: Mikrochip, Versicherung

---

## 🎛️ **Entitäten Übersicht**

Nach der Installation werden automatisch **60+ Entitäten** erstellt:

### 📊 **Sensoren**
```yaml
sensor.rex_status                    # Gesamtstatus
sensor.rex_feeding_status           # Fütterungsstatus  
sensor.rex_activity                 # Aktivitätsstatus
sensor.rex_daily_summary            # Tageszusammenfassung
sensor.rex_health_score             # Gesundheits-Score
sensor.rex_mood                     # Stimmung
sensor.rex_weekly_summary           # Wochenstatistik
```

### 🔘 **Binary Sensoren**
```yaml
binary_sensor.rex_feeding_complete       # Alle Mahlzeiten
binary_sensor.rex_daily_tasks_complete   # Tagesaufgaben
binary_sensor.rex_needs_attention        # Aufmerksamkeit nötig
binary_sensor.rex_health_status          # Gesundheitsprobleme
binary_sensor.rex_emergency_status       # Notfallstatus
binary_sensor.rex_medication_due         # Medikament fällig
binary_sensor.rex_vet_appointment_reminder # Tierarzttermin
```

### 🔴 **Buttons**
```yaml
button.rex_daily_reset              # Tagesreset
button.rex_feeding_reminder         # Fütterungserinnerung
button.rex_test_notification        # Test-Benachrichtigung
button.rex_emergency                # Notfall aktivieren
button.rex_quick_outside            # Schnell: Draußen
button.rex_morning_feeding          # Frühstück
button.rex_lunch_feeding            # Mittagessen
button.rex_evening_feeding          # Abendessen
```

### 🔢 **Helper Entitäten** (Automatisch erstellt)
```yaml
# Input Booleans
input_boolean.rex_feeding_morning    # Frühstück Status
input_boolean.rex_feeding_lunch      # Mittag Status
input_boolean.rex_feeding_evening    # Abend Status
input_boolean.rex_outside            # War draußen
input_boolean.rex_poop_done          # Geschäft gemacht
input_boolean.rex_visitor_mode_input # Besuchsmodus

# Counter
counter.rex_feeding_morning_count    # Frühstück Zähler
counter.rex_outside_count           # Draußen Zähler
counter.rex_poop_count              # Geschäft Zähler

# Input DateTime
input_datetime.rex_feeding_morning_time    # Frühstück Zeit
input_datetime.rex_last_outside           # Letzter Gartengang
input_datetime.rex_next_vet_appointment   # Nächster Tierarzt

# Input Numbers
input_number.rex_weight              # Gewicht
input_number.rex_health_score        # Gesundheits-Score
input_number.rex_temperature         # Körpertemperatur

# Input Select
input_select.rex_health_status       # Gesundheitsstatus
input_select.rex_mood               # Stimmung
input_select.rex_activity_level     # Aktivitätslevel

# Input Text
input_text.rex_notes                # Notizen
input_text.rex_health_notes         # Gesundheitsnotizen
input_text.rex_emergency_contact    # Notfallkontakt
```

---

## 🎮 **Services & Automationen**

### 🔧 **Verfügbare Services**

#### **hundesystem.trigger_feeding_reminder**
```yaml
service: hundesystem.trigger_feeding_reminder
data:
  meal_type: morning  # morning, lunch, evening, snack
  dog_name: rex      # optional
  message: "Zeit fürs Frühstück!" # optional
```

#### **hundesystem.log_activity**
```yaml
service: hundesystem.log_activity
data:
  activity_type: walk  # walk, outside, play, training, poop
  dog_name: rex
  duration: 30        # Minuten
  notes: "Schöner Spaziergang im Park"
```

#### **hundesystem.set_visitor_mode**
```yaml
service: hundesystem.set_visitor_mode
data:
  enabled: true
  visitor_name: "Maria Müller"
  dog_name: rex
```

#### **hundesystem.emergency_contact**
```yaml
service: hundesystem.emergency_contact
data:
  emergency_type: medical
  message: "Rex zeigt Anzeichen von Unwohlsein"
  location: "Zuhause"
  contact_vet: true
  dog_name: rex
```

### 🤖 **Automatisierungsbeispiele**

#### **Automatische Fütterungserinnerung**
```yaml
automation:
  - alias: "Rex - Frühstück Erinnerung"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: state
        entity_id: input_boolean.rex_feeding_morning
        state: "off"
      - condition: state
        entity_id: binary_sensor.rex_visitor_mode
        state: "off"
    action:
      - service: hundesystem.trigger_feeding_reminder
        data:
          meal_type: morning
          dog_name: rex
```

#### **Türsensor-basierte Aktivitätserkennung**
```yaml
automation:
  - alias: "Rex - Türsensor Draußen Erkennung"
    trigger:
      - platform: state
        entity_id: binary_sensor.garden_door
        from: "off"
        to: "on"
        for: "00:00:30"
    action:
      - delay: "00:00:10"
      - service: hundesystem.send_notification
        data:
          title: "🐶 War Rex draußen?"
          message: "Türsensor hat Bewegung erkannt"
          data:
            actions:
              - action: "REX_OUTSIDE_YES"
                title: "✅ Ja, war draußen"
              - action: "REX_OUTSIDE_NO" 
                title: "❌ Nein, nur Tür"
```

#### **Gesundheitsüberwachung**
```yaml
automation:
  - alias: "Rex - Gesundheit Aufmerksamkeit"
    trigger:
      - platform: state
        entity_id: binary_sensor.rex_needs_attention
        to: "on"
        for: "00:30:00"
    condition:
      - condition: template
        value_template: "{{ 'health' in state_attr('binary_sensor.rex_needs_attention', 'reasons') | join(' ') }}"
    action:
      - service: hundesystem.send_notification
        data:
          title: "⚠️ Rex - Gesundheit beachten"
          message: "{{ state_attr('binary_sensor.rex_needs_attention', 'reasons') | join(', ') }}"
```

#### **Wetter-basierte Empfehlungen**
```yaml
automation:
  - alias: "Rex - Wetter Warnung"
    trigger:
      - platform: numeric_state
        entity_id: sensor.temperature
        above: 28
    condition:
      - condition: state
        entity_id: input_boolean.rex_outside
        state: "off"
      - condition: time
        after: "10:00:00"
        before: "18:00:00"
    action:
      - service: hundesystem.send_notification
        data:
          title: "🌡️ Heiß heute!"
          message: "Es ist sehr heiß ({{ states('sensor.temperature') }}°C). Rex sollte früh morgens oder spät abends raus."
```

---

## 📱 **Dashboard Integration**

### 🎨 **Automatisches Mushroom Dashboard**

Die Integration erstellt automatisch ein vollständiges Dashboard mit:

- **📊 Übersichtskarten** für alle Funktionen
- **🎛️ Schnellaktionen** für häufige Aufgaben
- **📈 Statistik-Ansichten** mit Trends
- **📝 Notiz-Bereiche** für Beobachtungen
- **🏥 Gesundheits-Monitoring** mit Scores
- **📱 Mobile-optimiert** für Smartphone-Nutzung

#### **Beispiel Dashboard-Karte**
```yaml
type: custom:mushroom-template-card
primary: "Rex"
secondary: "{{ states('sensor.rex_status') }}"
icon: mdi:dog
icon_color: >-
  {% set status = states('sensor.rex_status') %}
  {% if 'Notfall' in status %} red
  {% elif 'Aufmerksamkeit' in status %} orange
  {% elif 'Alles in Ordnung' in status %} green
  {% else %} blue {% endif %}
badge_icon: >-
  {% if is_state('binary_sensor.rex_needs_attention', 'on') %} mdi:alert-circle
  {% elif is_state('binary_sensor.rex_visitor_mode', 'on') %} mdi:account-group
  {% endif %}
tap_action:
  action: more-info
```

### 📊 **Erweiterte Statistik-Karten**

```yaml
# Wöchentliche Fütterungsstatistik
type: custom:mini-graph-card
entities:
  - entity: counter.rex_feeding_morning_count
    name: Frühstück
    color: orange
  - entity: counter.rex_feeding_evening_count
    name: Abendessen
    color: red
name: Fütterungen diese Woche
hours_to_show: 168
group_by: date
aggregate_func: max
```

---

## 🔧 **Erweiterte Konfiguration**

### 🎯 **Multi-Hund Setup**

```yaml
# Automatisches Hinzufügen eines zweiten Hundes
service: hundesystem.add_dog
data:
  dog_name: bella
  push_devices: 
    - mobile_app_smartphone
  door_sensor: binary_sensor.back_door
  create_dashboard: true
```

### 🏥 **Gesundheitsmonitoring Konfiguration**

```yaml
# Erweiterte Gesundheitsüberwachung
input_number:
  rex_target_weight:
    name: "Rex Zielgewicht"
    min: 1
    max: 50
    step: 0.1
    unit_of_measurement: "kg"
    
input_text:
  rex_medical_conditions:
    name: "Rex Medizinische Bedingungen"
    max: 255
```

### 🌦️ **Wetter-Integration Setup**

```yaml
# In configuration.yaml
template:
  - sensor:
      - name: "Rex Weather Recommendation"
        state: >-
          {% set temp = states('sensor.temperature') | float %}
          {% set condition = states('weather.home') %}
          {% if temp > 30 %}
            Zu heiß - Nur kurze Spaziergänge
          {% elif temp < 0 %}
            Sehr kalt - Pfoten schützen
          {% elif condition in ['rainy', 'pouring'] %}
            Regen - Kurze Runden oder drinnen bleiben
          {% else %}
            Perfekt für Aktivitäten
          {% endif %}
```

---

## 🚨 **Notfall-System**

### 📞 **Notfallkontakte Konfiguration**

```yaml
# Notfallkontakte in input_text
input_text:
  rex_emergency_contact_1:
    name: "Notfallkontakt 1"
    initial: "Maria Müller - 0123-456789"
    
  rex_vet_emergency:
    name: "Tierarzt Notfall"
    initial: "Tierklinik 24/7 - 0987-654321"
```

### 🚨 **Notfall-Automation**

```yaml
automation:
  - alias: "Rex - Notfall aktiviert"
    trigger:
      - platform: state
        entity_id: input_boolean.rex_emergency_mode
        to: "on"
    action:
      - service: notify.all_devices
        data:
          title: "🚨 NOTFALL - Rex"
          message: "Notfallmodus für Rex wurde aktiviert!"
          data:
            priority: high
            ttl: 0
      - service: script.emergency_call_sequence
```

---

## 🔍 **Troubleshooting**

### ❓ **Häufige Probleme**

#### **Helper-Entitäten werden nicht erstellt**
```bash
# Lösung:
1. Home Assistant vollständig neustarten
2. Integration entfernen und neu hinzufügen
3. Logs prüfen: Einstellungen → System → Protokolle
```

#### **Dashboard wird nicht angezeigt**
```bash
# Lösung:
1. Mushroom Cards installieren: HACS → Frontend
2. Browser-Cache löschen
3. Dashboard manuell aktualisieren
```

#### **Benachrichtigungen funktionieren nicht**
```yaml
# Test-Service aufrufen:
service: hundesystem.test_notification
data:
  dog_name: rex
```

#### **Türsensor reagiert nicht**
```yaml
# Sensor in Automationen prüfen:
trigger:
  - platform: state
    entity_id: binary_sensor.your_door_sensor
action:
  - service: system_log.write
    data:
      message: "Türsensor ausgelöst"
      level: info
```

### 📊 **Debug-Logs aktivieren**

```yaml
# In configuration.yaml
logger:
  default: warning
  logs:
    custom_components.hundesystem: debug
```

---

## 🔮 **Roadmap & Geplante Features**

### 🎯 **Version 2.1 (Q3 2025)**
- [ ] **GPS-Tracking** Integration für Standort-basierte Features
- [ ] **Kalender-Integration** für Tierarzttermine und Impfungen
- [ ] **Photo-Upload** für Gesundheitsdokumentation
- [ ] **Voice-Integration** (Alexa/Google Assistant)

### 🎯 **Version 2.2 (Q4 2025)**
- [ ] **IoT-Sensoren** Integration (Smart Futterschale, Wasserspender)
- [ ] **Machine Learning** für Verhaltensanalyse
- [ ] **Mobile Companion App** 
- [ ] **Backup & Sync** Cloud-Features

### 🎯 **Version 3.0 (2026)**
- [ ] **Multi-Pet Support** (Katzen, andere Haustiere)
- [ ] **Vet Integration** API für direkte Terminbuchung
- [ ] **Community Features** Hundebesitzer-Netzwerk
- [ ] **AR Features** für interaktive Gesundheitschecks

---

## 🤝 **Community & Support**

### 💬 **Support Kanäle**
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/Bigdaddy1990/hundesystem/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/Bigdaddy1990/hundesystem/discussions)
- **📧 Direkte Hilfe**: [E-Mail Support](mailto:support@hundesystem.dev)
- **💬 Community Chat**: [Discord Server](https://discord.gg/hundesystem)

### 🏆 **Mitwirken**

Beiträge sind herzlich willkommen! 

```bash
# Repository forken und klonen
git clone https://github.com/yourusername/hundesystem.git
cd hundesystem

# Feature Branch erstellen
git checkout -b feature/amazing-new-feature

# Änderungen committen
git commit -m 'Add amazing new feature'

# Push und Pull Request erstellen
git push origin feature/amazing-new-feature
```

#### **Entwicklung Setup**
```bash
# Dependencies installieren
pip install -r requirements_dev.txt

# Code Style prüfen
pre-commit run --all-files

# Tests ausführen
pytest tests/

# Integration testen
hass --script check_config --config config/
```

### 🎖️ **Hall of Fame**
Besonderer Dank an alle Mitwirkenden:

- **@Bigdaddy1990** - Hauptentwickler
- **@TestUser1** - Beta-Testing und Feedback
- **@VetDoc** - Gesundheitsfeatures Consulting
- **@MobileGuru** - Dashboard Optimierungen
- **Community** - Unzählige Verbesserungsvorschläge

---

## 📄 **Lizenz & Rechtliches**

```
MIT License

Copyright (c) 2025 Hundesystem Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

### ⚖️ **Datenschutz**
- **🔒 Lokal**: Alle Daten werden lokal in Home Assistant gespeichert
- **🚫 No Cloud**: Keine externen Cloud-Services erforderlich
- **🔐 Privacy-First**: Keine Datenübertragung an Dritte
- **🛡️ Sicher**: Alle Kommunikation erfolgt innerhalb Ihres Netzwerks

---

## ❤️ **Danksagungen**

- **🏠 Home Assistant Community** für die großartige Plattform
- **🎨 Mushroom Cards** für die wunderschönen UI-Komponenten
- **🐕 Alle Hundebesitzer** die Feedback und Ideen beigetragen haben
- **👨‍⚕️ Tierärzte** die bei den Gesundheitsfeatures geholfen haben
- **🧪 Beta-Tester** für unermüdliches Testen und Feedback

---

## ☕ **Unterstützung**

Wenn Ihnen diese Integration gefällt und Sie die Entwicklung unterstützen möchten:

- ⭐ **Stern geben** auf GitHub
- 🐛 **Bugs melden** für bessere Qualität  
- 💡 **Features vorschlagen** für neue Ideen
- ☕ **[Kaffee spendieren](https://ko-fi.com/bigdaddy1990)** für den Entwickler
- 📢 **Weiterempfehlen** an andere Hundebesitzer

---

<div align="center">

## 🐶 Made with ❤️ for Dog Lovers

**Hundesystem** - *Weil jeder Hund das Beste verdient hat!*

[🏠 Home Assistant](https://www.home-assistant.io/) | [🎨 Mushroom Cards](https://github.com/piitaya/lovelace-mushroom) | [📦 HACS](https://hacs.xyz/)

---

*Entwickelt mit Liebe für Hunde und Smart Home Enthusiasten* 🐕🏠

</div>
