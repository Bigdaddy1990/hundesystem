# 🐶 Hundesystem - Smart Dog Care für Home Assistant

Eine umfassende Integration für die intelligente Betreuung und Überwachung Ihres Hundes in Home Assistant.

## ✨ **Features**

### 🍽️ **Intelligente Fütterungsverwaltung**
- Automatische Fütterungszeiten und Erinnerungen
- Tracking von 4 Mahlzeiten (Frühstück, Mittagessen, Abendessen, Leckerli)
- Überfälligkeits-Detection mit Severity-Leveln
- Portionsgrößen-Tracking und Überfressen-Warnung

### 🏃 **Aktivitäts-Monitoring**
- Umfassende Aktivitätssensoren (Gassi, Spielen, Training, Draußen)
- Inaktivitätswarnungen mit konfigurierbaren Schwellenwerten
- Milestone-Celebrations für Aktivitätsfortschritte
- Automatische Last-Activity Tracking

### 🏥 **Gesundheits-Überwachung**
- Comprehensive Health Score basierend auf mehreren Faktoren
- Mood-Tracking mit Faktor-Analyse
- Medikamenten-Erinnerungen und Tracking
- Tierarzt-Terminverwaltung mit Erinnerungen

### 🚨 **Notfall & Sicherheit**
- Emergency Protocol System mit automatischer Benachrichtigung
- Multi-Level Alert System (Low, Medium, High, Critical)
- Attention-Needed Detection mit intelligenter Priorisierung
- Emergency Contact Management

### 👥 **Besucherverwaltung**
- Visitor Mode mit automatischer Zeitplanung
- Besuchername & Kontakt-Tracking
- Session-Duration Calculation

### 📊 **Reporting & Analytics**
- Daily Summary mit Score-Berechnung
- Weekly Trends und Verlaufsanalyse
- Comprehensive Reports (Daily, Weekly, Monthly)
- Real-time Dashboard Data

### 🤖 **Intelligente Automatisierung**
- Smart Feeding Reminders basierend auf Zeiten
- Activity Milestone Notifications
- Health Deterioration Alerts
- Emergency Response Automation

### 🎯 **Services & Actions**
- 12 Service-Endpoints für alle Hundebetreuungs-Aktionen
- One-Click Actions (Feed, Walk, Play, Training, etc.)
- Health Check Services mit umfassender Dokumentation
- Report Generation mit Email-Integration

## 🚀 **Installation**

### **Via HACS (Empfohlen)**

1. **HACS öffnen** in Home Assistant
2. **Integrationen** auswählen
3. **⋮** (drei Punkte) oben rechts klicken
4. **"Benutzerdefinierte Repositories"** wählen
5. **URL hinzufügen**: `https://github.com/Bigdaddy1990/hundesystem`
6. **Kategorie**: "Integration"
7. **"Hinzufügen"** klicken
8. **"Hundesystem"** suchen und installieren
9. **Home Assistant neu starten**

### **Manuelle Installation**

1. **Repository herunterladen** oder klonen
2. **`custom_components/hundesystem`** in Ihr Home Assistant `custom_components/` Verzeichnis kopieren
3. **Home Assistant neu starten**
4. **Integration hinzufügen** über Einstellungen → Geräte & Dienste

## ⚙️ **Konfiguration**

### **Erste Einrichtung**

1. **Einstellungen** → **Geräte & Dienste**
2. **"Integration hinzufügen"** klicken
3. **"Hundesystem"** suchen
4. **Hundename eingeben** (z.B. "Rex", "Bella")
5. **Optionale Einstellungen** konfigurieren:
   - Benachrichtigungsgeräte
   - Personenverfolgung
   - Automatisches Dashboard
   - Türsensor (optional)

### **Erweiterte Konfiguration**

Nach der Installation können Sie erweiterte Einstellungen konfigurieren:

- **Fütterungszeiten** anpassen
- **Gesundheits-Schwellenwerte** definieren
- **Automatisierungen** aktivieren/deaktivieren
- **Benachrichtigungseinstellungen** anpassen

## 📱 **Dashboard**

