from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "window_ventilation.yaml"


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def sensor_names(package):
    names = []
    for block in package["template"]:
        for sensor in block.get("sensor", []):
            names.append(sensor["name"])
    return names


def automation_by_id(package, automation_id):
    for automation in package["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"automation {automation_id!r} not found")


def test_window_ventilation_required_entities_are_defined():
    package = load_package()

    assert "Window Ventilation Indoor Dew Point" in sensor_names(package)
    assert "Window Ventilation Recommendation" in sensor_names(package)
    assert "Window Ventilation Reason" in sensor_names(package)

    binary_names = [
        sensor["name"]
        for block in package["template"]
        for sensor in block.get("binary_sensor", [])
    ]
    assert "Window Ventilation Favorable" in binary_names
    assert "Window Ventilation Unfavorable" in binary_names


def test_window_ventilation_uses_household_relative_air_quality_baselines():
    package = load_package()
    statistic_sensors = package["sensor"]

    assert {
        sensor["entity_id"] for sensor in statistic_sensors
    } == {"sensor.thermostat_carbon_dioxide", "sensor.thermostat_vocs"}
    assert all(sensor["platform"] == "statistics" for sensor in statistic_sensors)
    assert all(sensor["state_characteristic"] == "mean" for sensor in statistic_sensors)

    package_text = PACKAGE.read_text()
    assert "sensor.window_ventilation_co2_baseline" in package_text
    assert "sensor.window_ventilation_voc_baseline" in package_text
    assert "co2 >= 1400" in package_text
    assert "co2_base > 0 and co2 >= 1400" in package_text
    assert "voc >= 650" in package_text
    assert "voc_base > 0 and voc >= 650" in package_text
    assert "sensor.temperature_forecast_high_today" not in package_text
    assert "states('sensor.weather_outdoor_temperature')" in package_text
    assert "states('sensor.weather_outdoor_dew_point')" in package_text
    assert "state_attr('weather.forecast_home', 'temperature')" not in package_text
    assert "state_attr('weather.forecast_home', 'dew_point')" not in package_text


def test_window_ventilation_notifications_are_advisory_and_gated():
    package = load_package()

    open_advisory = automation_by_id(package, "window_ventilation_open_advisory")
    close_advisory = automation_by_id(package, "window_ventilation_close_advisory")
    neutral_clear = automation_by_id(
        package, "window_ventilation_neutral_clear_notification"
    )

    assert open_advisory["trigger"][0]["for"] == {"minutes": 15}
    assert close_advisory["trigger"][0]["for"] == {"minutes": 7}

    for automation in (open_advisory, close_advisory):
        conditions = automation["condition"]
        assert {
            condition["condition"] for condition in conditions
        } >= {"state", "numeric_state", "time"}
        assert any(
            condition.get("entity_id") == "zone.home" and condition.get("above") == 0
            for condition in conditions
        )
        assert automation["action"][-1]["service"] == "notify.all_mobile_devices"

    assert neutral_clear["action"][0]["data"]["message"] == "clear_notification"


def test_window_ventilation_close_advisory_only_fires_after_open_advisory():
    package = load_package()
    close_advisory = automation_by_id(package, "window_ventilation_close_advisory")
    trigger = close_advisory["trigger"][0]

    assert trigger["from"] == "open"
    assert trigger["to"] == "close"


def test_window_ventilation_neutral_to_close_does_not_match_close_advisory():
    package = load_package()
    close_advisory = automation_by_id(package, "window_ventilation_close_advisory")
    trigger = close_advisory["trigger"][0]

    assert not (
        trigger.get("from") in (None, "neutral")
        and trigger["to"] == "close"
    )
