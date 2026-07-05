# Daily Energy Flow Solar

Eine Home-Assistant-Custom-Integration, die aus vorhandenen
**Tageszählern** und Leistungssensoren tägliche Energiefluss-Sensoren
berechnet — PV-Eigenverbrauch, Hausverbrauch, Autarkie und dynamische
Netzbezugskosten.

Alles wird als echte Home-Assistant-Sensor-Entität über eine Custom
Integration bereitgestellt. Es werden keine YAML-Template-Sensoren
verwendet.

- Domain: `daily_energy_flow_solar`
- Version: `0.5.0`
- Config Flow: ja (nur über die GUI, deutsche Begriffe)
- IoT-Klasse: `local_polling`

## Was die Integration macht

Aus einer Handvoll vorhandener Sensoren (Netzbezug/Netzeinspeisung als
Tageszähler, Solarproduktion, Akkuladung/-entladung, Solar- und
Netzeinspeisungsleistung sowie einem aktuellen Strompreis) berechnet
Daily Energy Flow Solar:

- Normalisierte Leistungs- und Tagesenergiewerte.
- PV-Eigenverbrauch (Leistung und Tagesenergie).
- Täglichen Hausverbrauch.
- Autarkie- und PV-Eigenverbrauchs-Prozentsätze.
- Den aktuellen Netzstrompreis, normalisiert auf EUR/kWh.
- Dynamische tägliche Netzbezugskosten, berechnet aus Verbrauchs-Deltas
  statt einer einfachen Multiplikation.
- Den heute durchschnittlich bezahlten Netzstrompreis.

## Wichtig: nur Tageszähler

Diese Integration arbeitet **immer** mit Tageszählern — Sensoren, die
täglich auf null zurückgesetzt werden (wie es die meisten
Wechselrichter/Energiezähler von Haus aus liefern). Es gibt:

- KEINEN Modus zur Auswahl zwischen Tageszähler und Gesamtzähler.
- KEIN `energy_source_mode`.
- KEINE Baseline-Berechnung für Gesamtzähler.
- KEINE gespeicherten Tagesstartwerte für Energiezähler.

Wenn dir nur Gesamtzähler zur Verfügung stehen, ist diese Integration
nicht direkt geeignet — du müsstest zunächst mit einem Helper (z. B.
einem Utility Meter) einen Tageszähler daraus ableiten.

## Installation

Repository: <https://github.com/Maverick3008/home-assistant-Daily-Energy-Flow-Solar>

### Manuelle Installation

1. Kopiere den Ordner `custom_components/daily_energy_flow_solar` aus diesem
   Repository in dein Home-Assistant-`custom_components`-Verzeichnis,
   sodass am Ende
   `<config>/custom_components/daily_energy_flow_solar/...` existiert.
2. Home Assistant neu starten.
3. Unter **Einstellungen → Geräte & Dienste → Integration
   hinzufügen** nach **Daily Energy Flow Solar** suchen.

### Installation über HACS

1. Gehe in HACS zu **Integrationen → ⋮ → Benutzerdefinierte
   Repositories** und trage ein:
   - Repository: `https://github.com/Maverick3008/home-assistant-Daily-Energy-Flow-Solar`
   - Kategorie: `Integration`
2. Installiere **Daily Energy Flow Solar** über HACS.
3. Home Assistant neu starten.
4. Unter **Einstellungen → Geräte & Dienste → Integration
   hinzufügen** nach **Daily Energy Flow Solar** suchen.

## Einrichtung über die GUI

Die gesamte Konfiguration erfolgt über die Home-Assistant-Oberfläche
(Config Flow) — es wird kein YAML benötigt. Bei der Einrichtung wirst
du gebeten, folgende vorhandenen Entitäten und Optionen auszuwählen:

### Benötigte Energie-Tageszähler (`device_class: energy`, Einheit Wh/kWh/MWh)

| Feld                    | Beschreibung                          |
| ------------------------ | -------------------------------------- |
| Netzbezug heute          | Tageszähler für den Netzbezug          |
| Netzeinspeisung heute    | Tageszähler für die Netzeinspeisung    |
| Solarproduktion heute    | Tageszähler für die Solarproduktion    |
| Akkuladung heute         | Tageszähler für die Akkuladung         |
| Akkuentladung heute      | Tageszähler für die Akkuentladung      |

### Benötigte Leistungssensoren (`device_class: power`, Einheit W/kW/MW)

| Feld                                                              | Beschreibung                       |
| --------------------------------------------------------------------- | ------------------------------------ |
| Solarproduktion Leistung                                              | Aktuelle Solarproduktionsleistung   |
| Netzleistung (positiv = Netzbezug, negativ = Netzeinspeisung)         | Ein einziger **bidirektionaler** Netzleistungssensor |
| Akkuleistung (positiv = Laden, negativ = Entladen)                    | Ein einziger **bidirektionaler** Akkuleistungssensor |

