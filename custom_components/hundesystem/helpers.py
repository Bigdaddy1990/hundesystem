"""Helper functions for creating entities."""
import logging
import asyncio
from datetime import datetime
from homeassistant.core import HomeAssistant

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
    
    try:
        # Wait a moment for the system to be ready
        await asyncio.sleep(0.5)
        
        # Create input_boolean entities
        await _create_input_booleans(hass, dog_name)
        
        # Create counter entities  
        await _create_counters(hass, dog_name)
        
        # Create input_datetime entities
        await _create_input_datetimes(hass, dog_name)
        
        # Create input_text entities
        await _create_input_texts(hass, dog_name)
        
        # Create input_number entities
        await _create_input_numbers(hass, dog_name)
        
        # Create input_select entities
        await _create_input_selects(hass, dog_name)
        
        _LOGGER.info("All helper entities created successfully for %s", dog_name)
        
    except Exception as e:
        _LOGGER.error("Error creating helper entities for %s: %s", dog_name, e)
        raise


async def _create_input_booleans(hass: HomeAssistant, dog_name: str) -> None:
    """Create input_boolean entities."""
    
    boolean_entities = [
        # Feeding booleans
        (f"{dog_name}_feeding_morning", "Frühstück", ICONS["morning"]),
        (f"{dog_name}_feeding_lunch", "Mittagessen", ICONS["lunch"]),
        (f"{dog_name}_feeding_evening", "Abendessen", ICONS["evening"]),
        (f"{dog_name}_feeding_snack", "Leckerli", ICONS["snack"]),
        
        # Activity booleans
        (f"{dog_name}_outside", "War draußen", ICONS["outside"]),
        (f"{dog_name}_poop_done", "Geschäft gemacht", ICONS["poop"]),
        
        # Status booleans
        (f"{dog_name}_visitor_mode_input", "Besuchsmodus", ICONS["visitor"]),
        (f"{dog_name}_emergency_mode", "Notfallmodus", ICONS["emergency"]),
        (f"{dog_name}_medication_given", "Medikament gegeben", ICONS["medication"]),
        
        # Health booleans
        (f"{dog_name}_feeling_well", "Fühlt sich wohl", ICONS["health"]),
        (f"{dog_name}_appetite_normal", "Normaler Appetit", ICONS["food"]),
        (f"{dog_name}_energy_normal", "Normale Energie", ICONS["play"]),
        
        # Special features
        (f"{dog_name}_auto_reminders", "Automatische Erinnerungen", ICONS["bell"]),
        (f"{dog_name}_tracking_enabled", "Tracking aktiviert", ICONS["status"]),
        (f"{dog_name}_weather_alerts", "Wetter-Warnungen", "mdi:weather-partly-cloudy"),
    ]
    
    for entity_name, friendly_name, icon in boolean_entities:
        entity_id = f"input_boolean.{entity_name}"
        
        # Check if entity already exists
        if hass.states.get(entity_id) is None:
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
                # Small delay between creations
                await asyncio.sleep(0.1)
                
            except Exception as e:
                _LOGGER.warning("Failed to create input_boolean %s: %s", entity_id, e)


async def _create_counters(hass: HomeAssistant, dog_name: str) -> None:
    """Create counter entities."""
    
    counter_entities = [
        # Feeding counters
        (f"{dog_name}_feeding_morning_count", "Frühstück Zähler", ICONS["morning"]),
        (f"{dog_name}_feeding_lunch_count", "Mittagessen Zähler", ICONS["lunch"]),
        (f"{dog_name}_feeding_evening_count", "Abendessen Zähler", ICONS["evening"]),
        (f"{dog_name}_feeding_snack_count", "Leckerli Zähler", ICONS["snack"]),
        
        # Activity counters
        (f"{dog_name}_outside_count", "Draußen Zähler", ICONS["outside"]),
        (f"{dog_name}_walk_count", "Gassi Zähler", ICONS["walk"]),
        (f"{dog_name}_play_count", "Spiel Zähler", ICONS["play"]),
        (f"{dog_name}_training_count", "Training Zähler", ICONS["training"]),
        (f"{dog_name}_poop_count", "Geschäft Zähler", ICONS["poop"]),
        
        # Health counters
        (f"{dog_name}_vet_visits_count", "Tierarzt Besuche", ICONS["vet"]),
        (f"{dog_name}_medication_count", "Medikamente", ICONS["medication"]),
        (f"{dog_name}_grooming_count", "Pflege", ICONS["grooming"]),
        
        # Activity counters
        (f"{dog_name}_activity_count", "Aktivitäten", ICONS["status"]),
        
        # Emergency counters
        (f"{dog_name}_emergency_calls", "Notrufe", ICONS["emergency"]),
    ]
    
    for entity_name, friendly_name, icon in counter_entities:
        entity_id = f"counter.{entity_name}"
        
        if hass.states.get(entity_id) is None:
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
                await asyncio.sleep(0.1)
                
            except Exception as e:
                _LOGGER.warning("Failed to create counter %s: %s", entity_id, e)


