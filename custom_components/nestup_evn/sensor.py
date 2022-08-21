from typing import Any
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import nestup_evn
from .const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_AREA,
    CONF_CUSTOMER_ID,
    CONF_DEVICE_MANUFACTURER,
    CONF_DEVICE_MODEL,
    CONF_DEVICE_NAME,
    CONF_DEVICE_SW_VERSION,
    CONF_MONTHLY_START,
    CONF_SUCCESS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

from .types import EVN_SENSORS, VIETNAM_EVN_AREA, EVNSensorEntityDescription

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Setup the sensor platform."""

    entry_config = hass.data[DOMAIN][entry.entry_id]

    evn_api = nestup_evn.EVNAPI(hass)
    evn_device = EVNDevice(entry_config, evn_api)

    await evn_device.async_create_coordinator(hass)

    entities = []
    entities.extend([EVNSensor(evn_device, description) for description in EVN_SENSORS])

    async_add_entities(entities, True)


class EVNDevice:
    """EVN Device Instance"""

    def __init__(self, dataset, api: nestup_evn.EVNAPI) -> None:
        """Construct a device wrapper."""

        self._name = f"{CONF_DEVICE_NAME}: {dataset[CONF_CUSTOMER_ID]}"
        self._coordinator: DataUpdateCoordinator | None = None

        self._username = dataset[CONF_USERNAME] or None
        self._password = dataset[CONF_PASSWORD] or None

        self._area_name = dataset[CONF_AREA]
        self._customer_id = dataset[CONF_CUSTOMER_ID]
        self._monthly_start = dataset[CONF_MONTHLY_START]

        self._api = api
        self._data = {}

    async def update(self) -> dict[str, Any]:
        if self._area_name == VIETNAM_EVN_AREA[0].name:
            login_state = await self._api.login(
                self._area_name, self._username, self._password
            )

            if login_state != CONF_SUCCESS:
                return

        _LOGGER.debug(
            "[EVN Monitor] Updating data for EVN Customer ID %s", self._customer_id
        )

        self._data = await self._api.request_update(
            self._area_name, self._customer_id, self._monthly_start
        )

        return self._data

    async def _async_update(self):
        """Pull the latest data from EVN."""
        await self.update()

    async def async_create_coordinator(self, hass: HomeAssistant) -> None:
        """Get the coordinator for a specific device."""
        if self._coordinator:
            return

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{self._customer_id}",
            update_method=self._async_update,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        await coordinator.async_refresh()
        self._coordinator = coordinator

    @property
    def info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        return DeviceInfo(
            name=self._name,
            identifiers={(DOMAIN, self._customer_id)},
            manufacturer=CONF_DEVICE_MANUFACTURER,
            sw_version=CONF_DEVICE_SW_VERSION,
            model=CONF_DEVICE_MODEL,
        )

    @property
    def coordinator(self) -> DataUpdateCoordinator | None:
        """Return coordinator associated."""
        return self._coordinator


class EVNSensor(CoordinatorEntity, SensorEntity):
    """EVN Sensor Instance"""

    def __init__(self, device: EVNDevice, description: EVNSensorEntityDescription):
        super().__init__(device.coordinator)

        self._device = device
        self._attr_unique_id = f"{device._customer_id}_{description.key}"
        self._attr_name = f"{device._name} {description.name}"

        self.entity_description = description

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self._device._data)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.info

    def available(self) -> bool:
        return self._device._data["status"] == CONF_SUCCESS
