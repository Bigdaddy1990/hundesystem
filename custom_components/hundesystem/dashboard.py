"""Dashboard creation for Hundesystem."""
import logging
import os
from typing import Any, Dict
from homeassistant.core import HomeAssistant

from .const import CONF_DOG_NAME, MEAL_TYPES, ACTIVITY_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_create_dashboard(hass: HomeAssistant, dog_name: str, config: Dict[str, Any]) -> None:
    """Create a comprehensive dashboard for the dog system."""
    
    try:
        # Create main dashboard
        main_dashboard = await _generate_main_dashboard(dog_name, config)
        await _save_dashboard(hass, f"hundesystem_{dog_name}", main_dashboard)
        
        # Create mobile dashboard (simplified)
        mobile_dashboard = await _generate_mobile_dashboard(dog_name, config)
        await _save_dashboard(hass, f"hundesystem_{dog_name}_mobile", mobile_dashboard)
        
        # Create admin dashboard
        admin_dashboard = await _generate_admin_dashboard(dog_name, config)
        await _save_dashboard(hass, f"hundesystem_{dog_name}_admin", admin_dashboard)
        
        _LOGGER.info("All dashboards created successfully for %s", dog_name)
        
    except Exception as e:
        _LOGGER.error("Failed to create dashboards for %s: %s", dog_name, e)
        raise


