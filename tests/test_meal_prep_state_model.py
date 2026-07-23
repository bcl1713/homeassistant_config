from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "meal_prep.yaml"
PACKAGE_README = ROOT / "packages" / "README.md"
NOW = datetime(2026, 7, 23, 18, 0, tzinfo=timezone.utc)


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def sensor_by_name(name):
    for block in load_package()["template"]:
        for sensor in block.get("sensor", []):
            if sensor["name"] == name:
                return sensor
    raise AssertionError(f"template sensor {name!r} not found")


def as_timestamp(value, default=None):
    if value in (None, "", "unknown", "unavailable"):
        return default
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (AttributeError, ValueError):
        return default


def render(template, state_map):
    environment = Environment(trim_blocks=True, lstrip_blocks=True)
    environment.globals.update(
        states=lambda entity_id: state_map.get(entity_id, "unknown"),
        is_state=lambda entity_id, state: state_map.get(entity_id) == state,
        state_attr=lambda entity_id, attribute: None,
        as_timestamp=as_timestamp,
        now=lambda: NOW,
        none=None,
    )
    return environment.from_string(template).render().strip()


def evaluate(state_map):
    """Evaluate sensors in their dependency order using a fixed time fixture."""
    state_map = dict(state_map)
    source = sensor_by_name("Meal Prep Source Status")
    state_map["sensor.meal_prep_source_status"] = render(source["state"], state_map)
    for name, entity_id in (
        ("Meal Prep Meal", "sensor.meal_prep_meal"),
        ("Meal Prep Meal Type", "sensor.meal_prep_meal_type"),
        ("Meal Prep Recipe Reference", "sensor.meal_prep_recipe_reference"),
        ("Meal Prep Recipe URL", "sensor.meal_prep_recipe_url"),
        ("Meal Prep Target Time", "sensor.meal_prep_target_time"),
        ("Meal Prep Current Step", "sensor.meal_prep_current_step"),
        ("Meal Prep Next Step", "sensor.meal_prep_next_step"),
    ):
        state_map[entity_id] = render(sensor_by_name(name)["state"], state_map)
    state_map["sensor.meal_prep_session_state"] = render(
        sensor_by_name("Meal Prep Session State")["state"], state_map
    )
    return state_map


@pytest.fixture
def ready_meal():
    return {
        "input_text.meal_prep_source_status": "ready",
        "input_datetime.meal_prep_source_updated_at": "2026-07-23 17:30:00+00:00",
        "input_text.meal_prep_meal_title": "Vegetable Lasagna",
        "input_text.meal_prep_meal_type": "dinner",
        "input_text.meal_prep_recipe_reference": "recipe-123",
        "input_text.meal_prep_recipe_url": "https://mealie.example/recipe/recipe-123",
        "input_text.meal_prep_current_step": "Chop vegetables",
        "input_text.meal_prep_next_step": "Preheat oven",
        "input_datetime.meal_prep_target_time": "2026-07-23 19:00:00+00:00",
        "input_text.meal_prep_snooze_until": "",
        "input_boolean.meal_prep_active": "off",
        "input_boolean.meal_prep_done": "off",
    }


def test_helpers_are_stable_named_and_restored_without_initial_values():
    package = load_package()
    expected_helpers = {
        "input_boolean": {
            "meal_prep_active": ("Meal Prep Active", "mdi:chef-hat"),
            "meal_prep_done": ("Meal Prep Complete", "mdi:check-circle-outline"),
        },
        "input_datetime": {
            "meal_prep_target_time": ("Meal Prep Target Time", "mdi:calendar-clock"),
            "meal_prep_source_updated_at": ("Meal Prep Source Updated At", "mdi:database-clock-outline"),
        },
        "input_text": {
            "meal_prep_source_status": ("Meal Prep Source Status Input", "mdi:database-alert-outline"),
            "meal_prep_meal_title": ("Meal Prep Meal Title Input", "mdi:food-outline"),
            "meal_prep_meal_type": ("Meal Prep Meal Type Input", "mdi:format-list-bulleted-type"),
            "meal_prep_recipe_reference": ("Meal Prep Recipe Reference Input", "mdi:identifier"),
            "meal_prep_recipe_url": ("Meal Prep Recipe URL Input", "mdi:link-variant"),
            "meal_prep_current_step": ("Meal Prep Current Step Input", "mdi:format-list-numbered"),
            "meal_prep_next_step": ("Meal Prep Next Step Input", "mdi:skip-next-outline"),
            "meal_prep_snooze_until": ("Meal Prep Snooze Until", "mdi:pause-circle-outline"),
        },
    }

    for domain, helpers in expected_helpers.items():
        for entity_id, (name, icon) in helpers.items():
            assert package[domain][entity_id]["name"] == name
            assert package[domain][entity_id]["icon"] == icon
            assert "initial" not in package[domain][entity_id]

    assert "Restored; no `initial` is set." in PACKAGE_README.read_text()


@pytest.mark.parametrize(
    ("name", "changes", "expected_source", "expected_session"),
    [
        (
            "idle_no_meal",
            {
                "input_text.meal_prep_meal_title": "",
                "input_datetime.meal_prep_target_time": "unknown",
            },
            "ready",
            "idle",
        ),
        ("planned", {}, "ready", "planned"),
        (
            "prep_due",
            {"input_datetime.meal_prep_target_time": "2026-07-23 17:59:00+00:00"},
            "ready",
            "prep_due",
        ),
        ("active", {"input_boolean.meal_prep_active": "on"}, "ready", "active"),
        (
            "paused_snoozed",
            {"input_text.meal_prep_snooze_until": "2026-07-23 18:30:00+00:00"},
            "ready",
            "paused",
        ),
        ("complete", {"input_boolean.meal_prep_done": "on"}, "ready", "complete"),
        (
            "unavailable_source",
            {"input_text.meal_prep_source_status": "error"},
            "error",
            "unavailable",
        ),
        (
            "stale_source",
            {"input_datetime.meal_prep_source_updated_at": "2026-07-23 14:59:00+00:00"},
            "stale",
            "unavailable",
        ),
    ],
)
def test_fixture_matrix_covers_every_session_state(
    ready_meal, name, changes, expected_source, expected_session
):
    states = ready_meal | changes
    evaluated = evaluate(states)

    assert evaluated["sensor.meal_prep_source_status"] == expected_source, name
    assert evaluated["sensor.meal_prep_session_state"] == expected_session, name


def test_ready_snapshot_exposes_normalized_meal_recipe_and_instruction_seams(ready_meal):
    evaluated = evaluate(ready_meal)

    assert evaluated["sensor.meal_prep_meal"] == "Vegetable Lasagna"
    assert evaluated["sensor.meal_prep_meal_type"] == "dinner"
    assert evaluated["sensor.meal_prep_recipe_reference"] == "recipe-123"
    assert evaluated["sensor.meal_prep_recipe_url"] == "https://mealie.example/recipe/recipe-123"
    assert evaluated["sensor.meal_prep_target_time"] == "2026-07-23 19:00:00+00:00"
    assert evaluated["sensor.meal_prep_current_step"] == "Chop vegetables"
    assert evaluated["sensor.meal_prep_next_step"] == "Preheat oven"


@pytest.mark.parametrize(
    ("changes", "expected_source", "expected_meal", "expected_step"),
    [
        (
            {"input_text.meal_prep_source_status": "not-a-valid-status"},
            "unavailable",
            "unavailable",
            "unavailable",
        ),
        (
            {"input_datetime.meal_prep_source_updated_at": "not-a-timestamp"},
            "unavailable",
            "unavailable",
            "unavailable",
        ),
        (
            {"input_text.meal_prep_meal_title": "unknown"},
            "ready",
            "unavailable",
            "Chop vegetables",
        ),
        (
            {"input_text.meal_prep_current_step": "unavailable"},
            "ready",
            "Vegetable Lasagna",
            "unavailable",
        ),
        (
            {"input_text.meal_prep_recipe_url": "not a URL"},
            "ready",
            "Vegetable Lasagna",
            "Chop vegetables",
        ),
    ],
)
def test_invalid_source_values_fail_closed_without_fabricating_content(
    ready_meal, changes, expected_source, expected_meal, expected_step
):
    evaluated = evaluate(ready_meal | changes)

    assert evaluated["sensor.meal_prep_source_status"] == expected_source
    assert evaluated["sensor.meal_prep_meal"] == expected_meal
    assert evaluated["sensor.meal_prep_current_step"] == expected_step
    if changes.get("input_text.meal_prep_recipe_url") == "not a URL":
        assert evaluated["sensor.meal_prep_recipe_url"] == "unavailable"


def test_source_status_exposes_explicit_visible_reasons(ready_meal):
    status = sensor_by_name("Meal Prep Source Status")

    missing_time_reason = render(
        status["attributes"]["reason"],
        ready_meal | {"input_datetime.meal_prep_source_updated_at": "unknown"},
    )
    stale_reason = render(
        status["attributes"]["reason"],
        ready_meal | {"input_datetime.meal_prep_source_updated_at": "2026-07-23 14:59:00+00:00"},
    )

    assert missing_time_reason == "missing source update time"
    assert stale_reason == "source update is older than 180 minutes"


def test_package_is_source_independent_and_defers_actions_to_later_cards():
    package = load_package()
    package_text = PACKAGE.read_text()

    assert set(package) == {"input_boolean", "input_datetime", "input_text", "template"}
    assert "rest:" not in package_text
    assert "automation:" not in package_text
    assert "script:" not in package_text
    assert "service:" not in package_text
    assert "#209" in package_text
    assert "#208/#210" in package_text
    assert "180 minutes" in PACKAGE_README.read_text()