async def _create_input_datetimes(hass: HomeAssistant, dog_name: str) -> None:
    """Create input_datetime entities."""
    
    # Feeding schedule times
    feeding_time_entities = []
    for meal_type in FEEDING_TYPES:
        feeding_time_entities.append((
            f"{dog_name}_feeding_{meal_type}_time",
            f"{MEAL_TYPES[meal_type]} Zeit",
            ICONS[meal_type],
            True,  # has_time
            False, # has_date
            DEFAULT_FEEDING_TIMES[meal_type]
        ))
    
    # Last activity timestamps
    last_activity_entities = [
        (f"{dog_name}_last_feeding_morning", "Letztes Frühstück", ICONS["morning"], True, True, None),
        (f"{dog_name}_last_feeding_lunch", "Letztes Mittagessen", ICONS["lunch"], True, True, None),
        (f"{dog_name}_last_feeding_evening", "Letztes Abendessen", ICONS["evening"], True, True, None),
        (f"{dog_name}_last_feeding_snack", "Letztes Leckerli", ICONS["snack"], True, True, None),
        (f"{dog_name}_last_outside", "Letzter Gartengang", ICONS["outside"], True, True, None),
        (f"{dog_name}_last_walk", "Letzter Spaziergang", ICONS["walk"], True, True, None),
        (f"{dog_name}_last_play", "Letztes Spielen", ICONS["play"], True, True, None),
        (f"{dog_name}_last_training", "Letztes Training", ICONS["training"], True, True, None),
        (f"{dog_name}_last_poop", "Letztes Geschäft", ICONS["poop"], True, True, None),
        (f"{dog_name}_last_activity", "Letzte Aktivität", ICONS["status"], True, True, None),
        (f"{dog_name}_last_door_ask", "Letzte Türfrage", "mdi:door", True, True, None),
    ]
    
    # Health & vet appointments
    health_entities = [
        (f"{dog_name}_last_vet_visit", "Letzter Tierarztbesuch", ICONS["vet"], True, True, None),
        (f"{dog_name}_next_vet_appointment", "Nächster Tierarzttermin", ICONS["vet"], True, True, None),
        (f"{dog_name}_last_vaccination", "Letzte Impfung", "mdi:needle", True, True, None),
        (f"{dog_name}_next_vaccination", "Nächste Impfung", "mdi:needle", True, True, None),
        (f"{dog_name}_medication_time", "Medikamentenzeit", ICONS["medication"], True, False, "08:00:00"),
        (f"{dog_name}_last_grooming", "Letzte Pflege", ICONS["grooming"], True, True, None),
        (f"{dog_name}_next_grooming", "Nächste Pflege", ICONS["grooming"], True, True, None),
    ]
    
    # Emergency & special events
    special_entities = [
        (f"{dog_name}_emergency_contact_time", "Notfall Kontakt Zeit", ICONS["emergency"], True, True, None),
        (f"{dog_name}_visitor_start", "Besuch Start", ICONS["visitor"], True, True, None),
        (f"{dog_name}_visitor_end", "Besuch Ende", ICONS["visitor"], True, True, None),
    ]
    
    all_datetime_entities = feeding_time_entities + last_activity_entities + health_entities + special_entities
    
    for entity_name, friendly_name, icon, has_time, has_date, initial in all_datetime_entities:
        entity_id = f"input_datetime.{entity_name}"
        
        if hass.states.get(entity_id) is None:
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
                await asyncio.sleep(0.1)
                
            except Exception as e:
                _LOGGER.warning("Failed to create input_datetime %s: %s", entity_id, e)