async def _generate_main_dashboard(dog_name: str, config: Dict[str, Any]) -> str:
    """Generate the main comprehensive dashboard."""
    
    dashboard_config = f"""
# 🐶 Hundesystem Dashboard für {dog_name.title()}
# Automatisch generiert von der Hundesystem Integration
# Version: 2.0 - Vollständig erweitert

title: "🐶 {dog_name.title()} - Hundesystem"
theme: Backend-selected
background: var(--lovelace-background)

views:
  - title: Übersicht
    path: overview
    icon: mdi:dog
    panel: false
    cards:
      # Header Card mit Hundestatus
      - type: custom:mushroom-template-card
        primary: "{dog_name.title()}"
        secondary: "{{{{ states('sensor.{dog_name}_status') }}}}"
        icon: mdi:dog
        icon_color: >-
          {{% set status = states('sensor.{dog_name}_status') %}}
          {{% if 'Notfall' in status %}} red
          {{% elif 'Aufmerksamkeit' in status %}} orange
          {{% elif 'Besuchsmodus' in status %}} purple
          {{% elif 'Alles in Ordnung' in status %}} green
          {{% else %}} blue {{% endif %}}
        badge_icon: >-
          {{% if is_state('binary_sensor.{dog_name}_needs_attention', 'on') %}} mdi:alert-circle
          {{% elif is_state('binary_sensor.{dog_name}_visitor_mode', 'on') %}} mdi:account-group
          {{% elif is_state('binary_sensor.{dog_name}_feeding_complete', 'on') %}} mdi:check-circle
          {{% endif %}}
        badge_color: >-
          {{% if is_state('binary_sensor.{dog_name}_needs_attention', 'on') %}} red
          {{% elif is_state('binary_sensor.{dog_name}_visitor_mode', 'on') %}} purple
          {{% elif is_state('binary_sensor.{dog_name}_feeding_complete', 'on') %}} green
          {{% endif %}}
        tap_action:
          action: more-info
        hold_action:
          action: navigate
          navigation_path: /lovelace-hundesystem-{dog_name}/admin

      # Schnellaktionen
      - type: horizontal-stack
        cards:
          - type: custom:mushroom-template-card
            primary: "Draußen"
            secondary: "{{{{ states('counter.{dog_name}_outside_count') }}}}x heute"
            icon: mdi:door-open
            icon_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_outside', 'on') else 'blue' }}}}"
            tap_action:
              action: call-service
              service: input_boolean.toggle
              target:
                entity_id: input_boolean.{dog_name}_outside
              confirmation:
                text: "War {dog_name.title()} draußen?"
          
          - type: custom:mushroom-template-card
            primary: "Geschäft"
            secondary: "{{{{ states('counter.{dog_name}_poop_count') }}}}x heute"
            icon: mdi:emoticon-poop
            icon_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_poop_done', 'on') else 'brown' }}}}"
            tap_action:
              action: call-service
              service: input_boolean.toggle
              target:
                entity_id: input_boolean.{dog_name}_poop_done

      # Fütterungsbereich
      - type: custom:mushroom-title-card
        title: "🍽️ Fütterung"
        subtitle: "Mahlzeiten und Fütterungszeiten"

      - type: grid
        columns: 2
        square: false
        cards:
          - type: custom:mushroom-template-card
            primary: "Frühstück"
            secondary: >-
              {{{{ states('counter.{dog_name}_feeding_morning_count') }}}}x
              {{% if states('input_datetime.{dog_name}_last_feeding_morning') != 'unknown' %}}
              - {{{{ as_timestamp(states('input_datetime.{dog_name}_last_feeding_morning')) | timestamp_custom('%H:%M') }}}}
              {{% endif %}}
            icon: mdi:weather-sunrise
            icon_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_feeding_morning', 'on') else 'orange' }}}}"
            badge_icon: "{{{{ 'mdi:check' if is_state('input_boolean.{dog_name}_feeding_morning', 'on') else 'mdi:clock' }}}}"
            badge_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_feeding_morning', 'on') else 'orange' }}}}"
            tap_action:
              action: call-service
              service: input_boolean.toggle
              target:
                entity_id: input_boolean.{dog_name}_feeding_morning
            hold_action:
              action: call-service
              service: hundesystem.trigger_feeding_reminder
              data:
                meal_type: morning
                dog_name: {dog_name}

          - type: custom:mushroom-template-card
            primary: "Mittagessen"
            secondary: >-
              {{{{ states('counter.{dog_name}_feeding_lunch_count') }}}}x
              {{% if states('input_datetime.{dog_name}_last_feeding_lunch') != 'unknown' %}}
              - {{{{ as_timestamp(states('input_datetime.{dog_name}_last_feeding_lunch')) | timestamp_custom('%H:%M') }}}}
              {{% endif %}}
            icon: mdi:weather-sunny
            icon_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_feeding_lunch', 'on') else 'orange' }}}}"
            badge_icon: "{{{{ 'mdi:check' if is_state('input_boolean.{dog_name}_feeding_lunch', 'on') else 'mdi:clock' }}}}"
            badge_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_feeding_lunch', 'on') else 'orange' }}}}"
            tap_action:
              action: call-service
              service: input_boolean.toggle
              target:
                entity_id: input_boolean.{dog_name}_feeding_lunch
            hold_action:
              action: call-service
              service: hundesystem.trigger_feeding_reminder
              data:
                meal_type: lunch
                dog_name: {dog_name}

          - type: custom:mushroom-template-card
            primary: "Abendessen"
            secondary: >-
              {{{{ states('counter.{dog_name}_feeding_evening_count') }}}}x
              {{% if states('input_datetime.{dog_name}_last_feeding_evening') != 'unknown' %}}
              - {{{{ as_timestamp(states('input_datetime.{dog_name}_last_feeding_evening')) | timestamp_custom('%H:%M') }}}}
              {{% endif %}}
            icon: mdi:weather-sunset
            icon_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_feeding_evening', 'on') else 'orange' }}}}"
            badge_icon: "{{{{ 'mdi:check' if is_state('input_boolean.{dog_name}_feeding_evening', 'on') else 'mdi:clock' }}}}"
            badge_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_feeding_evening', 'on') else 'orange' }}}}"
            tap_action:
              action: call-service
              service: input_boolean.toggle
              target:
                entity_id: input_boolean.{dog_name}_feeding_evening
            hold_action:
              action: call-service
              service: hundesystem.trigger_feeding_reminder
              data:
                meal_type: evening
                dog_name: {dog_name}

          - type: custom:mushroom-template-card
            primary: "Leckerli"
            secondary: >-
              {{{{ states('counter.{dog_name}_feeding_snack_count') }}}}x
              {{% if states('input_datetime.{dog_name}_last_feeding_snack') != 'unknown' %}}
              - {{{{ as_timestamp(states('input_datetime.{dog_name}_last_feeding_snack')) | timestamp_custom('%H:%M') }}}}
              {{% endif %}}
            icon: mdi:food-croissant
            icon_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_feeding_snack', 'on') else 'grey' }}}}"
            badge_icon: "{{{{ 'mdi:check' if is_state('input_boolean.{dog_name}_feeding_snack', 'on') else 'mdi:plus' }}}}"
            badge_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_feeding_snack', 'on') else 'blue' }}}}"
            tap_action:
              action: call-service
              service: input_boolean.toggle
              target:
                entity_id: input_boolean.{dog_name}_feeding_snack
            hold_action:
              action: call-service
              service: hundesystem.trigger_feeding_reminder
              data:
                meal_type: snack
                dog_name: {dog_name}

      # Aktivitätsbereich
      - type: custom:mushroom-title-card
        title: "🎾 Aktivitäten"
        subtitle: "Bewegung und Beschäftigung"

      - type: horizontal-stack
        cards:
          - type: custom:mushroom-template-card
            primary: "Gassi"
            secondary: "{{{{ states('counter.{dog_name}_walk_count') }}}}x heute"
            icon: mdi:walk
            icon_color: blue
            tap_action:
              action: call-service
              service: hundesystem.log_activity
              data:
                activity_type: walk
                dog_name: {dog_name}
            hold_action:
              action: more-info
              entity_id: counter.{dog_name}_walk_count

          - type: custom:mushroom-template-card
            primary: "Spielen"
            secondary: "{{{{ states('counter.{dog_name}_play_count') }}}}x heute"
            icon: mdi:tennis-ball
            icon_color: green
            tap_action:
              action: call-service
              service: hundesystem.log_activity
              data:
                activity_type: play
                dog_name: {dog_name}

          - type: custom:mushroom-template-card
            primary: "Training"
            secondary: "{{{{ states('counter.{dog_name}_training_count') }}}}x heute"
            icon: mdi:school
            icon_color: purple
            tap_action:
              action: call-service
              service: hundesystem.log_activity
              data:
                activity_type: training
                dog_name: {dog_name}

      # Gesundheit & Besonders
      - type: grid
        columns: 2
        square: false
        cards:
          - type: custom:mushroom-template-card
            primary: "Besuchsmodus"
            secondary: >-
              {{{{ 'Aktiv' if is_state('input_boolean.{dog_name}_visitor_mode_input', 'on') else 'Inaktiv' }}}}
              {{% if states('input_text.{dog_name}_visitor_name') not in ['', 'unknown'] %}}
              - {{{{ states('input_text.{dog_name}_visitor_name') }}}}
              {{% endif %}}
            icon: mdi:account-group
            icon_color: "{{{{ 'orange' if is_state('input_boolean.{dog_name}_visitor_mode_input', 'on') else 'grey' }}}}"
            tap_action:
              action: call-service
              service: hundesystem.set_visitor_mode
              data:
                enabled: "{{{{ not is_state('input_boolean.{dog_name}_visitor_mode_input', 'on') }}}}"
                dog_name: {dog_name}

          - type: custom:mushroom-template-card
            primary: "Gesundheit"
            secondary: "{{{{ states('input_select.{dog_name}_health_status') | default('Gut', true) }}}}"
            icon: mdi:heart-pulse
            icon_color: >-
              {{% set health = states('input_select.{dog_name}_health_status') %}}
              {{% if health in ['Ausgezeichnet', 'Gut'] %}} green
              {{% elif health == 'Normal' %}} blue
              {{% elif health in ['Schwach', 'Krank'] %}} orange
              {{% elif health == 'Notfall' %}} red
              {{% else %}} grey {{% endif %}}
            tap_action:
              action: more-info
              entity_id: input_select.{dog_name}_health_status

      # Tageszusammenfassung
      - type: custom:mushroom-template-card
        primary: "Tageszusammenfassung"
        secondary: "{{{{ states('sensor.{dog_name}_daily_summary') }}}}"
        icon: mdi:calendar-today
        icon_color: blue
        tap_action:
          action: navigate
          navigation_path: /lovelace-hundesystem-{dog_name}/statistics

  - title: Statistiken
    path: statistics
    icon: mdi:chart-line
    cards:
      # Wochenübersicht
      - type: custom:mushroom-title-card
        title: "📊 Wochenstatistiken"
        subtitle: "Verlauf der letzten 7 Tage"

      - type: custom:mini-graph-card
        entities:
          - entity: counter.{dog_name}_feeding_morning_count
            name: Frühstück
            color: orange
          - entity: counter.{dog_name}_feeding_lunch_count
            name: Mittag
            color: yellow
          - entity: counter.{dog_name}_feeding_evening_count
            name: Abend
            color: red
        name: Fütterungen
        icon: mdi:food-variant
        hours_to_show: 168
        group_by: date
        aggregate_func: max
        smoothing: false

      - type: custom:mini-graph-card
        entities:
          - entity: counter.{dog_name}_outside_count
            name: Draußen
            color: green
          - entity: counter.{dog_name}_walk_count
            name: Gassi
            color: blue
          - entity: counter.{dog_name}_play_count
            name: Spielen
            color: purple
        name: Aktivitäten
        icon: mdi:run
        hours_to_show: 168
        group_by: date
        aggregate_func: max

      # Heute im Detail
      - type: custom:mushroom-title-card
        title: "📅 Heute im Detail"

      - type: entities
        title: "Fütterungen"
        show_header_toggle: false
        entities:
          - entity: input_boolean.{dog_name}_feeding_morning
            name: "Frühstück"
            secondary_info: last-updated
          - entity: input_boolean.{dog_name}_feeding_lunch
            name: "Mittagessen"
            secondary_info: last-updated
          - entity: input_boolean.{dog_name}_feeding_evening
            name: "Abendessen"
            secondary_info: last-updated
          - entity: input_boolean.{dog_name}_feeding_snack
            name: "Leckerli"
            secondary_info: last-updated

      - type: entities
        title: "Aktivitäten"
        show_header_toggle: false
        entities:
          - entity: counter.{dog_name}_outside_count
            name: "Mal draußen"
          - entity: counter.{dog_name}_walk_count
            name: "Gassi Runden"
          - entity: counter.{dog_name}_play_count
            name: "Spielsessions"
          - entity: counter.{dog_name}_training_count
            name: "Training"
          - entity: counter.{dog_name}_poop_count
            name: "Geschäfte"

      # Gesundheitstrends
      - type: custom:mushroom-title-card
        title: "❤️ Gesundheit & Wohlbefinden"

      - type: entities
        title: "Aktuelle Werte"
        show_header_toggle: false
        entities:
          - entity: input_select.{dog_name}_health_status
            name: "Gesundheitsstatus"
          - entity: input_select.{dog_name}_mood
            name: "Stimmung"
          - entity: input_select.{dog_name}_energy_level_category
            name: "Energie Level"
          - entity: input_select.{dog_name}_appetite_level
            name: "Appetit"

  - title: Gesundheit
    path: health
    icon: mdi:heart-pulse
    cards:
      # Gesundheitsübersicht
      - type: custom:mushroom-template-card
        primary: "Gesundheitsstatus"
        secondary: "{{{{ states('input_select.{dog_name}_health_status') }}}}"
        icon: mdi:heart-pulse
        icon_color: >-
          {{% set health = states('input_select.{dog_name}_health_status') %}}
          {{% if health in ['Ausgezeichnet', 'Gut'] %}} green
          {{% elif health == 'Normal' %}} blue
          {{% elif health in ['Schwach', 'Krank'] %}} orange
          {{% elif health == 'Notfall' %}} red
          {{% else %}} grey {{% endif %}}
        badge_icon: >-
          {{% if is_state('input_boolean.{dog_name}_emergency_mode', 'on') %}} mdi:alarm-light
          {{% elif is_state('input_boolean.{dog_name}_medication_given', 'on') %}} mdi:pill
          {{% endif %}}
        badge_color: >-
          {{% if is_state('input_boolean.{dog_name}_emergency_mode', 'on') %}} red
          {{% elif is_state('input_boolean.{dog_name}_medication_given', 'on') %}} blue
          {{% endif %}}

      # Gesundheitswerte
      - type: grid
        columns: 2
        square: false
        cards:
          - type: custom:mushroom-number-card
            entity: input_number.{dog_name}_weight
            name: "Gewicht"
            icon: mdi:weight-kilogram
            display_mode: buttons

          - type: custom:mushroom-number-card
            entity: input_number.{dog_name}_temperature
            name: "Temperatur"
            icon: mdi:thermometer
            display_mode: buttons

          - type: custom:mushroom-number-card
            entity: input_number.{dog_name}_health_score
            name: "Gesundheits-Score"
            icon: mdi:heart-pulse
            display_mode: slider

          - type: custom:mushroom-number-card
            entity: input_number.{dog_name}_energy_level
            name: "Energie Level"
            icon: mdi:flash
            display_mode: slider

      # Medikamente
      - type: custom:mushroom-title-card
        title: "💊 Medikamente & Behandlung"

      - type: entities
        entities:
          - entity: input_boolean.{dog_name}_medication_given
            name: "Medikament gegeben"
            icon: mdi:pill
          - entity: input_datetime.{dog_name}_medication_time
            name: "Medikamenten-Zeit"
          - entity: input_text.{dog_name}_medication_notes
            name: "Medikamenten-Notizen"

      # Tierarzttermine
      - type: custom:mushroom-title-card
        title: "🏥 Tierarzttermine"

      - type: entities
        entities:
          - entity: input_datetime.{dog_name}_last_vet_visit
            name: "Letzter Tierarztbesuch"
          - entity: input_datetime.{dog_name}_next_vet_appointment
            name: "Nächster Termin"
          - entity: input_datetime.{dog_name}_last_vaccination
            name: "Letzte Impfung"
          - entity: input_datetime.{dog_name}_next_vaccination
            name: "Nächste Impfung"
          - entity: input_text.{dog_name}_vet_notes
            name: "Tierarzt Notizen"

      # Notfallkontakte
      - type: custom:mushroom-title-card
        title: "🚨 Notfallkontakte"

      - type: entities
        entities:
          - entity: input_text.{dog_name}_emergency_contact
            name: "Notfallkontakt"
          - entity: input_text.{dog_name}_vet_contact
            name: "Tierarzt Kontakt"
          - entity: input_text.{dog_name}_backup_contact
            name: "Ersatzkontakt"

  - title: Notizen
    path: notes
    icon: mdi:note-text
    cards:
      # Tagesnotizen
      - type: custom:mushroom-title-card
        title: "📝 Notizen & Beobachtungen"

      - type: entities
        title: "Allgemeine Notizen"
        entities:
          - entity: input_text.{dog_name}_notes
            name: "Allgemeine Notizen"
          - entity: input_text.{dog_name}_daily_notes
            name: "Tagesnotizen"
          - entity: input_text.{dog_name}_behavior_notes
            name: "Verhaltensnotizen"

      # Aktivitätsnotizen
      - type: entities
        title: "Aktivitätsnotizen"
        entities:
          - entity: input_text.{dog_name}_last_activity_notes
            name: "Letzte Aktivität"
          - entity: input_text.{dog_name}_walk_notes
            name: "Spaziergang Notizen"
          - entity: input_text.{dog_name}_play_notes
            name: "Spiel Notizen"
          - entity: input_text.{dog_name}_training_notes
            name: "Training Notizen"

      # Hundeinfos
      - type: entities
        title: "Hundeinformationen"
        entities:
          - entity: input_text.{dog_name}_breed
            name: "Rasse"
          - entity: input_text.{dog_name}_color
            name: "Farbe"
          - entity: input_text.{dog_name}_microchip_id
            name: "Mikrochip ID"
          - entity: input_text.{dog_name}_insurance_number
            name: "Versicherung"

      # Futter & Vorlieben
      - type: entities
        title: "Futter & Vorlieben"
        entities:
          - entity: input_text.{dog_name}_food_brand
            name: "Futtermarke"
          - entity: input_text.{dog_name}_food_allergies
            name: "Allergien"
          - entity: input_text.{dog_name}_favorite_treats
            name: "Lieblingsleckerli"

  - title: Admin
    path: admin
    icon: mdi:cog
    cards:
      # Systemsteuerung
      - type: custom:mushroom-title-card
        title: "⚙️ Systemsteuerung"
        subtitle: "Administration und Einstellungen"

      # Schnellaktionen
      - type: grid
        columns: 3
        square: false
        cards:
          - type: custom:mushroom-template-card
            primary: "Tagesreset"
            secondary: "Statistiken zurücksetzen"
            icon: mdi:restart
            icon_color: red
            tap_action:
              action: call-service
              service: hundesystem.daily_reset
              data:
                dog_name: {dog_name}
              confirmation:
                text: "Wirklich alle Tagesstatistiken zurücksetzen?"

          - type: custom:mushroom-template-card
            primary: "Test Push"
            secondary: "Benachrichtigung testen"
            icon: mdi:test-tube
            icon_color: blue
            tap_action:
              action: call-service
              service: hundesystem.test_notification
              data:
                dog_name: {dog_name}

          - type: custom:mushroom-template-card
            primary: "Notfall"
            secondary: "Notfallmodus aktivieren"
            icon: mdi:alarm-light
            icon_color: red
            tap_action:
              action: call-service
              service: input_boolean.toggle
              target:
                entity_id: input_boolean.{dog_name}_emergency_mode
              confirmation:
                text: "Notfallmodus aktivieren?"

      # Systemstatus
      - type: entities
        title: "Systemstatus"
        show_header_toggle: false
        entities:
          - entity: binary_sensor.{dog_name}_feeding_complete
            name: "Fütterung komplett"
          - entity: binary_sensor.{dog_name}_daily_tasks_complete
            name: "Tagesaufgaben komplett"
          - entity: binary_sensor.{dog_name}_needs_attention
            name: "Braucht Aufmerksamkeit"
          - entity: binary_sensor.{dog_name}_visitor_mode
            name: "Besuchsmodus aktiv"

      # Einstellungen
      - type: entities
        title: "Einstellungen"
        entities:
          - entity: input_boolean.{dog_name}_auto_reminders
            name: "Automatische Erinnerungen"
          - entity: input_boolean.{dog_name}_tracking_enabled
            name: "Tracking aktiviert"
          - entity: input_boolean.{dog_name}_weather_alerts
            name: "Wetter-Warnungen"

      # Services zum Testen
      - type: custom:mushroom-title-card
        title: "🧪 Service Tests"

      - type: grid
        columns: 2
        square: false
        cards:
          - type: custom:mushroom-template-card
            primary: "Fütterungserinnerung"
            secondary: "Morgen"
            icon: mdi:bell-ring
            icon_color: orange
            tap_action:
              action: call-service
              service: hundesystem.trigger_feeding_reminder
              data:
                meal_type: morning
                dog_name: {dog_name}

          - type: custom:mushroom-template-card
            primary: "Aktivität loggen"
            secondary: "Spaziergang"
            icon: mdi:walk
            icon_color: green
            tap_action:
              action: call-service
              service: hundesystem.log_activity
              data:
                activity_type: walk
                dog_name: {dog_name}
                notes: "Test Spaziergang vom Dashboard"
"""

    return dashboard_config


