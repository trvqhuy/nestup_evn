from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_MANUFACTURER,
    CONF_DEVICE_MODEL,
    CONF_DEVICE_SW_VERSION,
    DEVICE_ENTITIES,
    DOMAIN,
    POLLING_INTERVAL_IN_MINS,
)
from . import nestup_evn

from datetime import timedelta

SCAN_INTERVAL = timedelta(minutes=POLLING_INTERVAL_IN_MINS)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EVN Component."""

    component = hass.data[DOMAIN][config_entry.entry_id]

    evn_api = nestup_evn.EVNAPI()
    data_probe = nestup_evn.EVNData(config_entry.data, evn_api)

    new_devices = []
    for entity in DEVICE_ENTITIES:
        new_devices.append(EVNSensor(component.device, data_probe, entity))

    if new_devices:
        async_add_entities(new_devices, True)


class Component:
    def __init__(self, hass: HomeAssistant, host: str) -> None:
        self._host = host
        self._hass = hass
        self._name = host
        self._id = f"{host.lower()}_component"
        self.device = Device(
            f"evn_monitor_{self._id}", f"EVN Monitor: {self._name}", self
        )
        self.online = True

    @property
    def component_id(self) -> str:
        return self._id


class Device:
    def __init__(self, device_id: str, name: str, component: Component) -> None:
        self._id = device_id
        self.name = name

        self.sw_version = CONF_DEVICE_SW_VERSION
        self.model = CONF_DEVICE_MODEL
        self.manufacturer = CONF_DEVICE_MANUFACTURER

    @property
    def device_id(self) -> str:
        return self._id

    @property
    def online(self) -> bool:
        return True


class EVNSensor(SensorEntity):
    def __init__(self, device, probe, entityInfo):
        self._probe = probe
        self._device = device
        self._id = entityInfo.id

        self._attr_unique_id = f"{self._device.device_id}_{entityInfo.id}"
        self._attr_name = f"{self._device.name} {entityInfo.friendly_name}"
        self._attr_device_class = entityInfo.entity_class
        self._attr_native_unit_of_measurement = entityInfo.unit
        self._icon = entityInfo.icon

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device.device_id)},
            manufacturer=self._device.manufacturer,
            name=self._device.name,
            sw_version=self._device.sw_version,
            model=self._device.model,
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._probe.get_data(self._id)

    def update(self):
        """Get the latest data from the EVN API and updates the state."""
        self._probe.update()

    @property
    def icon(self):
        return self._icon

    def available(self) -> bool:
        return self._device.online
