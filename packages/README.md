# Home Assistant Packages

This directory contains Home Assistant packages loaded by `configuration.yaml` via:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Each active `*.yaml` file is part of the live configuration. Files ending in `.yaml.disabled` are inactive reference material and are documented separately below.

## Package boundaries

Use packages for feature-owned entities, helpers, scripts, templates, and automations. Keep cross-cutting contracts in `shared_infrastructure.yaml` so feature packages can consume the same notifier and dashboard wiring without redefining root-level Home Assistant configuration.

Complex domains should stay split by responsibility. Climate is the current model: schedule helpers, occupancy behavior, extreme-heat overlay, and dashboard diagnostics live in separate packages so operator controls and automation behavior remain easier to review.

## Active packages

| Package | Responsibility |
|---|---|
| `air_quality.yaml` | Composite air-quality status and alerts. Defines AQI/CO2/VOC thresholds, enable flags, derived status sensors, and recheck notifications through the shared mobile notifier. |
| `cameras.yaml` | Camera notification automation for motion/event payloads, with guard logic for actionable mobile alerts. |
| `climate_diagnostics.yaml` | Dashboard-facing climate diagnostics derived from thermostat state and room temperature sensors. This package does not change thermostat behavior. |
| `climate_extreme_heat.yaml` | Extreme-heat overlay for the climate system: forecast hot-day detection, configurable threshold/offset helpers, pre-cool eligibility, and bounded restore behavior. |
| `climate_occupancy.yaml` | Presence-aware climate behavior: away targets, return-home schedule resume, and pre-arrival recovery based on person/proximity abstractions. |
| `climate_schedule.yaml` | Baseline climate control for the dining-room thermostat: setpoint helpers, schedule windows, occupied setpoint application, and startup resync. |
| `device_batteries.yaml` | Battery monitoring rollups, proactive alert thresholds, critical/low battery notifications, and notification action handling. |
| `device_connectivity.yaml` | Device health monitoring for stale devices, Z-Wave node health, integration availability, and conservative alerting. |
| `exterior_door_monitoring.yaml` | Two-minute continuous-open household alerts and matching per-door tagged clears for the front, back, and garage interior contacts. Immediate armed-security and secure-house checks remain in their separate packages. |
| `garage_door_monitoring.yaml` | Garage-door open-duration monitoring, reminder/escalation helpers, actionable notifications, and related scripts/templates. |
| `known_batteries.yaml` | Template sensors that normalize known battery-powered devices into consistent names and attributes for the battery-health package. |
| `light_groups.yaml` | Logical Home Assistant light groups for easier control by rooms or household areas. |
| `notifications.yaml` | Shared notification automations that do not belong to a larger feature package, currently including bus/school-day notification handling. |
| `presence.yaml` | Presence-related behavior, including alarm-panel helpers and lighting automations tied to occupancy/time conditions. |
| `remotes.yaml` | Z-Wave remote support: helper toggles, scripts, and blueprint-backed automations for Brian and Hester remotes. |
| `routines.yaml` | Household scripts such as the Good Night routine, intended for direct calls from automations, dashboards, or voice assistants. |
| `seasonal.yaml` | Active seasonal lighting automation, currently for seasonal/holiday decoration behavior. |
| `security_door_alerts.yaml` | Immediate high-priority alerts when front, back, or garage-interior security-boundary contacts open while the alarm is armed away/night. Uses a separate security tag namespace, clears only those tags on close, and announces once through the master bedroom display. |
| `security_lights.yaml` | Security-focused lighting helpers and automations, including after-dark/security-event lighting behavior. |
| `security_sanity.yaml` | Reusable secure-house sanity check workflow used by routines and presence flows to verify/notify about doors, locks, garage state, and other security context. |
| `shared_infrastructure.yaml` | Shared package contracts: `notify.all_mobile_devices` and YAML-managed Lovelace dashboards for climate control and ventilation advice. |
| `towner_notifications.yaml` | School arrival/departure notification workflow that handles infrequent location updates, race conditions, verification windows, and timeout/reset states. |
| `weather.yaml` | Weather processing and cache helpers, including MQTT weather data, forecast sensors, and event-based automation triggers. |
| `window_ventilation.yaml` | Advisory window-ventilation recommendations using indoor/outdoor comfort, dew point, rain forecast, HVAC state, and relative air-quality context. |

## Climate subsystem

Climate control is intentionally split across packages:

- `climate_schedule.yaml` owns the normal setpoint schedule and thermostat application script.
- `climate_occupancy.yaml` adjusts behavior for away, return-home, guest, and pre-arrival contexts.
- `climate_extreme_heat.yaml` layers a bounded pre-cool overlay on top of the baseline schedule when forecast heat warrants it.
- `climate_diagnostics.yaml` exposes read-only diagnostic sensors for the dashboard.
- `dashboards/climate_control.yaml` is registered by `shared_infrastructure.yaml` and is the operator-facing view for the subsystem.

Do not collapse these packages into one file just because they share a thermostat. The split keeps tuning helpers, behavioral automation, overlays, and diagnostics reviewable.

## Notifications

Packages that send household alerts should use `notify.all_mobile_devices` from `shared_infrastructure.yaml` unless they have a clear reason to target a narrower notify service. This keeps mobile fan-out in one place and prevents feature packages from duplicating root-level notifier definitions.

Notification-heavy packages include:

- `air_quality.yaml`
- `device_batteries.yaml`
- `device_connectivity.yaml`
- `garage_door_monitoring.yaml`
- `notifications.yaml`
- `security_sanity.yaml`
- `towner_notifications.yaml`
- `window_ventilation.yaml`

## Dashboards and operator views

`shared_infrastructure.yaml` registers YAML dashboards from `dashboards/`:

- `climate-control` from `dashboards/climate_control.yaml`
- `window-ventilation` from `dashboards/window_ventilation.yaml` (title: "Ventilation Advisor")

Packages should add dashboard-facing sensors/templates inside the feature package that owns the data, then wire the presentation in `dashboards/` when a dedicated operator view is needed.

## Disabled package files

| File | Status |
|---|---|
| `aircraft.yaml.disabled` | Inactive aircraft-tracking reference package. Not loaded by Home Assistant. |
| `chores.yaml.disabled` | Inactive chore-rotation reference package. Not loaded by Home Assistant. |
| `seasonal.yaml.disabled` | Inactive previous seasonal automation reference. The active seasonal package is `seasonal.yaml`. |

## Adding or changing a package

1. Start from the latest `dev` branch and make changes in a focused branch.
2. Keep related entities, helpers, scripts, templates, and automations together in the owning package.
3. Put shared root-level infrastructure in `shared_infrastructure.yaml`, not in individual feature packages.
4. Add or update dashboard files under `dashboards/` when an operator view is required.
5. Update this README whenever `packages/*.yaml` is added, renamed, removed, enabled, or disabled.
6. Prefer static YAML/package validation first. Do not restart or reload the live Home Assistant host unless a task explicitly authorizes that side effect.

See `../DEVELOPMENT.md` for the broader development workflow.
