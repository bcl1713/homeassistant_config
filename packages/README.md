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
| `meal_prep.yaml` | Kitchen meal-preparation state model and deterministic manual Start/Done/Skip/Snooze/Finish/display/clear script seams. It owns persistent helper seams and read-only normalized meal/status/step/session/recipe-context sensors. |
| `meal_prep_target_policy.yaml` | Explicit Kitchen Prep target-time resolution: valid Mealie scheduled timestamp, matching local per-day/per-meal override, then household default dinner time; no usable value remains unconfigured. |
| `mealie_read_only.yaml` | Read-only Mealie GET adapter. It refreshes a bounded today/upcoming plan and linked recipe into `meal_prep.yaml` helpers every 15 minutes. |
| `meal_prep_orchestration.yaml` | Kitchen Prep automatic start/cleanup and one-time Cast behavior, bounded by fresh source data, today’s target/prep window, household presence, and guest mode. |
| `notifications.yaml` | Shared notification automations that do not belong to a larger feature package, currently including bus/school-day notification handling. |
| `presence.yaml` | Presence-related behavior, including alarm-panel helpers and lighting automations tied to occupancy/time conditions. |
| `protected_contacts.yaml` | Canonical, read-only inventory and open-state summary for eight window contacts plus Front Door, Back Door, and Garage Interior Door. Future packages should consume this seam rather than duplicate the protected-contact roster. |
| `remotes.yaml` | Z-Wave remote support: helper toggles, scripts, and blueprint-backed automations for Brian and Hester remotes. |
| `routines.yaml` | Household scripts such as the Good Night routine, intended for direct calls from automations, dashboards, or voice assistants. |
| `seasonal.yaml` | Active seasonal lighting automation, currently for seasonal/holiday decoration behavior. |
| `security_door_alerts.yaml` | Immediate high-priority alerts when front, back, or garage-interior security-boundary contacts open while the alarm is armed away/night. Uses a separate security tag namespace, clears only those tags on close, and announces once through the master bedroom display. |
| `security_lights.yaml` | Security-focused lighting helpers and automations, including after-dark/security-event lighting behavior. |
| `security_sanity.yaml` | Reusable secure-house sanity check workflow used by routines and presence flows to verify/notify about doors, locks, garage state, and other security context. |
| `shared_infrastructure.yaml` | Shared package contracts: `notify.all_mobile_devices` and YAML-managed Lovelace dashboards for climate control, ventilation advice, and Kitchen Prep. |
| `towner_notifications.yaml` | School arrival/departure notification workflow that handles infrequent location updates, race conditions, verification windows, and timeout/reset states. |
| `trash_recycling_reminder.yaml` | Municipality-calendar-driven trash/recycling-night Zooz LED reminder. It snapshots and restores explicitly scoped wall-switch/dimmer LED settings, shows blue for garbage-only and green when recycling is also listed, and safely ignores unknown or recycling-only calendar text. |
| `weather.yaml` | Weather processing and cache helpers, including MQTT weather data, forecast sensors, and an open-window rain alert that names affected monitored windows and clears after they all close. |
| `window_ventilation.yaml` | Advisory window-ventilation recommendations using indoor/outdoor comfort, dew point, rain forecast, HVAC state, and relative air-quality context. |

## Climate subsystem

Climate control is intentionally split across packages:

- `climate_schedule.yaml` owns the normal setpoint schedule and thermostat application script.
- `climate_occupancy.yaml` adjusts behavior for away, return-home, guest, and pre-arrival contexts.
- `climate_extreme_heat.yaml` layers a bounded pre-cool overlay on top of the baseline schedule when forecast heat warrants it.
- `climate_diagnostics.yaml` exposes read-only diagnostic sensors for the dashboard.
- `dashboards/climate_control.yaml` is registered by `shared_infrastructure.yaml` and is the operator-facing view for the subsystem.

Do not collapse these packages into one file just because they share a thermostat. The split keeps tuning helpers, behavioral automation, overlays, and diagnostics reviewable.

