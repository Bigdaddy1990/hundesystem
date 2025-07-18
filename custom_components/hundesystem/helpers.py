"""Improved helper functions for creating entities with robust error handling."""
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

# Erhöhte Timeouts für langsamere Systeme
ENTITY_CREATION_TIMEOUT = 30.0  # Erhöht von 15s auf 30s
DOMAIN_CREATION_DELAY = 0.5     # Erhöht von 0.2s auf 0.5s
MAX_RETRIES_PER_ENTITY = 3      # Neu: Retry-Mechanismus


async def async_create_helpers(hass: HomeAssistant, dog_name: str, config: dict) -> None:
    """Create all helper entities for the dog system with improved error handling."""
    
    try:
        _LOGGER.info("Starting helper entity creation for %s", dog_name)
        
        # Wait a moment for the system to be ready
        await asyncio.sleep(1.0)  # Erhöht von 0.5s
        
        # Create entities in order with progress tracking
        creation_steps = [
            ("input_boolean", _create_input_booleans),
            ("counter", _create_counters),
            ("input_datetime", _create_input_datetimes),
            ("input_text", _create_input_texts),
            ("input_number", _create_input_numbers),
            ("input_select", _create_input_selects),
        ]
        
        total_steps = len(creation_steps)
        for step_num, (domain, creation_func) in enumerate(creation_steps, 1):
            _LOGGER.info("Step %d/%d: Creating %s entities for %s", 
                        step_num, total_steps, domain, dog_name)
            
            try:
                await creation_func(hass, dog_name)
                _LOGGER.info("✅ Successfully created %s entities", domain)
                
                # Pause between domains to avoid overwhelming the system
                if step_num < total_steps:
                    await asyncio.sleep(2.0)
                    
            except Exception as e:
                _LOGGER.error("❌ Failed to create %s entities: %s", domain, e)
                # Continue with other domains even if one fails
                continue
        
        _LOGGER.info("✅ Helper entity creation completed for %s", dog_name)
        
    except Exception as e:
        _LOGGER.error("❌ Critical error in helper entity creation for %s: %s", dog_name, e)
        raise


async def _create_helpers_for_domain_robust(
    hass: HomeAssistant, 
    domain: str, 
    entities: list, 
    dog_name: str
) -> dict:
    """Create helpers for a specific domain with comprehensive error handling."""
    
    results = {
        "created": 0,
        "skipped": 0,
        "failed": 0,
        "failed_entities": []
    }
    
    _LOGGER.info("Creating %d %s entities for %s", len(entities), domain, dog_name)
    
    for entity_data in entities:
        entity_name = entity_data[0]
        friendly_name = entity_data[1]
        entity_id = f"{domain}.{entity_name}"
        
        # Skip if already exists
        if hass.states.get(entity_id):
            _LOGGER.debug("Entity %s already exists, skipping", entity_id)
            results["skipped"] += 1
            continue
        
        # Retry mechanism for entity creation
        success = False
        for attempt in range(MAX_RETRIES_PER_ENTITY):
            try:
                service_data = _build_service_data(domain, entity_data, dog_name)
                
                # Service call with extended timeout
                await asyncio.wait_for(
                    hass.services.async_call(domain, "create", service_data, blocking=True),
                    timeout=ENTITY_CREATION_TIMEOUT
                )
                
                # Verify entity was actually created
                await asyncio.sleep(0.5)  # Give time for entity to appear
                if hass.states.get(entity_id):
                    _LOGGER.debug("✅ Created %s: %s", domain, entity_id)
                    results["created"] += 1
                    success = True
                    break
                else:
                    _LOGGER.warning("Entity %s not found after creation attempt %d", entity_id, attempt + 1)
                    
            except asyncio.TimeoutError:
                _LOGGER.warning("⏱️ Timeout creating %s (attempt %d/%d): %s", 
                               domain, attempt + 1, MAX_RETRIES_PER_ENTITY, entity_id)
            except Exception as e:
                _LOGGER.warning("❌ Error creating %s (attempt %d/%d): %s - %s", 
                               domain, attempt + 1, MAX_RETRIES_PER_ENTITY, entity_id, e)
            
            # Progressive delay between retries
            if attempt < MAX_RETRIES_PER_ENTITY - 1:
                await asyncio.sleep(1.0 * (attempt + 1))
        
        if not success:
            _LOGGER.error("❌ Failed to create %s after %d attempts: %s", 
                         domain, MAX_RETRIES_PER_ENTITY, entity_id)
            results["failed"] += 1
            results["failed_entities"].append(entity_id)
        else:
            # Small delay between successful creations
            await asyncio.sleep(DOMAIN_CREATION_DELAY)
    
    _LOGGER.info("Domain %s results for %s: %d created, %d skipped, %d failed", 
                 domain, dog_name, results["created"], results["skipped"], results["failed"])
    
    if results["failed_entities"]:
        _LOGGER.warning("Failed entities in %s: %s", domain, results["failed_entities"])
    
    return results


