"""Config flow for the Daily Energy Flow Solar integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY_CHARGE_TODAY,
    CONF_BATTERY_DISCHARGE_TODAY,
    CONF_BATTERY_POWER,
    CONF_BATTERY_POWER_INVERTED,
    CONF_DECIMAL_PLACES,
    CONF_GRID_POWER,
    CONF_GRID_POWER_INVERTED,
    CONF_GRID_EXPORT_TODAY,
    CONF_GRID_IMPORT_TODAY,
    CONF_NAME,
    CONF_PRICE_SOURCE,
    CONF_PRICE_UNIT,
    CONF_SOLAR_PRODUCTION_POWER,
    CONF_SOLAR_PRODUCTION_TODAY,
    DEFAULT_BATTERY_POWER_INVERTED,
    DEFAULT_DECIMAL_PLACES,
    DEFAULT_GRID_POWER_INVERTED,
    DEFAULT_PRICE_UNIT,
    DOMAIN,
    ENERGY_UNITS,
    POWER_UNITS,
    PRICE_SOURCE_DOMAINS,
    PRICE_UNITS,
)


def _energy_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor", device_class="energy")
    )


def _power_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor", device_class="power")
    )


def _price_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain=PRICE_SOURCE_DOMAINS)
    )


def _price_unit_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=PRICE_UNITS,
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key="price_unit",
        )
    )


def _build_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "Daily Energy Flow Solar")): str,
            vol.Required(
                CONF_GRID_IMPORT_TODAY, default=defaults.get(CONF_GRID_IMPORT_TODAY)
            ): _energy_selector(),
            vol.Required(
                CONF_GRID_EXPORT_TODAY, default=defaults.get(CONF_GRID_EXPORT_TODAY)
            ): _energy_selector(),
            vol.Required(
                CONF_SOLAR_PRODUCTION_TODAY,
                default=defaults.get(CONF_SOLAR_PRODUCTION_TODAY),
            ): _energy_selector(),
            vol.Required(
                CONF_BATTERY_CHARGE_TODAY,
                default=defaults.get(CONF_BATTERY_CHARGE_TODAY),
            ): _energy_selector(),
            vol.Required(
                CONF_BATTERY_DISCHARGE_TODAY,
                default=defaults.get(CONF_BATTERY_DISCHARGE_TODAY),
            ): _energy_selector(),
            vol.Required(
                CONF_SOLAR_PRODUCTION_POWER,
                default=defaults.get(CONF_SOLAR_PRODUCTION_POWER),
            ): _power_selector(),
            vol.Required(
                CONF_GRID_POWER, default=defaults.get(CONF_GRID_POWER)
            ): _power_selector(),
            vol.Required(
                CONF_GRID_POWER_INVERTED,
                default=defaults.get(
                    CONF_GRID_POWER_INVERTED,
                    DEFAULT_GRID_POWER_INVERTED,
                ),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_BATTERY_POWER,
                default=defaults.get(CONF_BATTERY_POWER),
            ): _power_selector(),
            vol.Required(
                CONF_BATTERY_POWER_INVERTED,
                default=defaults.get(
                    CONF_BATTERY_POWER_INVERTED,
                    DEFAULT_BATTERY_POWER_INVERTED,
                ),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_PRICE_SOURCE, default=defaults.get(CONF_PRICE_SOURCE)
            ): _price_selector(),
            vol.Required(
                CONF_PRICE_UNIT,
                default=defaults.get(CONF_PRICE_UNIT, DEFAULT_PRICE_UNIT),
            ): _price_unit_selector(),
            vol.Required(
                CONF_DECIMAL_PLACES,
                default=defaults.get(CONF_DECIMAL_PLACES, DEFAULT_DECIMAL_PLACES),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=6, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
        }
    )


def _validate_units(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> dict[str, str]:
    """Validate that the chosen entities report a supported unit.

    Returns a dict of field -> error key, suitable for FlowResult errors.
    """
    errors: dict[str, str] = {}

    energy_fields = [
        CONF_GRID_IMPORT_TODAY,
        CONF_GRID_EXPORT_TODAY,
        CONF_SOLAR_PRODUCTION_TODAY,
        CONF_BATTERY_CHARGE_TODAY,
        CONF_BATTERY_DISCHARGE_TODAY,
    ]
    power_fields = [
        CONF_SOLAR_PRODUCTION_POWER,
        CONF_GRID_POWER,
        CONF_BATTERY_POWER,
    ]

    for field in energy_fields:
        entity_id = user_input.get(field)
        if not entity_id:
            continue
        state = hass.states.get(entity_id)
        unit = state.attributes.get("unit_of_measurement") if state else None
        if unit not in ENERGY_UNITS:
            errors[field] = "invalid_energy_unit"

    for field in power_fields:
        entity_id = user_input.get(field)
        if not entity_id:
            continue
        state = hass.states.get(entity_id)
        unit = state.attributes.get("unit_of_measurement") if state else None
        if unit not in POWER_UNITS:
            errors[field] = "invalid_power_unit"

    return errors


class DailyEnergyFlowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Daily Energy Flow Solar."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_units(self.hass, user_input)
            if not errors:
                await self.async_set_unique_id(
                    f"{DOMAIN}_{user_input[CONF_NAME].lower().replace(' ', '_')}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> DailyEnergyFlowOptionsFlow:
        return DailyEnergyFlowOptionsFlow(config_entry)


class DailyEnergyFlowOptionsFlow(config_entries.OptionsFlow):
    """Handle an options flow for Daily Energy Flow Solar."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        current = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            errors = _validate_units(self.hass, user_input)
            if not errors:
                # Name cannot be changed here, keep the original one.
                merged = {**current, **user_input}
                return self.async_create_entry(title="", data=merged)

        schema = _build_schema(current)
        # Remove the name field from the options form; it's fixed after setup.
        schema_dict = {
            key: value
            for key, value in schema.schema.items()
            if str(key) != CONF_NAME
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )
