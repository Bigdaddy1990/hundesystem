"""Helper functions for creating entities."""
import logging
from datetime import datetime
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    FEEDING_TYPES,
    MEAL_TYPES,
    ACTIVITY_TYPES,
    ICONS,
    DEFAULT_FEEDING_TIMES,
    ENTITIES,
)

_LOGGER = logging.getLogger(__name__)


async def async_create_helpers(hass: HomeAssistant, dog_name: str, config: dict) -> None:
    """Create all helper entities for the dog system."""
    entity_registry = er.async_get(hass)
    
    try:
        # Create input_boolean entities
        await _create_input_booleans(hass, entity_registry, dog_name)
        
        # Create counter entities
        await _create_counters(hass, entity_registry, dog_name)
        
        # Create input_datetime entities
        await _create_input_datetimes(hass, entity_registry, dog_name)
        
        # Create input_text entities
        await _create_input_texts(hass, entity_registry, dog_name)
        
        # Create input_number entities (for health tracking)
        await _create_input_numbers(hass, entity_registry, dog_name)
        
        # Create input_select entities
        await _create_input_selects(hass, entity_registry, dog_name)
        
        _LOGGER.info("All helper entities created successfully for %s", dog_name)
        
    except Exception as e:
        _LOGGER.error("Error creating helper entities for %s: %s", dog_name, e)
        raise


async def _create_input_booleans(hass: HomeAssistant, entity_registry, dog_name: str) -> None:
    """Create input_boolean entities."""
    
    boolean_entities = [
        # Feeding booleans
        ("feeding_morning", "Frühstück", ICONS["morning"]),
        ("feeding_lunch", "Mittagessen", ICONS["lunch"]),
        ("feeding_evening", "Abendessen", ICONS["evening"]),
        ("feeding_snack", "Leckerli", ICONS["snack"]),
        
        # Activity booleans
        ("outside", "War draußen", ICONS["outside"]),
        ("was_dog", "War es der Hund?", ICONS["dog"]),
        ("poop_done", "Geschäft gemacht", ICONS["poop"]),
        
        # Status booleans
        ("visitor_mode_input", "Besuchsmodus", ICONS["visitor"]),
        ("emergency_mode", "Notfallmodus", ICONS["emergency"]),
        ("medication_given", "Medikament gegeben", ICONS["medication"]),
        
        # Health booleans
        ("feeling_well", "Fühlt sich wohl", ICONS["health"]),
        ("appetite_normal", "Normaler Appetit", ICONS["food"]),
        ("energy_normal", "Normale Energie", ICONS["play"]),
        
        # Special features
        ("auto_reminders", "Automatische Erinnerungen", ICONS["bell"]),
        ("tracking_enabled", "Tracking aktiviert", ICONS["status"]),
        ("weather_alerts", "Wetter-Warnungen", "mdi:weather-partly-cloudy"),
    ]
    
    for suffix, friendly_name, icon in boolean_entities:
        entity_id = f"input_boolean.{dog_name}_{suffix}"
        
        if not entity_registry.async_get(entity_id):
            try:
                await hass.services.async_call(
                    "input_boolean", "create",
                    {
                        "name": f"{dog_name.title()} {friendly_name}",
                        "icon": icon,
                    },
                    blocking=True
                )
                _LOGGER.debug("Created input_boolean: %s", entity_id)
            except Exception as e:
                _LOGGER.warning("Failed to create input_boolean %s: %s", entity_id, e)


async def _create_counters(hass: HomeAssistant, entity_registry, dog_name: str) -> None:
    """Create counter entities."""
    
    counter_entities = [
        # Feeding counters
        ("feeding_morning_count", "Frühstück Zähler", ICONS["morning"]),
        ("feeding_lunch_count", "Mittagessen Zähler", ICONS["lunch"]),
        ("feeding_evening_count", "Abendessen Zähler", ICONS["evening"]),
        ("feeding_snack_count", "Leckerli Zähler", ICONS["snack"]),
        
        # Activity counters
        ("outside_count", "Draußen Zähler", ICONS["outside"]),
        ("walk_count", "Gassi Zähler", ICONS["walk"]),
        ("play_count", "Spiel Zähler", ICONS["play"]),
        ("training_count", "Training Zähler", ICONS["training"]),
        ("poop_count", "Geschäft Zähler", ICONS["poop"]),
        
        # Health counters
        ("vet_visits_count", "Tierarzt Besuche", ICONS["vet"]),
        ("medication_count", "Medikamente", ICONS["medication"]),
        ("grooming_count", "Pflege", ICONS["grooming"]),
        
        # Weekly/Monthly counters
        ("weekly_activities", "Wöchentliche Aktivitäten", ICONS["status"]),
        ("monthly_vet_visits", "Monatliche Tierarzt Besuche", ICONS["vet"]),
        
        # Emergency counters
        ("emergency_calls", "Notrufe", ICONS["emergency"]),
        ("missed_feedings", "Verpasste Fütterungen", ICONS["attention"]),
    ]
    
    for suffix, friendly_name, icon in counter_entities:
        entity_id = f"counter.{dog_name}_{suffix}"
        
        if not entity_registry.async_get(entity_id):
            try:
                await hass.services.async_call(
                    "counter", "create",
                    {
                        "name": f"{dog_name.title()} {friendly_name}",
                        "icon": icon,
                        "initial": 0,
                        "step": 1,
                        "minimum": 0,
                    },
                    blocking=True
                )
                _LOGGER.debug("Created counter: %s", entity_id)
            except Exception as e:
                _LOGGER.warning("Failed to create counter %s: %s", entity_id, e)


