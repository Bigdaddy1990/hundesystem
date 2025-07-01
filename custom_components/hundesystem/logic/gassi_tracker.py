import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

async def track_door_event(hass, sensor, hundeliste):
    now = datetime.now().strftime("%H:%M:%S")
    _LOGGER.info(f"[Hundesystem] Türsensor {sensor} ausgelöst – Zeit: {now}")
    hass.states.async_set("sensor.hundesystem_letzter_gassi", now)

    for hund in hundeliste.split(","):
        hund = hund.strip().lower()
        hass.states.async_set(f"sensor.{hund}_letzte_aktion", now)
