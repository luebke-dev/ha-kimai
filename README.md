# Kimai

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for [Kimai](https://www.kimai.org/) time tracking.

## Features

### Binary Sensors
- **Is Day Off** — Indicates if today is a day off (weekend or vacation/holiday activity)
- **Work Time Fulfilled** — Indicates if the required work time for today has been tracked

### Sensors
- **Next Day Off** — Date of the next day off (weekend or vacation, excluding today)
- **Next Workday** — Date of the next workday (weekday without vacation, excluding today)
- **Today Tracked** — Tracked minutes today
- **Missing Minutes Today** — Remaining minutes to fulfill required work time (0 on days off)
- **Overtime Today** — Overtime minutes today (on days off, all tracked time counts as overtime)

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select **Custom repositories**
4. Enter `luebke-dev/ha-kimai` as repository and select **Integration** as category
5. Click "Add"
6. Search for "Kimai" in HACS and install it
7. Restart Home Assistant

### Manual

Copy the `custom_components/kimai` folder into your Home Assistant `config/custom_components/` directory.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Kimai"
3. Enter your Kimai instance URL, API user, and API token
4. Optionally configure vacation activity IDs (comma-separated) to enable day-off detection
5. Set the required minutes per workday (default: 480 = 8 hours)

## API Token

You can generate an API token in your Kimai instance under **User → API Access**.

## Vacation Activity IDs

To enable vacation/holiday detection, enter the activity IDs that represent vacation or holidays in your Kimai instance (comma-separated, e.g. `48,49`). These are used to determine if a day is a day off and to calculate the next workday.
