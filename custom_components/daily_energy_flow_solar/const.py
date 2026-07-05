"""Constants for the Daily Energy Flow Solar integration."""
from __future__ import annotations

DOMAIN = "daily_energy_flow_solar"
PLATFORMS = ["sensor"]

# Config / options keys (technical, never shown directly to the user;
# the German labels live in strings.json / translations)
CONF_NAME = "name"
CONF_GRID_IMPORT_TODAY = "grid_import_today"
CONF_GRID_EXPORT_TODAY = "grid_export_today"
CONF_SOLAR_PRODUCTION_TODAY = "solar_production_today"
CONF_BATTERY_CHARGE_TODAY = "battery_charge_today"
CONF_BATTERY_DISCHARGE_TODAY = "battery_discharge_today"

CONF_SOLAR_PRODUCTION_POWER = "solar_production_power"
# A single, bidirectional grid power sensor. By convention (matching most
# smart meters / inverters):
#   positive value -> Netzbezug (grid import)
#   negative value -> Netzeinspeisung (grid export)
CONF_GRID_POWER = "grid_power"
CONF_GRID_POWER_INVERTED = "grid_power_inverted"

CONF_BATTERY_CHARGE_POWER = "battery_charge_power"
CONF_BATTERY_DISCHARGE_POWER = "battery_discharge_power"

CONF_PRICE_SOURCE = "price_source"
CONF_PRICE_UNIT = "price_unit"
CONF_DECIMAL_PLACES = "decimal_places"

DEFAULT_DECIMAL_PLACES = 2
DEFAULT_GRID_POWER_INVERTED = False
DEFAULT_PRICE_UNIT = "EUR/kWh"

PRICE_UNIT_EUR_KWH = "EUR/kWh"
PRICE_UNIT_CT_KWH = "ct/kWh"
PRICE_UNITS = [PRICE_UNIT_EUR_KWH, PRICE_UNIT_CT_KWH]

# Units accepted for energy / power input entities
ENERGY_UNITS = ["Wh", "kWh", "MWh"]
POWER_UNITS = ["W", "kW", "MW"]

# Domains allowed for the price source
PRICE_SOURCE_DOMAINS = ["sensor", "input_number"]

# Storage
STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}_cost_tracker"

# Signal used to notify sensor entities that the hub recomputed its values
SIGNAL_UPDATE = f"{DOMAIN}_update_{{entry_id}}"

# Hub attribute keys (internal, used to look up computed values)
ATTR_SOLAR_PRODUCTION_POWER = "solar_production_power"
ATTR_GRID_IMPORT_POWER = "grid_import_power"
ATTR_GRID_EXPORT_POWER = "grid_export_power"
ATTR_PV_SELF_CONSUMPTION_POWER = "pv_self_consumption_power"
ATTR_BATTERY_CHARGE_POWER = "battery_charge_power"
ATTR_BATTERY_DISCHARGE_POWER = "battery_discharge_power"
ATTR_HOUSE_CONSUMPTION_POWER = "house_consumption_power"

ATTR_GRID_IMPORT_TODAY = "grid_import_today"
ATTR_GRID_EXPORT_TODAY = "grid_export_today"
ATTR_SOLAR_PRODUCTION_TODAY = "solar_production_today"
ATTR_BATTERY_CHARGE_TODAY = "battery_charge_today"
ATTR_BATTERY_DISCHARGE_TODAY = "battery_discharge_today"
ATTR_PV_SELF_CONSUMPTION_TODAY = "pv_self_consumption_today"
ATTR_HOUSE_CONSUMPTION_TODAY = "house_consumption_today"

ATTR_AUTARKY_PERCENT = "autarky_percent"
ATTR_PV_SELF_CONSUMPTION_PERCENT = "pv_self_consumption_percent"

ATTR_CURRENT_GRID_PRICE = "current_grid_price"
ATTR_GRID_IMPORT_COST_TODAY = "grid_import_cost_today"
ATTR_GRID_IMPORT_AVERAGE_PRICE_TODAY = "grid_import_average_price_today"

MANUFACTURER = "Daily Energy Flow Solar"
MODEL = "Daily Energy Flow Solar Calculator"
