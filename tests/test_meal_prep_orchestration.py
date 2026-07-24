from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "meal_prep_orchestration.yaml"
STATE_MODEL = ROOT / "packages" / "meal_prep.yaml"
MEALIE = ROOT / "packages" / "mealie_read_only.yaml"

NOW = datetime(2026, 7, 23, 18, 30, tzinfo=timezone.utc)
IDENTITY = "2026-07-23|recipe-123"


def load_yaml(path):
    class SecretLoader(yaml.SafeLoader):
        pass

    SecretLoader.add_constructor(
        "!secret", lambda loader, node: f"!secret {loader.construct_scalar(node)}"
    )
    return yaml.load(path.read_text(), Loader=SecretLoader)


def automation_by_id(package, automation_id):
    return next(item for item in package["automation"] if item["id"] == automation_id)


def actions(node):
    found = []
    if isinstance(node, dict):
        if "action" in node:
            found.append(node["action"])
        for value in node.values():
            found.extend(actions(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(actions(value))
    return found


def duration_minutes(value):
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?", value or "")
    if not match or value == "PT":
        return None
    minutes = int(match.group(1) or 0) * 60 + int(match.group(2) or 0)
    return minutes or None


def resolve_lead_time(*, policy="total_time", prep="PT30M", cook="PT20M", total="PT50M"):
    prep_minutes = duration_minutes(prep)
    cook_minutes = duration_minutes(cook)
    total_minutes = duration_minutes(total)
    if policy == "prep_only":
        return (prep_minutes, "prep_time") if prep_minutes else (None, "none")
    if policy == "prep_plus_cook":
        return (
            (prep_minutes + cook_minutes, "prep_plus_cook")
            if prep_minutes and cook_minutes
            else (None, "none")
        )
    if policy == "total_time":
        if total_minutes:
            return total_minutes, "total_time"
        if prep_minutes and cook_minutes:
            return prep_minutes + cook_minutes, "prep_plus_cook_fallback"
    return None, "none"


def automatic_start_is_eligible(
    *,
    source="ready",
    meal="Dinner",
    recipe="recipe-123",
    target=NOW + timedelta(minutes=20),
    policy="total_time",
    prep_time="PT30M",
    cook_time="PT20M",
    total_time="PT50M",
    home=1,
    guest=False,
    active=False,
    done=False,
    snoozed=False,
    handled_key="",
):
    minutes, _duration_source = resolve_lead_time(
        policy=policy, prep=prep_time, cook=cook_time, total=total_time
    )
    identity = f"{NOW.date().isoformat()}|{recipe}"
    return (
        source == "ready"
        and meal not in {"none", "unknown", "unavailable"}
        and bool(re.fullmatch(r"[^\s|]+", recipe or ""))
        and target is not None
        and target.date() == NOW.date()
        and minutes is not None
        and target - timedelta(minutes=minutes) <= NOW < target
        and home > 0
        and not guest
        and not active
        and not done
        and not snoozed
        and handled_key != identity
    )


def test_automatic_start_has_bounded_triggers_and_exact_cast_payload():
    automatic = automation_by_id(load_yaml(PACKAGE), "meal_prep_automatic_start")
    text = PACKAGE.read_text()

    assert automatic["mode"] == "single"
    assert {trigger["platform"] for trigger in automatic["trigger"]} == {
        "homeassistant",
        "time_pattern",
        "state",
    }
    assert any(trigger.get("minutes") == "/1" for trigger in automatic["trigger"])
    assert actions(automatic["action"]) == [
        "input_text.set_value",
        "input_text.set_value",
        "input_boolean.turn_on",
        "cast.show_lovelace_view",
    ]
    cast = automatic["action"][-1]
    assert cast["target"]["entity_id"] == "media_player.kitchen_display"
    assert cast["data"] == {
        "dashboard_path": "kitchen-prep",
        "view_path": "kitchen-prep",
    }
    assert automatic["action"][-1]["action"] == "cast.show_lovelace_view"
    assert "homeassistant.turn_off" not in text


def test_lead_time_policy_selects_only_verified_duration_forms_and_fails_closed():
    assert duration_minutes("PT45M") == 45
    assert duration_minutes("PT1H15M") == 75
    for invalid in ("PT", "", "PT0M", "PT0H", "-PT30M", "45 minutes", "P1D", "PT30S", "PT1.5H"):
        assert duration_minutes(invalid) is None, invalid

    assert resolve_lead_time(policy="prep_only", prep="PT30M") == (30, "prep_time")
    assert resolve_lead_time(policy="prep_plus_cook", prep="PT30M", cook="PT20M") == (50, "prep_plus_cook")
    assert resolve_lead_time(policy="total_time", prep="PT30M", cook="PT20M", total="PT45M") == (45, "total_time")
    assert resolve_lead_time(policy="total_time", prep="PT30M", cook="PT20M", total="") == (50, "prep_plus_cook_fallback")
    assert resolve_lead_time(policy="total_time", prep="PT30M", cook="PT20M", total="PT0M") == (50, "prep_plus_cook_fallback")
    assert resolve_lead_time(policy="prep_plus_cook", prep="PT30M", cook="") == (None, "none")
    assert resolve_lead_time(policy="prep_only", prep="PT0M") == (None, "none")
    assert resolve_lead_time(policy="unexpected", prep="PT30M", cook="PT20M", total="PT50M") == (None, "none")

    assert automatic_start_is_eligible()
    assert automatic_start_is_eligible(policy="prep_only", prep_time="PT30M")
    assert automatic_start_is_eligible(policy="prep_plus_cook", prep_time="PT30M", cook_time="PT20M")
    assert automatic_start_is_eligible(policy="total_time", prep_time="PT30M", cook_time="PT20M", total_time="")
    assert not automatic_start_is_eligible(target=None)
    assert not automatic_start_is_eligible(target=NOW + timedelta(days=1))
    assert not automatic_start_is_eligible(policy="prep_only", prep_time="")
    assert not automatic_start_is_eligible(policy="prep_plus_cook", cook_time="PT0M")
    assert not automatic_start_is_eligible(policy="total_time", prep_time="", cook_time="", total_time="PT0M")
    assert not automatic_start_is_eligible(target=NOW + timedelta(minutes=90), total_time="PT30M")
    assert not automatic_start_is_eligible(target=NOW)


def test_automatic_start_requires_fresh_valid_meal_home_and_non_guest_context():
    for changes in (
        {"source": "stale"},
        {"source": "unavailable"},
        {"meal": "none"},
        {"recipe": "recipe 123"},
        {"recipe": "recipe|123"},
        {"home": 0},
        {"guest": True},
    ):
        assert not automatic_start_is_eligible(**changes), changes


def test_handled_identity_and_manual_overrides_prevent_repeat_start_or_cast():
    assert not automatic_start_is_eligible(handled_key=IDENTITY)
    assert not automatic_start_is_eligible(active=True)
    assert not automatic_start_is_eligible(done=True)
    assert not automatic_start_is_eligible(snoozed=True)

    state_model = load_yaml(STATE_MODEL)
    start = state_model["script"]["meal_prep_start_preparation"]
    finish = state_model["script"]["meal_prep_finish_for_today"]
    assert "input_text.meal_prep_automatic_handled_key" in str(start["sequence"])
    assert "input_text.meal_prep_automatic_handled_key" in str(finish["sequence"])
    assert "initial" not in state_model["input_text"]["meal_prep_automatic_handled_key"]


def test_cleanup_covers_restart_rollover_away_and_stale_without_display_or_extras():
    cleanup = automation_by_id(load_yaml(PACKAGE), "meal_prep_automatic_cleanup")
    text = PACKAGE.read_text()

    assert cleanup["mode"] == "single"
    assert {trigger["platform"] for trigger in cleanup["trigger"]} == {
        "homeassistant",
        "time",
        "state",
    }
    assert cleanup["action"] == [{"action": "script.meal_prep_clear_session"}]
    condition = cleanup["condition"][0]["value_template"]
    assert "sensor.meal_prep_source_status" in condition
    assert "session_key != meal_prep_identity" in condition
    assert "zone.home" in condition
    assert "input_boolean.mode_guest" in condition
    assert "media_player" not in str(cleanup)
    assert "light." not in text
    assert "notify." not in text
    assert "rest_command" not in text
    assert "kitchen occupancy" not in text.lower()


def test_mealie_prep_time_is_bounded_source_data_and_no_write_endpoint_was_added():
    mealie = load_yaml(MEALIE)
    helpers = load_yaml(STATE_MODEL)["input_text"]
    text = MEALIE.read_text()

    assert helpers["meal_prep_recipe_prep_time"]["max"] == 40
    assert "input_text.meal_prep_recipe_prep_time" in text
    assert "mealie_recipe.prepTime" in text
    assert all(command["method"] == "GET" for command in mealie["rest_command"].values())
    for forbidden in ("POST", "PUT", "PATCH", "DELETE"):
        assert forbidden not in text
