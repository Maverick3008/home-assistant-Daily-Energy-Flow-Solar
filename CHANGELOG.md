# Changelog

All notable changes to the Daily Energy Flow Solar integration are documented here.

## [0.5.0]

- **Fixed the battery power input.** The two separate fields "Akkuladung
  Leistung" and "Akkuentladung Leistung" have been replaced with a
  single **bidirectional** field: **Akkuleistung** (`battery_power`),
  matching how most battery inverters actually report power. By
  convention: positive = Akkuladung (charging), negative =
  Akkuentladung (discharging).
- Added a **"Vorzeichen ist umgekehrt"** ("Sign is reversed") toggle
  for the battery power sensor, for systems using the opposite
  convention — mirroring the existing toggle for the grid power
  sensor.
- `battery_charge_power` and `battery_discharge_power` are now derived
  internally from this one sensor and used in the "Hausverbrauch
  Leistung" (house consumption power) formula exactly as before.
- Updated diagnostic attributes, translations (DE/EN) and
  documentation.

## [0.4.0]

- Added two new required power input fields: **Akkuladung Leistung**
  (battery charge power) and **Akkuentladung Leistung** (battery
  discharge power).
- Added a new sensor: **Hausverbrauch Leistung** (house consumption
  power), calculated in real time as:
  ```
  house_consumption_power = max(
      grid_import_power + solar_production_power - grid_export_power
      - battery_charge_power + battery_discharge_power,
      0
  )
  ```
  This mirrors the existing daily house consumption formula, but uses
  live power readings instead of daily energy counters.
- Added diagnostic attributes to the new sensor (`formula`, the raw
  power values used, and a `battery_note`).
- Updated German and English translations and documentation.

## [0.3.0]

- **Fixed a sign-convention bug** in the grid power handling. There is
  now a single, bidirectional grid power input field ("Netzleistung")
  instead of an export-only field. By convention: positive value =
  Netzbezug (grid import), negative value = Netzeinspeisung (grid
  export). Both `grid_import_power` and `grid_export_power` are now
  correctly derived from this one sensor.
- Renamed the config field `grid_export_power` → `grid_power`, and the
  toggle `grid_export_power_negative` → `grid_power_inverted` ("Sign is
  reversed"), which now only needs to be enabled for sensors using the
  opposite convention (positive = export, negative = import).
- Added a new sensor: **Netzbezug Leistung** (grid import power),
  derived from the same bidirectional grid power sensor as "Netzeinspeisung
  Leistung".
- Updated diagnostic attributes on the PV self-consumption power
  sensor to include the used grid import power value and a note about
  the shared grid power sensor convention.
- Updated German and English translations and documentation to reflect
  the new field.

## [0.2.9] - Initial release

- Initial version 0.2.9.
- Always uses daily counters (Tageszähler) for energy input — there is
  no mode to switch to lifetime/total counters.
- No `energy_source_mode`, no daily/total selector, no baseline
  calculation for total counters, no stored daily start values.
- Config flow entity pickers are filtered by device class: only
  `device_class: energy` sensors for energy fields, only
  `device_class: power` sensors for power fields.
- Unit validation on save for Wh/kWh/MWh (energy) and W/kW/MW (power),
  with clear German error messages if the unit doesn't match.
- PV self-consumption is calculated correctly as solar production minus
  grid export (`pv_self_consumption = solar_production - grid_export`).
- Battery charging counts as PV self-consumption (it is not fed into
  the grid), but is correctly excluded from house consumption.
- Battery discharging is correctly added to house consumption.
- House consumption formula accounts for grid import, solar
  production, grid export, battery charge and battery discharge.
- Dynamic grid import cost calculation based on import deltas
  multiplied by the currently valid electricity price, instead of
  multiplying the full daily counter by the current price.
- Grid import cost data is persisted so a Home Assistant restart does
  not lose the accumulated cost for the day.
- Full German and English translations for the config flow, options
  flow and entities.
- HACS and GitHub Actions files for automated releases.