**Wichtig:** Sowohl das Netzleistungs- als auch das
Akkuleistungs-Feld sind bidirektional — jeweils der eine Sensor, den
dein Zähler/Wechselrichter/Batteriesystem ohnehin schon liefert und
der **beide** Richtungen in einem einzigen Wert abbildet, per
Konvention:

- **Netzleistung:** positiv → Netzbezug (Bezug aus dem Netz), negativ
  → Netzeinspeisung (Einspeisung ins Netz)
- **Akkuleistung:** positiv → Akkuladung (Laden), negativ →
  Akkuentladung (Entladen)

Aus diesen Werten leitet die Integration die Sensoren „Netzbezug
Leistung" / „Netzeinspeisung Leistung" sowie intern die
Akkuladung/-entladung Leistung für die Hausverbrauchs-Formel ab.
Nutzt einer deiner Sensoren die umgekehrte Konvention, aktiviere den
jeweiligen Schalter **„Vorzeichen ist umgekehrt"**, um das Vorzeichen
umzudrehen.

### Preisquelle

| Feld                           | Beschreibung                                            |
| -------------------------------- | ---------------------------------------------------------- |
| Aktueller Netzstrompreis         | Ein `sensor` oder `input_number` mit dem aktuellen Strompreis |
| Einheit des Netzstrompreises     | `€/kWh` oder `ct/kWh` — intern wird immer in €/kWh gerechnet |

### Weitere Optionen

| Feld              | Beschreibung                                          |
| ------------------- | -------------------------------------------------------- |
| Nachkommastellen    | Anzahl der Nachkommastellen, auf die Sensorwerte gerundet werden |

Alle Entitäten werden beim Speichern geprüft: Energie-Felder müssen
Wh, kWh oder MWh melden, Leistungs-Felder müssen W, kW oder MW melden.
Passt die Einheit nicht, erscheint eine verständliche deutsche
Fehlermeldung und du kannst deine Auswahl korrigieren.

Alle Werte lassen sich später unter **Einstellungen → Geräte &
Dienste → Daily Energy Flow Solar → Konfigurieren** ändern. Eine
Options-Änderung lädt die Integration automatisch neu.

## Erzeugte Sensoren

| Sensor                                   | Einheit  | device_class | state_class  |
| ------------------------------------------ | -------- | ------------- | ------------- |
| Solarproduktion Leistung                   | W        | power         | measurement   |
| Netzbezug Leistung                         | W        | power         | measurement   |
| Netzeinspeisung Leistung                   | W        | power         | measurement   |
| PV-Eigenverbrauch Leistung                 | W        | power         | measurement   |
| Hausverbrauch Leistung                     | W        | power         | measurement   |
| Netzbezug heute                            | kWh      | energy        | total         |
| Netzeinspeisung heute                      | kWh      | energy        | total         |
| Solarproduktion heute                      | kWh      | energy        | total         |
| Akkuladung heute                           | kWh      | energy        | total         |
| Akkuentladung heute                        | kWh      | energy        | total         |
| PV-Eigenverbrauch heute                    | kWh      | energy        | total         |
| Hausverbrauch heute                        | kWh      | energy        | total         |
| Autarkie                                   | %        | –             | measurement   |
| PV-Eigenverbrauch                          | %        | –             | measurement   |
| Aktueller Netzstrompreis                   | EUR/kWh  | –             | measurement   |
| Netzbezug Kosten heute                     | EUR      | monetary      | total         |
| Durchschnittlicher Netzstrompreis heute    | EUR/kWh  | –             | measurement   |

Ausgewählte Sensoren liefern zusätzlich Diagnose-Attribute, die genau
erklären, wie ihr Wert zustande kam (`formula`, die verwendeten
Rohwerte und ein `battery_note`).

## Einheiten-Normalisierung

**Energie:**
- Wh → durch 1000 teilen, um kWh zu erhalten
- kWh → unverändert
- MWh → mit 1000 multiplizieren, um kWh zu erhalten

**Leistung:**
- W → unverändert
- kW → mit 1000 multiplizieren, um W zu erhalten
- MW → mit 1.000.000 multiplizieren, um W zu erhalten

**Preis:**
- €/kWh → unverändert
- ct/kWh → durch 100 teilen, um €/kWh zu erhalten

## Formeln

### Aufteilung des bidirektionalen Netzleistungssensors

```
grid_import_power = max(grid_power, 0)
grid_export_power = max(-grid_power, 0)
```

(`grid_power` wird zuerst negiert, falls „Vorzeichen ist umgekehrt"
aktiviert ist.)