def _build_service_data(domain: str, entity_data: tuple, dog_name: str) -> dict:
    """Build service data for entity creation based on domain."""
    
    entity_name = entity_data[0]
    friendly_name = entity_data[1]
    
    service_data = {
        "name": f"{dog_name.title()} {friendly_name}",
    }
    
    if domain == "input_boolean":
        icon = entity_data[2] if len(entity_data) > 2 else "mdi:dog"
        service_data["icon"] = icon
        
    elif domain == "counter":
        icon = entity_data[2] if len(entity_data) > 2 else "mdi:counter"
        service_data.update({
            "initial": 0,
            "step": 1,
            "minimum": 0,
            "maximum": 999,  # Set reasonable maximum
            "icon": icon,
            "restore": True  # Preserve value across restarts
        })
        
    elif domain == "input_datetime":
        has_time, has_date, initial = entity_data[2], entity_data[3], entity_data[4]
        icon = entity_data[5] if len(entity_data) > 5 else "mdi:calendar-clock"
        service_data.update({
            "has_time": has_time,
            "has_date": has_date,
            "icon": icon
        })
        if initial:
            service_data["initial"] = initial
            
    elif domain == "input_text":
        max_length = entity_data[2]
        icon = entity_data[3] if len(entity_data) > 3 else "mdi:text"
        service_data.update({
            "max": max_length,
            "initial": "",
            "icon": icon,
            "mode": "text"  # Ensure text mode
        })
        
    elif domain == "input_number":
        step, min_val, max_val, initial, unit = entity_data[2:7]
        icon = entity_data[7] if len(entity_data) > 7 else "mdi:numeric"
        service_data.update({
            "min": min_val,
            "max": max_val,
            "step": step,
            "initial": initial,
            "unit_of_measurement": unit,
            "icon": icon,
            "mode": "slider"  # Default to slider mode
        })
        
    elif domain == "input_select":
        options, initial = entity_data[2], entity_data[3]
        icon = entity_data[4] if len(entity_data) > 4 else "mdi:format-list-bulleted"
        service_data.update({
            "options": options,
            "initial": initial,
            "icon": icon
        })
    
    return service_data


async def _create_input_booleans(hass: HomeAssistant, dog_name: str) -> None:
    """Create input_boolean entities with enhanced definitions."""
    
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
        
        # Additional useful booleans
        (f"{dog_name}_needs_grooming", "Pflege benötigt", ICONS["grooming"]),
        (f"{dog_name}_training_session", "Training heute", ICONS["training"]),
        (f"{dog_name}_vet_visit_due", "Tierarztbesuch fällig", ICONS["vet"]),
    ]
    
    results = await _create_helpers_for_domain_robust(hass, "input_boolean", boolean_entities, dog_name)
    return results


async def _create_counters(hass: HomeAssistant, dog_name: str) -> None:
    """Create counter entities with enhanced tracking."""
    
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
        
        # Summary counters
        (f"{dog_name}_activity_count", "Aktivitäten gesamt", ICONS["status"]),
        (f"{dog_name}_emergency_calls", "Notrufe", ICONS["emergency"]),
        (f"{dog_name}_daily_score", "Tages-Score", "mdi:star"),
    ]
    
    results = await _create_helpers_for_domain_robust(hass, "counter", counter_entities, dog_name)
    return results