## Kitchen meal-preparation state seam

`meal_prep.yaml` is a state-model package, not an integration package. It is
safe to load before a source is configured: the source-status sensor fails
closed, and presentation sensors report `unavailable` or `none` rather than
inventing meal or instruction content.

| Entity ID | Friendly name | Purpose | Persistence decision |
|---|---|---|---|
| `input_boolean.meal_prep_active` | Meal Prep Active | Manual active-session flag for the matching meal/date identity. | Restored; no `initial` is set. |
| `input_boolean.meal_prep_done` | Meal Prep Complete | Manual finish-for-today flag for the matching meal/date identity. | Restored; no `initial` is set. |
| `input_datetime.meal_prep_target_time` | Meal Prep Target Time | Local dinner-ready target-time seam. | Restored; no `initial` is set. |
| `input_datetime.meal_prep_source_updated_at` | Meal Prep Source Updated At | Snapshot timestamp for freshness. | Restored; no `initial` is set. |
| `input_text.meal_prep_snooze_until` | Meal Prep Snooze Until | ISO timestamp seam for a paused session. | Restored; no `initial` is set. |
| `input_text.meal_prep_session_key` | Meal Prep Session Key | Date + recipe-reference identity that scopes restored active/done/snooze state. | Restored; no `initial` is set. |
| `input_text.meal_prep_last_skipped_step` | Meal Prep Last Skipped Step | Bounded record of the most recent deliberate skip; it never marks the meal complete. | Restored; no `initial` is set. |
| `input_text.meal_prep_remaining_steps` | Meal Prep Remaining Steps | Bounded escaped-delimiter source queue after the current/next steps, used only for deterministic manual advancement. | Restored; no `initial` is set. |
| `input_text.meal_prep_recipe_prep_time`, `input_text.meal_prep_recipe_cook_time`, `input_text.meal_prep_recipe_total_time` | Meal Prep Recipe Timing Inputs | Raw Mealie `prepTime`, `cookTime`, and `totalTime` durations for automatic lead-time calculation. | Restored; no `initial` is set. |
| `input_text.meal_prep_automatic_handled_key` | Meal Prep Automatic Handled Key | Date + recipe identity manually or automatically claimed to prevent repeat automatic starts/Casts. | Restored; no `initial` is set. |
| `input_boolean.meal_prep_mealie_writeback_enabled` | Enable Mealie made-this write-back | Explicit opt-in for the separate confirmed Mealie last-made PATCH. Defaults off when no state is restored. | Restored; off without a prior state. |
| `input_text.meal_prep_mealie_marked_key`, `input_text.meal_prep_mealie_write_pending_key`, `input_text.meal_prep_mealie_write_pending_timestamp` | Mealie write identity | Local stable identity and timestamp used to prevent duplicates and make an unknown-outcome retry send the same PATCH body. | Restored; no `initial` is set. |
| `input_text.meal_prep_mealie_write_status`, `input_text.meal_prep_mealie_write_reason` | Mealie write-back result | Bounded local success/failure result only; never stores a Mealie payload, URL, or credential. | Restored; no `initial` is set. |
| `input_text.meal_prep_source_status` | Meal Prep Source Status Input | Future normalizer's raw status seam. | Restored; no `initial` is set. |
| `input_text.meal_prep_meal_title`, `input_text.meal_prep_meal_type` | Meal Prep Meal Title/Type Input | Raw meal-identity seams. | Restored; no `initial` is set. |
| `input_text.meal_prep_recipe_reference`, `input_text.meal_prep_recipe_url` | Meal Prep Recipe Reference/URL Input | Raw recipe seams. | Restored; no `initial` is set. |
| `input_text.meal_prep_current_step`, `input_text.meal_prep_next_step` | Meal Prep Current/Next Step Input | Raw instruction-presentation seams. | Restored; no `initial` is set. |
| `sensor.meal_prep_source_status` | Meal Prep Source Status | Normalized freshness/status and visible reason. | Derived at runtime. |
| `sensor.meal_prep_meal`, `sensor.meal_prep_meal_type` | Meal Prep Meal/Meal Type | Safe normalized meal identity. | Derived at runtime. |
| `sensor.meal_prep_recipe_reference`, `sensor.meal_prep_recipe_url` | Meal Prep Recipe Reference/URL | Safe normalized recipe seams. | Derived at runtime. |
| `sensor.meal_prep_target_time` | Meal Prep Target Time | Safe local dinner-ready target-time presentation. | Derived at runtime. |
| `input_select.meal_prep_automatic_lead_time_policy` | Meal Prep Automatic Lead-Time Policy | Configurable dinner-ready timing semantic. | Defaults to `total_time` by first option; selection is restored. |
| `sensor.meal_prep_automatic_start_time` | Meal Prep Automatic Start Time | Safe calculated start from target minus selected lead time. | Derived at runtime. |
| `sensor.meal_prep_current_step`, `sensor.meal_prep_next_step` | Meal Prep Current/Next Step | Safe normalized instruction seams. | Derived at runtime. |
| `sensor.meal_prep_session_state` | Meal Prep Session State | `idle`, `planned`, `prep_due`, `active`, `paused`, `complete`, or `unavailable`. | Derived at runtime. |

