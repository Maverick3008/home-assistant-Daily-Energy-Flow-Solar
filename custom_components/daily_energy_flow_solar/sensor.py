"""Sensor platform for Daily Energy Flow Solar."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_AUTARKY_PERCENT,
    ATTR_BATTERY_CHARGE_TODAY,
    ATTR_BATTERY_DISCHARGE_TODAY,
    ATTR_CURRENT_GRID_PRICE,
    ATTR_GRID_EXPORT_POWER,
    ATTR_GRID_EXPORT_TODAY,
    ATTR_GRID_IMPORT_AVERAGE_PRICE_TODAY,
    ATTR_GRID_IMPORT_COST_TODAY,
    ATTR_GRID_IMPORT_TODAY,
    ATTR_HOUSE_CONSUMPTION_TODAY,
    ATTR_PV_SELF_CONSUMPTION_PERCENT,
    ATTR_PV_SELF_CONSUMPTION_POWER,
    ATTR_PV_SELF_CONSUMPTION_TODAY,
    ATTR_SOLAR_PRODUCTION_POWER,
    ATTR_SOLAR_PRODUCTION_TODAY,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    SIGNAL_UPDATE,
)
from .hub import DailyEnergyFlowHub

CURRENCY_EUR = "EUR"
PRICE_EUR_PER_KWH = "EUR/kWh"


@dataclass(frozen=True, kw_only=True)
class DailyEnergyFlowEntityDescription(SensorEntityDescription):
    """Describes a Daily Energy Flow Solar sensor entity."""

    value_key: str = ""
    attributes_fn: Callable[[DailyEnergyFlowHub], dict[str, Any]] | None = None


POWER_SENSORS: tuple[DailyEnergyFlowEntityDescription, ...] = (
    DailyEnergyFlowEntityDescription(
        key="solar_production_power",
        translation_key="solar_production_power",
        name="Solarproduktion Leistung",
        value_key=ATTR_SOLAR_PRODUCTION_POWER,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        icon="mdi:solar-power",
    ),
    DailyEnergyFlowEntityDescription(
        key="grid_export_power",
        translation_key="grid_export_power",
        name="Netzeinspeisung Leistung",
        value_key=ATTR_GRID_EXPORT_POWER,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        icon="mdi:transmission-tower-export",
    ),
    DailyEnergyFlowEntityDescription(
        key="pv_self_consumption_power",
        translation_key="pv_self_consumption_power",
        name="PV-Eigenverbrauch Leistung",
        value_key=ATTR_PV_SELF_CONSUMPTION_POWER,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        icon="mdi:home-lightning-bolt",
        attributes_fn=lambda hub: hub.pv_self_consumption_power_attributes(),
    ),
)

ENERGY_SENSORS: tuple[DailyEnergyFlowEntityDescription, ...] = (
    DailyEnergyFlowEntityDescription(
        key="grid_import_today",
        translation_key="grid_import_today",
        name="Netzbezug heute",
        value_key=ATTR_GRID_IMPORT_TODAY,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:transmission-tower-import",
    ),
    DailyEnergyFlowEntityDescription(
        key="grid_export_today",
        translation_key="grid_export_today",
        name="Netzeinspeisung heute",
        value_key=ATTR_GRID_EXPORT_TODAY,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:transmission-tower-export",
    ),
    DailyEnergyFlowEntityDescription(
        key="solar_production_today",
        translation_key="solar_production_today",
        name="Solarproduktion heute",
        value_key=ATTR_SOLAR_PRODUCTION_TODAY,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:solar-power-variant",
    ),
    DailyEnergyFlowEntityDescription(
        key="battery_charge_today",
        translation_key="battery_charge_today",
        name="Akkuladung heute",
        value_key=ATTR_BATTERY_CHARGE_TODAY,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:battery-arrow-up",
    ),
    DailyEnergyFlowEntityDescription(
        key="battery_discharge_today",
        translation_key="battery_discharge_today",
        name="Akkuentladung heute",
        value_key=ATTR_BATTERY_DISCHARGE_TODAY,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:battery-arrow-down",
    ),
    DailyEnergyFlowEntityDescription(
        key="pv_self_consumption_today",
        translation_key="pv_self_consumption_today",
        name="PV-Eigenverbrauch heute",
        value_key=ATTR_PV_SELF_CONSUMPTION_TODAY,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:home-battery",
        attributes_fn=lambda hub: hub.pv_self_consumption_today_attributes(),
    ),
    DailyEnergyFlowEntityDescription(
        key="house_consumption_today",
        translation_key="house_consumption_today",
        name="Hausverbrauch heute",
        value_key=ATTR_HOUSE_CONSUMPTION_TODAY,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:home-import-outline",
        attributes_fn=lambda hub: hub.house_consumption_today_attributes(),
    ),
)

PERCENT_SENSORS: tuple[DailyEnergyFlowEntityDescription, ...] = (
    DailyEnergyFlowEntityDescription(
        key="autarky_percent",
        translation_key="autarky_percent",
        name="Autarkie",
        value_key=ATTR_AUTARKY_PERCENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:home-percent",
    ),
    DailyEnergyFlowEntityDescription(
        key="pv_self_consumption_percent",
        translation_key="pv_self_consumption_percent",
        name="PV-Eigenverbrauch",
        value_key=ATTR_PV_SELF_CONSUMPTION_PERCENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:percent",
    ),
)

COST_AND_PRICE_SENSORS: tuple[DailyEnergyFlowEntityDescription, ...] = (
    DailyEnergyFlowEntityDescription(
        key="current_grid_price",
        translation_key="current_grid_price",
        name="Aktueller Netzstrompreis",
        value_key=ATTR_CURRENT_GRID_PRICE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PRICE_EUR_PER_KWH,
        icon="mdi:currency-eur",
    ),
    DailyEnergyFlowEntityDescription(
        key="grid_import_cost_today",
        translation_key="grid_import_cost_today",
        name="Netzbezug Kosten heute",
        value_key=ATTR_GRID_IMPORT_COST_TODAY,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=CURRENCY_EUR,
        icon="mdi:cash",
        attributes_fn=lambda hub: hub.grid_import_cost_today_attributes(),
    ),
    DailyEnergyFlowEntityDescription(
        key="grid_import_average_price_today",
        translation_key="grid_import_average_price_today",
        name="Durchschnittlicher Netzstrompreis heute",
        value_key=ATTR_GRID_IMPORT_AVERAGE_PRICE_TODAY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PRICE_EUR_PER_KWH,
        icon="mdi:cash-multiple",
    ),
)

ALL_SENSORS = POWER_SENSORS + ENERGY_SENSORS + PERCENT_SENSORS + COST_AND_PRICE_SENSORS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daily Energy Flow Solar sensors from a config entry."""
    hub: DailyEnergyFlowHub = hass.data[DOMAIN][entry.entry_id]

    entities = [
        DailyEnergyFlowSensor(hub, entry, description) for description in ALL_SENSORS
    ]
    async_add_entities(entities)


class DailyEnergyFlowSensor(SensorEntity):
    """Representation of a single Daily Energy Flow Solar calculated sensor."""

    entity_description: DailyEnergyFlowEntityDescription
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        hub: DailyEnergyFlowHub,
        entry: ConfigEntry,
        description: DailyEnergyFlowEntityDescription,
    ) -> None:
        self._hub = hub
        self._entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to hub updates once the entity is registered."""
        signal = SIGNAL_UPDATE.format(entry_id=self._entry.entry_id)
        self.async_on_remove(
            async_dispatcher_connect(self.hass, signal, self._async_hub_updated)
        )

    @callback
    def _async_hub_updated(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        raw_value = self._hub.data.get(self.entity_description.value_key)
        if raw_value is None:
            return None
        return round(float(raw_value), self._hub.decimal_places)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self._hub)

    @property
    def available(self) -> bool:
        return self.entity_description.value_key in self._hub.data
