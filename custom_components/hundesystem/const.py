"""Constants for the Hundesystem integration."""

# Integration domain
DOMAIN = "hundesystem"

# Configuration keys
CONF_DOG_NAME = "dog_name"
CONF_PUSH_DEVICES = "push_devices"
CONF_PERSON_TRACKING = "person_tracking"
CONF_CREATE_DASHBOARD = "create_dashboard"
CONF_DOOR_SENSOR = "door_sensor"
CONF_FEEDING_TIMES = "feeding_times"
CONF_RESET_TIME = "reset_time"

# Default values
DEFAULT_DOG_NAME = "hund"
DEFAULT_CREATE_DASHBOARD = True
DEFAULT_PERSON_TRACKING = True
DEFAULT_RESET_TIME = "23:59:00"

# Entity types
BINARY_SENSOR_PREFIX = "binary_sensor"
SENSOR_PREFIX = "sensor"
INPUT_BOOLEAN_PREFIX = "input_boolean"
COUNTER_PREFIX = "counter"
INPUT_DATETIME_PREFIX = "input_datetime"
INPUT_TEXT_PREFIX = "input_text"
BUTTON_PREFIX = "button"

# Feeding types
FEEDING_TYPES = ["morning", "lunch", "evening", "snack"]

# Meal types with German translations
MEAL_TYPES = {
    "morning": "Frühstück",
    "lunch": "Mittagessen", 
    "evening": "Abendessen",
    "snack": "Leckerli"
}

# Activity types with German translations
ACTIVITY_TYPES = {
    "walk": "Gassi gehen",
    "outside": "Draußen",
    "play": "Spielen",
    "training": "Training",
    "other": "Sonstiges",
    "poop": "Geschäft gemacht",
    "vet": "Tierarzt",
    "grooming": "Pflege"
}

# Service names
SERVICE_TRIGGER_FEEDING_REMINDER = "trigger_feeding_reminder"
SERVICE_DAILY_RESET = "daily_reset"
SERVICE_SEND_NOTIFICATION = "send_notification"
SERVICE_SET_VISITOR_MODE = "set_visitor_mode"
SERVICE_LOG_ACTIVITY = "log_activity"
SERVICE_ADD_DOG = "add_dog"
SERVICE_TEST_NOTIFICATION = "test_notification"
SERVICE_EMERGENCY_CONTACT = "emergency_contact"
SERVICE_HEALTH_CHECK = "health_check"

# Entity suffixes
ENTITIES = {
    # Binary sensors
    "feeding_complete": "feeding_complete",
    "daily_tasks_complete": "daily_tasks_complete", 
    "visitor_mode": "visitor_mode",
    "outside_status": "outside_status",
    "needs_attention": "needs_attention",
    "health_status": "health_status",
    "emergency_status": "emergency_status",
    
    # Sensors
    "status": "status",
    "feeding_status": "feeding_status",
    "activity": "activity",
    "daily_summary": "daily_summary",
    "last_activity": "last_activity",
    "health_score": "health_score",
    "mood": "mood",
    "weekly_summary": "weekly_summary",
    
    # Input booleans
    "feeding_morning": "feeding_morning",
    "feeding_lunch": "feeding_lunch", 
    "feeding_evening": "feeding_evening",
    "feeding_snack": "feeding_snack",
    "outside": "outside",
    "visitor_mode_input": "visitor_mode_input",
    "was_dog": "was_dog",
    "poop_done": "poop_done",
    "medication_given": "medication_given",
    "emergency_mode": "emergency_mode",
    
    # Counters
    "feeding_morning_count": "feeding_morning_count",
    "feeding_lunch_count": "feeding_lunch_count",
    "feeding_evening_count": "feeding_evening_count",
    "feeding_snack_count": "feeding_snack_count",
    "outside_count": "outside_count",
    "activity_count": "activity_count",
    "poop_count": "poop_count",
    "walk_count": "walk_count",
    "play_count": "play_count",
    "training_count": "training_count",
    
    # Input datetimes
    "last_feeding_morning": "last_feeding_morning",
    "last_feeding_lunch": "last_feeding_lunch",
    "last_feeding_evening": "last_feeding_evening", 
    "last_feeding_snack": "last_feeding_snack",
    "last_outside": "last_outside",
    "last_activity": "last_activity",
    "last_door_ask": "last_door_ask",
    "last_poop": "last_poop",
    "last_vet_visit": "last_vet_visit",
    "next_vet_appointment": "next_vet_appointment",
    "medication_time": "medication_time",
    
    # Input texts
    "notes": "notes",
    "visitor_name": "visitor_name",
    "last_activity_notes": "last_activity_notes",
    "emergency_contact": "emergency_contact",
    "vet_contact": "vet_contact",
    "medication_notes": "medication_notes",
    "health_notes": "health_notes",
    "behavior_notes": "behavior_notes",
    
    # Buttons
    "daily_reset_button": "daily_reset_button",
    "feeding_reminder_button": "feeding_reminder_button",
    "test_notification_button": "test_notification_button",
    "emergency_button": "emergency_button",
    "quick_outside_button": "quick_outside_button",
    "quick_feeding_button": "quick_feeding_button",
}