On a clean Home Assistant start, un-restored source helpers do not claim a
meal: the operator check is that `sensor.meal_prep_source_status` is
`unavailable` with a reason and `sensor.meal_prep_session_state` is
`unavailable` or `idle`. A future normalizer must write a coherent `ready`
snapshot and its timestamp together. A non-`ready` status, a missing or
unparseable update time, a future-dated timestamp, or a timestamp more than
180 minutes old fails closed. `mealie_read_only.yaml` is the only automated
writer for source helpers. Manual controls are script-only and perform no
refresh, notification, or inferred cooking transition.

### Kitchen Prep manual controls

`meal_prep.yaml` owns these stable script service IDs:

| Service | Deterministic behavior |
|---|---|
| `script.meal_prep_start_preparation` | Requires a fresh valid meal/current step, records a new date+recipe identity once, and activates the session. Re-running it for the same restored identity does not reset progress. |
| `script.meal_prep_complete_current_step` | Requires an active matching fresh session and a valid supplied next step; promotes next to current once and clears next. It has no startup/reload trigger. |
| `script.meal_prep_skip_current_step` | Records the skipped current step, promotes a valid next step when one exists, and never sets the completion flag or fabricates a later step. |
| `script.meal_prep_snooze_preparation` | Requires an active matching fresh session and writes an ISO deadline bounded to 5–60 minutes (dashboard default: 30). |
| `script.meal_prep_finish_for_today` | Stops the active matching session, clears its snooze, and sets its restored done flag; a different date/recipe identity does not inherit completion. |
| `script.meal_prep_mark_made_in_mealie` | Separate, disabled-by-default Mealie write. It requires the dashboard's confirmation and a fresh UUID-linked recipe, then PATCHes only that recipe's `last-made` timestamp. It never runs from Start or Finish today; local identity/timestamp state blocks duplicates and makes unknown-outcome retries safe. |
| `script.meal_prep_show_dashboard` | When the kitchen display is off, wakes it and waits briefly for the receiver before calling `cast.show_lovelace_view` for the registered `kitchen-prep` view; repository validation does not call it. |
| `script.meal_prep_clear_session` | Clears only local session flags/audit state, never the Mealie snapshot. |

All scripts use `mode: single`, have no triggers, and fail closed on missing,
stale, malformed, or non-matching source/session state. The normalizer preserves
current/next values during an active matching session, so its 15-minute refresh
cannot replay an already advanced step. Later source steps are held only in a
bounded, delimiter-safe queue; controls never invent steps beyond that source data.

### Kitchen Prep automatic orchestration

