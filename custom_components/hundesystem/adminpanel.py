title: Hundesystem Admin
path: hundesystem_admin
icon: mdi:cog-outline
type: custom:vertical-stack
cards:
  - type: markdown
    content: >
      # 🐶 Hundesystem Adminpanel  
      Übersicht über alle konfigurierten Hunde, Status & Aktionen

  - type: entities
    title: Hund: Rex
    entities:
      - entity: input_boolean.rex_feeding_morning
        name: Frühstück erledigt
      - entity: input_boolean.rex_feeding_evening
        name: Abendessen erledigt
      - entity: counter.rex_feeding_morning
        name: Frühstücks-Zähler
      - entity: counter.rex_outside
        name: Gassi-Zähler
      - entity: input_boolean.rex_visitor_mode
        name: Besucherhund-Modus

  - type: custom:mushroom-template-card
    icon: mdi:dog-service
    primary: Rückfrage starten
    tap_action:
      action: call-service
      service: script.rex_trigger_feeding_check
      data: {}

  - type: custom:mushroom-template-card
    icon: mdi:bell-ring
    primary: Push-Test senden
    tap_action:
      action: call-service
      service: script.rex_push_test
      data: {}

  - type: custom:mushroom-template-card
    icon: mdi:restart
    primary: Tagesstatistik zurücksetzen
    tap_action:
      action: call-service
      service: script.rex_daily_reset
      data: {}
