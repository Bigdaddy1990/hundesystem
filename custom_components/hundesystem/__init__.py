from .const import (
    DOMAIN,
    CONF_DOG_NAME,
    CONF_PUSH_DEVICES,
    CONF_PERSON_TRACKING,
    CONF_CREATE_DASHBOARD,
    CONF_DOOR_SENSOR,
    SERVICE_TRIGGER_FEEDING_REMINDER,
    SERVICE_DAILY_RESET,
    SERVICE_SEND_NOTIFICATION,
    SERVICE_SET_VISITOR_MODE,
    SERVICE_LOG_ACTIVITY,
    SERVICE_ADD_DOG,
    SERVICE_TEST_NOTIFICATION,
    SERVICE_EMERGENCY_CONTACT,
    SERVICE_HEALTH_CHECK,
    MEAL_TYPES,
    ACTIVITY_TYPES,
    FEEDING_TYPES,
    ICONS,
)
from .helpers import async_create_helpers, verify_helper_creation
from .dashboard import async_create_dashboard

_LOGGER = logging.getLogger(__name__)

PLATFORMS: List[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.BUTTON,
]

# Service schemas with improved validation
TRIGGER_FEEDING_REMINDER_SCHEMA = vol.Schema({
    vol.Required("meal_type"): vol.In(MEAL_TYPES.keys()),
    vol.Optional("message"): cv.string,
    vol.Optional("dog_name"): cv.string,
})

SEND_NOTIFICATION_SCHEMA = vol.Schema({
    vol.Required("title"): cv.string,
    vol.Required("message"): cv.string,
    vol.Optional("target"): cv.string,
    vol.Optional("dog_name"): cv.string,
    vol.Optional("data"): dict,
})

SET_VISITOR_MODE_SCHEMA = vol.Schema({
    vol.Required("enabled"): cv.boolean,
    vol.Optional("visitor_name", default=""): cv.string,
    vol.Optional("dog_name"): cv.string,
})

LOG_ACTIVITY_SCHEMA = vol.Schema({
    vol.Required("activity_type"): vol.In(ACTIVITY_TYPES.keys()),
    vol.Optional("duration"): vol.Range(min=1, max=480),
    vol.Optional("notes", default=""): cv.string,
    vol.Optional("dog_name"): cv.string,
})

ADD_DOG_SCHEMA = vol.Schema({
    vol.Required("dog_name"): cv.string,
    vol.Optional("push_devices", default=[]): [cv.string],
    vol.Optional("door_sensor"): cv.entity_id,
    vol.Optional("create_dashboard", default=True): cv.boolean,
})

TEST_NOTIFICATION_SCHEMA = vol.Schema({
    vol.Optional("dog_name"): cv.string,
})

EMERGENCY_CONTACT_SCHEMA = vol.Schema({
    vol.Required("emergency_type"): vol.In(["medical", "lost", "injury", "behavioral", "other"]),
    vol.Required("message"): cv.string,
    vol.Optional("location", default=""): cv.string,
    vol.Optional("contact_vet", default=False): cv.boolean,
    vol.Required("dog_name"): cv.string,
})

HEALTH_CHECK_SCHEMA = vol.Schema({
    vol.Optional("check_type", default="general"): vol.In(["general", "feeding", "activity", "behavior", "symptoms"]),
    vol.Optional("notes", default=""): cv.string,
    vol.Optional("temperature"): vol.Range(min=35.0, max=42.0),
    vol.Optional("weight"): vol.Range(min=0.1, max=100.0),
    vol.Required("dog_name"): cv.string,
})