async def _create_input_texts(hass: HomeAssistant, dog_name: str) -> None:
    """Create input_text entities."""
    
    text_entities = [
        # Basic notes
        (f"{dog_name}_notes", "Notizen", ICONS["notes"], 255),
        (f"{dog_name}_daily_notes", "Tagesnotizen", ICONS["notes"], 255),
        (f"{dog_name}_behavior_notes", "Verhaltensnotizen", ICONS["notes"], 255),
        
        # Activity notes
        (f"{dog_name}_last_activity_notes", "Letzte Aktivität Notizen", ICONS["notes"], 255),
        (f"{dog_name}_walk_notes", "Spaziergang Notizen", ICONS["walk"], 255),
        (f"{dog_name}_play_notes", "Spiel Notizen", ICONS["play"], 255),
        (f"{dog_name}_training_notes", "Training Notizen", ICONS["training"], 255),
        
        # Visitor information
        (f"{dog_name}_visitor_name", "Besuchername", ICONS["visitor"], 100),
        (f"{dog_name}_visitor_contact", "Besucher Kontakt", ICONS["visitor"], 200),
        (f"{dog_name}_visitor_notes", "Besucher Notizen", ICONS["visitor"], 255),
        
        # Health information
        (f"{dog_name}_health_notes", "Gesundheitsnotizen", ICONS["health"], 255),
        (f"{dog_name}_medication_notes", "Medikamenten Notizen", ICONS["medication"], 255),
        (f"{dog_name}_vet_notes", "Tierarzt Notizen", ICONS["vet"], 255),
        (f"{dog_name}_symptoms", "Symptome", ICONS["health"], 255),
        
        # Emergency contacts
        (f"{dog_name}_emergency_contact", "Notfallkontakt", ICONS["emergency"], 200),
        (f"{dog_name}_vet_contact", "Tierarzt Kontakt", ICONS["vet"], 200),
        (f"{dog_name}_backup_contact", "Ersatzkontakt", "mdi:phone", 200),
        
        # Dog information
        (f"{dog_name}_breed", "Rasse", ICONS["dog"], 100),
        (f"{dog_name}_color", "Farbe", ICONS["dog"], 100),
        (f"{dog_name}_microchip_id", "Mikrochip ID", "mdi:chip", 50),
        (f"{dog_name}_insurance_number", "Versicherungsnummer", "mdi:shield", 100),
        
        # Food preferences
        (f"{dog_name}_food_brand", "Futtermarke", ICONS["food"], 100),
        (f"{dog_name}_food_allergies", "Futterallergien", ICONS["food"], 255),
        (f"{dog_name}_favorite_treats", "Lieblingsleckerli", ICONS["snack"], 255),
        
        # Special status
        (f"{dog_name}_current_mood", "Aktuelle Stimmung", ICONS["happy"], 50),
        (f"{dog_name}_weather_preference", "Wetter Präferenz", "mdi:weather-partly-cloudy", 100),
        (f"{dog_name}_special_instructions", "Besondere Anweisungen", ICONS["attention"], 255),
    ]
    
    for entity_name, friendly_name, icon, max_length in text_entities:
        entity_id = f"input_text.{entity_name}"
        
        if hass.states.get(entity_id) is None:
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
                await asyncio.sleep(0.1)
                
            except Exception as e:
                _LOGGER.warning("Failed to create input_text %s: %s", entity_id, e)