async def _create_input_datetimes(hass: HomeAssistant, dog_name: str) -> None:
    """Create input_datetime entities with comprehensive time tracking."""
    
    # Feeding schedule times (time only)
    feeding_time_entities = []
    for meal_type in FEEDING_TYPES:
        feeding_time_entities.append((
            f"{dog_name}_feeding_{meal_type}_time",
            f"{MEAL_TYPES[meal_type]} Zeit",
            True,  # has_time
            False, # has_date
            DEFAULT_FEEDING_TIMES[meal_type],
            ICONS[meal_type]
        ))
    
    # Last activity timestamps (date + time)
    last_activity_entities = [
        (f"{dog_name}_last_feeding_morning", "Letztes Frühstück", True, True, None, ICONS["morning"]),
        (f"{dog_name}_last_feeding_lunch", "Letztes Mittagessen", True, True, None, ICONS["lunch"]),
        (f"{dog_name}_last_feeding_evening", "Letztes Abendessen", True, True, None, ICONS["evening"]),
        (f"{dog_name}_last_feeding_snack", "Letztes Leckerli", True, True, None, ICONS["snack"]),
        (f"{dog_name}_last_outside", "Letzter Gartengang", True, True, None, ICONS["outside"]),
        (f"{dog_name}_last_walk", "Letzter Spaziergang", True, True, None, ICONS["walk"]),
        (f"{dog_name}_last_play", "Letztes Spielen", True, True, None, ICONS["play"]),
        (f"{dog_name}_last_training", "Letztes Training", True, True, None, ICONS["training"]),
        (f"{dog_name}_last_poop", "Letztes Geschäft", True, True, None, ICONS["poop"]),
        (f"{dog_name}_last_activity", "Letzte Aktivität", True, True, None, ICONS["status"]),
        (f"{dog_name}_last_door_ask", "Letzte Türfrage", True, True, None, "mdi:door"),
    ]
    
    # Health & vet appointments
    health_entities = [
        (f"{dog_name}_last_vet_visit", "Letzter Tierarztbesuch", True, True, None, ICONS["vet"]),
        (f"{dog_name}_next_vet_appointment", "Nächster Tierarzttermin", True, True, None, ICONS["vet"]),
        (f"{dog_name}_last_vaccination", "Letzte Impfung", True, True, None, "mdi:needle"),
        (f"{dog_name}_next_vaccination", "Nächste Impfung", True, True, None, "mdi:needle"),
        (f"{dog_name}_medication_time", "Medikamentenzeit", True, False, "08:00:00", ICONS["medication"]),
        (f"{dog_name}_last_grooming", "Letzte Pflege", True, True, None, ICONS["grooming"]),
        (f"{dog_name}_next_grooming", "Nächste Pflege", True, True, None, ICONS["grooming"]),
    ]
    
    # Emergency & special events
    special_entities = [
        (f"{dog_name}_emergency_contact_time", "Notfall Kontakt Zeit", True, True, None, ICONS["emergency"]),
        (f"{dog_name}_visitor_start", "Besuch Start", True, True, None, ICONS["visitor"]),
        (f"{dog_name}_visitor_end", "Besuch Ende", True, True, None, ICONS["visitor"]),
        (f"{dog_name}_birth_date", "Geburtsdatum", False, True, None, ICONS["dog"]),
        (f"{dog_name}_last_weight_check", "Letzte Gewichtskontrolle", True, True, None, "mdi:weight-kilogram"),
    ]
    
    all_datetime_entities = feeding_time_entities + last_activity_entities + health_entities + special_entities
    
    results = await _create_helpers_for_domain_robust(hass, "input_datetime", all_datetime_entities, dog_name)
    return results