async def _generate_mobile_dashboard(dog_name: str, config: Dict[str, Any]) -> str:
    """Generate a simplified mobile dashboard."""
    
    mobile_dashboard = f"""
# 📱 Mobile Dashboard für {dog_name.title()}
# Optimiert für Smartphone-Nutzung

title: "📱 {dog_name.title()}"
theme: Backend-selected

views:
  - title: Home
    path: mobile_home
    icon: mdi:home
    panel: false
    cards:
      # Status Header
      - type: custom:mushroom-template-card
        primary: "{dog_name.title()}"
        secondary: "{{{{ states('sensor.{dog_name}_status') }}}}"
        icon: mdi:dog
        icon_color: auto
        layout: horizontal

      # Quick Actions
      - type: grid
        columns: 2
        square: true
        cards:
          - type: custom:mushroom-template-card
            primary: "Draußen"
            icon: mdi:door-open
            icon_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_outside', 'on') else 'blue' }}}}"
            tap_action:
              action: toggle
              entity_id: input_boolean.{dog_name}_outside

          - type: custom:mushroom-template-card
            primary: "Geschäft"
            icon: mdi:emoticon-poop
            icon_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_poop_done', 'on') else 'brown' }}}}"
            tap_action:
              action: toggle
              entity_id: input_boolean.{dog_name}_poop_done

          - type: custom:mushroom-template-card
            primary: "Frühstück"
            icon: mdi:weather-sunrise
            icon_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_feeding_morning', 'on') else 'orange' }}}}"
            tap_action:
              action: toggle
              entity_id: input_boolean.{dog_name}_feeding_morning

          - type: custom:mushroom-template-card
            primary: "Abendessen"
            icon: mdi:weather-sunset
            icon_color: "{{{{ 'green' if is_state('input_boolean.{dog_name}_feeding_evening', 'on') else 'orange' }}}}"
            tap_action:
              action: toggle
              entity_id: input_boolean.{dog_name}_feeding_evening

      # Today Summary
      - type: custom:mushroom-template-card
        primary: "Heute"
        secondary: "{{{{ states('sensor.{dog_name}_daily_summary') }}}}"
        icon: mdi:calendar-today
        icon_color: blue
        layout: horizontal
"""

    return mobile_dashboard


