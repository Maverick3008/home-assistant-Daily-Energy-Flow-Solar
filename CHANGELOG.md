# Changelog

All notable changes to the Daily Energy Flow Solar integration are documented here.

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