async def _create_input_texts(hass: HomeAssistant, dog_name: str) -> None:
    """Create input_text entities for comprehensive note-taking."""
    
    text_entities = [
        # Basic notes
        (f"{dog_name}_notes", "Allgemeine Notizen", 255, ICONS["notes"]),
        (f"{dog_name}_daily_notes", "Tagesnotizen", 255, ICONS["notes"]),
        (f"{dog_name}_behavior_notes", "Verhaltensnotizen", 255, ICONS["notes"]),
        
        # Activity notes
        (f"{dog_name}_last_activity_notes", "Letzte Aktivität Notizen", 255, ICONS["notes"]),
        (f"{dog_name}_walk_notes", "Spaziergang Notizen", 255, ICONS["walk"]),
        (f"{dog_name}_play_notes", "Spiel Notizen", 255, ICONS["play"]),
        (f"{dog_name}_training_notes", "Training Notizen", 255, ICONS["training"]),
        
        # Visitor information
        (f"{dog_name}_visitor_name", "Besuchername", 100, ICONS["visitor"]),
        (f"{dog_name}_visitor_contact", "Besucher Kontakt", 200, ICONS["visitor"]),
        (f"{dog_name}_visitor_notes", "Besucher Notizen", 255, ICONS["visitor"]),
        (f"{dog_name}_visitor_instructions", "Anweisungen für Besucher", 500, ICONS["visitor"]),
        
        # Health information
        (f"{dog_name}_health_notes", "Gesundheitsnotizen", 255, ICONS["health"]),
        (f"{dog_name}_medication_notes", "Medikamenten Notizen", 255, ICONS["medication"]),
        (f"{dog_name}_vet_notes", "Tierarzt Notizen", 255, ICONS["vet"]),
        (f"{dog_name}_symptoms", "Aktuelle Symptome", 255, ICONS["health"]),
        (f"{dog_name}_allergies", "Allergien", 255, ICONS["health"]),
        
        # Emergency contacts
        (f"{dog_name}_emergency_contact", "Notfallkontakt", 200, ICONS["emergency"]),
        (f"{dog_name}_vet_contact", "Tierarzt Kontakt", 200, ICONS["vet"]),
        (f"{dog_name}_backup_contact", "Ersatzkontakt", 200, "mdi:phone"),
        
        # Dog information
        (f"{dog_name}_breed", "Rasse", 100, ICONS["dog"]),
        (f"{dog_name}_color", "Farbe/Markierungen", 100, ICONS["dog"]),
        (f"{dog_name}_microchip_id", "Mikrochip ID", 50, "mdi:chip"),
        (f"{dog_name}_insurance_number", "Versicherungsnummer", 100, "mdi:shield"),
        (f"{dog_name}_registration_number", "Registrierungsnummer", 100, "mdi:card-account-details"),
        
        # Food preferences
        (f"{dog_name}_food_brand", "Futtermarke", 100, ICONS["food"]),
        (f"{dog_name}_food_allergies", "Futterallergien", 255, ICONS["food"]),
        (f"{dog_name}_favorite_treats", "Lieblingsleckerli", 255, ICONS["snack"]),
        (f"{dog_name}_feeding_instructions", "Fütterungsanweisungen", 500, ICONS["food"]),
        
        # Special status
        (f"{dog_name}_current_mood_description", "Stimmung Beschreibung", 255, ICONS["happy"]),
        (f"{dog_name}_weather_preference", "Wetter Präferenz", 100, "mdi:weather-partly-cloudy"),
        (f"{dog_name}_special_instructions", "Besondere Anweisungen", 500, ICONS["attention"]),
        (f"{dog_name}_quirks", "Eigenarten", 255, ICONS["dog"]),
        
        # Location tracking
        (f"{dog_name}_favorite_places", "Lieblingsplätze", 255, "mdi:map-marker"),
        (f"{dog_name}_restricted_areas", "Verbotene Bereiche", 255, "mdi:map-marker-off"),
    ]
    
    results = await _create_helpers_for_domain_robust(hass, "input_text", text_entities, dog_name)
    return results


