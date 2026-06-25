from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
WEATHER_YAML = ROOT / "packages" / "weather.yaml"
ROUTINES_YAML = ROOT / "packages" / "routines.yaml"
GARAGE_YAML = ROOT / "packages" / "garage_door_monitoring.yaml"
FIXED_NOW = datetime(2026, 6, 3, 12, 0, 0)


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def render_template(template_string: str, *, state_map=None, context=None):
    env = Environment(trim_blocks=True, lstrip_blocks=True)
    state_map = state_map or {}
    context = context or {}

    def states(entity_id):
        return state_map.get(entity_id)

    def as_timestamp(value):
        if isinstance(value, datetime):
            return value.timestamp()
        if value in (None, "", "unknown", "unavailable"):
            raise ValueError(f"invalid timestamp source: {value!r}")
        return datetime.fromisoformat(value).timestamp()

    env.globals.update(
        states=states,
        is_state=lambda entity_id, expected: states(entity_id) == expected,
        state_attr=lambda entity_id, attr: context.get("state_attr", {}).get((entity_id, attr)),
        as_timestamp=as_timestamp,
        now=lambda: FIXED_NOW,
    )
    return env.from_string(template_string).render(context)


def normalize_bool(value):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise AssertionError(f"expected boolean-like render, got {value!r}")


def routine_variables(script_name: str):
    sequence = load_yaml(ROUTINES_YAML)["script"][script_name]["sequence"]
    for step in sequence:
        if "variables" in step:
            return step["variables"]
    raise AssertionError(f"script {script_name!r} has no variables step")


def weather_automation(automation_id: str):
    for automation in load_yaml(WEATHER_YAML)["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"weather automation {automation_id!r} not found")


def garage_automation(automation_id: str):
    for automation in load_yaml(GARAGE_YAML)["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"garage automation {automation_id!r} not found")


def garage_active_tag_templates():
    closed_reset = garage_automation("garage_door_closed_reset_notification")
    action_handler = garage_automation("garage_door_notification_actions")
    choose_blocks = action_handler["action"][0]["choose"]
    return [
        closed_reset["action"][2]["if"][0]["value_template"],
        choose_blocks[1]["sequence"][2]["if"][0]["value_template"],
        choose_blocks[2]["sequence"][2]["if"][0]["value_template"],
    ]


def test_weather_refresh_treats_empty_and_none_last_updated_as_invalid():
    template_string = weather_automation("weather_data_refresh")["condition"][0]["value_template"]

    for invalid_value in ("unknown", "unavailable", "", None):
        rendered = render_template(
            template_string,
            state_map={
                "sensor.weather_last_updated": invalid_value,
                "input_number.weather_update_frequency": "30",
            },
        )
        assert normalize_bool(rendered) is True



def test_good_night_dishwasher_availability_handles_empty_and_none_states():
    variables = routine_variables("good_night")
    template_string = variables["is_dishwasher_available"]

    for invalid_value in ("unknown", "unavailable", "", None):
        rendered = render_template(
            template_string,
            state_map={"sensor.kitchen_dishwasher_operation_state": invalid_value},
            context={"dishwasher_state": invalid_value},
        )
        assert normalize_bool(rendered) is False

    rendered = render_template(
        template_string,
        state_map={"sensor.kitchen_dishwasher_operation_state": "run"},
        context={"dishwasher_state": "run"},
    )
    assert normalize_bool(rendered) is True



def test_garage_notification_tag_checks_share_the_same_invalid_state_handling():
    for template_string in garage_active_tag_templates():
        for invalid_value in ("unknown", "unavailable", "", None, "unset"):
            rendered = render_template(template_string, context={"active_tag": invalid_value})
            assert normalize_bool(rendered) is False

        rendered = render_template(template_string, context={"active_tag": "garage-door-open-123"})
        assert normalize_bool(rendered) is True
