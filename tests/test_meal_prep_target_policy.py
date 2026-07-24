from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "packages" / "meal_prep_target_policy.yaml"
MEALIE = ROOT / "packages" / "mealie_read_only.yaml"
DASHBOARD = ROOT / "dashboards" / "kitchen_prep.yaml"


def resolve_target(*, meal_date, meal_type="dinner", scheduled=None, override_key="", override=None, default=None, tz=ZoneInfo("America/Chicago")):
    """Reference the documented policy; inputs are source/configuration seams."""
    if not meal_date or not meal_type:
        return None, "none"
    if scheduled:
        try:
            value = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
        except ValueError:
            value = None
        if value and value.tzinfo and value.astimezone(tz).date().isoformat() == meal_date:
            return value.astimezone(tz), "mealie"
    if override and override_key == f"{meal_date}|{meal_type}":
        try:
            value = datetime.fromisoformat(override)
        except ValueError:
            value = None
        if value and value.date().isoformat() == meal_date:
            return value.replace(tzinfo=tz) if value.tzinfo is None else value.astimezone(tz), "override"
    if meal_type == "dinner" and default:
        return datetime.combine(datetime.fromisoformat(meal_date).date(), time.fromisoformat(default), tz), "default"
    return None, "none"


def test_policy_declares_household_default_override_and_fixed_precedence():
    policy = yaml.safe_load(POLICY.read_text())
    helpers = policy["input_datetime"]

    assert helpers["meal_prep_default_dinner_time"] == {
        "name": "Meal Prep Default Dinner Time",
        "icon": "mdi:clock-outline",
        "has_date": False,
        "has_time": True,
    }
    assert helpers["meal_prep_target_time_override"]["has_date"] is True
    assert helpers["meal_prep_target_time_override"]["has_time"] is True
    text = POLICY.read_text()
    assert "valid Mealie scheduled timestamp" in text
    assert "matching local per-day/per-meal override" in text
    assert "household's local default dinner time" in text


def test_default_override_and_valid_mealie_time_follow_precedence():
    default = "18:00:00"
    override = "2026-07-24 18:30:00"
    value, source = resolve_target(
        meal_date="2026-07-24", override_key="2026-07-24|dinner", override=override, default=default
    )
    assert (value.strftime("%H:%M:%S"), source) == ("18:30:00", "override")

    value, source = resolve_target(
        meal_date="2026-07-24",
        scheduled="2026-07-24T23:00:00+00:00",
        override_key="2026-07-24|dinner",
        override=override,
        default=default,
    )
    assert (value.strftime("%H:%M:%S"), source) == ("18:00:00", "mealie")

    value, source = resolve_target(meal_date="2026-07-24", default=default)
    assert (value.strftime("%H:%M:%S"), source) == ("18:00:00", "default")


def test_missing_malformed_ambiguous_and_mismatched_values_never_guess_a_target():
    assert resolve_target(meal_date="2026-07-24")[1] == "none"
    assert resolve_target(meal_date="2026-07-24", scheduled="2026-07-24T18:00:00", default=None)[1] == "none"
    assert resolve_target(meal_date="2026-07-24", scheduled="not-a-time", default=None)[1] == "none"
    assert resolve_target(
        meal_date="2026-07-24", override_key="2026-07-25|dinner", override="2026-07-24 18:00:00"
    )[1] == "none"
    assert resolve_target(meal_date="2026-07-24", meal_type="lunch", default="18:00:00")[1] == "none"


def test_timezone_conversion_and_date_rollover_use_local_meal_date_identity():
    # 00:30Z is still the prior local evening in America/Chicago.
    value, source = resolve_target(
        meal_date="2026-07-24", scheduled="2026-07-25T00:30:00+00:00"
    )
    assert (value.date().isoformat(), value.strftime("%H:%M"), source) == ("2026-07-24", "19:30", "mealie")
    assert resolve_target(
        meal_date="2026-07-25", scheduled="2026-07-25T00:30:00+00:00"
    )[1] == "none"


def test_mealie_mapping_and_dashboard_surface_resolved_target_source_without_writes():
    mealie = MEALIE.read_text()
    dashboard = DASHBOARD.read_text()

    assert "mealie_meal_date" in mealie
    assert "mealie_scheduled_time" in mealie
    assert "timezone-less timestamp is rejected" in mealie
    assert "input_text.meal_prep_source_scheduled_time" in mealie
    assert "POST" not in mealie and "PUT" not in mealie and "PATCH" not in mealie and "DELETE" not in mealie
    assert "Target-time source:" in dashboard
    assert "attribute: source" in dashboard


def test_lead_time_policy_defaults_to_total_time_and_exposes_safe_start_calculation():
    policy = yaml.safe_load(POLICY.read_text())
    selector = policy["input_select"]["meal_prep_automatic_lead_time_policy"]
    start = next(
        item
        for block in policy["template"]
        for item in block["sensor"]
        if item["name"] == "Meal Prep Automatic Start Time"
    )
    text = POLICY.read_text()

    assert selector["options"] == ["total_time", "prep_plus_cook", "prep_only"]
    assert "Dinner-ready lead-time policy defaults to `total_time`" in text
    assert "regex_match('^PT(?:[0-9]+H)?(?:[0-9]+M)?$')" in start["state"]
    assert "prep_plus_cook_fallback" in start["attributes"]["duration_source"]
    assert "total is never added" in text
    for duration in ("prep_time", "cook_time", "total_time"):
        assert f"input_text.meal_prep_recipe_{duration}" in text
    environment = Environment()
    environment.parse(start["state"])
    environment.parse(start["attributes"]["policy"])
    environment.parse(start["attributes"]["duration_source"])
