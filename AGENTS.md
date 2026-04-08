# AGENTS.md

## Project

Home Assistant custom integration (HACS) for Kimai time tracking. No build system, no test framework, no CI — just raw Python under `custom_components/kimai/`.

## Structure

- `custom_components/kimai/` — the integration (all source code lives here)
- `ha-config/`, `ha-test-config/` — gitignored local HA instances for manual testing (not symlinks; copies must be refreshed manually)
- `hacs.json` — HACS metadata

## Key files

| File | Role |
|------|------|
| `__init__.py` | Entry point: sets up API client + coordinator, forwards to platforms |
| `api.py` | Kimai REST API client (uses `X-AUTH-USER` / `X-AUTH-TOKEN` headers) |
| `coordinator.py` | `DataUpdateCoordinator` — polls every 60s, computes day-off/overtime logic |
| `const.py` | Config keys, defaults (480 min/day, 60s interval) |
| `config_flow.py` | Config entry flow via voluptuous schema |
| `sensor.py` | 5 sensors: next_day_off, next_workday, today_tracked, missing_minutes, overtime_today |
| `binary_sensor.py` | 2 binary sensors: is_day_off, work_time_fulfilled |
| `manifest.json` | HA manifest; `requirements: []` (all deps from HA core) |
| `strings.json` + `translations/` | UI strings (en, de) |

## Development

- No lint, typecheck, or test commands exist. There is nothing to `run`.
- All imports are from `homeassistant.*` — do not add external pip dependencies; they must go in `manifest.json.requirements` if needed.
- Follow HA integration conventions: `async_setup_entry`, `CoordinatorEntity`, platform forwarding via `PLATFORMS`.
- Vacation activity IDs are parsed from comma-separated string in config flow → stored as `list[int]`.
- `coordinator.py` weekend detection uses `weekday() in {5, 6}` (Mon=0).

## Local testing

1. Copy `custom_components/kimai/` into an HA config dir's `custom_components/kimai/`.
2. Start HA against that config dir (e.g. `ha-test-config/` uses port 8124).
3. Add the integration via UI: Settings → Devices & Services → Kimai.