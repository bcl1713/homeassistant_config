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


def template_sensor_by_name(package, name):
    for block in package["template"]:
        for sensor in block.get("sensor", []):
            if sensor["name"] == name:
                return sensor
    raise AssertionError(f"template sensor {name!r} not found")


def automation_by_id(package, automation_id):
    for automation in package["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"automation {automation_id!r} not found")


def test_window_ventilation_required_entities_are_defined():
    package = load_package()

    assert "Window Ventilation Indoor Dew Point" in sensor_names(package)
    assert "Window Ventilation Decision Context" in sensor_names(package)
    assert "Window Ventilation Recommendation" in sensor_names(package)
    assert "Window Ventilation Reason" in sensor_names(package)

    binary_names = [
        sensor["name"]
        for block in package["template"]
        for sensor in block.get("binary_sensor", [])
    ]
    assert "Window Ventilation Favorable" in binary_names
    assert "Window Ventilation Unfavorable" in binary_names
    assert "Window Ventilation Brief Purge" in binary_names


def test_window_ventilation_uses_household_relative_air_quality_baselines():
    package = load_package()
    statistic_sensors = package["sensor"]

    assert {
        sensor["entity_id"] for sensor in statistic_sensors
    } == {"sensor.thermostat_carbon_dioxide", "sensor.thermostat_vocs"}
    assert all(sensor["platform"] == "statistics" for sensor in statistic_sensors)
    assert all(sensor["state_characteristic"] == "mean" for sensor in statistic_sensors)
    assert all(sensor["max_age"] == {"hours": 24} for sensor in statistic_sensors)
    assert all(sensor["sampling_size"] >= 2880 for sensor in statistic_sensors)
    assert all(sensor["sampling_size"] == 3600 for sensor in statistic_sensors)

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
    assert "rain_probability >= 30" in package_text
    assert "rain > 0.1" not in package_text


def test_window_ventilation_reuses_canonical_decision_context():
    package = load_package()

    context = template_sensor_by_name(package, "Window Ventilation Decision Context")
    recommendation = template_sensor_by_name(
        package, "Window Ventilation Recommendation"
    )
    reason = template_sensor_by_name(package, "Window Ventilation Reason")

    context_text = str(context)
    recommendation_text = str(recommendation)
    reason_text = str(reason)

    assert context["unique_id"] == "window_ventilation_decision_context"
    assert "sensor.window_ventilation_decision_context" in recommendation_text
    assert "sensor.window_ventilation_decision_context" in reason_text
    assert recommendation["attributes"]["context_entity"] == (
        "sensor.window_ventilation_decision_context"
    )

    for canonical_attribute in (
        "outdoor_cooler",
        "outdoor_drier",
        "raining",
        "hvac_running",
        "winter_mode",
        "humidity_reason",
        "air_quality_reason",
        "severe_stale_air_reason",
        "brief_purge_outdoor_temperature_ok",
        "brief_purge_outdoor_dew_point_ok",
        "brief_purge",
        "mild_open",
    ):
        assert canonical_attribute in context["attributes"]
        assert f"state_attr(ctx, '{canonical_attribute}')" in recommendation_text

    for source_reference in (
        "states('sensor.dining_room_thermostat_temperature')",
        "states('sensor.thermostat_humidity')",
        "states('sensor.weather_outdoor_temperature')",
        "states('sensor.weather_outdoor_dew_point')",
        "states('sensor.precipitation_forecast_next_hour')",
        "states('sensor.condition_forecast_next_hour')",
        "states('sensor.thermostat_carbon_dioxide')",
        "states('sensor.thermostat_vocs')",
        "states('sensor.air_quality_composite_status')",
        "states('sensor.air_quality_trend')",
    ):
        assert source_reference in context_text
        assert source_reference not in recommendation_text
        assert source_reference not in reason_text


def test_window_ventilation_has_distinct_brief_purge_recommendation_path():
    package = load_package()
    context = template_sensor_by_name(package, "Window Ventilation Decision Context")
    recommendation = template_sensor_by_name(
        package, "Window Ventilation Recommendation"
    )
    reason = template_sensor_by_name(package, "Window Ventilation Reason")
    package_text = PACKAGE.read_text()

    context_text = str(context)
    recommendation_state = recommendation["state"]
    reason_state = reason["state"]

    assert "window_ventilation_brief_purge_max_outdoor_temperature_delta" in package_text
    assert "window_ventilation_brief_purge_max_outdoor_dew_point" in package_text
    assert "severe_stale_air_reason" in context["attributes"]
    assert "brief_purge" in context["attributes"]
    assert "air_quality_composite_status') == 'poor'" in context_text
    assert "air_quality_trend') == 'worsening'" in context_text
    assert "co2 >= 1500" in context_text
    assert "co2 >= (co2_base + 400)" in context_text
    assert "voc >= 1000" in context_text
    assert "voc >= (voc_base * 1.75)" in context_text
    assert "open_briefly" in recommendation_state
    assert "elif brief_purge" in recommendation_state
    assert "rec == 'open_briefly'" in reason_state
    assert "5-10 minutes" in reason_state
    assert "short purge" in reason_state
    assert "rec == 'open'" in reason_state


def test_window_ventilation_brief_purge_keeps_hvac_and_rain_suppression():
    package = load_package()
    recommendation = template_sensor_by_name(
        package, "Window Ventilation Recommendation"
    )
    state_template = recommendation["state"]

    assert "elif raining or hvac_running" in state_template
    assert state_template.index("elif raining or hvac_running") < state_template.index(
        "elif brief_purge"
    )


def test_window_ventilation_brief_purge_is_not_winter_purge_classification():
    package = load_package()
    context = template_sensor_by_name(package, "Window Ventilation Decision Context")

    temperature_template = context["attributes"][
        "brief_purge_outdoor_temperature_ok"
    ]
    brief_purge_template = context["attributes"]["brief_purge"]

    assert "input_number.window_ventilation_winter_threshold" in temperature_template
    assert "outdoor >= winter_threshold" in temperature_template
    assert "input_number.window_ventilation_winter_threshold" in brief_purge_template
    assert (
        "{% set winter_mode = outdoor is not none and outdoor < winter_threshold %}"
        in brief_purge_template
    )
    assert "not winter_mode" in brief_purge_template


def test_window_ventilation_notifications_are_advisory_and_gated():
    package = load_package()

    open_advisory = automation_by_id(package, "window_ventilation_open_advisory")
    close_advisory = automation_by_id(package, "window_ventilation_close_advisory")
    neutral_clear = automation_by_id(
        package, "window_ventilation_neutral_clear_notification"
    )

    assert {trigger["to"] for trigger in open_advisory["trigger"]} == {
        "open",
        "open_briefly",
    }
    assert all(trigger["for"] == {"minutes": 15} for trigger in open_advisory["trigger"])
    assert {trigger["from"] for trigger in close_advisory["trigger"]} == {
        "open",
        "open_briefly",
    }
    assert all(trigger["to"] == "close" for trigger in close_advisory["trigger"])
    assert all(trigger["for"] == {"minutes": 7} for trigger in close_advisory["trigger"])

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

    open_text = str(open_advisory)
    assert "open_briefly" in open_text
    assert "Brief Purge" in open_text
    assert "5-10 minute" in open_text


def test_window_ventilation_close_advisory_only_fires_after_open_advisory():
    package = load_package()
    close_advisory = automation_by_id(package, "window_ventilation_close_advisory")

    assert {trigger["from"] for trigger in close_advisory["trigger"]} == {
        "open",
        "open_briefly",
    }
    assert all(trigger["to"] == "close" for trigger in close_advisory["trigger"])


def test_window_ventilation_neutral_to_close_does_not_match_close_advisory():
    package = load_package()
    close_advisory = automation_by_id(package, "window_ventilation_close_advisory")

    assert not any(
        trigger.get("from") in (None, "neutral") and trigger["to"] == "close"
        for trigger in close_advisory["trigger"]
    )
