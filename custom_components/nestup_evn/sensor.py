"""Setup and manage HomeAssistant Entities."""

import logging
from typing import Any
import os
import json

from homeassistant.components.sensor import (
    DOMAIN as ENTITY_DOMAIN,
    SensorEntity,
    SensorStateClass,
)
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
    CONF_AREA,
    CONF_CUSTOMER_ID,
    CONF_DEVICE_MANUFACTURER,
    CONF_DEVICE_MODEL,
    CONF_DEVICE_NAME,
    CONF_DEVICE_SW_VERSION,
    CONF_ERR_INVALID_AUTH,
    CONF_MONTHLY_START,
    CONF_PASSWORD,
    CONF_SUCCESS,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .types import EVN_SENSORS, EVNSensorEntityDescription

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Setup the sensor platform."""

    entry_config = hass.data[DOMAIN][entry.entry_id]

    evn_api = nestup_evn.EVNAPI(hass, True)
    evn_device = EVNDevice(entry_config, evn_api)

    await evn_device.async_create_coordinator(hass)

    entities = []
    entities.extend(
        [EVNSensor(evn_device, description, hass) for description in EVN_SENSORS]
    )

    async_add_entities(entities)


class EVNDevice:
    """EVN Device Instance"""

    def __init__(self, dataset, api: nestup_evn.EVNAPI) -> None:
        """Construct Device wrapper."""
        self._name = f"{CONF_DEVICE_NAME}: {dataset[CONF_CUSTOMER_ID]}"
        self._coordinator: DataUpdateCoordinator = None
        self.hass = api.hass
        self._username = dataset.get(CONF_USERNAME)
        self._password = dataset.get(CONF_PASSWORD)
        self._area_name = dataset.get(CONF_AREA)
        self._customer_id = dataset.get(CONF_CUSTOMER_ID)
        self._monthly_start = dataset.get(CONF_MONTHLY_START)
        self._api = api
        self._data = {}
        self._branches_data = None  # Will store the branch data

    async def async_load_branches(self):
        """Load EVN branches data asynchronously"""
        try:
            file_path = os.path.join(os.path.dirname(nestup_evn.__file__), "evn_branches.json")
            self._branches_data = await self.hass.async_add_executor_job(
                nestup_evn.read_evn_branches_file, file_path
            )
        except Exception as ex:
            _LOGGER.error("Error loading branches data: %s", str(ex))

    async def update(self) -> dict[str, Any]:
        """Update device data from EVN Endpoints."""

        self._data = await self._api.request_update(
            self._area_name, self._username, self._password, self._customer_id, self._monthly_start
        )

        status = self._data.get("status")

        if status != CONF_SUCCESS:

            if status == CONF_ERR_INVALID_AUTH:
                _LOGGER.info(
                    "[EVN ID %s] Expired session, try reauthenticating.",
                    self._customer_id,
                )

                login_state = await self._api.login(
                    self._area_name, self._username, self._password
                )

                if login_state == CONF_SUCCESS:
                    self._data = await self._api.request_update(
                        self._area_name, self._customer_id, self._monthly_start
                    )
                    status = self._data.get("status")

        if status == CONF_SUCCESS:
            _LOGGER.info(
                "[EVN ID %s] Successfully fetched new data from EVN Server.",
                self._customer_id,
            )

        else:
            _LOGGER.warn(
                "[EVN ID %s] Could not fetch new data - %s",
                self._customer_id,
                self._data.get("data"),
            )

        return self._data

    async def _async_update(self):
        """Fetch the latest data from EVN."""
        await self.update()

    async def async_create_coordinator(self, hass: HomeAssistant) -> None:
        """Create the coordinator for this specific device."""
        if self._coordinator:
            return

        await self.async_load_branches()

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{self._customer_id}",
            update_method=self._async_update,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        await coordinator.async_config_entry_first_refresh()
        self._coordinator = coordinator

    @property
    def info(self) -> DeviceInfo:
        """Return device description for device registry."""
        evn_area = nestup_evn.get_evn_info_sync(self._customer_id, self._branches_data)
        hw_version = f"by {self._area_name['name']}"

        if (evn_area["status"] == CONF_SUCCESS) and (
            evn_area["evn_branch"] != "Unknown"
        ):
            hw_version = f"by {evn_area['evn_branch']}"

        return DeviceInfo(
            name=self._name,
            identifiers={(DOMAIN, self._customer_id)},
            manufacturer=CONF_DEVICE_MANUFACTURER,
            sw_version=CONF_DEVICE_SW_VERSION,
            hw_version=hw_version,
            model=CONF_DEVICE_MODEL,
        )

    @property
    def coordinator(self) -> DataUpdateCoordinator or None:
        """Return coordinator associated."""
        return self._coordinator

    @property
    def branch_info(self):
        """Get branch info synchronously."""
        if self._branches_data is None:
            return {"status": CONF_ERR_UNKNOWN}
        return nestup_evn.get_evn_info_sync(self._customer_id, self._branches_data)


class EVNSensor(CoordinatorEntity, SensorEntity):
    """EVN Sensor Instance."""

    def __init__(
        self, device: EVNDevice, description: EVNSensorEntityDescription, hass
    ):
        """Construct EVN sensor wrapper."""
        super().__init__(device.coordinator)

        self._device = device
        self._attr_name = f"{device._name} {description.name}"
        self._unique_id = str(f"{device._customer_id}_{description.key}").lower()
        self._default_name = description.name

        self.entity_id = (
            f"{ENTITY_DOMAIN}.{device._customer_id}_{description.key}".lower()
        )
        self.entity_description = description

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self.entity_description.value_fn(self._device._data)

        if self.entity_description.dynamic_name:
            self._attr_name = f"{self._default_name} {data.get('info')}"

        if self.entity_description.dynamic_icon:
            self._attr_icon = data.get("info")

        return data.get("value")

    @property
    def device_info(self):
        """Return a device description for device registry."""
        hw_version = f"by {self._device._area_name['name']}"

        evn_area = self._device.branch_info
        if (evn_area["status"] == CONF_SUCCESS) and (
            evn_area["evn_branch"] != "Unknown"
        ):
            hw_version = f"by {evn_area['evn_branch']}"

        return DeviceInfo(
            name=self._device._name,
            identifiers={(DOMAIN, self._device._customer_id)},
            manufacturer=CONF_DEVICE_MANUFACTURER,
            sw_version=CONF_DEVICE_SW_VERSION,
            hw_version=hw_version,
            model=CONF_DEVICE_MODEL,
        )

    @property
    def available(self) -> bool:
        """Return the availability of the sensor."""
        return (
            self._device._data["status"] == CONF_SUCCESS
            and self.native_value is not None
        )

    @property
    def last_reset(self):
        if self.entity_description.state_class == SensorStateClass.TOTAL:
            data = self.entity_description.value_fn(self._device._data)

            return data.get("info")

        return None