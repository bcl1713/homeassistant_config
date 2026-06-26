from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WEATHER = ROOT / "packages" / "weather.yaml"


def load_weather():
    return yaml.safe_load(WEATHER.read_text())


def weather_refresh_action():
    for automation in load_weather()["automation"]:
        if automation["id"] == "weather_data_refresh":
            return automation["action"]
    raise AssertionError("weather_data_refresh automation not found")


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
    assert "forecast[:2]" in sensor["state"]
    assert "ns.high" in sensor["state"]


def test_precipitation_next_hour_uses_nws_probability_semantics():
    sensor = template_sensor("Precipitation forecast next hour")

    assert sensor["unit_of_measurement"] == "%"
    assert "precipitation_probability" in sensor["state"]