async def _create_input_datetimes(hass: HomeAssistant, entity_registry, dog_name: str) -> None:
    """Create input_datetime entities."""
    
    # Feeding schedule times
    feeding_time_entities = []
    for meal_type in FEEDING_TYPES:
        feeding_time_entities.append((
            f"feeding_{meal_type}_time",
            f"{MEAL_TYPES[meal_type]} Zeit",
            ICONS[meal_type],
            True,  # has_time
            False, # has_date
            DEFAULT_FEEDING_TIMES[meal_type]
        ))
    
    # Last activity timestamps
    last_activity_entities = [
        ("last_feeding_morning", "Letztes Frühstück", ICONS["morning"], True, True, None),
        ("last_feeding_lunch", "Letztes Mittagessen", ICONS["lunch"], True, True, None),
        ("last_feeding_evening", "Letztes Abendessen", ICONS["evening"], True, True, None),
        ("last_feeding_snack", "Letztes Leckerli", ICONS["snack"], True, True, None),
        ("last_outside", "Letzter Gartengang", ICONS["outside"], True, True, None),
        ("last_walk", "Letzter Spaziergang", ICONS["walk"], True, True, None),
        ("last_play", "Letztes Spielen", ICONS["play"], True, True, None),
        ("last_training", "Letztes Training", ICONS["training"], True, True, None),
        ("last_poop", "Letztes Geschäft", ICONS["poop"], True, True, None),
        ("last_activity", "Letzte Aktivität", ICONS["status"], True, True, None),
        ("last_door_ask", "Letzte Türfrage", "mdi:door", True, True, None),
    ]
    
    # Health & vet appointments
    health_entities = [
        ("last_vet_visit", "Letzter Tierarztbesuch", ICONS["vet"], True, True, None),
        ("next_vet_appointment", "Nächster Tierarzttermin", ICONS["vet"], True, True, None),
        ("last_vaccination", "Letzte Impfung", "mdi:needle", True, True, None),
        ("next_vaccination", "Nächste Impfung", "mdi:needle", True, True, None),
        ("medication_time", "Medikamentenzeit", ICONS["medication"], True, False, "08:00:00"),
        ("last_grooming", "Letzte Pflege", ICONS["grooming"], True, True, None),
        ("next_grooming", "Nächste Pflege", ICONS["grooming"], True, True, None),
    ]
    
    # Emergency & special events
    special_entities = [
        ("emergency_contact_time", "Notfall Kontakt Zeit", ICONS["emergency"], True, True, None),
        ("visitor_start", "Besuch Start", ICONS["visitor"], True, True, None),
        ("visitor_end", "Besuch Ende", ICONS["visitor"], True, True, None),
    ]
    
    all_datetime_entities = feeding_time_entities + last_activity_entities + health_entities + special_entities
    
    for suffix, friendly_name, icon, has_time, has_date, initial in all_datetime_entities:
        entity_id = f"input_datetime.{dog_name}_{suffix}"
        
        if not entity_registry.async_get(entity_id):
            try:
                datetime_config = {
                    "name": f"{dog_name.title()} {friendly_name}",
                    "icon": icon,
                    "has_time": has_time,
                    "has_date": has_date,
                }
                
                if initial:
                    if has_time and not has_date:
                        datetime_config["initial"] = initial
                    elif has_time and has_date:
                        datetime_config["initial"] = datetime.now().strftime(f"%Y-%m-%d {initial}")
                
                await hass.services.async_call(
                    "input_datetime", "create",
                    datetime_config,
                    blocking=True
                )
                _LOGGER.debug("Created input_datetime: %s", entity_id)
            except Exception as e:
                _LOGGER.warning("Failed to create input_datetime %s: %s", entity_id, e)