`meal_prep_orchestration.yaml` starts only for a fresh, valid meal whose target
timestamp is today, in the half-open `[automatic start, target)` window, with
`zone.home` above zero and guest mode off. The dinner-ready policy is configured
by `input_select.meal_prep_automatic_lead_time_policy`: `total_time` (the
default) treats the target as ready-to-serve and uses valid Mealie `totalTime`;
`prep_plus_cook` sums valid `prepTime` and `cookTime`; and `prep_only` uses valid
`prepTime` alone when the target means cooking should begin. `total_time` falls
back only to valid positive prep-plus-cook when `totalTime` is missing or invalid;
it never adds total to either component, so it cannot double-count. The only
accepted forms are positive ISO-8601 `PT#H#M` values. Zero, negative, malformed,
partial, date/day, second, fractional, and otherwise unsupported values result
in no automatic start rather than guessing.

The restored `input_text.meal_prep_automatic_handled_key` is set for both manual
and automatic starts. It prevents refreshes, reloads, and restarts from repeating
the same meal's Cast. The only automatic device action is the shared display script, which conditionally
wakes `media_player.kitchen_display`, waits for its receiver to settle, then
calls `cast.show_lovelace_view` with `dashboard_path` and `view_path` both
`kitchen-prep`. It adds no lights, announcements, occupancy inference, or Mealie
writes. Cleanup clears only local
Kitchen Prep state for stale/invalid source, meal rollover, or everyone away
outside guest mode; `presence_everyone_left` remains the authoritative
display-off automation.

### Mealie read-only wiring

`mealie_read_only.yaml` uses only `GET` requests: the today endpoint first, then
one bounded today-to-seven-day range only when today is empty, and one linked
recipe request for the selected entry. It refreshes at Home Assistant startup
and every 15 minutes (a 15-minute cadence); the single automation mode prevents
overlapping API calls. No meal, recipe, shopping, or food write endpoint is configured by the
refresh automation.

### Optional confirmed Mealie made-this write-back

The separate `script.meal_prep_mark_made_in_mealie` is the only Kitchen Prep
write path. It is disabled by default through
`input_boolean.meal_prep_mealie_writeback_enabled`; `Finish today`, Start, the
15-minute refresh, and automatic orchestration remain local/read-only. When an
operator enables the toggle, the dashboard's **Mark made in Mealie** button
still presents a confirmation dialog and sends `confirm: true` to the script.

The verified Mealie `mealie-next` contract (upstream commit
`23603cc218f04d8cebfbf99d19d9877c69cb95dd`, 2026-07-24) is
`PATCH /api/recipes/{slug}/last-made` with JSON `{"timestamp":"<ISO-8601>"}`.
The Kitchen Prep adapter accepts only a fresh UUID-linked recipe and verifies a
200 JSON recipe response with the same ID before recording local success. This
changes only Mealie's linked recipe **Last made** timestamp; it does not create
a meal plan, timeline event, shopping entry, or any Home Assistant completion
state.

Before enabling it, add `mealie_mark_made_url` to `secrets.yaml` as the full
`/api/recipes/{{ mealie_recipe_id }}/last-made` URL. Do not commit or display
that URL, its authorization header, request payload, or response. The script
persists the date+recipe identity and a single ISO timestamp before the PATCH:
a successful identity prevents duplicate writes, while a timeout or transport
failure leaves the identity unmarked so a retry sends the exact same timestamp.
Unauthorized, duplicate, malformed, unavailable, timeout, transport, and
unsupported-endpoint responses fail closed and store only a bounded local
status/reason. To disable the feature immediately, turn off
`input_boolean.meal_prep_mealie_writeback_enabled`; no restart or reload is
needed.

Before deploying, the operator must add these values to the existing Home
Assistant `secrets.yaml` (never commit that file):

- `mealie_authorization_header`: the complete OAuth2 `Bearer ...` header value.
- `mealie_today_url`: the full `/api/households/mealplans/today` URL.
- `mealie_range_url`: the full bounded range URL containing literal Jinja
  `{{ mealie_range_start }}` and `{{ mealie_range_end }}` placeholders.
- `mealie_recipe_url`: the full recipe URL containing literal
  `{{ mealie_recipe_id }}`.
