# 🐶 Hundesystem – Home Assistant Integration

![Version](https://img.shields.io/badge/version-1.0.3-blue.svg)
![HACS](https://img.shields.io/badge/hacs-compatible-green)
![License](https://img.shields.io/github/license/Bigdaddy1990/hundesystem)

Ein vollständiges, modulares Smart-Home-System zur **automatisierten Hunde-Betreuung** in Home Assistant.

---

## 🔧 Funktionen

| Kategorie             | Beschreibung |
|----------------------|--------------|
| 🍽️ Fütterung         | Erinnerungen für Frühstück, Mittag, Abend, Leckerli |
| 🚪 Türsensor-Tracking | „Draußen“-Protokoll mit Rückfragen |
| 📲 Push-Logik         | Nachricht an anwesende Person(en) oder manuelle Geräte |
| 📅 Tagesstatistik     | Counter pro Aktion + automatischer Reset |
| 🧍 Besucherhunde      | Optionaler Besuchsmodus & Statusanzeige |
| 🧠 Adminpanel         | zentrale Übersicht, manuelle Steuerung, Push-Test |
| 📊 Dashboard          | Mushroom-fähig, responsiv, Chip + Template-Karten |
| 💬 Rückfragen         | „Hund schon gefüttert?“ via Notification |
| 🔁 Flexibel           | beliebig viele Hunde, jede Funktion einzeln abschaltbar |

---

## 🚀 Installation über HACS

1. Öffne HACS → `Integrationen` → Drei-Punkte-Menü → `Benutzerdefiniertes Repository hinzufügen`  
   → URL: `https://github.com/Bigdaddy1990/hundesystem`  
   → Kategorie: `Integration`

2. Nach Installation: Home Assistant neustarten.

3. Gehe zu `Einstellungen` → `Integrationen` → `+ Hinzufügen` → `Hundesystem`

4. Folge dem Setup-Assistenten:
   - Namen des Hundesystems (z. B. `Rex`)
   - Push-Geräte auswählen oder `person.*` aktivieren
   - Optional: Dashboard automatisch erstellen lassen

---

## 🧩 Konfigurationsbeispiele

```yaml
lovelace:
  dashboards:
    hundesystem:
      mode: yaml
      title: Hundesystem
      icon: mdi:dog-service
      filename: dashboards/hundesystem/dashboard.yaml
      show_in_sidebar: true