# Global services registry to prevent double registration
_SERVICES_REGISTERED = False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hundesystem from a config entry with improved error handling."""
    global _SERVICES_REGISTERED
    
    hass.data.setdefault(DOMAIN, {})
    
    dog_name = entry.data[CONF_DOG_NAME]
    _LOGGER.info("=== HUNDESYSTEM SETUP START for %s ===", dog_name)
    
    # Store config data
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "dog_name": dog_name,
        "store": Store(hass, 1, f"{DOMAIN}_{dog_name}"),
        "listeners": [],  # Track event listeners for cleanup
    }
    
    try:
        # Step 1: Wait for core domains to be ready
        _LOGGER.info("Step 1: Waiting for core domains to be ready...")
        if not await _wait_for_core_domains(hass):
            _LOGGER.error("Core domains not ready, setup may be incomplete")
        
        # Step 2: Create helper entities with improved robustness
        _LOGGER.info("Step 2: Creating helper entities for %s", dog_name)
        await async_create_helpers_robust(hass, dog_name, entry.data)
        _LOGGER.info("Helper entities created successfully for %s", dog_name)
        
        # Step 3: Verify helper creation
        _LOGGER.info("Step 3: Verifying helper entities...")
        verification_results = await verify_helper_creation(hass, dog_name)
        if verification_results["success_rate"] < 70:
            _LOGGER.warning("Helper creation success rate low: %.1f%%", verification_results["success_rate"])
        
        # Step 4: Wait for entities to stabilize
        _LOGGER.info("Step 4: Waiting for entities to stabilize...")
        await asyncio.sleep(3.0)
        
        # Step 5: Set up platforms
        _LOGGER.info("Step 5: Setting up platforms for %s", dog_name)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info("Platforms set up successfully for %s", dog_name)
        
        # Step 6: Register services (only once globally)
        if not _SERVICES_REGISTERED:
            _LOGGER.info("Step 6: Registering global services")
            await _register_services(hass)
            _SERVICES_REGISTERED = True
        else:
            _LOGGER.debug("Services already registered, skipping")
        
        # Step 7: Create dashboard if requested
        if entry.data.get(CONF_CREATE_DASHBOARD, True):
            _LOGGER.info("Step 7: Creating dashboard for %s", dog_name)
            try:
                await async_create_dashboard(hass, dog_name, entry.data)
            except Exception as e:
                _LOGGER.warning("Dashboard creation failed for %s: %s", dog_name, e)
        
        # Step 8: Setup automations and listeners
        _LOGGER.info("Step 8: Setting up automations for %s", dog_name)
        await _setup_automations(hass, entry, dog_name)
        
        # Step 9: Final verification
        _LOGGER.info("Step 9: Final verification for %s", dog_name)
        await _final_verification(hass, dog_name)
        
        _LOGGER.info("=== HUNDESYSTEM SETUP COMPLETE for %s ===", dog_name)
        return True
        
    except Exception as e:
        _LOGGER.error("=== HUNDESYSTEM SETUP FAILED for %s: %s ===", dog_name, e, exc_info=True)
        # Clean up partial setup
        await _cleanup_partial_setup(hass, entry)
        return False


async def _wait_for_core_domains(hass: HomeAssistant, timeout: int = 30) -> bool:
    """Wait for core domains to be available."""
    required_domains = ["input_boolean", "counter", "input_datetime", "input_text", "input_number", "input_select"]
    
    for _ in range(timeout):
        all_ready = True
        for domain in required_domains:
            if not hass.services.has_service(domain, "create"):
                all_ready = False
                break
        
        if all_ready:
            _LOGGER.debug("All core domains ready")
            return True
        
        await asyncio.sleep(1)
    
    _LOGGER.warning("Timeout waiting for core domains")
    return False


async def async_create_helpers_robust(hass: HomeAssistant, dog_name: str, config: dict) -> None:
    """Create helper entities with maximum robustness and error recovery."""
    
    try:
        # Import the improved helpers function
        from .helpers import async_create_helpers
        
        # Call the improved helper creation function
        await async_create_helpers(hass, dog_name, config)
        
    except Exception as e:
        _LOGGER.error("Helper creation failed for %s: %s", dog_name, e)
        # Try alternative approach or create minimal set
        await _create_minimal_helpers(hass, dog_name)


async def _create_minimal_helpers(hass: HomeAssistant, dog_name: str) -> None:
    """Create minimal set of helpers as fallback."""
    _LOGGER.info("Creating minimal helper set for %s", dog_name)
    
    minimal_helpers = [
        # Essential input_booleans
        (f"{dog_name}_feeding_morning", "Frühstück", "input_boolean", {"icon": "mdi:weather-sunrise"}),
        (f"{dog_name}_feeding_evening", "Abendessen", "input_boolean", {"icon": "mdi:weather-sunset"}),
        (f"{dog_name}_outside", "War draußen", "input_boolean", {"icon": "mdi:door-open"}),
        
        # Essential counters
        (f"{dog_name}_outside_count", "Draußen Zähler", "counter", {"initial": 0, "step": 1}),
        
        # Essential text
        (f"{dog_name}_notes", "Notizen", "input_text", {"max": 255}),
    ]
    
    for entity_name, friendly_name, domain, attrs in minimal_helpers:
        try:
            service_data = {
                "name": f"{dog_name.title()} {friendly_name}",
                **attrs
            }
            
            await hass.services.async_call(
                domain, "create", service_data, blocking=True
            )
            
            _LOGGER.debug("Created minimal helper: %s.%s", domain, entity_name)
            await asyncio.sleep(0.5)
            
        except Exception as e:
            _LOGGER.error("Failed to create minimal helper %s: %s", entity_name, e)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry with proper cleanup."""
    global _SERVICES_REGISTERED
    
    _LOGGER.info("Unloading Hundesystem entry for %s", entry.data[CONF_DOG_NAME])
    
    # Clean up listeners
    entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
    listeners = entry_data.get("listeners", [])
    for remove_listener in listeners:
        try:
            remove_listener()
        except Exception as e:
            _LOGGER.warning("Error removing listener: %s", e)
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        
        # Remove services if no more instances
        if not hass.data[DOMAIN]:
            await _unregister_services(hass)
            _SERVICES_REGISTERED = False
            _LOGGER.info("All Hundesystem instances removed, services unregistered")
    
    return unload_ok