Das System erstellt automatisch ein vollständiges Dashboard mit:

- **Übersichtskarten** für Status, Fütterung, Aktivität
- **Schnellaktionen** für häufige Aufgaben
- **Gesundheits-Monitoring** mit Trend-Anzeigen
- **Aktivitäts-Timeline** mit Details
- **Notfall-Bedienelemente** für kritische Situationen

## 🎯 **Services**

### **Verfügbare Services:**

- `hundesystem.feed_dog` - Hund füttern
- `hundesystem.walk_dog` - Gassi gehen
- `hundesystem.play_with_dog` - Mit Hund spielen
- `hundesystem.training_session` - Training durchführen
- `hundesystem.health_check` - Gesundheitscheck
- `hundesystem.medication_given` - Medikament gegeben
- `hundesystem.vet_visit` - Tierarztbesuch
- `hundesystem.grooming_session` - Pflegesession
- `hundesystem.activate_emergency_mode` - Notfallmodus
- `hundesystem.toggle_visitor_mode` - Besuchsmodus
- `hundesystem.daily_reset` - Tagesreset
- `hundesystem.generate_report` - Bericht generieren

## 🔧 **Systemanforderungen**

- **Home Assistant** 2024.1.0 oder höher
- **Python** 3.11 oder höher
- **Speicher**: ~50MB für Installation
- **RAM**: ~100MB während der Nutzung

## 📊 **Entitäten**

Das System erstellt automatisch ~120-150 Entitäten:

- **20+ Input Boolean** (Fütterung, Aktivitäten, Status)
- **15+ Counter** (Aktivitätszähler)
- **25+ Input DateTime** (Zeitstempel, Termine)
- **30+ Input Text** (Notizen, Kontakte, Informationen)
- **20+ Input Number** (Metriken, Scores, Messungen)
- **15+ Input Select** (Status-Auswahlen)
- **8 Sensoren** (Status, Aktivität, Gesundheit, etc.)
- **12 Binary Sensoren** (Warnungen, Alerts, Status)

## 🤝 **Support**

### **Hilfe & Support**

- **🐛 Bugs melden**: [GitHub Issues](https://github.com/Bigdaddy1990/hundesystem/issues)
- **💡 Features vorschlagen**: [GitHub Discussions](https://github.com/Bigdaddy1990/hundesystem/discussions)
- **📖 Dokumentation**: [GitHub Wiki](https://github.com/Bigdaddy1990/hundesystem/wiki)

### **Community**

- **Discord**: [Hundesystem Community](https://discord.gg/hundesystem)
- **Forum**: [Home Assistant Community](https://community.home-assistant.io)

## 🔍 **Troubleshooting**

### **Häufige Probleme**

**Helper-Entitäten werden nicht erstellt:**
1. Home Assistant vollständig neustarten
2. Integration entfernen und neu hinzufügen
3. Logs prüfen: Einstellungen → System → Protokolle

**Dashboard wird nicht angezeigt:**
1. Mushroom Cards installieren (über HACS)
2. Browser-Cache löschen
3. Dashboard manuell aktualisieren

**Benachrichtigungen funktionieren nicht:**
1. Benachrichtigungsdienste in der Integration konfigurieren
2. Mobile App Benachrichtigungen aktivieren
3. Test-Service aufrufen

### **Debug-Logs aktivieren**

```yaml
# In configuration.yaml
logger:
  default: warning
  logs:
    custom_components.hundesystem: debug
```

## 📄 **Lizenz**

MIT License - Siehe [LICENSE](https://github.com/Bigdaddy1990/hundesystem/blob/main/LICENSE) für Details.

## ❤️ **Dank**

Besonderer Dank an:
- **Home Assistant Community** für die großartige Plattform
- **HACS Team** für das großartige Repository-System
- **Alle Beta-Tester** für Feedback und Verbesserungsvorschläge
- **Mushroom Cards** für die wunderschönen UI-Komponenten

---

## 🐶 Made with ❤️ for Dog Lovers

**Hundesystem** - *Weil jeder Hund das Beste verdient hat!*
