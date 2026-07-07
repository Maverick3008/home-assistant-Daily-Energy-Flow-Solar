# Daily Energy Flow Solar

A Home Assistant custom integration that calculates daily energy flow
sensors — PV self-consumption, house consumption, autarky, and dynamic
grid import cost — from your existing **daily counters** and power
sensors.

Everything is implemented as real Home Assistant sensor entities
provided by a custom integration. No YAML template sensors are used.

- Domain: `daily_energy_flow_solar`
- Version: `1.0.0`
- Config flow: yes (GUI only, German labels)
- IoT class: `local_polling`

## What this integration does

Given a handful of existing sensors (grid import/export daily
counters, solar production, battery charge/discharge, solar and grid
export power, and a current electricity price), Daily Energy Flow Solar
computes:

- Normalized power and daily energy readings.
- PV self-consumption (power and daily energy).
- Daily house consumption.
- Autarky percentage and PV self-consumption percentage.
- The current grid electricity price, normalized to EUR/kWh.
- Dynamic daily grid import cost, tracked from consumption deltas
  rather than a naive multiplication.
- The average grid electricity price paid today.

## Important: daily counters only

This integration **always** works with daily counters
("Tageszähler") — sensors that reset to zero every day (as most
inverters/energy meters provide out of the box). There is:

- No mode selector for daily vs. total/lifetime counters.
- No `energy_source_mode`.
- No baseline calculation for total/lifetime counters.
- No stored daily start values for energy counters.

If your only available sensors are lifetime/total counters, this
integration is not the right fit — you would need a helper (e.g. a
Riemann sum / utility meter) to first convert them into daily counters
before using them here.

## Installation

Repository: <https://github.com/Maverick3008/home-assistant-Daily-Energy-Flow-Solar>

### Manual installation

1. Copy the `custom_components/daily_energy_flow_solar` folder from this
   repository into your Home Assistant `custom_components` directory,
   so you end up with
   `<config>/custom_components/daily_energy_flow_solar/...`.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration** and
   search for **Daily Energy Flow Solar**.

### Installation via HACS

1. In HACS, go to **Integrations → ⋮ → Custom repositories** and add:
   - Repository: `https://github.com/Maverick3008/home-assistant-Daily-Energy-Flow-Solar`
   - Category: `Integration`
2. Install **Daily Energy Flow Solar** from HACS.
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration** and
   search for **Daily Energy Flow Solar**.

## Setup via the GUI

The entire configuration happens through the Home Assistant UI (config
flow) — no YAML is required. During setup you will be asked to select
the following existing entities and options (labels are shown in
German in the UI):

### Required daily energy counters (`device_class: energy`, unit Wh/kWh/MWh)

| Field (German label)     | Description                              |
| ------------------------ | ----------------------------------------- |
| Netzbezug heute           | Daily grid import counter                |
| Netzeinspeisung heute     | Daily grid export counter                |
| Solarproduktion heute     | Daily solar production counter           |
| Akkuladung heute          | Daily battery charge counter             |
| Akkuentladung heute       | Daily battery discharge counter          |

### Required power sensors (`device_class: power`, unit W/kW/MW)

| Field (German label)                                              | Description               |
| -------------------------------------------------------------------- | -------------------------- |
| Solarproduktion Leistung                                             | Current solar production power |
| Netzleistung (positiv = Netzbezug, negativ = Netzeinspeisung)         | A single **bidirectional** grid power sensor |
| Akkuleistung (positiv = Laden, negativ = Entladen)                   | A single **bidirectional** battery power sensor |

**Important:** both the grid power and battery power fields are
bidirectional — each is the one sensor your meter/inverter/battery
system already provides that reports **both** directions of flow in a
single value, by convention:

- **Grid power:** positive → Netzbezug (grid import), negative →
  Netzeinspeisung (grid export)
- **Battery power:** positive → Akkuladung (charging), negative →
  Akkuentladung (discharging)

From these values, the integration derives the "Netzbezug Leistung" /
"Netzeinspeisung Leistung" sensors and the internal battery
charge/discharge power used in the house consumption formula. If
either of your sensors uses the opposite convention, enable the
corresponding **"Vorzeichen ist umgekehrt"** ("Sign is reversed")
toggle to flip it.

### Price source

| Field (German label)             | Description                                    |
| ---------------------------------- | ----------------------------------------------- |
| Aktueller Netzstrompreis           | A `sensor` or `input_number` with the current electricity price |
| Einheit des Netzstrompreises       | `EUR/kWh` or `ct/kWh` — internally always converted to EUR/kWh |

### Other options

| Field (German label) | Description                                  |
| ---------------------- | --------------------------------------------- |
| Nachkommastellen        | Number of decimal places used to round sensor values |

All entities are validated when you save the form: energy fields must
report Wh, kWh or MWh, and power fields must report W, kW or MW. If the
unit doesn't match, you'll see a clear German error message and can
correct your selection.

You can later change any of these values from **Settings → Devices &
Services → Daily Energy Flow Solar → Configure**. Changing options
automatically reloads the integration.

## Generated sensors