async def _register_services(hass: HomeAssistant) -> None:
    """Register services for the integration with comprehensive error handling."""
    
    # Check if already registered
    if hass.services.has_service(DOMAIN, SERVICE_TRIGGER_FEEDING_REMINDER):
        _LOGGER.debug("Services already registered")
        return
    
    async def trigger_feeding_reminder(call: ServiceCall) -> None:
        """Handle feeding reminder service call."""
        try:
            meal_type = call.data["meal_type"]
            message = call.data.get("message", f"🐶 Zeit für {MEAL_TYPES[meal_type]}!")
            dog_name = call.data.get("dog_name")
            
            if meal_type not in MEAL_TYPES:
                raise ServiceValidationError(f"Invalid meal_type: {meal_type}")
            
            # Get target config entries
            target_entries = await _get_target_entries(hass, dog_name)
            
            for entry_data in target_entries:
                config = entry_data["config"]
                dog = entry_data["dog_name"]
                
                try:
                    # Update feeding datetime
                    datetime_entity = f"input_datetime.{dog}_last_feeding_{meal_type}"
                    if hass.states.get(datetime_entity):
                        await hass.services.async_call(
                            "input_datetime", "set_datetime",
                            {
                                "entity_id": datetime_entity,
                                "datetime": datetime.now().isoformat()
                            },
                            blocking=True
                        )
                    
                    # Send notification
                    await _send_notification(hass, config, f"🍽️ Fütterungszeit - {dog.title()}", message)
                    
                    _LOGGER.info("Feeding reminder sent for %s: %s", dog, meal_type)
                    
                except Exception as e:
                    _LOGGER.error("Failed to send feeding reminder for %s: %s", dog, e)
                    continue
                    
        except ServiceValidationError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error in feeding reminder service: %s", e)
            raise ServiceValidationError(f"Service execution failed: {e}")
    
    async def daily_reset(call: ServiceCall) -> None:
        """Handle daily reset service call."""
        try:
            dog_name = call.data.get("dog_name")
            target_entries = await _get_target_entries(hass, dog_name)
            
            for entry_data in target_entries:
                dog = entry_data["dog_name"]
                config = entry_data["config"]
                
                try:
                    await _perform_daily_reset(hass, dog)
                    
                    # Send confirmation
                    await _send_notification(
                        hass, config,
                        f"🔄 Tagesreset - {dog.title()}", 
                        "Alle Statistiken wurden zurückgesetzt"
                    )
                    
                    _LOGGER.info("Daily reset completed for %s", dog)
                    
                except Exception as e:
                    _LOGGER.error("Error during daily reset for %s: %s", dog, e)
                    continue
                    
        except Exception as e:
            _LOGGER.error("Unexpected error in daily reset service: %s", e)
            raise ServiceValidationError(f"Daily reset failed: {e}")
    
    async def send_notification(call: ServiceCall) -> None:
        """Handle send notification service call."""
        try:
            title = call.data["title"]
            message = call.data["message"]
            target = call.data.get("target")
            dog_name = call.data.get("dog_name")
            data = call.data.get("data", {})
            
            target_entries = await _get_target_entries(hass, dog_name)
            
            for entry_data in target_entries:
                config = entry_data["config"]
                await _send_notification(hass, config, title, message, target, data)
                
        except Exception as e:
            _LOGGER.error("Error in send notification service: %s", e)
            raise ServiceValidationError(f"Notification failed: {e}")
    
    async def set_visitor_mode(call: ServiceCall) -> None:
        """Handle set visitor mode service call."""
        try:
            enabled = call.data["enabled"]
            visitor_name = call.data.get("visitor_name", "")
            dog_name = call.data.get("dog_name")
            
            target_entries = await _get_target_entries(hass, dog_name)
            
            for entry_data in target_entries:
                dog = entry_data["dog_name"]
                
                # Set visitor mode input_boolean
                visitor_entity = f"input_boolean.{dog}_visitor_mode_input"
                if hass.states.get(visitor_entity):
                    action = "turn_on" if enabled else "turn_off"
                    await hass.services.async_call(
                        "input_boolean", action,
                        {"entity_id": visitor_entity},
                        blocking=True
                    )
                
                # Set visitor name
                if visitor_name:
                    name_entity = f"input_text.{dog}_visitor_name"
                    if hass.states.get(name_entity):
                        await hass.services.async_call(
                            "input_text", "set_value",
                            {"entity_id": name_entity, "value": visitor_name},
                            blocking=True
                        )
                
                _LOGGER.info("Visitor mode %s for %s", "enabled" if enabled else "disabled", dog)
                
        except Exception as e:
            _LOGGER.error("Error in visitor mode service: %s", e)
            raise ServiceValidationError(f"Visitor mode failed: {e}")
    
    async def log_activity(call: ServiceCall) -> None:
        """Handle log activity service call."""
        try:
            activity_type = call.data["activity_type"]
            duration = call.data.get("duration", 0)
            notes = call.data.get("notes", "")
            dog_name = call.data.get("dog_name")
            
            if activity_type not in ACTIVITY_TYPES:
                raise ServiceValidationError(f"Invalid activity_type: {activity_type}")
            
            target_entries = await _get_target_entries(hass, dog_name)
            
            for entry_data in target_entries:
                dog = entry_data["dog_name"]
                
                await _log_activity_for_dog(hass, dog, activity_type, duration, notes)
                _LOGGER.info("Activity logged for %s: %s", dog, activity_type)
                
        except ServiceValidationError:
            raise
        except Exception as e:
            _LOGGER.error("Error in log activity service: %s", e)
            raise ServiceValidationError(f"Activity logging failed: {e}")
    
    async def test_notification(call: ServiceCall) -> None:
        """Handle test notification service call."""
        try:
            dog_name = call.data.get("dog_name")
            target_entries = await _get_target_entries(hass, dog_name)
            
            for entry_data in target_entries:
                config = entry_data["config"]
                dog = entry_data["dog_name"]
                
                await _send_notification(
                    hass, config,
                    f"🧪 Test - {dog.title()}", 
                    "Test-Benachrichtigung funktioniert! 🐶"
                )
                
        except Exception as e:
            _LOGGER.error("Error in test notification service: %s", e)
            raise ServiceValidationError(f"Test notification failed: {e}")
    
    async def emergency_contact(call: ServiceCall) -> None:
        """Handle emergency contact service call."""
        try:
            emergency_type = call.data["emergency_type"]
            message = call.data["message"]
            location = call.data.get("location", "")
            contact_vet = call.data.get("contact_vet", False)
            dog_name = call.data["dog_name"]
            
            target_entries = await _get_target_entries(hass, dog_name)
            
            for entry_data in target_entries:
                dog = entry_data["dog_name"]
                config = entry_data["config"]
                
                # Set emergency mode
                emergency_entity = f"input_boolean.{dog}_emergency_mode"
                if hass.states.get(emergency_entity):
                    await hass.services.async_call(
                        "input_boolean", "turn_on",
                        {"entity_id": emergency_entity},
                        blocking=True
                    )
                
                # Send high priority notification
                emergency_message = f"🚨 NOTFALL - {dog.title()}\n\n"
                emergency_message += f"Art: {emergency_type}\n"
                emergency_message += f"Beschreibung: {message}\n"
                if location:
                    emergency_message += f"Standort: {location}\n"
                
                await _send_notification(
                    hass, config,
                    f"🚨 NOTFALL - {dog.title()}",
                    emergency_message,
                    data={"priority": "high", "ttl": 0}
                )
                
                _LOGGER.warning("Emergency activated for %s: %s", dog, emergency_type)
                
        except Exception as e:
            _LOGGER.error("Error in emergency contact service: %s", e)
            raise ServiceValidationError(f"Emergency contact failed: {e}")
    
    async def health_check(call: ServiceCall) -> None:
        """Handle health check service call."""
        try:
            check_type = call.data.get("check_type", "general")
            notes = call.data.get("notes", "")
            temperature = call.data.get("temperature")
            weight = call.data.get("weight")
            dog_name = call.data["dog_name"]
            
            target_entries = await _get_target_entries(hass, dog_name)
            
            for entry_data in target_entries:
                dog = entry_data["dog_name"]
                
                await _perform_health_check(hass, dog, check_type, notes, temperature, weight)
                _LOGGER.info("Health check completed for %s", dog)
                
        except Exception as e:
            _LOGGER.error("Error in health check service: %s", e)
            raise ServiceValidationError(f"Health check failed: {e}")
    
    # Register all services
    services = [
        (SERVICE_TRIGGER_FEEDING_REMINDER, trigger_feeding_reminder, TRIGGER_FEEDING_REMINDER_SCHEMA),
        (SERVICE_DAILY_RESET, daily_reset, None),
        (SERVICE_SEND_NOTIFICATION, send_notification, SEND_NOTIFICATION_SCHEMA),
        (SERVICE_SET_VISITOR_MODE, set_visitor_mode, SET_VISITOR_MODE_SCHEMA),
        (SERVICE_LOG_ACTIVITY, log_activity, LOG_ACTIVITY_SCHEMA),
        (SERVICE_TEST_NOTIFICATION, test_notification, TEST_NOTIFICATION_SCHEMA),
        (SERVICE_EMERGENCY_CONTACT, emergency_contact, EMERGENCY_CONTACT_SCHEMA),
        (SERVICE_HEALTH_CHECK, health_check, HEALTH_CHECK_SCHEMA),
    ]
    
    for service_name, service_func, schema in services:
        try:
            hass.services.async_register(
                DOMAIN, service_name, service_func, schema
            )
            _LOGGER.debug("Registered service: %s", service_name)
        except Exception as e:
            _LOGGER.error("Failed to register service %s: %s", service_name, e)
    
    _LOGGER.info("All Hundesystem services registered successfully")