### Aufteilung des bidirektionalen Akkuleistungssensors

```
battery_charge_power = max(battery_power, 0)
battery_discharge_power = max(-battery_power, 0)
```

(`battery_power` wird zuerst negiert, falls der zugehörige Schalter
„Vorzeichen ist umgekehrt" aktiviert ist.)

### PV-Eigenverbrauch

```
pv_self_consumption_power = max(solar_production_power - grid_export_power, 0)
pv_self_consumption_today = max(solar_production_today - grid_export_today, 0)
```

**Akkuladung zählt als PV-Eigenverbrauch.** Solarstrom, der in den
Akku geladen wird, wird nicht ins Netz eingespeist — aus Sicht des
Eigenverbrauchs wurde er also vor Ort verbraucht. Er darf hier nicht
abgezogen werden.

Beispiel: Solarproduktion = 702 W, Netzeinspeisung = 25 W →
PV-Eigenverbrauch = 677 W. Ist die Netzeinspeisung 0 W, entspricht der
PV-Eigenverbrauch exakt der Solarproduktion.

### Hausverbrauch

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

Die Leistungs-Variante nutzt Live-Leistungswerte statt Tageszähler und
liefert damit den aktuellen Hausverbrauch in Echtzeit.

**Akkuladung wird abgezogen** — Energie, die in den Akku fließt, wurde
noch nicht vom Haus verbraucht. **Akkuentladung wird addiert** —
Energie, die aus dem Akku kommt, wird gerade jetzt vom Haus verbraucht.

### Autarkie

```
autarky_percent = (house_consumption_today - grid_import_today) / house_consumption_today * 100
```
Ergebnis ist 0, wenn `house_consumption_today <= 0` ist, und wird auf
den Bereich 0–100 begrenzt.

### PV-Eigenverbrauch in Prozent

```
pv_self_consumption_percent = pv_self_consumption_today / solar_production_today * 100
```
Ergebnis ist 0, wenn `solar_production_today <= 0` ist, und wird auf
den Bereich 0–100 begrenzt.

### Dynamische Netzbezugskosten

Der Strompreis kann sich im Laufe des Tages ändern, deshalb werden die
Kosten **nicht** als `grid_import_today * current_price` berechnet.
Stattdessen werden die Kosten aus den Deltas des Netzbezugs-Tageszählers
aufsummiert:

```
grid_import_cost_today += grid_import_delta_kwh * current_grid_import_price
```

Konkret bedeutet das:

1. Beim Start wird der aktuelle Netzbezugswert als Ausgangswert
   gespeichert.
2. Bei jeder Änderung des Netzbezugs-Tageszählers wird die Differenz
   zum zuletzt bekannten Wert berechnet.
3. Diese Differenz (Delta) wird mit dem aktuell gültigen Strompreis
   multipliziert.
4. Das Ergebnis wird zur laufenden Tagessumme addiert.
5. Die Summe wird um Mitternacht auf null zurückgesetzt.
6. Alle Tracking-Daten werden persistent gespeichert, sodass ein
   Home-Assistant-Neustart die bisher aufgelaufenen Kosten des Tages
   nicht verliert.
7. Springt der Tageszähler außerhalb des normalen Mitternachts-Resets
   zurück (z. B. durch einen Sensor-/Wechselrichter-Reset), wird der
   neue Wert als neuer Ausgangswert übernommen, statt negative Kosten
   zu erzeugen.

Beispiel:

- 08:00 Uhr — 2 kWh Netzbezug zu 0,19 €/kWh → 0,38 €
- 12:00 Uhr — 1 kWh Netzbezug zu 0,25 €/kWh → 0,25 €
- Netzbezug Kosten heute = 0,63 €

### Durchschnittlicher Netzstrompreis heute

```
grid_import_average_price_today = grid_import_cost_today / grid_import_today
```
Ergebnis ist 0, wenn `grid_import_today <= 0` ist.

## Häufige Fragen

**Kann ich Gesamtzähler statt Tageszähler verwenden?**
Nein — diese Integration unterstützt bewusst ausschließlich
Tageszähler. Nutze einen Helper (z. B. ein Utility Meter), um zunächst
einen Tageszähler aus einem Gesamtzähler abzuleiten.

**Warum zählt Akkuladung zum PV-Eigenverbrauch, aber nicht zum
Hausverbrauch?**
Weil diese Energie von deiner PV-Anlage produziert und nicht ins Netz
eingespeist wurde — aus Netzsicht wurde sie also vor Ort „verbraucht".
Sie hat aber die Verbraucher im Haus noch nicht erreicht, sondern
liegt im Akku — deshalb zählt sie erst beim Entladen als
Hausverbrauch.

## Lizenz

MIT — siehe [LICENSE](LICENSE).
