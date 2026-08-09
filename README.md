# Home Assistant Configuration

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.3.4-blue?style=flat-square&logo=home-assistant)
![License](https://img.shields.io/github/license/bcl1713/homeassistant_config?style=flat-square)
![GitHub last commit](https://img.shields.io/github/last-commit/bcl1713/homeassistant_config?style=flat-square)
![GitHub issues](https://img.shields.io/github/issues/bcl1713/homeassistant_config?style=flat-square)

This repository contains Brian's Home Assistant configuration. It is organized for safe, reviewable development: feature packages live under `packages/`, generated or secret runtime files stay out of Git, and contributor changes flow through pull requests to `dev` before any `main` release gate.

## Current system overview

The active configuration is package-first. `configuration.yaml` keeps global includes small and loads most feature logic through Home Assistant packages:

- `homeassistant.packages: !include_dir_named packages` loads feature packages.
- `automation: !include_dir_merge_list automation` loads standalone automations.
- `input_boolean: !include_dir_merge_named input_boolean` loads helper modes such as guest mode.
- `scene`, `recorder`, and `logbook` are split into their own root-level files.
- `packages/shared_infrastructure.yaml` owns shared contracts consumed by other packages, including `notify.all_mobile_devices` and YAML-managed Lovelace dashboard registration.

The system currently emphasizes:

- Climate control for `climate.dining_room_thermostat`, split across schedule, occupancy, extreme-heat overlay, and diagnostics packages.
- Mobile-first operational dashboards for climate control and window ventilation advice.
- Device health monitoring for batteries, stale devices, Z-Wave health, and integration availability.
- Household safety and security flows for cameras, garage doors, secure-house sanity checks, security lighting, routines, and notifications.
- Weather, air-quality, seasonal, school, and window-ventilation advice driven by templates and helper entities.
- ESPHome/device-specific configuration, currently including a RATGDO garage-door controller YAML file.

## Repository layout

```text
/
├── .github/                 # GitHub Actions validation workflow and CI notes
├── automation/              # Standalone automation includes
├── blueprints/              # Imported and local automation/script/template blueprints
├── dashboards/              # YAML-managed Lovelace dashboards
├── esphome/                 # ESPHome device configuration tracked with the repo
├── input_boolean/           # Mode/helper booleans loaded by configuration.yaml
├── packages/                # Feature packages loaded with !include_dir_named
├── scripts/                 # Repo utility scripts, including HA context export helpers
├── automations.yaml         # UI-managed or legacy automation file
├── configuration.yaml       # Main Home Assistant entry point and includes
├── logbook.yaml             # Logbook filters/configuration
├── recorder.yaml            # Recorder filters/configuration
└── scenes.yaml              # Scene definitions
```

## Active package inventory

All active package files under `packages/*.yaml` are documented in `packages/README.md`. The current active set is:

- `air_quality.yaml` - composite air-quality status, thresholds, alerts, and recheck notifications.
- `cameras.yaml` - camera notification automation payloads and guards.
- `climate_diagnostics.yaml` - dashboard-facing thermostat/temperature diagnostics.
- `climate_extreme_heat.yaml` - hot-day detection and bounded pre-cool overlay behavior.
- `climate_occupancy.yaml` - away, return-home, and pre-arrival climate recovery behavior.
- `climate_schedule.yaml` - baseline thermostat setpoint helpers and schedule application.
- `device_batteries.yaml` - battery health summaries and alerting.
- `device_connectivity.yaml` - stale-device, Z-Wave, and integration-health monitoring.
- `exterior_door_monitoring.yaml` - two-minute open alerts and matching tagged clears for monitored exterior door contacts.
- `garage_door_monitoring.yaml` - garage-door duration monitoring, reminders, and controls.
- `known_batteries.yaml` - normalized template sensors for known battery-powered devices.
- `light_groups.yaml` - logical light groups.
- `meal_prep.yaml`, `meal_prep_target_policy.yaml`, `mealie_read_only.yaml`, and `meal_prep_orchestration.yaml` - Kitchen Prep helper/state model, dinner-target and configurable lead-time policy, deterministic manual controls, bounded read-only Mealie adapter, and once-per-meal automatic prep-window/Cast orchestration.
- `notifications.yaml` - shared notification automations that do not belong to a larger package.
- `presence.yaml` - presence, alarm-panel, and presence-related lighting behavior.
- `remotes.yaml` - Z-Wave remote helper scripts and blueprint-backed automations.
- `routines.yaml` - household routines, including Good Night.
- `seasonal.yaml` - active seasonal lighting automation.
- `security_door_alerts.yaml` - immediate armed away/night security-boundary door alerts, dedicated tagged clears, and concise bedroom-display announcements.
- `security_lights.yaml` - security-focused lighting automations.
- `security_sanity.yaml` - reusable secure-house sanity check workflow.
- `shared_infrastructure.yaml` - shared notifier/dashboard contracts for packages.
- `towner_notifications.yaml` - school arrival/departure notification state handling.
- `trash_recycling_reminder.yaml` - municipal calendar-driven Zooz wall-switch/dimmer LED reminder with per-device snapshot and midnight restore.
- `weber_temp_watch.yaml` - temporary notification-only Weber Connect Hub temperature watch for the current grill test; remove after the test.
- `weather.yaml` - weather caching, MQTT data, forecasts, and weather-driven automation.
- `window_ventilation.yaml` - advisory ventilation recommendations and notification-only open-window HVAC warnings.

Disabled package files, such as `*.yaml.disabled`, are retained as inactive reference material and are not part of the active package inventory.

## Dashboards

YAML-managed dashboards live in `dashboards/` and are registered by `packages/shared_infrastructure.yaml`:

- `dashboards/climate_control.yaml` provides the mobile-first climate operator view, thermostat controls, temperature and air-quality trend graphs, extreme-heat overlay controls, and diagnostics.
- `dashboards/window_ventilation.yaml` provides the advisory ventilation view, current recommendation, comfort/dew-point context, rain/HVAC context, air-quality baseline comparisons, and tuning helpers.
- `dashboards/kitchen_prep.yaml` provides a hidden, phone-first Kitchen Prep view. It renders only fresh meal-prep source data, exposes the selected dinner-ready timing policy and computed automatic start, presents #210-owned manual controls that fail closed outside a valid session, and is the future direct-view target for the kitchen display.

## Notifications and shared contracts

Feature packages should consume shared infrastructure instead of redefining it. The important current contracts are:

- `notify.all_mobile_devices` for fan-out mobile notifications.
- YAML Lovelace dashboard registration under `lovelace.dashboards`.
- Package-local helpers for thresholds and enable flags when a feature needs operator tuning.

## Development and contribution flow

Use `dev` as the normal integration branch:

1. Start from the latest `dev`.
2. Create a focused feature, fix, docs, or chore branch.
3. Make repository-local changes only; do not reload, restart, or modify the live Home Assistant host unless a task explicitly authorizes it.
4. Run relevant local checks or static validation.
5. Open a pull request targeting `dev`.
6. Wait for reviewer approval and the established integration flow. Do not self-merge changes to `main`.

See `DEVELOPMENT.md` for implementation standards and `CONTRIBUTING.md` for the contributor-facing process.

## Local validation

For documentation-only changes, verify the package inventory and run a Markdown/link sanity check when available. For configuration changes, prefer static validation first and only run Home Assistant config checks when the task or environment provides a known-safe local command.

The GitHub Actions workflow in `.github/workflows/validate.yaml` prepares dummy credential files and non-secret package-secret placeholders, then runs a required Home Assistant Core configuration check with `frenck/action-home-assistant`.

## License

This project is licensed under the MIT License. See `LICENSE.md` for details.