async def _unregister_services(hass: HomeAssistant) -> None:
    """Unregister all services."""
    services = [
        SERVICE_TRIGGER_FEEDING_REMINDER,
        SERVICE_DAILY_RESET,
        SERVICE_SEND_NOTIFICATION,
        SERVICE_SET_VISITOR_MODE,
        SERVICE_LOG_ACTIVITY,
        SERVICE_TEST_NOTIFICATION,
        SERVICE_EMERGENCY_CONTACT,
        SERVICE_HEALTH_CHECK,
    ]
    
    for service_name in services:
        if hass.services.has_service(DOMAIN, service_name):
            hass.services.async_remove(DOMAIN, service_name)
            _LOGGER.debug("Unregistered service: %s", service_name)


async def _get_target_entries(hass: HomeAssistant, dog_name: Optional[str]) -> List[Dict[str, Any]]:
    """Get target entries based on dog name."""
    if dog_name:
        # Find specific dog
        for entry_data in hass.data[DOMAIN].values():
            if isinstance(entry_data, dict) and entry_data.get("dog_name") == dog_name:
                return [entry_data]
        raise ServiceValidationError(f"Dog '{dog_name}' not found")
    else:
        # All dogs
        return [data for data in hass.data[DOMAIN].values() if isinstance(data, dict)]


