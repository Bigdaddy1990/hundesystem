"""Constants for Hundesystem integration."""

DOMAIN = "hundesystem"

# Configuration keys
CONF_PUSH_DEVICES = "push_devices"
CONF_PERSON_TRACKING = "use_person_tracking"
CONF_DASHBOARD = "create_dashboard"

# Services
SERVICE_TRIGGER_FEEDING_REMINDER = "trigger_feeding_reminder"
SERVICE_DAILY_RESET = "daily_reset"
SERVICE_SEND_NOTIFICATION = "send_notification"

# Entity types
FEEDING_TYPES = ["morning", "lunch", "evening", "snack"]
ACTIVITY_TYPES = ["outside", "visitor_mode"]
HELPER_TYPES = ["statistic_reset"]

# Icons
ICONS = {
    "morning": "mdi:weather-sunrise",
    "lunch": "mdi:weather-sunny", 
    "evening": "mdi:weather-sunset",
    "snack": "mdi:food-croissant",
    "outside": "mdi:door-open",
    "visitor_mode": "mdi:account-group",
    "reset": "mdi:restart",
    "dog": "mdi:dog",
    "status": "mdi:information-outline"
}

# Meal translations
MEAL_TRANSLATIONS = {
    "morning": "Frühstück",
    "lunch": "Mittagessen",
    "evening": "Abendessen", 
    "snack": "Leckerli"
}