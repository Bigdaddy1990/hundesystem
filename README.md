# Hundesystem - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/Bigdaddy1990/hundesystem.svg)](https://github.com/Bigdaddy1990/hundesystem/releases)

Eine Home Assistant Integration zur Verwaltung und Überwachung von Hundeaktivitäten wie Fütterung, Gassigehen und täglichen Routinen.

## 🐶 Features

- **Fütterungsmanagement**: Verfolge alle Mahlzeiten (Frühstück, Mittagessen, Abendessen, Leckerli)
- **Aktivitätstracking**: Überwache Gassigehzeiten und Außenaktivitäten
- **Besuchsmodus**: Spezielle Einstellungen für Gäste oder Hundesitter
- **Push-Benachrichtigungen**: Erinnerungen und Status-Updates
- **Automatisches Dashboard**: Generiert automatisch ein Mushroom-Dashboard
- **Tägliche Statistiken**: Vollständige Übersicht über alle Aktivitäten
- **Status-Sensoren**: Intelligente Sensoren für Aufmerksamkeitsbedarf

## 📋 Sensoren und Entitäten

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

### Helper-Entitäten (automatisch erstellt)
- Input Boolean für jede Fütterungsart und Aktivität
- Counter für Fütterungen und Außenaktivitäten
- Input DateTime für Fütterungszeiten
- Input Text für Notizen

## 🚀 Installation

### HACS (Empfohlen)
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

1. Gehe zu **Einstellungen** → **Geräte & Dienste**
2. Klicke auf **Integration hinzufügen**
3. Suche nach "Hundesystem"
4. Folge dem Konfigurationsassistenten:
   - **Hundename**: Name für deinen Hund (z.B. "rex")
   - **Push-Geräte**: Wähle Benachrichtigungsgeräte (optional)
   - **Personenverfolgung**: Aktiviere erweiterte Features (optional)
   - **Dashboard erstellen**: Automatisches Mushroom-Dashboard (empfohlen)

## 📊 Dashboard

Die Integration erstellt automatisch ein ansprechendes Dashboard mit:
- Übersichtskarten für alle Fütterungen
- Aktivitätstracking
- Besuchsmodus-Steuerung
- Schnellaktionen für Erinnerungen und Reset
- Statistikansicht
- Notizbereich

**Hinweis**: Für die beste Dashboard-Erfahrung sollte [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom) installiert sein.

## 🔧 Services

### `hundesystem.trigger_feeding_reminder`
Sendet eine Fütterungserinnerung
```yaml
service: hundesystem.trigger_feeding_reminder
data:
  meal_type: morning  # morning, lunch, evening, snack
  message: "Zeit fürs Frühstück!"  # optional
```

### `hundesystem.daily_reset`
Setzt alle Tagesstatistiken zurück
```yaml
service: hundesystem.daily_reset
```

### `hundesystem.send_notification`
Sendet eine benutzerdefinierte Benachrichtigung
```yaml
service: hundesystem.send_notification
data:
  title: "Erinnerung"
  message: "Hast du Rex schon gefüttert?"
```

## 🤖 Automatisierung Beispiele

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

### Fütterungserinnerung
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

## 🎯 Geplante Features

- [ ] Historische Datenauswertung
- [ ] Gewichtstracking
- [ ] Tierarzttermin-Erinnerungen
- [ ] Foto-Upload für Aktivitäten
- [ ] Gesundheitsmonitoring
- [ ] Multi-Hund Support

## 🐛 Problembehebung

### Häufige Probleme

**Helper-Entitäten werden nicht erstellt**
- Überprüfe die Logs unter Entwicklertools → Logs
- Stelle sicher, dass die Input Boolean/Counter-Integrationen aktiviert sind

**Dashboard wird nicht erstellt**
- Überprüfe, ob der Ordner `dashboards/` im Home Assistant Konfigurationsverzeichnis existiert
- Installiere Mushroom Cards für die beste Erfahrung

**Benachrichtigungen funktionieren nicht**
- Überprüfe, ob die ausgewählten Notify-Services korrekt konfiguriert sind
- Teste die Services manuell in Entwicklertools → Services

## 🤝 Beitragen

Beiträge sind willkommen! Bitte:
1. Forke das Repository
2. Erstelle einen Feature-Branch
3. Committe deine Änderungen
4. Öffne einen Pull Request

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## ❤️ Unterstützung

Wenn dir diese Integration gefällt:
- ⭐ Gib dem Repository einen Stern
- 🐛 Melde Bugs über GitHub Issues
- 💡 Schlage neue Features vor
- ☕ [Spendiere mir einen Kaffee](https://ko-fi.com/bigdaddy1990)

---

**Entwickelt mit ❤️ für Hundeliebhaber und Home Assistant Enthusiasten**