async def _create_input_numbers(hass: HomeAssistant, dog_name: str) -> None:
    """Create input_number entities for health and metrics."""
    
    number_entities = [
        # Health metrics
        (f"{dog_name}_weight", "Gewicht", "kg", 0.1, 0, 100, 10, "mdi:weight-kilogram"),
        (f"{dog_name}_temperature", "Körpertemperatur", "°C", 0.1, 35, 42, 38.5, ICONS["thermometer"]),
        (f"{dog_name}_heart_rate", "Herzfrequenz", "bpm", 1, 60, 200, 100, ICONS["health"]),
        
        # Activity metrics
        (f"{dog_name}_daily_walk_duration", "Tägliche Gehzeit", "min", 1, 0, 300, 60, ICONS["walk"]),
        (f"{dog_name}_daily_play_time", "Tägliche Spielzeit", "min", 1, 0, 180, 30, ICONS["play"]),
        (f"{dog_name}_training_duration", "Trainingszeit", "min", 1, 0, 120, 15, ICONS["training"]),
        
        # Food metrics
        (f"{dog_name}_daily_food_amount", "Tägliche Futtermenge", "g", 10, 0, 2000, 400, ICONS["food"]),
        (f"{dog_name}_treat_amount", "Leckerli Menge", "g", 1, 0, 200, 20, ICONS["snack"]),
        (f"{dog_name}_water_intake", "Wasseraufnahme", "ml", 50, 0, 3000, 500, "mdi:cup-water"),
        
        # Age and lifespan
        (f"{dog_name}_age_years", "Alter", "Jahre", 0.1, 0, 30, 5, ICONS["dog"]),
        (f"{dog_name}_age_months", "Alter", "Monate", 1, 0, 360, 60, ICONS["dog"]),
        
        # Medication dosage
        (f"{dog_name}_medication_dosage", "Medikamenten Dosierung", "mg", 0.5, 0, 500, 5, ICONS["medication"]),
        
        # Ratings
        (f"{dog_name}_health_score", "Gesundheits Score", "points", 1, 0, 10, 8, ICONS["health"]),
        (f"{dog_name}_happiness_score", "Glücks Score", "points", 1, 0, 10, 8, ICONS["happy"]),
        (f"{dog_name}_energy_level", "Energie Level", "points", 1, 0, 10, 7, ICONS["play"]),
        (f"{dog_name}_appetite_score", "Appetit Score", "points", 1, 0, 10, 8, ICONS["food"]),
    ]
    
    for entity_name, friendly_name, unit, step, min_val, max_val, initial, icon in number_entities:
        entity_id = f"input_number.{entity_name}"
        
        if hass.states.get(entity_id) is None:
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
                await asyncio.sleep(0.1)
                
            except Exception as e:
                _LOGGER.warning("Failed to create input_number %s: %s", entity_id, e)


async def _create_input_selects(hass: HomeAssistant, dog_name: str) -> None:
    """Create input_select entities for categorical choices."""
    
    select_entities = [
        # Activity level
        (f"{dog_name}_activity_level", "Aktivitätslevel", [
            "Sehr niedrig", "Niedrig", "Normal", "Hoch", "Sehr hoch"
        ], "Normal", ICONS["play"]),
        
        # Mood
        (f"{dog_name}_mood", "Stimmung", [
            "Sehr glücklich", "Glücklich", "Neutral", "Gestresst", "Ängstlich", "Krank"
        ], "Glücklich", ICONS["happy"]),
        
        # Weather preference
        (f"{dog_name}_weather_preference", "Wetter Präferenz", [
            "Sonnig", "Bewölkt", "Regen OK", "Schnee OK", "Alle Wetter"
        ], "Sonnig", "mdi:weather-sunny"),
        
        # Size category
        (f"{dog_name}_size_category", "Größenkategorie", [
            "Sehr klein", "Klein", "Mittel", "Groß", "Sehr groß"
        ], "Mittel", ICONS["dog"]),
        
        # Energy level
        (f"{dog_name}_energy_level_category", "Energie Level", [
            "Sehr müde", "Müde", "Normal", "Energiegeladen", "Hyperaktiv"
        ], "Normal", ICONS["play"]),
        
        # Appetite level
        (f"{dog_name}_appetite_level", "Appetit Level", [
            "Kein Appetit", "Wenig Appetit", "Normal", "Guter Appetit", "Sehr hungrig"
        ], "Normal", ICONS["food"]),
        
        # Health status
        (f"{dog_name}_health_status", "Gesundheitsstatus", [
            "Ausgezeichnet", "Gut", "Normal", "Schwach", "Krank", "Notfall"
        ], "Gut", ICONS["health"]),
        
        # Seasonal adjustment
        (f"{dog_name}_seasonal_mode", "Saisonaler Modus", [
            "Frühling", "Sommer", "Herbst", "Winter", "Automatisch"
        ], "Automatisch", "mdi:calendar"),
        
        # Training level
        (f"{dog_name}_training_level", "Trainingslevel", [
            "Anfänger", "Grundlagen", "Fortgeschritten", "Experte", "Champion"
        ], "Grundlagen", ICONS["training"]),
        
        # Emergency status
        (f"{dog_name}_emergency_level", "Notfall Level", [
            "Normal", "Aufmerksamkeit", "Warnung", "Dringend", "Kritisch"
        ], "Normal", ICONS["emergency"]),
    ]
    
    for entity_name, friendly_name, options, initial, icon in select_entities:
        entity_id = f"input_select.{entity_name}"
        
        if hass.states.get(entity_id) is None:
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
                await asyncio.sleep(0.1)
                
            except Exception as e:
                _LOGGER.warning("Failed to create input_select %s: %s", entity_id, e)