async def _create_input_numbers(hass: HomeAssistant, dog_name: str) -> None:
    """Create input_number entities for comprehensive metrics tracking."""
    
    number_entities = [
        # Health metrics
        (f"{dog_name}_weight", "Gewicht", 0.1, 0, 100, 10, "kg", "mdi:weight-kilogram"),
        (f"{dog_name}_target_weight", "Zielgewicht", 0.1, 0, 100, 10, "kg", "mdi:target"),
        (f"{dog_name}_temperature", "Körpertemperatur", 0.1, 35, 42, 38.5, "°C", ICONS["thermometer"]),
        (f"{dog_name}_heart_rate", "Herzfrequenz", 1, 60, 200, 100, "bpm", ICONS["health"]),
        (f"{dog_name}_respiratory_rate", "Atemfrequenz", 1, 10, 50, 20, "bpm", ICONS["health"]),
        
        # Activity metrics
        (f"{dog_name}_daily_walk_duration", "Tägliche Gehzeit", 1, 0, 300, 60, "min", ICONS["walk"]),
        (f"{dog_name}_daily_play_time", "Tägliche Spielzeit", 1, 0, 180, 30, "min", ICONS["play"]),
        (f"{dog_name}_training_duration", "Trainingszeit", 1, 0, 120, 15, "min", ICONS["training"]),
        (f"{dog_name}_sleep_hours", "Schlafstunden", 0.5, 0, 24, 12, "h", "mdi:sleep"),
        
        # Food metrics
        (f"{dog_name}_daily_food_amount", "Tägliche Futtermenge", 10, 0, 2000, 400, "g", ICONS["food"]),
        (f"{dog_name}_treat_amount", "Leckerli Menge", 1, 0, 200, 20, "g", ICONS["snack"]),
        (f"{dog_name}_water_intake", "Wasseraufnahme", 50, 0, 3000, 500, "ml", "mdi:cup-water"),
        
        # Age and lifespan
        (f"{dog_name}_age_years", "Alter", 0.1, 0, 30, 5, "Jahre", ICONS["dog"]),
        (f"{dog_name}_age_months", "Alter", 1, 0, 360, 60, "Monate", ICONS["dog"]),
        (f"{dog_name}_expected_lifespan", "Erwartete Lebenszeit", 1, 8, 25, 14, "Jahre", ICONS["dog"]),
        
        # Size measurements
        (f"{dog_name}_height", "Schulterhöhe", 0.5, 10, 100, 50, "cm", "mdi:ruler"),
        (f"{dog_name}_length", "Körperlänge", 0.5, 20, 150, 70, "cm", "mdi:ruler"),
        (f"{dog_name}_neck_circumference", "Halsumfang", 0.5, 10, 80, 35, "cm", "mdi:tape-measure"),
        (f"{dog_name}_chest_circumference", "Brustumfang", 0.5, 20, 120, 60, "cm", "mdi:tape-measure"),
        
        # Medication dosage
        (f"{dog_name}_medication_dosage", "Medikamenten Dosierung", 0.5, 0, 500, 5, "mg", ICONS["medication"]),
        (f"{dog_name}_medication_frequency", "Dosierungsfrequenz", 1, 1, 4, 2, "x/Tag", ICONS["medication"]),
        
        # Ratings and scores
        (f"{dog_name}_health_score", "Gesundheits Score", 0.1, 0, 10, 8, "Punkte", ICONS["health"]),
        (f"{dog_name}_happiness_score", "Glücks Score", 0.1, 0, 10, 8, "Punkte", ICONS["happy"]),
        (f"{dog_name}_energy_level", "Energie Level", 0.1, 0, 10, 7, "Punkte", ICONS["play"]),
        (f"{dog_name}_appetite_score", "Appetit Score", 0.1, 0, 10, 8, "Punkte", ICONS["food"]),
        (f"{dog_name}_obedience_score", "Gehorsam Score", 0.1, 0, 10, 7, "Punkte", ICONS["training"]),
        (f"{dog_name}_socialization_score", "Sozialverhalten Score", 0.1, 0, 10, 7, "Punkte", ICONS["dog"]),
        
        # Environmental preferences
        (f"{dog_name}_preferred_temperature", "Wohlfühltemperatur", 1, -10, 40, 20, "°C", "mdi:thermometer"),
        (f"{dog_name}_exercise_requirements", "Bewegungsbedarf", 1, 1, 10, 5, "Level", ICONS["walk"]),
        (f"{dog_name}_noise_sensitivity", "Geräuschempfindlichkeit", 1, 1, 10, 5, "Level", "mdi:volume-high"),
    ]
    
    results = await _create_helpers_for_domain_robust(hass, "input_number", number_entities, dog_name)
    return results