async def _create_input_texts(hass: HomeAssistant, entity_registry, dog_name: str) -> None:
    """Create input_text entities."""
    
    text_entities = [
        # Basic notes
        ("notes", "Notizen", ICONS["notes"], 255),
        ("daily_notes", "Tagesnotizen", ICONS["notes"], 255),
        ("behavior_notes", "Verhaltensnotizen", ICONS["notes"], 255),
        
        # Activity notes
        ("last_activity_notes", "Letzte Aktivität Notizen", ICONS["notes"], 255),
        ("walk_notes", "Spaziergang Notizen", ICONS["walk"], 255),
        ("play_notes", "Spiel Notizen", ICONS["play"], 255),
        ("training_notes", "Training Notizen", ICONS["training"], 255),
        
        # Visitor information
        ("visitor_name", "Besuchername", ICONS["visitor"], 100),
        ("visitor_contact", "Besucher Kontakt", ICONS["visitor"], 200),
        ("visitor_notes", "Besucher Notizen", ICONS["visitor"], 255),
        
        # Health information
        ("health_notes", "Gesundheitsnotizen", ICONS["health"], 255),
        ("medication_notes", "Medikamenten Notizen", ICONS["medication"], 255),
        ("vet_notes", "Tierarzt Notizen", ICONS["vet"], 255),
        ("symptoms", "Symptome", ICONS["health"], 255),
        
        # Emergency contacts
        ("emergency_contact", "Notfallkontakt", ICONS["emergency"], 200),
        ("vet_contact", "Tierarzt Kontakt", ICONS["vet"], 200),
        ("backup_contact", "Ersatzkontakt", "mdi:phone", 200),
        
        # Dog information
        ("breed", "Rasse", ICONS["dog"], 100),
        ("color", "Farbe", ICONS["dog"], 100),
        ("microchip_id", "Mikrochip ID", "mdi:chip", 50),
        ("insurance_number", "Versicherungsnummer", "mdi:shield", 100),
        
        # Food preferences
        ("food_brand", "Futtermarke", ICONS["food"], 100),
        ("food_allergies", "Futterallergien", ICONS["food"], 255),
        ("favorite_treats", "Lieblingsleckerli", ICONS["snack"], 255),
        
        # Special status
        ("current_mood", "Aktuelle Stimmung", ICONS["happy"], 50),
        ("weather_preference", "Wetter Präferenz", "mdi:weather-partly-cloudy", 100),
        ("special_instructions", "Besondere Anweisungen", ICONS["attention"], 255),
    ]
    
    for suffix, friendly_name, icon, max_length in text_entities:
        entity_id = f"input_text.{dog_name}_{suffix}"
        
        if not entity_registry.async_get(entity_id):
            try:
                await hass.services.async_call(
                    "input_text", "create",
                    {
                        "name": f"{dog_name.title()} {friendly_name}",
                        "icon": icon,
                        "max": max_length,
                        "initial": "",
                    },
                    blocking=True
                )
                _LOGGER.debug("Created input_text: %s", entity_id)
            except Exception as e:
                _LOGGER.warning("Failed to create input_text %s: %s", entity_id, e)