async def _perform_daily_reset(hass: HomeAssistant, dog_name: str) -> None:
    """Perform daily reset for a specific dog."""
    
    # Reset all feeding input_booleans
    for meal in FEEDING_TYPES:
        entity_id = f"input_boolean.{dog_name}_feeding_{meal}"
        if hass.states.get(entity_id):
            await hass.services.async_call(
                "input_boolean", "turn_off",
                {"entity_id": entity_id},
                blocking=True
            )
    
    # Reset activity booleans
    activity_entities = [
        f"input_boolean.{dog_name}_outside",
        f"input_boolean.{dog_name}_poop_done",
        f"input_boolean.{dog_name}_visitor_mode_input"
    ]
    
    for entity_id in activity_entities:
        if hass.states.get(entity_id):
            await hass.services.async_call(
                "input_boolean", "turn_off",
                {"entity_id": entity_id},
                blocking=True
            )
    
    # Reset counters
    counter_types = FEEDING_TYPES + ["outside", "walk", "play", "training", "poop", "activity"]
    for counter_type in counter_types:
        entity_id = f"counter.{dog_name}_{counter_type}_count"
        if hass.states.get(entity_id):
            await hass.services.async_call(
                "counter", "reset",
                {"entity_id": entity_id},
                blocking=True
            )
    
    # Clear daily notes
    notes_entity = f"input_text.{dog_name}_daily_notes"
    if hass.states.get(notes_entity):
        await hass.services.async_call(
            "input_text", "set_value",
            {"entity_id": notes_entity, "value": ""},
            blocking=True
        )