- `mealie_mark_made_url`: only when enabling optional write-back, the full
  `/api/recipes/{{ mealie_recipe_id }}/last-made` URL.

The adapter passes those values as explicit `rest_command` service data when it
calls the range and recipe endpoints. Do not rely on automation-local variables
being implicitly available while a secret-backed `rest_command` URL is rendered.

The adapter accepts the verified camelCase fields only (`entryType`, `recipeId`,
`prepTime`, `cookTime`, `totalTime`, `recipeIngredient`, and
`recipeInstructions`). It stores current/next instruction strings plus a
255-character, escaped-delimiter bounded queue for later instructions, six concise
ingredient labels / 255 characters, and a 160-character timing/servings
summary. Empty plans become the explicit ready/no-meal state. During an active
matching manual session, refresh preserves the current/next pair rather than
overwriting manual progress. Missing recipe
links, malformed payloads, auth errors, timeouts, and server errors fail closed.
A prior snapshot may remain visible only for its 180-minute freshness bound and
its source reason explicitly says it is a fresh cached snapshot after a Mealie
failure; it is never presented as a newly fetched result.

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

## Protected-contact state seam

`protected_contacts.yaml` owns the complete protected-contact inventory. Its
`sensor.protected_contact_summary` state is the number of currently open
contacts; its attributes expose friendly-name lists for open windows and
security-boundary doors, plus separate unavailable and unknown contact counts
and lists. The summary is read-only and creates no notifications. Other
packages should read `sensor.protected_contact_inventory` and
`sensor.protected_contact_summary` instead of embedding another contact list.

## Dashboards and operator views

`shared_infrastructure.yaml` registers YAML dashboards from `dashboards/`:

- `climate-control` from `dashboards/climate_control.yaml`
- `window-ventilation` from `dashboards/window_ventilation.yaml` (title: "Ventilation Advisor")
- `kitchen-prep` from `dashboards/kitchen_prep.yaml` (title: "Kitchen Prep", hidden from the sidebar)

The Kitchen Prep dashboard presents only normalized, fresh state from
`meal_prep.yaml`. It defers prep/cook metadata, servings, and concise ingredient
context to the read-only Mealie normalizer (#209), and its seven manual buttons
call the #210-owned stable Start/Done/Skip/Snooze/Finish/display/clear scripts.
Each script guards invalid source/session state, so the buttons have no dangling
service references or unsafe fallback behavior. After deployment, an operator can smoke-test the direct
`kitchen-prep` Lovelace view with `cast.show_lovelace_view` on
`media_player.kitchen_display`; that live check is not performed by repository
validation.

### Kitchen Prep deployment, recovery, and live smoke

Mealie remains the source of truth; Home Assistant only reads and presents its
meal/recipe snapshot and keeps local preparation-session state. Deploy the
reviewed `dev` revision through the established Home Assistant deployment
workflow, then confirm that `sensor.meal_prep_source_status`,
`sensor.meal_prep_session_state`, and the `kitchen-prep` dashboard load. Do
not expose the secret-backed Mealie header or URL values while checking this.

For a live smoke test, use a controlled planned meal with a linked recipe and
verify the fresh-source status, target time, manual controls, and one-time Cast
payload (`dashboard_path: kitchen-prep`, `view_path: kitchen-prep`) on the
physical `media_player.kitchen_display`. Record the verification time and
automation/script trace IDs in the deployment record. Do not reload Home
Assistant, invoke Cast, or alter household state solely for repository
validation.

To stop automatic Kitchen Prep behavior, disable
`automation.meal_prep_automatic_start` and
`automation.meal_prep_automatic_cleanup` through normal operator controls.
`automation.meal_prep_refresh_from_mealie` can also be disabled when the
read-only source refresh must be paused. Use
`script.meal_prep_clear_session` to recover from a stale or abandoned local
session; it preserves the Mealie snapshot. Do not add a separate display-off
action: `presence_everyone_left` remains the sole away display-off owner.

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