async def _create_input_numbers(hass: HomeAssistant, entity_registry, dog_name: str) -> None:
    """Create input_number entities for health and metrics."""
    
    number_entities = [
        # Health metrics
        ("weight", "Gewicht", "kg", 0.1, 0, 100, 10, "mdi:weight-kilogram"),
        ("temperature", "Körpertemperatur", "°C", 0.1, 35, 42, 38.5, ICONS["thermometer"]),
        ("heart_rate", "Herzfrequenz", "bpm", 1, 60, 200, 100, ICONS["health"]),
        
        # Activity metrics
        ("daily_walk_duration", "Tägliche Gehzeit", "min", 1, 0, 300, 60, ICONS["walk"]),
        ("daily_play_time", "Tägliche Spielzeit", "min", 1, 0, 180, 30, ICONS["play"]),
        ("training_duration", "Trainingszeit", "min", 1, 0, 120, 15, ICONS["training"]),
        
        # Food metrics
        ("daily_food_amount", "Tägliche Futtermenge", "g", 10, 0, 2000, 400, ICONS["food"]),
        ("treat_amount", "Leckerli Menge", "g", 1, 0, 200, 20, ICONS["snack"]),
        ("water_intake", "Wasseraufnahme", "ml", 50, 0, 3000, 500, "mdi:cup-water"),
        
        # Age and lifespan
        ("age_years", "Alter", "Jahre", 0.1, 0, 30, 5, ICONS["dog"]),
        ("age_months", "Alter", "Monate", 1, 0, 360, 60, ICONS["dog"]),
        
        # Medication dosage
        ("medication_dosage", "Medikamenten Dosierung", "mg", 0.5, 0, 500, 5, ICONS["medication"]),
        
        # Ratings
        ("health_score", "Gesundheits Score", "points", 1, 0, 10, 8, ICONS["health"]),
        ("happiness_score", "Glücks Score", "points", 1, 0, 10, 8, ICONS["happy"]),
        ("energy_level", "Energie Level", "points", 1, 0, 10, 7, ICONS["play"]),
        ("appetite_score", "Appetit Score", "points", 1, 0, 10, 8, ICONS["food"]),
    ]
    
    for suffix, friendly_name, unit, step, min_val, max_val, initial, icon in number_entities:
        entity_id = f"input_number.{dog_name}_{suffix}"
        
        if not entity_registry.async_get(entity_id):
            try:
                await hass.services.async_call(
                    "input_number", "create",
                    {
                        "name": f"{dog_name.title()} {friendly_name}",
                        "min": min_val,
                        "max": max_val,
                        "step": step,
                        "initial": initial,
                        "unit_of_measurement": unit,
                        "icon": icon,
                    },
                    blocking=True
                )
                _LOGGER.debug("Created input_number: %s", entity_id)
            except Exception as e:
                _LOGGER.warning("Failed to create input_number %s: %s", entity_id, e)


async def _create_input_selects(hass: HomeAssistant, entity_registry, dog_name: str) -> None:
    """Create input_select entities for categorical choices."""
    
    select_entities = [
        # Activity level
        ("activity_level", "Aktivitätslevel", [
            "Sehr niedrig", "Niedrig", "Normal", "Hoch", "Sehr hoch"
        ], "Normal", ICONS["play"]),
        
        # Mood
        ("mood", "Stimmung", [
            "Sehr glücklich", "Glücklich", "Neutral", "Gestresst", "Ängstlich", "Krank"
        ], "Glücklich", ICONS["happy"]),
        
        # Weather preference
        ("weather_preference", "Wetter Präferenz", [
            "Sonnig", "Bewölkt", "Regen OK", "Schnee OK", "Alle Wetter"
        ], "Sonnig", "mdi:weather-sunny"),
        
        # Size category
        ("size_category", "Größenkategorie", [
            "Sehr klein", "Klein", "Mittel", "Groß", "Sehr groß"
        ], "Mittel", ICONS["dog"]),
        
        # Energy level
        ("energy_level_category", "Energie Level", [
            "Sehr müde", "Müde", "Normal", "Energiegeladen", "Hyperaktiv"
        ], "Normal", ICONS["play"]),
        
        # Appetite level
        ("appetite_level", "Appetit Level", [
            "Kein Appetit", "Wenig Appetit", "Normal", "Guter Appetit", "Sehr hungrig"
        ], "Normal", ICONS["food"]),
        
        # Health status
        ("health_status", "Gesundheitsstatus", [
            "Ausgezeichnet", "Gut", "Normal", "Schwach", "Krank", "Notfall"
        ], "Gut", ICONS["health"]),
        
        # Seasonal adjustment
        ("seasonal_mode", "Saisonaler Modus", [
            "Frühling", "Sommer", "Herbst", "Winter", "Automatisch"
        ], "Automatisch", "mdi:calendar"),
        
        # Training level
        ("training_level", "Trainingslevel", [
            "Anfänger", "Grundlagen", "Fortgeschritten", "Experte", "Champion"
        ], "Grundlagen", ICONS["training"]),
        
        # Emergency status
        ("emergency_level", "Notfall Level", [
            "Normal", "Aufmerksamkeit", "Warnung", "Dringend", "Kritisch"
        ], "Normal", ICONS["emergency"]),
    ]
    
    for suffix, friendly_name, options, initial, icon in select_entities:
        entity_id = f"input_select.{dog_name}_{suffix}"
        
        if not entity_registry.async_get(entity_id):
            try:
                await hass.services.async_call(
                    "input_select", "create",
                    {
                        "name": f"{dog_name.title()} {friendly_name}",
                        "options": options,
                        "initial": initial,
                        "icon": icon,
                    },
                    blocking=True
                )
                _LOGGER.debug("Created input_select: %s", entity_id)
            except Exception as e:
                _LOGGER.warning("Failed to create input_select %s: %s", entity_id, e)