async def _log_activity_for_dog(hass: HomeAssistant, dog_name: str, activity_type: str, duration: int, notes: str) -> None:
    """Log activity for a specific dog."""
    
    # Increment activity counter
    counter_entity = f"counter.{dog_name}_{activity_type}_count"
    if hass.states.get(counter_entity):
        await hass.services.async_call(
            "counter", "increment",
            {"entity_id": counter_entity},
            blocking=True
        )
    
    # Increment general activity counter
    general_counter = f"counter.{dog_name}_activity_count"
    if hass.states.get(general_counter):
        await hass.services.async_call(
            "counter", "increment",
            {"entity_id": general_counter},
            blocking=True
        )
    
    # Update last activity datetime
    datetime_entity = f"input_datetime.{dog_name}_last_activity"
    if hass.states.get(datetime_entity):
        await hass.services.async_call(
            "input_datetime", "set_datetime",
            {
                "entity_id": datetime_entity,
                "datetime": datetime.now().isoformat()
            },
            blocking=True
        )
    
    # Update activity-specific datetime
    specific_datetime_entity = f"input_datetime.{dog_name}_last_{activity_type}"
    if hass.states.get(specific_datetime_entity):
        await hass.services.async_call(
            "input_datetime", "set_datetime",
            {
                "entity_id": specific_datetime_entity,
                "datetime": datetime.now().isoformat()
            },
            blocking=True
        )
    
    # Update notes if provided
    if notes:
        notes_entity = f"input_text.{dog_name}_last_activity_notes"
        if hass.states.get(notes_entity):
            activity_note = f"{ACTIVITY_TYPES[activity_type]}"
            if duration:
                activity_note += f" ({duration} min)"
            activity_note += f": {notes}"
            
            await hass.services.async_call(
                "input_text", "set_value",
                {"entity_id": notes_entity, "value": activity_note},
                blocking=True
            )


async def _perform_health_check(hass: HomeAssistant, dog_name: str, check_type: str, notes: str, temperature: Optional[float], weight: Optional[float]) -> None:
    """Perform health check for a specific dog."""
    
    # Update temperature if provided
    if temperature is not None:
        temp_entity = f"input_number.{dog_name}_temperature"
        if hass.states.get(temp_entity):
            await hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": temp_entity, "value": temperature},
                blocking=True
            )
    
    # Update weight if provided
    if weight is not None:
        weight_entity = f"input_number.{dog_name}_weight"
        if hass.states.get(weight_entity):
            await hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": weight_entity, "value": weight},
                blocking=True
            )
    
    # Update health notes
    if notes:
        health_notes_entity = f"input_text.{dog_name}_health_notes"
        if hass.states.get(health_notes_entity):
            timestamp = datetime.now().strftime("%d.%m. %H:%M")
            health_note = f"[{timestamp}] {check_type}: {notes}"
            
            await hass.services.async_call(
                "input_text", "set_value",
                {"entity_id": health_notes_entity, "value": health_note},
                blocking=True
            )


