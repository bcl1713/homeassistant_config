import ast
from pathlib import Path

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
WEATHER = ROOT / "packages" / "weather.yaml"
PROTECTED_CONTACTS = ROOT / "packages" / "protected_contacts.yaml"


def load_weather():
    return yaml.safe_load(WEATHER.read_text())


def canonical_window_contacts():
    package = yaml.safe_load(PROTECTED_CONTACTS.read_text())
    inventory = next(
        sensor
        for block in package["template"]
        for sensor in block.get("sensor", [])
        if sensor["name"] == "Protected Contact Inventory"
    )
    contacts = ast.literal_eval(
        Environment().from_string(inventory["attributes"]["contacts"]).render()
    )
    return [contact for contact in contacts if contact["category"] == "window"]


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


def render_template(template, state_map, attributes=None, **variables):
    attributes = attributes or {}
    environment = Environment(trim_blocks=True, lstrip_blocks=True)
    environment.globals.update(
        is_state=lambda entity_id, state: state_map.get(entity_id) == state,
        states=lambda entity_id: state_map.get(entity_id, "unknown"),
        state_attr=lambda entity_id, attribute: attributes.get((entity_id, attribute)),
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


def test_rain_alert_uses_canonical_window_inventory_for_dynamic_names_and_static_trigger_parity():
    rain_alert = automation_by_id("notification_rain_forecast")
    contacts = canonical_window_contacts()
    window_contact_ids = [contact["entity_id"] for contact in contacts]
    open_window_names = rain_alert["variables"]["open_window_names"]

    assert "rain_window_contacts" not in rain_alert["variables"]
    assert "sensor.protected_contact_inventory" in open_window_names
    assert "contact.category" in open_window_names
    assert all(name not in WEATHER.read_text() for name in (contact["name"] for contact in contacts))

    closed_states = {entity_id: "off" for entity_id in window_contact_ids}
    open_states = {
        **closed_states,
        "binary_sensor.kitchen_kitchen_porch_window": "on",
        "binary_sensor.office_window": "on",
    }
    attributes = {("sensor.protected_contact_inventory", "contacts"): contacts}

    assert render_template(open_window_names, closed_states, attributes) == ""
    assert render_template(
        open_window_names, open_states, attributes
    ) == "Kitchen Porch Window, Office Window"
    renamed_contacts = [
        {
            **contact,
            "name": "Study Window",
        }
        if contact["entity_id"] == "binary_sensor.office_window"
        else contact
        for contact in contacts
    ] + [
        {
            "entity_id": "binary_sensor.example_door",
            "name": "Example Door",
            "category": "security_boundary_door",
        }
    ]
    assert render_template(
        open_window_names,
        {**open_states, "binary_sensor.example_door": "on"},
        {("sensor.protected_contact_inventory", "contacts"): renamed_contacts},
    ) == "Kitchen Porch Window, Study Window"
    assert {
        tuple(trigger["entity_id"])
        for trigger in rain_alert["trigger"]
        if trigger.get("id") == "window_open_trigger"
    } == {tuple(window_contact_ids)}
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
    contacts = canonical_window_contacts()
    window_contact_ids = [contact["entity_id"] for contact in contacts]
    has_open_windows = clear_alert["variables"]["has_open_windows"]
    closed_states = {entity_id: "off" for entity_id in window_contact_ids}
    one_open_state = {
        **closed_states,
        "binary_sensor.office_window": "on",
    }
    attributes = {("sensor.protected_contact_inventory", "contacts"): contacts}

    assert "automation.notification_rain_forecast" in str(rain_alert["condition"])
    assert "sensor.protected_contact_inventory" in has_open_windows
    assert "contact.category" in has_open_windows
    assert render_template(has_open_windows, closed_states, attributes) == ""
    assert render_template(
        has_open_windows,
        {**closed_states, "binary_sensor.example_door": "on"},
        {
            (
                "sensor.protected_contact_inventory",
                "contacts",
            ): contacts
            + [
                {
                    "entity_id": "binary_sensor.example_door",
                    "name": "Example Door",
                    "category": "security_boundary_door",
                }
            ]
        },
    ) == ""
    assert render_template(has_open_windows, one_open_state, attributes) == "true"
    assert clear_alert["condition"] == [
        {"condition": "template", "value_template": "{{ not has_open_windows }}"}
    ]
    assert {
        tuple(trigger["entity_id"])
        for trigger in clear_alert["trigger"]
        if trigger.get("platform") == "state"
    } == {tuple(window_contact_ids)}
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
