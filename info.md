# Daily Energy Flow Solar

Calculates daily energy flow sensors (PV self-consumption, house
consumption, autarky, dynamic grid import cost, ...) from your
existing **daily counters** and power sensors — no YAML template
sensors required, everything is a real Home Assistant sensor entity
provided by this custom integration.

## Highlights

- 100% GUI-based config flow (German labels), no YAML.
- Always works with daily counters — no total/lifetime counter mode.
- Correct PV self-consumption: `solar_production - grid_export`
  (battery charging counts as self-consumption, since it isn't fed
  into the grid).
- Correct house consumption, including battery charge/discharge.
- Autarky and PV self-consumption percentages.
- Dynamic grid import cost tracking, calculated from import deltas and
  the currently valid electricity price — not a naive
  `grid_import_today * current_price` calculation.
- Cost data survives Home Assistant restarts.

See `README.md` (English) or `README.de.md` (Deutsch) for full setup
instructions, required input sensors, all formulas and units.