async def _send_notification(
    hass: HomeAssistant, 
    config: dict, 
    title: str, 
    message: str, 
    target: Optional[str] = None,
    data: Optional[dict] = None
) -> None:
    """Send notification via configured services with improved error handling."""
    
    try:
        push_devices = config.get(CONF_PUSH_DEVICES, [])
        person_tracking = config.get(CONF_PERSON_TRACKING, False)
        
        # Determine notification targets
        notification_targets = []
        
        if person_tracking and not target:
            # Get home persons
            for entity_id in hass.states.async_entity_ids("person"):
                state = hass.states.get(entity_id)
                if state and state.state == "home":
                    person_name = entity_id.replace("person.", "")
                    mobile_app = f"mobile_app_{person_name}"
                    
                    # Check if this mobile app service exists
                    if hass.services.has_service("notify", mobile_app):
                        notification_targets.append(mobile_app)
        
        # Fallback to configured devices
        if not notification_targets:
            notification_targets = [target] if target else push_devices
        
        # Add persistent notification as final fallback
        if not notification_targets:
            notification_targets = ["persistent_notification"]
        
        # Prepare notification data
        notification_data = {"title": title, "message": message}
        if data:
            notification_data["data"] = data
        
        # Send notifications
        for device in notification_targets:
            try:
                service_name = device.replace("notify.", "") if device.startswith("notify.") else device
                
                await hass.services.async_call(
                    "notify", service_name,
                    notification_data,
                    blocking=False
                )
                
                _LOGGER.debug("Notification sent to %s: %s", service_name, title)
                
            except Exception as e:
                _LOGGER.warning("Failed to send notification to %s: %s", device, e)
                continue
        
    except Exception as e:
        _LOGGER.error("Error in notification system: %s", e)
        # Fallback to persistent notification
        try:
            await hass.services.async_call(
                "persistent_notification", "create",
                {
                    "title": title,
                    "message": message,
                    "notification_id": f"hundesystem_fallback_{datetime.now().timestamp()}"
                },
                blocking=False
            )
        except Exception as fallback_error:
            _LOGGER.error("Even fallback notification failed: %s", fallback_error)


async def _setup_automations(hass: HomeAssistant, entry: ConfigEntry, dog_name: str) -> None:
    """Setup automations and event listeners for a dog."""
    
    entry_data = hass.data[DOMAIN][entry.entry_id]
    listeners = entry_data["listeners"]
    
    try:
        # Setup daily reset automation
        def daily_reset_callback(now):
            """Daily reset callback."""
            hass.async_create_task(_async_daily_reset_callback(hass, dog_name))
        
        # Schedule daily reset at 23:59
        remove_listener = async_track_time_change(
            hass, daily_reset_callback,
            hour=23, minute=59, second=0
        )
        listeners.append(remove_listener)
        
        # Setup door sensor automation if configured
        door_sensor = entry.data.get(CONF_DOOR_SENSOR)
        if door_sensor:
            def door_sensor_callback(event):
                """Handle door sensor state changes."""
                hass.async_create_task(_async_door_sensor_callback(hass, dog_name, event))
            
            remove_listener = async_track_state_change_event(
                hass, [door_sensor], door_sensor_callback
            )
            listeners.append(remove_listener)
            
            _LOGGER.info("Door sensor automation set up for %s with sensor %s", dog_name, door_sensor)
        
        _LOGGER.info("Automations set up successfully for %s", dog_name)
        
    except Exception as e:
        _LOGGER.error("Failed to setup automations for %s: %s", dog_name, e)


@callback
def _async_daily_reset_callback(hass: HomeAssistant, dog_name: str):
    """Async daily reset callback - CORRECTED: @callback without async def."""
    hass.async_create_task(_perform_daily_reset_task(hass, dog_name))


async def _perform_daily_reset_task(hass: HomeAssistant, dog_name: str) -> None:
    """Perform daily reset task."""
    try:
        await hass.services.async_call(
            DOMAIN, SERVICE_DAILY_RESET,
            {"dog_name": dog_name},
            blocking=True
        )
    except Exception as err:
        _LOGGER.error("Daily reset failed for %s: %s", dog_name, err)


@callback 
def _async_door_sensor_callback(hass: HomeAssistant, dog_name: str, event):
    """Async door sensor callback - CORRECTED: @callback without async def."""
    hass.async_create_task(_handle_door_sensor_event(hass, dog_name, event))


