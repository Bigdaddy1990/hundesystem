"""Dashboard creation for Hundesystem."""
import logging
import os
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

async def async_create_dashboard(hass: HomeAssistant, name: str):
    """Create a dashboard for the dog system."""
    
    dashboard_config = f"""
# Hundesystem Dashboard für {name.title()}
# Automatisch generiert von der Hundesystem Integration

title: Hundesystem - {name.title()}
views:
  - title: Übersicht
    path: overview
    icon: mdi:dog
    cards:
      - type: vertical-stack
        cards:
          # Status Übersicht
          - type: custom:mushroom-template-card
            primary: "{name.title()}"
            secondary: "Hundesystem Übersicht"
            icon: mdi:dog
            icon_color: blue
            tap_action:
              action: none
          
          # Fütterung Sektion
          - type: horizontal-stack
            cards:
              - type: custom:mushroom-template-card
                primary: "Frühstück"
                secondary: "{{{{ states('counter.{name}_feeding_morning') }}}} mal"
                icon: mdi:weather-sunrise
                icon_color: "{{{{ 'green' if is_state('input_boolean.{name}_feeding_morning', 'on') else 'grey' }}}}"
                tap_action:
                  action: toggle
                  target:
                    entity_id: input_boolean.{name}_feeding_morning
              
              - type: custom:mushroom-template-card
                primary: "Mittag"
                secondary: "{{{{ states('counter.{name}_feeding_lunch') }}}} mal"
                icon: mdi:weather-sunny
                icon_color: "{{{{ 'green' if is_state('input_boolean.{name}_feeding_lunch', 'on') else 'grey' }}}}"
                tap_action:
                  action: toggle
                  target:
                    entity_id: input_boolean.{name}_feeding_lunch
          
          - type: horizontal-stack
            cards:
              - type: custom:mushroom-template-card
                primary: "Abend"
                secondary: "{{{{ states('counter.{name}_feeding_evening') }}}} mal"
                icon: mdi:weather-sunset
                icon_color: "{{{{ 'green' if is_state('input_boolean.{name}_feeding_evening', 'on') else 'grey' }}}}"
                tap_action:
                  action: toggle
                  target:
                    entity_id: input_boolean.{name}_feeding_evening
              
              - type: custom:mushroom-template-card
                primary: "Leckerli"
                secondary: "{{{{ states('counter.{name}_feeding_snack') }}}} mal"
                icon: mdi:food-croissant
                icon_color: "{{{{ 'green' if is_state('input_boolean.{name}_feeding_snack', 'on') else 'grey' }}}}"
                tap_action:
                  action: toggle
                  target:
                    entity_id: input_boolean.{name}_feeding_snack
          
          # Aktivitäten Sektion
          - type: custom:mushroom-template-card
            primary: "Gartengang"
            secondary: "{{{{ states('counter.{name}_outside') }}}} mal heute"
            icon: mdi:door-open
            icon_color: "{{{{ 'green' if is_state('input_boolean.{name}_outside', 'on') else 'blue' }}}}"
            tap_action:
              action: toggle
              target:
                entity_id: input_boolean.{name}_outside
          
          # Besuchermodus
          - type: custom:mushroom-template-card
            primary: "Besuchshund"
            secondary: "{{{{ 'Aktiv' if is_state('input_boolean.{name}_visitor_mode', 'on') else 'Inaktiv' }}}}"
            icon: mdi:account-group
            icon_color: "{{{{ 'orange' if is_state('input_boolean.{name}_visitor_mode', 'on') else 'grey' }}}}"
            tap_action:
              action: toggle
              target:
                entity_id: input_boolean.{name}_visitor_mode
          
          # Aktionen
          - type: horizontal-stack
            cards:
              - type: custom:mushroom-template-card
                primary: "Fütterung"
                secondary: "Erinnerung senden"
                icon: mdi:bell
                icon_color: blue
                tap_action:
                  action: call-service
                  service: hundesystem.trigger_feeding_reminder
                  service_data:
                    meal_type: morning
              
              - type: custom:mushroom-template-card
                primary: "Reset"
                secondary: "Tagesstatistik"
                icon: mdi:restart
                icon_color: red
                tap_action:
                  action: call-service
                  service: hundesystem.daily_reset
                confirmation:
                  text: "Wirklich alle Statistiken zurücksetzen?"

  - title: Statistiken
    path: statistics
    icon: mdi:chart-line
    cards:
      - type: vertical-stack
        cards:
          # Fütterungsstatistiken
          - type: entities
            title: "Fütterungen Heute"
            entities:
              - entity: counter.{name}_feeding_morning
                name: "Frühstück"
                icon: mdi:weather-sunrise
              - entity: counter.{name}_feeding_lunch
                name: "Mittagessen"
                icon: mdi:weather-sunny
              - entity: counter.{name}_feeding_evening
                name: "Abendessen"
                icon: mdi:weather-sunset
              - entity: counter.{name}_feeding_snack
                name: "Leckerli"
                icon: mdi:food-croissant
          
          # Aktivitätsstatistiken
          - type: entities
            title: "Aktivitäten Heute"
            entities:
              - entity: counter.{name}_outside
                name: "Gartengang"
                icon: mdi:door-open
          
          # Status Übersicht
          - type: entities
            title: "Status"
            entities:
              - entity: input_boolean.{name}_feeding_morning
                name: "Frühstück erledigt"
              - entity: input_boolean.{name}_feeding_lunch
                name: "Mittag erledigt"
              - entity: input_boolean.{name}_feeding_evening
                name: "Abend erledigt"
              - entity: input_boolean.{name}_feeding_snack
                name: "Leckerli gegeben"
              - entity: input_boolean.{name}_outside
                name: "War draußen"
              - entity: input_boolean.{name}_visitor_mode
                name: "Besuchsmodus"

  - title: Notizen
    path: notes
    icon: mdi:note-text
    cards:
      - type: entities
        title: "Notizen zu {name.title()}"
        entities:
          - entity: input_text.{name}_notes
            name: "Notizen"
          - entity: input_datetime.{name}_morning_time
            name: "Frühstück Zeit"
          - entity: input_datetime.{name}_lunch_time
            name: "Mittag Zeit"
          - entity: input_datetime.{name}_evening_time
            name: "Abend Zeit"
          - entity: input_datetime.{name}_snack_time
            name: "Leckerli Zeit"
"""
    
    # Dashboard-Datei speichern
    dashboard_path = hass.config.path("dashboards")
    os.makedirs(dashboard_path, exist_ok=True)
    
    dashboard_file = os.path.join(dashboard_path, f"hundesystem_{name}.yaml")
    
    try:
        with open(dashboard_file, "w", encoding="utf-8") as f:
            f.write(dashboard_config)
        
        _LOGGER.info("Dashboard created at: %s", dashboard_file)
        
        # Optional: Register dashboard in Home Assistant
        # This would require additional integration with dashboard system
        
    except Exception as e:
        _LOGGER.error("Failed to create dashboard file: %s", e)
        raise