async def _create_input_selects(hass: HomeAssistant, dog_name: str) -> None:
    """Create input_select entities for comprehensive categorical choices."""
    
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
            "Toy (< 4kg)", "Klein (4-10kg)", "Mittel (10-25kg)", "Groß (25-45kg)", "Riesig (> 45kg)"
        ], "Mittel (10-25kg)", ICONS["dog"]),
        
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
        
        # Age group
        (f"{dog_name}_age_group", "Altersgruppe", [
            "Welpe (< 6 Monate)", "Junghund (6-18 Monate)", "Erwachsen (1-7 Jahre)", 
            "Senior (7-10 Jahre)", "Hochbetagt (> 10 Jahre)"
        ], "Erwachsen (1-7 Jahre)", ICONS["dog"]),
        
        # Coat type
        (f"{dog_name}_coat_type", "Felltyp", [
            "Kurzhaar", "Langhaar", "Stockhaar", "Drahthaar", "Locken", "Haarlos"
        ], "Kurzhaar", ICONS["grooming"]),
        
        # Living situation
        (f"{dog_name}_living_situation", "Wohnsituation", [
            "Wohnung", "Haus mit Garten", "Haus mit großem Garten", "Bauernhof", "Andere"
        ], "Haus mit Garten", "mdi:home"),
        
        # Exercise needs
        (f"{dog_name}_exercise_needs", "Bewegungsbedarf", [
            "Minimal", "Niedrig", "Moderat", "Hoch", "Sehr hoch"
        ], "Moderat", ICONS["walk"]),
        
        # Socialization level
        (f"{dog_name}_socialization", "Sozialverhalten", [
            "Sehr schüchtern", "Schüchtern", "Normal", "Gesellig", "Sehr gesellig"
        ], "Normal", ICONS["dog"]),
        
        # Grooming needs
        (f"{dog_name}_grooming_needs", "Pflegebedarf", [
            "Minimal", "Niedrig", "Moderat", "Hoch", "Sehr hoch"
        ], "Moderat", ICONS["grooming"]),
    ]
    
    results = await _create_helpers_for_domain_robust(hass, "input_select", select_entities, dog_name)
    return results


async def verify_helper_creation(hass: HomeAssistant, dog_name: str) -> dict:
    """Verify that all critical helper entities were created successfully."""
    
    critical_entities = [
        f"input_boolean.{dog_name}_feeding_morning",
        f"input_boolean.{dog_name}_outside",
        f"counter.{dog_name}_outside_count",
        f"input_text.{dog_name}_notes",
        f"input_datetime.{dog_name}_last_outside",
        f"input_select.{dog_name}_health_status",
        f"input_number.{dog_name}_weight",
    ]
    
    verification_results = {
        "total_checked": len(critical_entities),
        "existing": [],
        "missing": [],
        "success_rate": 0.0
    }
    
    for entity_id in critical_entities:
        if hass.states.get(entity_id):
            verification_results["existing"].append(entity_id)
        else:
            verification_results["missing"].append(entity_id)
    
    verification_results["success_rate"] = (
        len(verification_results["existing"]) / verification_results["total_checked"] * 100
    )
    
    _LOGGER.info("Helper verification for %s: %.1f%% success rate (%d/%d entities)", 
                 dog_name, verification_results["success_rate"], 
                 len(verification_results["existing"]), verification_results["total_checked"])
    
    if verification_results["missing"]:
        _LOGGER.warning("Missing critical entities for %s: %s", 
                       dog_name, verification_results["missing"])
    
    return verification_results
