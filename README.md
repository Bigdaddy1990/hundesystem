# 🐶 Hundesystem – Home Assistant Integration

Eine smarte Mehrhundeverwaltung mit Sensoren, Push-Logik, Dashboard und Besuchsmodus.

…



\[!\[hacs\_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

\[!\[GitHub release](https://img.shields.io/github/v/release/Bigdaddy1990/hundesystem?include\_prereleases)](https://github.com/Bigdaddy1990/hundesystem/releases)

\[!\[License](https://img.shields.io/github/license/Bigdaddy1990/hundesystem)](LICENSE)



> \*\*Eine intelligente Hundeverwaltung für Home Assistant – mit Dashboard, Push-Benachrichtigungen, Besuchsmodus und Mehrhundesupport.\*\*



---



\## ✨ Features



| Kategorie             | Beschreibung |

|----------------------|--------------|

| 🧠 \*\*Einfaches Setup\*\* | Integration über UI mit nur wenigen Klicks |

| 🐕 \*\*Mehrhundesupport\*\* | Beliebig viele Hunde, individuell konfigurierbar |

| 🍽️ \*\*Fütterungserinnerung\*\* | Automatische Push-Benachrichtigungen für Frühstück, Mittag, Abend, Snack |

| 🚪 \*\*Aktivitäts-Tracking\*\* | Gartengang-Zähler, Besuchsmodus, täglicher Reset |

| 📲 \*\*Benachrichtigungen\*\* | Push mit Rückfrage-Funktion an Geräte oder `person.\*` |

| 📊 \*\*Dashboard inklusive\*\* | Mushroom-kompatibles YAML-Dashboard wird automatisch generiert |

| 🧾 \*\*Services \& Automationen\*\* | Eigene Services für Erinnerungen, Resets, Benachrichtigungen |

| 🧩 \*\*Modular \& flexibel\*\* | Alle Features einzeln deaktivierbar |



---



\## 📦 Installation über HACS



> ⚠️ Du musst \[HACS](https://hacs.xyz) installiert haben.



1\. Öffne Home Assistant → \*\*HACS\*\*

2\. Gehe zu \*\*Integrationen\*\* → „Custom Repositories“

3\. Gib folgende URL ein:



https://github.com/Bigdaddy1990/hundesystem

4\. Kategorie: \*\*Integration\*\*

5\. Installiere die Integration

6\. Home Assistant \*\*neu starten\*\*

7\. Integration hinzufügen → „Hundesystem“



---



\## 🧠 Konfiguration



Nach dem Hinzufügen wirst du durch folgende Einstellungen geführt:



\- 🐶 \*\*Name des Hundes\*\* (z. B. `rex`)

\- 📲 \*\*Push-Geräte auswählen\*\* (`notify.\*`)

\- 👤 \*\*Personen-Tracking aktivieren/deaktivieren\*\*

\- 📊 \*\*Dashboard automatisch erstellen\*\*



Es werden automatisch folgende Entitäten erzeugt:



\- `input\_boolean.rex\_feeding\_morning`

\- `counter.rex\_outside`

\- `sensor.rex\_status`

\- `binary\_sensor.rex\_needs\_attention`

\- ...



---



\## 🛠️ Verfügbare Services



| Service | Beschreibung |

|--------|--------------|

| `hundesystem.trigger\_feeding\_reminder` | Sendet Erinnerung an Fütterung |

| `hundesystem.daily\_reset`              | Setzt Zähler \& Status zurück |

| `hundesystem.send\_notification`        | Sendet beliebige Push-Nachricht |



---



\## 📸 Screenshots



> \*(Optional – Du kannst Bilder in `docs/screenshots/` ablegen)\*



| Übersicht | Statistik |

|----------|-----------|

| !\[](docs/screenshots/dashboard1.png) | !\[](docs/screenshots/stats1.png) |



---



\## 📚 Dokumentation



\- 📥 \[Installation](docs/installation.md)

\- ⚙️ \[Konfiguration](docs/configuration.md)

\- ⚙️ \[Services](custom\_components/hundesystem/services.yaml)



---



\## 🧑‍💻 Entwickler \& Beiträge



\- Quellcode: \[GitHub Repository](https://github.com/Bigdaddy1990/hundesystem)

\- Fehler oder Vorschläge? → \[Issues](https://github.com/Bigdaddy1990/hundesystem/issues)

\- Pull Requests sind willkommen! 🙌



---



\## 🛡️ Lizenz



MIT License – \[siehe LICENSE](LICENSE)



---



\*\*Hundesystem\*\* ist deine smarte Erweiterung für tierisch gute Home Assistant Automationen. Viel Spaß! 🐾



