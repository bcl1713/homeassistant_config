# Kitchen Prep target-time policy

`meal_prep_target_policy.yaml` resolves `sensor.meal_prep_target_time` without
refreshing Mealie, calling devices, or making any Mealie write.

## Configuration

- Set `input_datetime.meal_prep_default_dinner_time` to the household's local
  dinner target. It intentionally has no `initial`; leaving it unset means no
  default time is fabricated.
- For one meal, set both `input_datetime.meal_prep_target_time_override` (local
  date and time) and `input_text.meal_prep_target_time_override_key` to the
  exact `YYYY-MM-DD|dinner` meal identity, for example `2026-07-24|dinner`.

## Fixed precedence and validation

1. A valid Mealie scheduled time wins.
2. Otherwise, a matching per-day/per-meal override wins.
3. Otherwise, the configured default applies to a dinner meal only.
4. If none is valid, the target remains explicitly `none`.

Mealie's `date` field is a meal-date identity when it is `YYYY-MM-DD`. It is a
scheduled target only when it is ISO-8601 with an explicit `Z` or numeric UTC
offset. Timezone-less values, malformed values, and values whose converted Home
Assistant local date differs from the meal date are rejected. This preserves
local timezone behavior across UTC midnight and keeps the existing date+recipe
session/orchestration identity from carrying a target into another day.

The resolved sensor has a `source` attribute: `mealie`, `override`, `default`,
or `none`. The Kitchen Prep dashboard shows the resolved time and source. A
stale historical value in `input_datetime.meal_prep_target_time` is hidden when
source is `none`, so automatic orchestration cannot silently use it.
