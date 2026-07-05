"""The Daily Energy Flow Solar hub.

This module contains all the calculation logic for the integration. It
listens to the source entities selected in the config flow, normalizes
their values to a common unit system and derives all the calculated
sensors (PV self-consumption, house consumption, autarky, dynamic grid
import cost, ...).

No YAML template sensors are used - everything here feeds real sensor
entities registered by a Home Assistant custom integration.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, State, callback, Event
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_AUTARKY_PERCENT,
    ATTR_BATTERY_CHARGE_POWER,
    ATTR_BATTERY_CHARGE_TODAY,
    ATTR_BATTERY_DISCHARGE_POWER,
    ATTR_BATTERY_DISCHARGE_TODAY,
    ATTR_CURRENT_GRID_PRICE,
    ATTR_GRID_EXPORT_POWER,
    ATTR_GRID_EXPORT_TODAY,
    ATTR_GRID_IMPORT_AVERAGE_PRICE_TODAY,
    ATTR_GRID_IMPORT_COST_TODAY,
    ATTR_GRID_IMPORT_POWER,
    ATTR_GRID_IMPORT_TODAY,
    ATTR_HOUSE_CONSUMPTION_POWER,
    ATTR_HOUSE_CONSUMPTION_TODAY,
    ATTR_PV_SELF_CONSUMPTION_PERCENT,
    ATTR_PV_SELF_CONSUMPTION_POWER,
    ATTR_PV_SELF_CONSUMPTION_TODAY,
    ATTR_SOLAR_PRODUCTION_POWER,
    ATTR_SOLAR_PRODUCTION_TODAY,
    CONF_BATTERY_CHARGE_TODAY,
    CONF_BATTERY_DISCHARGE_TODAY,
    CONF_BATTERY_POWER,
    CONF_BATTERY_POWER_INVERTED,
    CONF_GRID_POWER,
    CONF_GRID_POWER_INVERTED,
    CONF_GRID_EXPORT_TODAY,
    CONF_GRID_IMPORT_TODAY,
    CONF_PRICE_SOURCE,
    CONF_PRICE_UNIT,
    CONF_SOLAR_PRODUCTION_POWER,
    CONF_SOLAR_PRODUCTION_TODAY,
    DEFAULT_DECIMAL_PLACES,
    CONF_DECIMAL_PLACES,
    PRICE_UNIT_CT_KWH,
    SIGNAL_UPDATE,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

BATTERY_NOTE = (
    "Akkuladung zählt als PV-Eigenverbrauch, aber nicht als Hausverbrauch. "
    "Akkuentladung zählt als Hausverbrauch."
)

COST_FORMULA = (
    "grid_import_cost_today += grid_import_delta_kwh * "
    "current_grid_import_price (bei jeder Änderung des Netzbezugs neu "
    "berechnet, nicht grid_import_today * current_price)"
)


def _to_float(value: Any) -> float | None:
    """Best-effort conversion of a state value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def normalize_energy(value: float, unit: str | None) -> float:
    """Normalize an energy value to kWh."""
    if unit == "Wh":
        return value / 1000.0
    if unit == "MWh":
        return value * 1000.0
    # kWh or unknown -> assume already kWh
    return value


def normalize_power(value: float, unit: str | None) -> float:
    """Normalize a power value to W."""
    if unit == "kW":
        return value * 1000.0
    if unit == "MW":
        return value * 1_000_000.0
    # W or unknown -> assume already W
    return value


def normalize_price(value: float, unit: str | None) -> float:
    """Normalize a price value to EUR/kWh."""
    if unit == PRICE_UNIT_CT_KWH:
        return value / 100.0
    return value


