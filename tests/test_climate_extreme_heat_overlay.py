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


def test_precool_restore_returns_day_targets_without_fighting_away_mode():
    item = automation("climate_extreme_heat_precool_restore")
    text = CLIMATE.read_text()

    assert any(trigger.get("at") == "18:00:00" for trigger in item["trigger"])
    assert any(trigger.get("id") == "away_started" for trigger in item["trigger"])
    assert "trigger.id != 'away_started'" in text
    assert "input_boolean.turn_off" in text
    assert "states('input_number.climate_cool_day')" in text
    assert "states('input_number.climate_heat_day')" in text
