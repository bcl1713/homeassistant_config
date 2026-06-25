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
        (daily_payload, "daily"),
    ):
        assert "source = 'weather.forecast_home'" in payload
        assert "payload =" in payload
        assert "payload.get('forecast', [])" in payload
        assert "'forecast': forecast" in payload
        assert "'forecast_count': forecast | count" in payload
        assert f"'forecast_type': '{forecast_type}'" in payload


def test_weather_derivative_sensors_accept_normalized_and_legacy_cache_shapes():
    weather_text = WEATHER.read_text()

    assert "state_attr('sensor.weather_hourly_forecast', 'forecast')" in weather_text
    assert "state_attr('sensor.weather_hourly_forecast', 'weather.forecast_home')" in weather_text
    assert "state_attr('sensor.weather_daily_forecast', 'forecast')" in weather_text
    assert "state_attr('sensor.weather_daily_forecast', 'weather.forecast_home')" in weather_text


def test_weather_package_exposes_current_condition_seam_sensors():
    expected = {
        "Weather Outdoor Temperature": "weather_outdoor_temperature",
        "Weather Outdoor Humidity": "weather_outdoor_humidity",
        "Weather Outdoor Dew Point": "weather_outdoor_dew_point",
    }

    for name, unique_id in expected.items():
        sensor = template_sensor(name)
        assert sensor["unique_id"] == unique_id
        assert "weather.forecast_home" in sensor["availability"]
        assert "weather.forecast_home" in sensor["state"]
