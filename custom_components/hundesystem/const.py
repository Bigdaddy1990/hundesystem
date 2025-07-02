"""Constants for the Hundesystem integration."""

# Integration domain
DOMAIN = "hundesystem"

# Configuration keys
CONF_DOG_NAME = "dog_name"
CONF_PUSH_DEVICES = "push_devices"
CONF_PERSON_TRACKING = "person_tracking"
CONF_CREATE_DASHBOARD = "create_dashboard"

# Default values
DEFAULT_DOG_NAME = "hund"
DEFAULT_CREATE_DASHBOARD = True
DEFAULT_PERSON_TRACKING = False

# Entity types
BINARY_SENSOR_PREFIX = "binary_sensor"
SENSOR_PREFIX = "sensor"
INPUT_BOOLEAN_PREFIX = "input_boolean"
COUNTER_PREFIX = "counter"
INPUT_DATETIME_PREFIX = "input_datetime"
INPUT_TEXT_PREFIX = "input_text"

# Meal types
MEAL_TYPES = {
    "morning": "Frühstück",
    "lunch": "Mittagessen", 
    "evening": "Abendessen",
    "snack": "Leckerli"
}

# Activity types
ACTIVITY_TYPES = {
    "walk": "Gassi gehen",
    "outside": "Draußen",
    "play": "Spielen",
    "training": "Training",
    "other": "Sonstiges"
}

# Service names
SERVICE_TRIGGER_FEEDING_REMINDER = "trigger_feeding_reminder"
SERVICE_DAILY_RESET = "daily_reset"
SERVICE_SEND_NOTIFICATION = "send_notification"
SERVICE_SET_VISITOR_MODE = "set_visitor_mode"
SERVICE_LOG_ACTIVITY = "log_activity"

# Entity suffixes
ENTITIES = {
    # Binary sensors
    "feeding_complete": "feeding_complete",
    "daily_tasks_complete": "daily_tasks_complete", 
    "visitor_mode": "visitor_mode",
    "outside_status": "outside_status",
    "needs_attention": "needs_attention",
    
    # Sensors
    "status": "status",
    "feeding_status": "feeding_status",
    "activity": "activity",
    "daily_summary": "daily_summary",
    "last_activity": "last_activity",
    
    # Input booleans
    "feeding_morning": "feeding_morning",
    "feeding_lunch": "feeding_lunch", 
    "feeding_evening": "feeding_evening",
    "feeding_snack": "feeding_snack",
    "outside": "outside",
    "visitor_mode_input": "visitor_mode_input",
    
    # Counters
    "feeding_count": "feeding_count",
    "outside_count": "outside_count",
    "activity_count": "activity_count",
    
    # Input datetimes
    "last_feeding_morning": "last_feeding_morning",
    "last_feeding_lunch": "last_feeding_lunch",
    "last_feeding_evening": "last_feeding_evening", 
    "last_feeding_snack": "last_feeding_snack",
    "last_outside": "last_outside",
    
    # Input texts
    "notes": "notes",
    "visitor_name": "visitor_name",
    "last_activity_notes": "last_activity_notes"
}

# Status messages
STATUS_MESSAGES = {
    "all_good": "Alles in Ordnung",
    "needs_feeding": "Fütterung erforderlich",
    "needs_outside": "Muss raus",
    "visitor_mode": "Besuchsmodus aktiv",
    "attention_needed": "Aufmerksamkeit erforderlich"
}

# Icons
ICONS = {
    "dog": "mdi:dog",
    "food": "mdi:food-variant",
    "walk": "mdi:walk",
    "outside": "mdi:door-open",
    "visitor": "mdi:account-supervisor",
    "attention": "mdi:alert-circle",
    "complete": "mdi:check-circle",
    "notes": "mdi:note-text"
}

# Update intervals (in seconds)
UPDATE_INTERVAL = 30

# Dashboard configuration
DASHBOARD_CONFIG = {
    "title": "🐶 Hundesystem",
    "icon": "mdi:dog",
    "path": "hundesystem",
    "show_in_sidebar": True,
    "require_admin": False
}