class DailyEnergyFlowHub:
    """Central hub that computes all Daily Energy Flow Solar values."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._unsub_listeners: list[Any] = []
        self._store: Store = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{entry.entry_id}"
        )

        # Cost tracker state
        self._last_grid_import_kwh: float | None = None
        self._grid_import_cost_today: float = 0.0
        self._tracked_day: date | None = None

        # Computed values, exposed to sensor entities
        self.data: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------
    def _conf(self, key: str, default: Any = None) -> Any:
        """Return an option if set, otherwise fall back to the config data."""
        if key in self.entry.options:
            return self.entry.options[key]
        return self.entry.data.get(key, default)

    @property
    def decimal_places(self) -> int:
        return int(self._conf(CONF_DECIMAL_PLACES, DEFAULT_DECIMAL_PLACES))

    def _entity_ids(self) -> list[str]:
        """All source entity ids this hub listens to."""
        keys = [
            CONF_GRID_IMPORT_TODAY,
            CONF_GRID_EXPORT_TODAY,
            CONF_SOLAR_PRODUCTION_TODAY,
            CONF_BATTERY_CHARGE_TODAY,
            CONF_BATTERY_DISCHARGE_TODAY,
            CONF_SOLAR_PRODUCTION_POWER,
            CONF_GRID_POWER,
            CONF_BATTERY_POWER,
            CONF_PRICE_SOURCE,
        ]
        return [self._conf(key) for key in keys if self._conf(key)]

    # ------------------------------------------------------------------
    # Setup / teardown
    # ------------------------------------------------------------------
    async def async_setup(self) -> None:
        """Set up state listeners, restore persisted cost data."""
        await self._async_restore_cost_data()

        entity_ids = self._entity_ids()
        if entity_ids:
            self._unsub_listeners.append(
                async_track_state_change_event(
                    self.hass, entity_ids, self._async_state_changed
                )
            )

        # Reset cost tracker at midnight, independent of state changes.
        self._unsub_listeners.append(
            async_track_time_change(
                self.hass, self._async_midnight_reset, hour=0, minute=0, second=0
            )
        )

        # Initial calculation using current states.
        await self._async_recalculate()

    async def async_unload(self) -> None:
        """Remove all listeners."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    async def _async_restore_cost_data(self) -> None:
        stored = await self._store.async_load()
        if not stored:
            return
        self._last_grid_import_kwh = stored.get("last_grid_import_kwh")
        self._grid_import_cost_today = stored.get("grid_import_cost_today", 0.0)
        tracked_day = stored.get("tracked_day")
        if tracked_day:
            try:
                self._tracked_day = date.fromisoformat(tracked_day)
            except ValueError:
                self._tracked_day = None

    async def _async_save_cost_data(self) -> None:
        await self._store.async_save(
            {
                "last_grid_import_kwh": self._last_grid_import_kwh,
                "grid_import_cost_today": self._grid_import_cost_today,
                "tracked_day": self._tracked_day.isoformat()
                if self._tracked_day
                else None,
            }
        )

    # ------------------------------------------------------------------
    # State reading helpers
    # ------------------------------------------------------------------
    def _read_energy(self, key: str) -> float:
        entity_id = self._conf(key)
        if not entity_id:
            return 0.0
        state = self.hass.states.get(entity_id)
        if state is None:
            return 0.0
        value = _to_float(state.state)
        if value is None:
            return 0.0
        unit = state.attributes.get("unit_of_measurement")
        return normalize_energy(value, unit)

    def _read_energy_or_none(self, key: str) -> float | None:
        """Like _read_energy, but returns None instead of 0.0 when the
        entity is missing, unavailable, or has an unparseable state.

        This distinction matters for the persistent grid import cost
        tracker: a transient "unavailable" state (e.g. right after a
        Home Assistant restart or an integration reload, before the
        source integration has repopulated its states) must NOT be
        treated as a real "0 kWh" reading. Doing so would corrupt the
        stored baseline and cause a large, bogus cost delta to be
        charged once the sensor reports its real value again.
        """
        entity_id = self._conf(key)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        value = _to_float(state.state)
        if value is None:
            return None
        unit = state.attributes.get("unit_of_measurement")
        return normalize_energy(value, unit)

    def _read_power(self, key: str) -> float:
        entity_id = self._conf(key)
        if not entity_id:
            return 0.0
        state = self.hass.states.get(entity_id)
        if state is None:
            return 0.0
        value = _to_float(state.state)
        if value is None:
            return 0.0
        unit = state.attributes.get("unit_of_measurement")
        return normalize_power(value, unit)

    def _read_price(self) -> float:
        entity_id = self._conf(CONF_PRICE_SOURCE)
        if not entity_id:
            return 0.0
        state = self.hass.states.get(entity_id)
        if state is None:
            return 0.0
        value = _to_float(state.state)
        if value is None:
            return 0.0
        price_unit = self._conf(CONF_PRICE_UNIT)
        return normalize_price(value, price_unit)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    @callback
    def _async_state_changed(self, event: Event) -> None:
        self.hass.async_create_task(self._async_recalculate())

    async def _async_midnight_reset(self, _now) -> None:
        """Reset the cost tracker at midnight."""
        self._grid_import_cost_today = 0.0
        self._last_grid_import_kwh = self._read_energy(CONF_GRID_IMPORT_TODAY)
        self._tracked_day = dt_util.now().date()
        await self._async_save_cost_data()
        await self._async_recalculate()

    # ------------------------------------------------------------------
    # Core calculation
    # ------------------------------------------------------------------
    def _update_grid_import_cost(
        self, grid_import_today: float | None, current_price: float
    ) -> None:
        """Update the accumulated grid import cost using deltas.

        Costs are calculated as:
            grid_import_cost_today += grid_import_delta_kwh * current_price

        This avoids the incorrect approach of multiplying the full daily
        counter by the current price, which would misrepresent costs when
        the price changes throughout the day.
        """
        if grid_import_today is None:
            # The grid import sensor is currently unavailable/unknown
            # (e.g. right after a restart or reload). Skip this cycle
            # entirely rather than treating it as a 0 kWh reading, which
            # would otherwise corrupt the stored baseline and cause a
            # bogus cost spike once the sensor comes back.
            return

        today = dt_util.now().date()

        if self._tracked_day is None:
            # First run ever (no persisted data yet).
            self._tracked_day = today
            self._last_grid_import_kwh = grid_import_today
            return

        if today != self._tracked_day:
            # Day rolled over (e.g. we were not listening at midnight).
            self._tracked_day = today
            self._grid_import_cost_today = 0.0
            self._last_grid_import_kwh = grid_import_today
            return

        if self._last_grid_import_kwh is None:
            self._last_grid_import_kwh = grid_import_today
            return

        delta = grid_import_today - self._last_grid_import_kwh

        if delta < 0:
            # The daily counter jumped backwards without a day change
            # (e.g. sensor / inverter reset). Treat the new value as the
            # new baseline instead of producing negative cost.
            self._last_grid_import_kwh = grid_import_today
            return

        if delta > 0:
            self._grid_import_cost_today += delta * current_price
            self._last_grid_import_kwh = grid_import_today

    async def _async_recalculate(self) -> None:
        """Recompute all derived values and notify sensors."""
        solar_production_power = self._read_power(CONF_SOLAR_PRODUCTION_POWER)

        # The grid power sensor is bidirectional and reports both Netzbezug
        # (grid import) and Netzeinspeisung (grid export) as a single signed
        # value. By convention: positive = Netzbezug, negative =
        # Netzeinspeisung. The "inverted" option flips this for sensors that
        # use the opposite sign convention.
        raw_grid_power = self._read_power(CONF_GRID_POWER)
        if self._conf(CONF_GRID_POWER_INVERTED, False):
            raw_grid_power = -raw_grid_power
        grid_import_power = max(raw_grid_power, 0.0)
        grid_export_power = max(-raw_grid_power, 0.0)

        pv_self_consumption_power = max(
            solar_production_power - grid_export_power, 0.0
        )

        # The battery power sensor is bidirectional and reports both
        # Akkuladung (battery charging) and Akkuentladung (battery
        # discharging) as a single signed value. By convention: positive =
        # Akkuladung, negative = Akkuentladung. The "inverted" option flips
        # this for sensors that use the opposite sign convention.
        raw_battery_power = self._read_power(CONF_BATTERY_POWER)
        if self._conf(CONF_BATTERY_POWER_INVERTED, False):
            raw_battery_power = -raw_battery_power
        battery_charge_power = max(raw_battery_power, 0.0)
        battery_discharge_power = max(-raw_battery_power, 0.0)

        house_consumption_power = max(
            grid_import_power
            + solar_production_power
            - grid_export_power
            - battery_charge_power
            + battery_discharge_power,
            0.0,
        )

        grid_import_today = self._read_energy(CONF_GRID_IMPORT_TODAY)
        grid_export_today = self._read_energy(CONF_GRID_EXPORT_TODAY)
        solar_production_today = self._read_energy(CONF_SOLAR_PRODUCTION_TODAY)
        battery_charge_today = self._read_energy(CONF_BATTERY_CHARGE_TODAY)
        battery_discharge_today = self._read_energy(CONF_BATTERY_DISCHARGE_TODAY)

        pv_self_consumption_today = max(
            solar_production_today - grid_export_today, 0.0
        )

        house_consumption_today = max(
            grid_import_today
            + solar_production_today
            - grid_export_today
            - battery_charge_today
            + battery_discharge_today,
            0.0,
        )

        if house_consumption_today <= 0:
            autarky_percent = 0.0
        else:
            autarky_percent = (
                (house_consumption_today - grid_import_today)
                / house_consumption_today
                * 100.0
            )
        autarky_percent = min(max(autarky_percent, 0.0), 100.0)

        if solar_production_today <= 0:
            pv_self_consumption_percent = 0.0
        else:
            pv_self_consumption_percent = (
                pv_self_consumption_today / solar_production_today * 100.0
            )
        pv_self_consumption_percent = min(
            max(pv_self_consumption_percent, 0.0), 100.0
        )

        current_grid_price = self._read_price()

        grid_import_today_for_cost = self._read_energy_or_none(CONF_GRID_IMPORT_TODAY)
        self._update_grid_import_cost(grid_import_today_for_cost, current_grid_price)
        await self._async_save_cost_data()

        if grid_import_today > 0:
            grid_import_average_price_today = (
                self._grid_import_cost_today / grid_import_today
            )
        else:
            grid_import_average_price_today = 0.0

        self.data = {
            ATTR_SOLAR_PRODUCTION_POWER: solar_production_power,
            ATTR_GRID_IMPORT_POWER: grid_import_power,
            ATTR_GRID_EXPORT_POWER: grid_export_power,
            ATTR_PV_SELF_CONSUMPTION_POWER: pv_self_consumption_power,
            ATTR_BATTERY_CHARGE_POWER: battery_charge_power,
            ATTR_BATTERY_DISCHARGE_POWER: battery_discharge_power,
            ATTR_HOUSE_CONSUMPTION_POWER: house_consumption_power,
            ATTR_GRID_IMPORT_TODAY: grid_import_today,
            ATTR_GRID_EXPORT_TODAY: grid_export_today,
            ATTR_SOLAR_PRODUCTION_TODAY: solar_production_today,
            ATTR_BATTERY_CHARGE_TODAY: battery_charge_today,
            ATTR_BATTERY_DISCHARGE_TODAY: battery_discharge_today,
            ATTR_PV_SELF_CONSUMPTION_TODAY: pv_self_consumption_today,
            ATTR_HOUSE_CONSUMPTION_TODAY: house_consumption_today,
            ATTR_AUTARKY_PERCENT: autarky_percent,
            ATTR_PV_SELF_CONSUMPTION_PERCENT: pv_self_consumption_percent,
            ATTR_CURRENT_GRID_PRICE: current_grid_price,
            ATTR_GRID_IMPORT_COST_TODAY: self._grid_import_cost_today,
            ATTR_GRID_IMPORT_AVERAGE_PRICE_TODAY: grid_import_average_price_today,
        }

        async_dispatcher_send(self.hass, SIGNAL_UPDATE.format(entry_id=self.entry.entry_id))

    # ------------------------------------------------------------------
    # Diagnostic attribute helpers, used by sensor.py
    # ------------------------------------------------------------------
    def pv_self_consumption_power_attributes(self) -> dict[str, Any]:
        return {
            "formula": "pv_self_consumption_power = max(solar_production_power - grid_export_power, 0)",
            "solar_production_power_used_w": self.data.get(ATTR_SOLAR_PRODUCTION_POWER),
            "grid_import_power_used_w": self.data.get(ATTR_GRID_IMPORT_POWER),
            "grid_export_power_used_w": self.data.get(ATTR_GRID_EXPORT_POWER),
            "calculated_pv_self_consumption_power_w": self.data.get(
                ATTR_PV_SELF_CONSUMPTION_POWER
            ),
            "grid_power_note": (
                "Netzbezug und Netzeinspeisung stammen aus demselben "
                "Netzleistungssensor: positiv = Netzbezug, negativ = "
                "Netzeinspeisung."
            ),
            "battery_note": BATTERY_NOTE,
        }

    def pv_self_consumption_today_attributes(self) -> dict[str, Any]:
        return {
            "formula": "pv_self_consumption_today = max(solar_production_today - grid_export_today, 0)",
            "solar_production_today_used_kwh": self.data.get(ATTR_SOLAR_PRODUCTION_TODAY),
            "grid_export_today_used_kwh": self.data.get(ATTR_GRID_EXPORT_TODAY),
            "calculated_pv_self_consumption_today_kwh": self.data.get(
                ATTR_PV_SELF_CONSUMPTION_TODAY
            ),
            "battery_note": BATTERY_NOTE,
        }

    def house_consumption_today_attributes(self) -> dict[str, Any]:
        return {
            "formula": (
                "house_consumption_today = max(grid_import_today + "
                "solar_production_today - grid_export_today - "
                "battery_charge_today + battery_discharge_today, 0)"
            ),
            "battery_note": BATTERY_NOTE,
        }

    def house_consumption_power_attributes(self) -> dict[str, Any]:
        return {
            "formula": (
                "house_consumption_power = max(grid_import_power + "
                "solar_production_power - grid_export_power - "
                "battery_charge_power + battery_discharge_power, 0)"
            ),
            "grid_import_power_used_w": self.data.get(ATTR_GRID_IMPORT_POWER),
            "solar_production_power_used_w": self.data.get(ATTR_SOLAR_PRODUCTION_POWER),
            "grid_export_power_used_w": self.data.get(ATTR_GRID_EXPORT_POWER),
            "battery_charge_power_used_w": self.data.get(ATTR_BATTERY_CHARGE_POWER),
            "battery_discharge_power_used_w": self.data.get(ATTR_BATTERY_DISCHARGE_POWER),
            "calculated_house_consumption_power_w": self.data.get(
                ATTR_HOUSE_CONSUMPTION_POWER
            ),
            "battery_power_note": (
                "Akkuladung und Akkuentladung stammen aus demselben "
                "Akkuleistungssensor: positiv = Akkuladung, negativ = "
                "Akkuentladung."
            ),
            "battery_note": BATTERY_NOTE,
        }

    def grid_import_cost_today_attributes(self) -> dict[str, Any]:
        return {
            "formula": COST_FORMULA,
            "note": (
                "Die Kosten werden aus den Netzbezugs-Deltas berechnet, "
                "nicht aus grid_import_today * current_price, da sich der "
                "Strompreis im Tagesverlauf ändern kann."
            ),
        }
