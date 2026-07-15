from pathlib import Path

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
WEATHER = ROOT / "packages" / "weather.yaml"


def load_weather():
    return yaml.safe_load(WEATHER.read_text())


def weather_refresh_action():
    for automation in load_weather()["automation"]:
        if automation["id"] == "weather_data_refresh":
            return automation["action"]
    raise AssertionError("weather_data_refresh automation not found")


def automation_by_id(automation_id):
    for automation in load_weather()["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"automation {automation_id!r} not found")


def render_template(template, state_map, **variables):
    environment = Environment(trim_blocks=True, lstrip_blocks=True)
    environment.globals.update(
        is_state=lambda entity_id, state: state_map.get(entity_id) == state,
        states=lambda entity_id: state_map.get(entity_id, "unknown"),
    )
    return environment.from_string(template).render(**variables).strip()


def mqtt_payload_for_topic(topic):
    for action in weather_refresh_action():
        if action.get("service") == "mqtt.publish" and action["data"]["topic"] == topic:
            return action["data"]["payload"]
    raise AssertionError(f"mqtt publish topic {topic!r} not found")


def template_sensor(name):
    for block in load_weather()["template"]:
        for sensor in block.get("sensor", []):
            if sensor["name"] == name:
                return sensor
    raise AssertionError(f"template sensor {name!r} not found")


def test_weather_forecast_cache_publishes_normalized_top_level_payloads():
    hourly_payload = mqtt_payload_for_topic("home/weather/hourly_forecast")
    daily_payload = mqtt_payload_for_topic("home/weather/daily_forecast")

    for payload, forecast_type in (
        (hourly_payload, "hourly"),
        (daily_payload, "twice_daily"),
    ):
        assert "source = 'weather.nws_home_kmle'" in payload
        assert "payload =" in payload
        assert "payload.get('forecast', [])" in payload
        assert "'forecast': forecast" in payload
        assert "'forecast_count': forecast | count" in payload
        assert f"'forecast_type': '{forecast_type}'" in payload


def test_weather_refresh_uses_nws_hourly_and_twice_daily_forecasts():
    forecast_calls = [
        action for action in weather_refresh_action()
        if action.get("service") == "weather.get_forecasts"
    ]

    assert [call["data"]["type"] for call in forecast_calls] == ["hourly", "twice_daily"]
    assert all(call["target"]["entity_id"] == "weather.nws_home_kmle" for call in forecast_calls)


def test_weather_derivative_sensors_accept_normalized_and_legacy_cache_shapes():
    weather_text = WEATHER.read_text()

    assert "state_attr('sensor.weather_hourly_forecast', 'forecast')" in weather_text
    assert "state_attr('sensor.weather_daily_forecast', 'forecast')" in weather_text
    assert "state_attr('sensor.weather_hourly_forecast', source_entity)" in weather_text
    assert "state_attr('sensor.weather_daily_forecast', source_entity)" in weather_text


def mqtt_sensor(name):
    for sensor in load_weather()["mqtt"]["sensor"]:
        if sensor["name"] == name:
            return sensor
    raise AssertionError(f"mqtt sensor {name!r} not found")


def test_weather_package_exposes_current_condition_seam_sensors():
    expected = {
        "Weather Outdoor Temperature": (
            "weather_outdoor_temperature",
            "sensor.nws_41_17166991853366_96_04711058392532_kmle_temperature",
        ),
        "Weather Outdoor Humidity": (
            "weather_outdoor_humidity",
            "sensor.nws_41_17166991853366_96_04711058392532_kmle_relative_humidity",
        ),
        "Weather Outdoor Dew Point": (
            "weather_outdoor_dew_point",
            "sensor.nws_41_17166991853366_96_04711058392532_kmle_dew_point",
        ),
    }

    for name, (unique_id, source_entity) in expected.items():
        sensor = template_sensor(name)
        assert sensor["unique_id"] == unique_id
        assert source_entity in sensor["availability"]
        assert source_entity in sensor["state"]


def test_forecast_mqtt_sensors_do_not_require_literal_open_brace_availability_payload():
    for name, topic in (
        ("Weather Hourly Forecast", "home/weather/hourly_forecast"),
        ("Weather Daily Forecast", "home/weather/daily_forecast"),
    ):
        sensor = mqtt_sensor(name)
        assert sensor["state_topic"] == topic
        assert sensor["json_attributes_topic"] == topic
        assert sensor.get("availability_topic") != topic
        assert sensor.get("payload_available") != "{"


def test_temperature_forecast_high_today_uses_deployment_fahrenheit_units():
    sensor = template_sensor("Temperature forecast high today")

    assert sensor["unit_of_measurement"] == "°F"
    assert "availability" in sensor
    assert "forecast[:2]" in sensor["state"]
    assert "ns.high" in sensor["state"]
    assert "weather_outdoor_temperature" not in sensor["state"]
    assert sensor["attributes"]["forecast_source"] == "sensor.weather_daily_forecast"
    assert "Fahrenheit" in sensor["attributes"]["forecast_unit_assumption"]
    assert "first two twice-daily periods" in sensor["attributes"]["decision_scope"]


def test_precipitation_next_hour_uses_nws_probability_semantics():
    sensor = template_sensor("Precipitation forecast next hour")

    assert sensor["unit_of_measurement"] == "%"
    assert "precipitation_probability" in sensor["state"]


def test_rain_alert_requires_open_monitored_windows_and_names_them():
    rain_alert = automation_by_id("notification_rain_forecast")
    contacts = rain_alert["variables"]["rain_window_contacts"]
    open_window_names = rain_alert["variables"]["open_window_names"]

    assert contacts == {
        "binary_sensor.kitchen_kitchen_porch_window": "Kitchen Porch Window",
        "binary_sensor.kitchen_kitchen_sink_window": "Kitchen Sink Window",
        "binary_sensor.living_room_living_room_window": "Living Room Window",
        "binary_sensor.master_bedroom_brian_s_window": "Brian's Window",
        "binary_sensor.master_bedroom_hester_s_window": "Hester's Window",
        "binary_sensor.porter_s_room_porter_s_window": "Porter's Window",
        "binary_sensor.towner_s_room_towner_s_window": "Towner's Window",
        "binary_sensor.office_window": "Office Window",
    }
    closed_states = {entity_id: "off" for entity_id in contacts}
    open_states = {
        **closed_states,
        "binary_sensor.kitchen_kitchen_porch_window": "on",
        "binary_sensor.office_window": "on",
    }

    assert render_template(
        open_window_names, closed_states, rain_window_contacts=contacts
    ) == ""
    assert render_template(
        open_window_names, open_states, rain_window_contacts=contacts
    ) == "Kitchen Porch Window, Office Window"
    assert {
        tuple(trigger["entity_id"])
        for trigger in rain_alert["trigger"]
        if trigger.get("id") == "window_open_trigger"
    } == {tuple(contacts)}
    assert any(
        condition.get("value_template") == "{{ open_window_names | trim != '' }}"
        for condition in rain_alert["condition"]
    )
    forecast_basis = rain_alert["variables"]["forecast_basis"]
    assert render_template(
        forecast_basis,
        {
            "sensor.precipitation_forecast_next_hour": "45",
            "sensor.condition_forecast_next_hour": "sunny",
            "weather.nws_home_kmle": "sunny",
        },
    ) == "45.0% chance of precipitation in the next hour"
    rain_criteria = next(
        condition["value_template"]
        for condition in rain_alert["condition"]
        if "weather_condition in" in condition.get("value_template", "")
    )
    assert render_template(
        rain_criteria,
        {
            **open_states,
            "sensor.precipitation_forecast_next_hour": "0",
            "sensor.condition_forecast_next_hour": "sunny",
            "weather.nws_home_kmle": "sunny",
        },
    ) == "False"
    assert render_template(
        rain_criteria,
        {
            **open_states,
            "sensor.precipitation_forecast_next_hour": "45",
            "sensor.condition_forecast_next_hour": "sunny",
            "weather.nws_home_kmle": "sunny",
        },
    ) == "True"


def test_rain_alert_reuses_its_throttle_and_clears_only_after_all_windows_close():
    rain_alert = automation_by_id("notification_rain_forecast")
    clear_alert = automation_by_id("notification_rain_forecast_open_windows_clear")
    contacts = rain_alert["variables"]["rain_window_contacts"]
    has_open_windows = clear_alert["variables"]["has_open_windows"]
    closed_states = {entity_id: "off" for entity_id in contacts}
    one_open_state = {
        **closed_states,
        "binary_sensor.office_window": "on",
    }

    assert "automation.notification_rain_forecast" in str(rain_alert["condition"])
    assert render_template(
        has_open_windows, closed_states, rain_window_contacts=contacts
    ) == ""
    assert render_template(
        has_open_windows, one_open_state, rain_window_contacts=contacts
    ) == "true"
    assert clear_alert["condition"] == [
        {"condition": "template", "value_template": "{{ not has_open_windows }}"}
    ]
    assert clear_alert["action"] == [
        {
            "action": "notify.mobile_app_brian_phone",
            "data": {
                "message": "clear_notification",
                "data": {"tag": "rain-open-windows"},
            },
        }
    ]
    notification = rain_alert["action"][0]
    assert notification["data"]["data"]["tag"] == "rain-open-windows"
    assert "{{ forecast_basis }}" in notification["data"]["message"]
