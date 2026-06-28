from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CLIMATE = ROOT / "packages" / "climate_control.yaml"


def load_climate():
    return yaml.safe_load(CLIMATE.read_text())


def automation(automation_id):
    for item in load_climate()["automation"]:
        if item["id"] == automation_id:
            return item
    raise AssertionError(f"automation {automation_id!r} not found")


def binary_sensor(name):
    for block in load_climate()["template"]:
        for sensor in block.get("binary_sensor", []):
            if sensor["name"] == name:
                return sensor
    raise AssertionError(f"binary sensor {name!r} not found")


def test_extreme_heat_helpers_are_configurable_in_fahrenheit():
    config = load_climate()

    threshold = config["input_number"]["climate_extreme_heat_threshold"]
    offset = config["input_number"]["climate_extreme_heat_precool_offset"]

    assert threshold["unit_of_measurement"] == "°F"
    assert threshold["initial"] == 95
    assert offset["unit_of_measurement"] == "°F"
    assert offset["min"] == 0
    assert offset["max"] == 2
    assert offset["initial"] == 1
    assert config["input_boolean"]["climate_extreme_heat_overlay_enabled"]["initial"] is True
    assert config["input_boolean"]["climate_extreme_heat_precool_active"]["initial"] is False


def test_extreme_heat_day_uses_validated_daily_forecast_attributes_not_derived_sensor():
    sensor = binary_sensor("Climate Extreme Heat Day")
    state = sensor["state"]
    attrs = sensor["attributes"]

    assert "state_attr('sensor.weather_daily_forecast', 'forecast')" in state
    assert "state_attr('sensor.weather_daily_forecast', source_entity)" in state
    assert "forecast[:2]" in state
    assert "period.temperature" in state
    assert "input_number.climate_extreme_heat_threshold" in state
    assert "sensor.temperature_forecast_high_today" not in state
    assert attrs["forecast_source"] == "sensor.weather_daily_forecast"
    assert "Fahrenheit" in attrs["forecast_unit_assumption"]


def test_precool_apply_is_bounded_occupied_and_one_shot():
    item = automation("climate_extreme_heat_precool_apply")
    text = CLIMATE.read_text()

    assert {trigger.get("id") for trigger in item["trigger"]} == {
        "overlay_window_start",
        "hot_day_detected",
        "guest_mode_enabled",
    }
    assert any(trigger.get("at") == "13:00:00" for trigger in item["trigger"])
    assert "before: \"18:00:00\"" in text
    assert "binary_sensor.climate_extreme_heat_day" in text
    assert "input_boolean.climate_extreme_heat_precool_active" in text
    assert "state: \"off\"" in text
    assert "zone.home" in text
    assert "input_boolean.mode_guest" in text
    assert "day - offset" in text
    assert "input_boolean.turn_on" in text


def test_precool_apply_rearms_for_guest_mode_without_return_home_race():
    item = automation("climate_extreme_heat_precool_apply")

    guest_enabled = next(
        trigger for trigger in item["trigger"] if trigger.get("id") == "guest_mode_enabled"
    )

    assert "return_home" not in {trigger.get("id") for trigger in item["trigger"]}
    assert guest_enabled == {
        "platform": "state",
        "entity_id": "input_boolean.mode_guest",
        "to": "on",
        "id": "guest_mode_enabled",
    }
    assert any(
        condition.get("entity_id") == "input_boolean.climate_extreme_heat_precool_active"
        and condition.get("state") == "off"
        for condition in item["condition"]
    )


def test_return_home_deactivate_applies_extreme_heat_overlay_before_day_restore():
    apply = automation("climate_extreme_heat_precool_apply")
    deactivate = automation("climate_away_mode_deactivate")
    extreme_heat_branch = deactivate["action"][1]["choose"][1]
    daytime_branch = deactivate["action"][1]["choose"][2]

    assert not any(
        trigger.get("entity_id") == "zone.home" for trigger in apply["trigger"]
    )
    assert deactivate["trigger"] == [
        {"platform": "numeric_state", "entity_id": "zone.home", "above": 0}
    ]
    assert any(
        condition.get("entity_id") == "input_boolean.climate_extreme_heat_overlay_enabled"
        and condition.get("state") == "on"
        for condition in extreme_heat_branch["conditions"]
    )
    assert any(
        condition.get("entity_id") == "binary_sensor.climate_extreme_heat_day"
        and condition.get("state") == "on"
        for condition in extreme_heat_branch["conditions"]
    )
    assert any(
        condition.get("condition") == "time"
        and condition.get("after") == "12:59:00"
        and condition.get("before") == "18:00:00"
        for condition in extreme_heat_branch["conditions"]
    )

    set_temperature_steps = [
        step
        for step in extreme_heat_branch["sequence"]
        if step.get("service") == "climate.set_temperature"
    ]
    assert len(set_temperature_steps) == 1
    assert "day - offset" in set_temperature_steps[0]["data"]["target_temp_high"]
    assert any(
        step.get("service") == "input_boolean.turn_on"
        and step.get("target", {}).get("entity_id")
        == "input_boolean.climate_extreme_heat_precool_active"
        for step in extreme_heat_branch["sequence"]
    )
    assert daytime_branch["conditions"] == [
        {"condition": "time", "after": "09:00:00", "before": "21:00:00"}
    ]


def test_precool_restore_returns_day_targets_without_fighting_away_mode():
    item = automation("climate_extreme_heat_precool_restore")
    text = CLIMATE.read_text()

    assert any(trigger.get("at") == "18:00:00" for trigger in item["trigger"])
    assert any(trigger.get("id") == "away_started" for trigger in item["trigger"])
    assert "trigger.id != 'away_started'" in text
    assert "input_boolean.turn_off" in text
    assert "states('input_number.climate_cool_day')" in text
    assert "states('input_number.climate_heat_day')" in text