async def _generate_admin_dashboard(dog_name: str, config: Dict[str, Any]) -> str:
    """Generate an admin dashboard for advanced management."""
    
    admin_dashboard = f"""
# 🛠️ Admin Dashboard für {dog_name.title()}
# Erweiterte Verwaltung und Systemkontrolle

title: "🛠️ {dog_name.title()} Admin"
theme: Backend-selected

views:
  - title: System
    path: admin_system
    icon: mdi:cog
    cards:
      # System Overview
      - type: custom:mushroom-title-card
        title: "System Übersicht"
        subtitle: "Status aller Komponenten"

      - type: glance
        entities:
          - entity: binary_sensor.{dog_name}_feeding_complete
            name: "Fütterung"
          - entity: binary_sensor.{dog_name}_daily_tasks_complete
            name: "Aufgaben"
          - entity: binary_sensor.{dog_name}_needs_attention
            name: "Aufmerksamkeit"
          - entity: binary_sensor.{dog_name}_visitor_mode
            name: "Besuchsmodus"

      # All Counters
      - type: entities
        title: "Alle Zähler"
        show_header_toggle: false
        entities:
          - counter.{dog_name}_feeding_morning_count
          - counter.{dog_name}_feeding_lunch_count
          - counter.{dog_name}_feeding_evening_count
          - counter.{dog_name}_feeding_snack_count
          - counter.{dog_name}_outside_count
          - counter.{dog_name}_walk_count
          - counter.{dog_name}_play_count
          - counter.{dog_name}_training_count
          - counter.{dog_name}_poop_count

      # All Input Booleans
      - type: entities
        title: "Status Schalter"
        show_header_toggle: false
        entities:
          - input_boolean.{dog_name}_feeding_morning
          - input_boolean.{dog_name}_feeding_lunch
          - input_boolean.{dog_name}_feeding_evening
          - input_boolean.{dog_name}_feeding_snack
          - input_boolean.{dog_name}_outside
          - input_boolean.{dog_name}_was_dog
          - input_boolean.{dog_name}_poop_done
          - input_boolean.{dog_name}_visitor_mode_input
          - input_boolean.{dog_name}_emergency_mode

      # Service Testing
      - type: custom:mushroom-title-card
        title: "Service Tests"

      - type: horizontal-stack
        cards:
          - type: button
            name: "Daily Reset"
            icon: mdi:restart
            tap_action:
              action: call-service
              service: hundesystem.daily_reset
              data:
                dog_name: {dog_name}
              confirmation:
                text: "Reset all daily statistics?"

          - type: button
            name: "Test Notification"
            icon: mdi:test-tube
            tap_action:
              action: call-service
              service: hundesystem.test_notification
              data:
                dog_name: {dog_name}

          - type: button
            name: "Feeding Reminder"
            icon: mdi:bell-ring
            tap_action:
              action: call-service
              service: hundesystem.trigger_feeding_reminder
              data:
                meal_type: morning
                dog_name: {dog_name}
"""

    return admin_dashboard


async def _save_dashboard(hass: HomeAssistant, filename: str, content: str) -> None:
    """Save dashboard to file."""
    dashboard_path = hass.config.path("dashboards")
    os.makedirs(dashboard_path, exist_ok=True)
    
    dashboard_file = os.path.join(dashboard_path, f"{filename}.yaml")
    
    try:
        with open(dashboard_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        _LOGGER.info("Dashboard saved: %s", dashboard_file)
        
    except Exception as e:
        _LOGGER.error("Failed to save dashboard %s: %s", dashboard_file, e)
        raise