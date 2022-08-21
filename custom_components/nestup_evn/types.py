from __future__ import annotations
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import ENERGY_KILO_WATT_HOUR
from .const import *
from dataclasses import dataclass


@dataclass
class Entity:
    """Describe the sensor entities."""

    id: str
    friendly_name: str
    entity_class: str
    unit: str
    icon: str
    state_class: SensorStateClass | None


@dataclass
class Area:
    """Describe the supported areas."""

    name: str
    evn_login_url: str
    evn_data_request_url: str


VIETNAM_EVN_AREA = [
    Area(
        "EVNHCMC - Ho Chi Minh City",
        "https://cskh.evnhcmc.vn/Dangnhap/checkLG",
        "https://cskh.evnhcmc.vn/Tracuu/ajax_dienNangTieuThuTheoNgay",
    ),
    Area(
        "EVNSPC - Southern Vietnam",
        "(EVNSPC does not need this field)",
        "https://www.cskh.evnspc.vn/TraCuu/TraCuuSanLuongDienTieuThuTrongNgay",
    ),
]


@dataclass
class EVNRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[Any], float]


@dataclass
class EVNSensorEntityDescription(SensorEntityDescription, EVNRequiredKeysMixin):
    """Describes EVN sensor entity."""


EVN_SENSORS: tuple[EVNSensorEntityDescription, ...] = (
    EVNSensorEntityDescription(
        key=ID_ECON_PER_DAY,
        name="Daily E-consump.",
        icon="mdi:flash-outline",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_PER_DAY],
    ),
    EVNSensorEntityDescription(
        key=ID_ECON_PER_MONTH,
        name="Monthly E-consump.",
        icon="mdi:flash-outline",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_PER_MONTH],
    ),
    EVNSensorEntityDescription(
        key=ID_ECOST_PER_DAY,
        name="Daily E-cost",
        icon="mdi:cash-multiple",
        native_unit_of_measurement="VNĐ",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data[ID_ECOST_PER_DAY],
    ),
    EVNSensorEntityDescription(
        key=ID_ECOST_PER_MONTH,
        name="Monthly E-cost",
        icon="mdi:cash-multiple",
        native_unit_of_measurement="VNĐ",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data[ID_ECOST_PER_MONTH],
    ),
    EVNSensorEntityDescription(
        key=ID_LATEST_UPDATE,
        name="Latest Update",
        icon="mdi:calendar-check",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data[ID_LATEST_UPDATE],
    ),
    EVNSensorEntityDescription(
        key=ID_FROM_DATE,
        name="Date Start",
        icon="mdi:calendar-clock",
        value_fn=lambda data: data[ID_FROM_DATE],
    ),
    EVNSensorEntityDescription(
        key=ID_TO_DATE,
        name="Last Date",
        icon="mdi:calendar-clock",
        value_fn=lambda data: data[ID_TO_DATE],
    ),
)
