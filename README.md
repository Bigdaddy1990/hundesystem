# 🐶 Hundesystem - Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Bigdaddy1990/hundesystem)](https://github.com/Bigdaddy1990/hundesystem/releases)
[![GitHub](https://img.shields.io/github/license/Bigdaddy1990/hundesystem)](LICENSE)
[![Buy me a coffee](https://img.shields.io/static/v1.svg?label=%20&message=Buy%20me%20a%20coffee&color=6f4e37&logo=buy%20me%20a%20coffee&logoColor=white)](https://ko-fi.com/bigdaddy1990)

Eine umfassende Home Assistant Integration zur Verwaltung und Überwachung von Hundeaktivitäten wie Fütterung, Gassigehen und täglichen Routinen.

## ✨ Features

### 🍽️ Fütterungsmanagement
- Verfolge alle Mahlzeiten (Frühstück, Mittagessen, Abendessen, Leckerli)
- Automatische Erinnerungen zu Fütterungszeiten
- Fütterungszähler und Statistiken

### 🚶 Aktivitätstracking
- Überwache Gassigehzeiten und Außenaktivitäten
- Aktivitätszähler für verschiedene Hundeaktivitäten
- Zeitstempel für letzte Aktivitäten

### 🏠 Besuchsmodus
- Spezielle Einstellungen für Gäste oder Hundesitter
- Reduzierte Benachrichtigungen während Besuchszeiten
- Besuchername-Tracking

### 📱 Push-Benachrichtigungen
- Erinnerungen und Status-Updates
- Konfigurierbare Benachrichtigungsgeräte
- Benutzerdefinierte Nachrichten

### 📊 Automatisches Dashboard
- Generiert automatisch ein ansprechendes Mushroom-Dashboard
- Übersichtskarten für alle Funktionen
- Schnellaktionen und Statistiken

### 📈 Intelligente Sensoren
- Tägliche Statistiken und Zusammenfassungen
- Status-Sensoren für Aufmerksamkeitsbedarf
- Vollständige Übersicht über alle Aktivitäten

## 🔧 Entitäten

### Binary Sensoren
- `binary_sensor.{name}_feeding_complete` - Fütterung komplett
- `binary_sensor.{name}_daily_tasks_complete` - Tagesaufgaben komplett  
- `binary_sensor.{name}_visitor_mode` - Besuchsmodus aktiv
- `binary_sensor.{name}_outside_status` - War draußen Status
- `binary_sensor.{name}_needs_attention` - Braucht Aufmerksamkeit

### Sensoren
- `sensor.{name}_status` - Allgemeiner Status
- `sensor.{name}_feeding_status` - Fütterungsstatus
- `sensor.{name}_activity` - Aktivitätsstatus
- `sensor.{name}_daily_summary` - Tageszusammenfassung
- `sensor.{name}_last_activity` - Letzte Aktivität (Zeitstempel)

### Helper-Entitäten
Die Integration erstellt automatisch alle benötigten Helper-Entitäten:
- Input Boolean für jede Fütterungsart und Aktivität
- Counter für Fütterungen und Außenaktivitäten  
- Input DateTime für Fütterungszeiten
- Input Text für Notizen

## 📦 Installation

### Via HACS (Empfohlen)

1. Öffne HACS in Home Assistant
2. Gehe zu "Integrationen"
3. Klicke auf die drei Punkte (⋮) oben rechts
4. Wähle "Benutzerdefinierte Repositories"
5. Füge die URL hinzu: `https://github.com/Bigdaddy1990/hundesystem`
6. Kategorie: "Integration"
7. Klicke "Hinzufügen"
8. Suche nach "Hundesystem" und installiere es
9. Starte Home Assistant neu

### Manuelle Installation

1. Lade die neueste Version herunter
2. Extrahiere den Inhalt nach `custom_components/hundesystem/`
3. Starte Home Assistant neu

## ⚙️ Konfiguration

1. Gehe zu Einstellungen → Geräte & Dienste
2. Klicke auf "Integration hinzufügen"
3. Suche nach "Hundesystem"
4. Folge dem Konfigurationsassistenten:
   - **Hundename**: Name für deinen Hund (z.B. "rex")
   - **Push-Geräte**: Wähle Benachrichtigungsgeräte (optional)
   - **Personenverfolgung**: Aktiviere erweiterte Features (optional)
   - **Dashboard erstellen**: Automatisches Mushroom-Dashboard (empfohlen)

## 🎛️ Dashboard

Die Integration erstellt automatisch ein ansprechendes Dashboard mit:

- 🍽️ Übersichtskarten für alle Fütterungen
- 🚶 Aktivitätstracking
- 🏠 Besuchsmodus-Steuerung
- ⚡ Schnellaktionen für Erinnerungen und Reset
- 📊 Statistikansicht
- 📝 Notizbereich

**Hinweis**: Für die beste Dashboard-Erfahrung sollte [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom) installiert sein.

## 🔧 Services

### Fütterungserinnerung senden
```yaml
service: hundesystem.trigger_feeding_reminder
data:
  meal_type: morning # morning, lunch, evening, snack
  message: "Zeit fürs Frühstück!" # optional
```

### Täglicher Reset
```yaml
service: hundesystem.daily_reset
```

### Benachrichtigung senden
```yaml
service: hundesystem.send_notification
data:
  title: "Erinnerung"
  message: "Hast du Rex schon gefüttert?"
```

### Besuchsmodus setzen
```yaml
service: hundesystem.set_visitor_mode
data:
  enabled: true
  visitor_name: "Maria" # optional
```

### Aktivität protokollieren
```yaml
service: hundesystem.log_activity
data:
  activity_type: walk # walk, outside, play, training, other
  duration: 30 # optional, in Minuten
  notes: "Schöner Spaziergang im Park" # optional
```

## 🤖 Automatisierungsbeispiele

### Täglicher Reset um Mitternacht
```yaml
automation:
  - alias: "Hundesystem - Täglicher Reset"
    trigger:
      - platform: time
        at: "00:00:00"
    action:
      - service: hundesystem.daily_reset
```

### Frühstück Erinnerung
```yaml
automation:
  - alias: "Hundesystem - Frühstück Erinnerung"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: state
        entity_id: input_boolean.rex_feeding_morning
        state: "off"
    action:
      - service: hundesystem.trigger_feeding_reminder
        data:
          meal_type: morning
```

### Aufmerksamkeit benötigt
```yaml
automation:
  - alias: "Hundesystem - Aufmerksamkeit benötigt"
    trigger:
      - platform: state
        entity_id: binary_sensor.rex_needs_attention
        to: "on"
        for: "00:30:00"
    action:
      - service: hundesystem.send_notification
        data:
          title: "🐶 Rex braucht Aufmerksamkeit"
          message: "{{ state_attr('binary_sensor.rex_needs_attention', 'reasons') | join(', ') }}"
```

## 🔮 Geplante Features

- 📊 Historische Datenauswertung
- ⚖️ Gewichtstracking
- 🏥 Tierarzttermin-Erinnerungen
- 📸 Foto-Upload für Aktivitäten
- ❤️ Gesundheitsmonitoring
- 🐕‍🦺 Multi-Hund Support

## 🔧 Fehlerbehebung

### Helper-Entitäten werden nicht erstellt
- Überprüfe die Logs unter Entwicklertools → Logs
- Stelle sicher, dass die Input Boolean/Counter-Integrationen aktiviert sind
- Starte Home Assistant nach der Installation neu

### Dashboard wird nicht erstellt
- Überprüfe, ob der Ordner `dashboards/` im Home Assistant Konfigurationsverzeichnis existiert
- Installiere [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom) für die beste Erfahrung
- Prüfe die Logs auf Dashboard-bezogene Fehler

### Benachrichtigungen funktionieren nicht
- Überprüfe, ob die ausgewählten Notify-Services korrekt konfiguriert sind
- Teste die Services manuell in Entwicklertools → Services
- Stelle sicher, dass Mobile App oder andere Notify-Integrationen eingerichtet sind

### Services nicht verfügbar
- Starte Home Assistant nach der Installation neu
- Überprüfe, ob die Integration erfolgreich geladen wurde
- Prüfe die Logs auf Fehlermeldungen bei der Integration

### Entitäten zeigen "Unbekannt" oder "Nicht verfügbar"
- Warte einige Minuten nach der ersten Installation
- Stelle sicher, dass alle Helper-Integrationen aktiviert sind
- Lösche und erstelle die Integration bei persistenten Problemen neu

## 📖 Debug-Informationen

Für detaillierte Debug-Informationen füge folgendes zu deiner `configuration.yaml` hinzu:

```yaml
logger:
  default: warning
  logs:
    custom_components.hundesystem: debug
```

## 🤝 Beitragen

Beiträge sind willkommen! Bitte:

1. 🍴 Forke das Repository
2. 🌿 Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. 💾 Committe deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. 📤 Pushe zum Branch (`git push origin feature/AmazingFeature`)
5. 🔄 Öffne einen Pull Request

### Entwicklung

```bash
# Repository klonen
git clone https://github.com/Bigdaddy1990/hundesystem.git
cd hundesystem

# Development-Umgebung einrichten
pip install -r requirements_dev.txt

# Code-Stil prüfen
pre-commit run --all-files

# Tests ausführen
pytest
```

## 📝 Changelog

### Version 1.0.0
- ✨ Erste Veröffentlichung
- 🍽️ Fütterungsmanagement mit allen Mahlzeiten
- 🚶 Aktivitätstracking für Gassigehen
- 🏠 Besuchsmodus-Funktionalität
- 📱 Push-Benachrichtigungen
- 📊 Automatisches Dashboard
- 🎯 Intelligente Aufmerksamkeits-Sensoren

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## ❤️ Unterstützung

Wenn dir diese Integration gefällt:

- ⭐ Gib dem Repository einen Stern
- 🐛 Melde Bugs über [GitHub Issues](https://github.com/Bigdaddy1990/hundesystem/issues)
- 💡 Schlage neue Features vor
- ☕ [Spendiere mir einen Kaffee](https://ko-fi.com/bigdaddy1990)

## 🏆 Danksagungen

- Dank an die Home Assistant Community für die großartige Plattform
- Dank an alle Mitwirkenden und Beta-Tester
- Besonderer Dank an alle Hundebesitzer, die Feedback gegeben haben

## 📞 Support & Community

- 💬 [GitHub Discussions](https://github.com/Bigdaddy1990/hundesystem/discussions) für Fragen und Ideen
- 🐛 [GitHub Issues](https://github.com/Bigdaddy1990/hundesystem/issues) für Bug-Reports
- 📧 [E-Mail Support](mailto:support@hundesystem.dev) für private Anfragen

---

Entwickelt mit ❤️ für Hundeliebhaber und Home Assistant Enthusiasten

*Hund ist der beste Freund des Menschen - und jetzt auch der beste Freund deines Smart Homes!* 🐶🏠