async def _handle_door_sensor_event(hass: HomeAssistant, dog_name: str, event) -> None:
    """Handle door sensor state changes."""
    try:
        # Get the new and old states from the event
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        
        if (new_state and new_state.state == "off" and 
            old_state and old_state.state == "on"):
            
            # Door closed - ask if dog was outside
            await asyncio.sleep(2)  # Wait a moment
            
            # Check if we should ask (avoid spam)
            last_ask_entity = f"input_datetime.{dog_name}_last_door_ask"
            last_ask_state = hass.states.get(last_ask_entity)
            
            should_ask = True
            if last_ask_state and last_ask_state.state not in ["unknown", "unavailable"]:
                try:
                    last_ask = datetime.fromisoformat(last_ask_state.state.replace("Z", "+00:00"))
                    if (datetime.now() - last_ask).total_seconds() < 300:  # 5 minutes
                        should_ask = False
                except ValueError:
                    pass
            
            if should_ask:
                # Update last ask time
                if hass.states.get(last_ask_entity):
                    await hass.services.async_call(
                        "input_datetime", "set_datetime",
                        {
                            "entity_id": last_ask_entity,
                            "datetime": datetime.now().isoformat()
                        }
                    )
                
                # Find config for this dog
                config = None
                for entry_data in hass.data[DOMAIN].values():
                    if isinstance(entry_data, dict) and entry_data.get("dog_name") == dog_name:
                        config = entry_data["config"]
                        break
                
                if config:
                    # Send interactive notification
                    notification_data = {
                        "actions": [
                            {"action": f"dog_outside_yes_{dog_name}", "title": "✅ Ja"},
                            {"action": f"dog_outside_no_{dog_name}", "title": "❌ Nein"}
                        ],
                        "tag": f"{dog_name}_door_question",
                        "group": f"hundesystem_{dog_name}"
                    }
                    
                    await _send_notification(
                        hass, config,
                        f"🚪 War {dog_name.title()} draußen?",
                        "Türsensor hat Bewegung erkannt. War der Hund draußen?",
                        data=notification_data
                    )
                    
                    _LOGGER.info("Door sensor question sent for %s", dog_name)
                    
    except Exception as e:
        _LOGGER.error("Error handling door sensor event for %s: %s", dog_name, e)


async def _final_verification(hass: HomeAssistant, dog_name: str) -> None:
    """Perform final verification of setup."""
    
    # Check some key entities
    key_entities = [
        f"input_boolean.{dog_name}_feeding_morning",
        f"input_boolean.{dog_name}_outside",
        f"counter.{dog_name}_outside_count",
        f"sensor.{dog_name}_status",
        f"binary_sensor.{dog_name}_feeding_complete",
    ]
    
    existing_entities = []
    missing_entities = []
    
    for entity_id in key_entities:
        if hass.states.get(entity_id):
            existing_entities.append(entity_id)
        else:
            missing_entities.append(entity_id)
    
    success_rate = len(existing_entities) / len(key_entities) * 100
    
    _LOGGER.info("Final verification for %s: %.1f%% entities exist (%d/%d)", 
                 dog_name, success_rate, len(existing_entities), len(key_entities))
    
    if missing_entities:
        _LOGGER.warning("Missing entities for %s: %s", dog_name, missing_entities)
    
    # Send setup notification
    status = "✅ Erfolgreich" if success_rate >= 80 else "⚠️ Teilweise"
    
    try:
        await hass.services.async_call(
            "persistent_notification", "create",
            {
                "title": f"🐶 Hundesystem für {dog_name.title()}",
                "message": f"""
Setup {status} abgeschlossen!

**Erstellte Entitäten:** {len(existing_entities)}/{len(key_entities)}

**Verfügbare Services:**
- hundesystem.trigger_feeding_reminder
- hundesystem.daily_reset  
- hundesystem.test_notification
- hundesystem.log_activity
- hundesystem.set_visitor_mode

**Nächste Schritte:**
Gehen Sie zu Einstellungen > Geräte & Dienste > Hundesystem um alle Entitäten zu sehen.

**Erfolgsrate:** {success_rate:.1f}%
                """,
                "notification_id": f"hundesystem_setup_{dog_name}"
            },
            blocking=False
        )
    except Exception as e:
        _LOGGER.warning("Could not send setup notification: %s", e)


async def _cleanup_partial_setup(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean up partial setup on failure."""
    
    try:
        # Remove entry data
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, {})
        
        # Clean up listeners
        listeners = entry_data.get("listeners", [])
        for remove_listener in listeners:
            try:
                remove_listener()
            except Exception:
                pass
        
        # Try to unload platforms
        try:
            await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        except Exception:
            pass
        
        _LOGGER.info("Cleaned up partial setup for %s", entry.data.get(CONF_DOG_NAME, "unknown"))
        
    except Exception as e:
        _LOGGER.error("Error during cleanup: %s", e)"""The Hundesystem integration - CORRECTED VERSION."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import async_track_time_change, async_track_state_change_event
from homeassistant.exceptions import ServiceValidationError

from .const import (
    DOMAIN,
    CONF_DOG_NAME,
    CONF_PUSH_DEVICES,
    CONF_PERSON_TRACKING,
    CONF_CREATE_DASHBOARD,
    CONF_DOOR_SENSOR,
    SERVICE_TRIGGER_FEEDING_REMINDER,
    SERVICE_DAILY_RESET,
    SERVICE_SEND_NOTIFICATION