| Sensor (German name)                     | Unit    | device_class | state_class  |
| ------------------------------------------ | ------- | ------------- | ------------- |
| Solarproduktion Leistung                   | W       | power         | measurement   |
| Netzbezug Leistung                         | W       | power         | measurement   |
| Netzeinspeisung Leistung                   | W       | power         | measurement   |
| PV-Eigenverbrauch Leistung                 | W       | power         | measurement   |
| Hausverbrauch Leistung                     | W       | power         | measurement   |
| Netzbezug heute                            | kWh     | energy        | total         |
| Netzeinspeisung heute                      | kWh     | energy        | total         |
| Solarproduktion heute                      | kWh     | energy        | total         |
| Akkuladung heute                           | kWh     | energy        | total         |
| Akkuentladung heute                        | kWh     | energy        | total         |
| PV-Eigenverbrauch heute                    | kWh     | energy        | total         |
| Hausverbrauch heute                        | kWh     | energy        | total         |
| Autarkie                                   | %       | –             | measurement   |
| PV-Eigenverbrauch                          | %       | –             | measurement   |
| Aktueller Netzstrompreis                   | EUR/kWh | –             | measurement   |
| Netzbezug Kosten heute                     | EUR     | monetary      | total         |
| Durchschnittlicher Netzstrompreis heute    | EUR/kWh | –             | measurement   |

Selected sensors also expose diagnostic attributes explaining exactly
how their value was calculated (`formula`, the raw inputs used, and a
`battery_note`).

## Unit normalization

**Energy:**
- Wh → divide by 1000 to get kWh
- kWh → unchanged
- MWh → multiply by 1000 to get kWh

**Power:**
- W → unchanged
- kW → multiply by 1000 to get W
- MW → multiply by 1,000,000 to get W

**Price:**
- EUR/kWh → unchanged
- ct/kWh → divide by 100 to get EUR/kWh

## Formulas

### Splitting the bidirectional grid power sensor

```
grid_import_power = max(grid_power, 0)
grid_export_power = max(-grid_power, 0)
```

(`grid_power` is negated first if "Sign is reversed" is enabled.)

### Splitting the bidirectional battery power sensor

```
battery_charge_power = max(battery_power, 0)
battery_discharge_power = max(-battery_power, 0)
```

(`battery_power` is negated first if its "Sign is reversed" toggle is
enabled.)

### PV self-consumption

```
pv_self_consumption_power = max(solar_production_power - grid_export_power, 0)
pv_self_consumption_today = max(solar_production_today - grid_export_today, 0)
```

**Battery charging counts as PV self-consumption.** Solar energy that
is stored in the battery is not fed into the grid, so from a
self-consumption point of view it is consumed on-site — it must not be
subtracted here.

Example: Solar production = 702 W, grid export = 25 W → PV
self-consumption = 677 W. If grid export is 0 W, PV self-consumption
equals solar production exactly.

### House consumption

```
house_consumption_today = max(
    grid_import_today
    + solar_production_today
    - grid_export_today
    - battery_charge_today
    + battery_discharge_today,
    0
)

house_consumption_power = max(
    grid_import_power
    + solar_production_power
    - grid_export_power
    - battery_charge_power
    + battery_discharge_power,
    0
)
```

The instantaneous power version uses live power readings instead of
daily energy counters, giving a real-time house consumption value.

**Battery charging is subtracted** — energy going into the battery is
not being consumed by the house yet. **Battery discharging is added**
— energy coming out of the battery is being consumed by the house
right now.

### Autarky

```
autarky_percent = (house_consumption_today - grid_import_today) / house_consumption_today * 100
```
Result is 0 if `house_consumption_today <= 0`, and clamped to the
range 0–100.

### PV self-consumption percentage

```
pv_self_consumption_percent = pv_self_consumption_today / solar_production_today * 100
```
Result is 0 if `solar_production_today <= 0`, and clamped to the range
0–100.

### Dynamic grid import cost

The electricity price can change throughout the day, so the cost is
**not** calculated as `grid_import_today * current_price`. Instead,
costs are accumulated from the deltas of the daily grid import
counter:

```
grid_import_cost_today += grid_import_delta_kwh * current_grid_import_price
```

In practice this means:

1. On start, the current grid import reading is stored as a baseline.
2. Whenever the grid import counter changes, the difference to the
   last known value is calculated.
3. That difference (delta) is multiplied by the currently valid
   electricity price.
4. The result is added to the running daily total.
5. The total is reset to zero at midnight.
6. All tracking data is persisted to disk, so a Home Assistant restart
   does not reset the accumulated cost for the day.
7. If the daily counter jumps backwards outside of the normal midnight
   reset (e.g. a sensor/inverter reset), the new value is treated as
   the new baseline instead of producing negative cost.

Example:

- 08:00 — 2 kWh grid import at 0.19 EUR/kWh → 0.38 EUR
- 12:00 — 1 kWh grid import at 0.25 EUR/kWh → 0.25 EUR
- Grid import cost today = 0.63 EUR

### Average grid electricity price today

```
grid_import_average_price_today = grid_import_cost_today / grid_import_today
```
Result is 0 if `grid_import_today <= 0`.

## Frequently asked questions

**Can I use total/lifetime counters instead of daily counters?**
No — this integration intentionally only supports daily counters. Use
a helper (such as a utility meter) to derive a daily counter from a
lifetime counter first.

**Why does battery charging count towards PV self-consumption but not
house consumption?**
Because that energy was produced by your solar system and was not fed
back into the grid — from the grid's perspective, it was "consumed" on
site. But it hasn't reached your house's loads yet; it's sitting in
the battery, so it isn't counted as house consumption until it is
discharged again.

## License

MIT — see [LICENSE](LICENSE).