# Status messages
STATUS_MESSAGES = {
    "all_good": "Alles in Ordnung",
    "needs_feeding": "Fütterung erforderlich",
    "needs_outside": "Muss raus",
    "visitor_mode": "Besuchsmodus aktiv",
    "attention_needed": "Aufmerksamkeit erforderlich",
    "emergency": "Notfall",
    "sick": "Gesundheitsprobleme",
    "happy": "Zufrieden",
    "active": "Sehr aktiv",
    "bored": "Gelangweilt",
    "tired": "Müde"
}

# Icons mapping
ICONS = {
    # General
    "dog": "mdi:dog",
    "food": "mdi:food-variant",
    "walk": "mdi:walk",
    "outside": "mdi:door-open",
    "visitor": "mdi:account-supervisor",
    "attention": "mdi:alert-circle",
    "complete": "mdi:check-circle",
    "notes": "mdi:note-text",
    "reset": "mdi:restart",
    "status": "mdi:information-outline",
    
    # Meals
    "morning": "mdi:weather-sunrise",
    "lunch": "mdi:weather-sunny", 
    "evening": "mdi:weather-sunset",
    "snack": "mdi:food-croissant",
    
    # Activities
    "play": "mdi:tennis-ball",
    "training": "mdi:school",
    "poop": "mdi:emoticon-poop",
    "vet": "mdi:medical-bag",
    "grooming": "mdi:brush",
    
    # Health & Emergency
    "health": "mdi:heart-pulse",
    "emergency": "mdi:alarm-light",
    "medication": "mdi:pill",
    "thermometer": "mdi:thermometer",
    
    # Buttons
    "bell": "mdi:bell-ring",
    "test": "mdi:test-tube",
    "quick": "mdi:flash",
    
    # Mood indicators
    "happy": "mdi:emoticon-happy",
    "sad": "mdi:emoticon-sad",
    "neutral": "mdi:emoticon-neutral",
    "excited": "mdi:emoticon-excited",
}

# Default feeding times
DEFAULT_FEEDING_TIMES = {
    "morning": "07:00:00",
    "lunch": "12:00:00",
    "evening": "18:00:00",
    "snack": "15:00:00"
}

# Health monitoring thresholds
HEALTH_THRESHOLDS = {
    "max_hours_without_food": 12,
    "max_hours_without_outside": 8,
    "max_days_without_poop": 2,
    "min_daily_activities": 2,
}

# Notification priorities
NOTIFICATION_PRIORITIES = {
    "low": "low",
    "normal": "normal", 
    "high": "high",
    "critical": "critical"
}

# Dashboard configuration
DASHBOARD_CONFIG = {
    "title": "🐶 Hundesystem",
    "icon": "mdi:dog",
    "path": "hundesystem",
    "show_in_sidebar": True,
    "require_admin": False
}

# Update intervals (in seconds)
UPDATE_INTERVAL = 30
HEALTH_CHECK_INTERVAL = 300  # 5 minutes

# Visitor mode settings
VISITOR_MODE_SETTINGS = {
    "reduced_notifications": True,
    "disable_automatic_reminders": True,
    "emergency_contacts_only": False
}

# Multi-dog support
MAX_DOGS = 10
DOG_NAME_PATTERN = r"^[a-z][a-z0-9_]*$"

# Blueprint automation names
BLUEPRINT_AUTOMATIONS = {
    "door_sensor": "hundesystem_door_sensor",
    "feeding_reminder": "hundesystem_feeding_reminder", 
    "daily_reset": "hundesystem_daily_reset",
    "health_check": "hundesystem_health_check"
}

# Event names for automations
EVENTS = {
    "dog_outside_confirmed": "hundesystem_dog_outside_confirmed",
    "dog_outside_denied": "hundesystem_dog_outside_denied", 
    "feeding_completed": "hundesystem_feeding_completed",
    "emergency_activated": "hundesystem_emergency_activated",
    "visitor_mode_changed": "hundesystem_visitor_mode_changed"
}

# Weather integration
WEATHER_CONDITIONS = {
    "rain": "Regen",
    "snow": "Schnee",
    "storm": "Sturm",
    "hot": "Heiß",
    "cold": "Kalt"
}

# Seasonal adjustments
SEASONAL_ADJUSTMENTS = {
    "summer": {
        "early_morning_walk": True,
        "midday_break": True,
        "extra_water": True
    },
    "winter": {
        "shorter_walks": True,
        "warm_clothing": True,
        "de_ice_paws": True
    }
}
    "