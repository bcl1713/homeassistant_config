from pathlib import Path

import yaml

from climate_package_helpers import load_climate_packages


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboards" / "climate_control.yaml"


def load_climate():
    return load_climate_packages()


def load_dashboard():
    return yaml.safe_load(DASHBOARD.read_text())


def template_entities(kind):
    for block in load_climate()["template"]:
        for entity in block.get(kind, []):
            yield entity


def named_template(kind, name):
    for entity in template_entities(kind):
        if entity["name"] == name:
            return entity
    raise AssertionError(f"{kind} template {name!r} not found")


def graph_card(name):
    cards = load_dashboard()["views"][0]["cards"]
    for card in cards:
        if card.get("type") == "custom:mini-graph-card" and card.get("name") == name:
            return card
    raise AssertionError(f"mini graph card {name!r} not found")


def assert_graph_detail_card(name, expected_entities):
    card = graph_card(name)

    assert card["hours_to_show"] == 24
    assert card["show"]["legend"] is True
    assert card["show"]["labels"] is True
    assert card["show"]["points"] is False
    assert entity_ids(card) == expected_entities
    assert "binary_sensor.climate_heating_active" not in expected_entities
    assert "binary_sensor.climate_cooling_active" not in expected_entities
    for entity in card["entities"]:
        assert entity["show_fill"] is False
        assert "y_axis" not in entity


def entity_ids(card):
    return [entity["entity"] for entity in card["entities"]]


def assert_binary_state_map(card):
    assert card["state_map"] == [
        {"value": "off", "label": "Inactive"},
        {"value": "on", "label": "Active"},
    ]


def assert_hvac_activity_entities(card):
    for entity in card["entities"][1:]:
        assert entity["y_axis"] == "secondary"
        assert entity["aggregate_func"] == "max"
        assert entity["show_line"] is False
        assert entity["show_fill"] is True
        assert entity["show_points"] is False
        assert entity["show_state"] is False
        assert entity["smoothing"] is False
        assert entity["color"].startswith("rgba(")


def test_climate_activity_helpers_derive_from_thermostat_hvac_action():
    heating = named_template("binary_sensor", "Climate Heating Active")
    cooling = named_template("binary_sensor", "Climate Cooling Active")

    assert heating["unique_id"] == "climate_heating_active"
    assert cooling["unique_id"] == "climate_cooling_active"
    assert "state_attr('climate.dining_room_thermostat', 'hvac_action') == 'heating'" in heating["state"]
    assert "state_attr('climate.dining_room_thermostat', 'hvac_action') == 'cooling'" in cooling["state"]


def test_average_indoor_temperature_uses_dining_room_and_bedroom():
    sensor = named_template("sensor", "Average Indoor Temperature")

    assert sensor["unique_id"] == "average_indoor_temperature"
    assert sensor["device_class"] == "temperature"
    assert sensor["state_class"] == "measurement"
    assert sensor["unit_of_measurement"] == "°F"
    assert "sensor.dining_room_thermostat_temperature" in sensor["availability"]
    assert "sensor.master_bedroom_sensor_temperature" in sensor["availability"]
    assert "sensor.dining_room_thermostat_temperature" in sensor["state"]
    assert "sensor.master_bedroom_sensor_temperature" in sensor["state"]
    assert "/ 2" in sensor["state"]


def test_temperature_trends_use_average_indoor_with_hvac_activity_correlation():
    card = graph_card("Temperature trends")

    assert "history-graph" not in DASHBOARD.read_text()
    assert card["hours_to_show"] == 24
    assert card["lower_bound_secondary"] == 0
    assert card["upper_bound_secondary"] == 1
    assert_binary_state_map(card)
    assert entity_ids(card) == [
        "sensor.average_indoor_temperature",
        "binary_sensor.climate_heating_active",
        "binary_sensor.climate_cooling_active",
    ]
    assert card["show"]["labels_secondary"] is False
    assert card["entities"][0]["line_width"] == 4
    assert card["entities"][0]["show_fill"] is False
    assert_hvac_activity_entities(card)


def test_room_temperature_detail_graph_keeps_underlying_sensor_readings_without_hvac_overlays():
    assert_graph_detail_card("Room temperatures", [
        "sensor.average_indoor_temperature",
        "sensor.dining_room_thermostat_temperature",
        "sensor.master_bedroom_sensor_temperature",
        "sensor.weather_outdoor_temperature",
    ])


def test_air_quality_trends_use_aqi_with_hvac_activity_correlation():
    card = graph_card("Air quality trends")

    assert card["hours_to_show"] == 24
    assert card["lower_bound_secondary"] == 0
    assert card["upper_bound_secondary"] == 1
    assert_binary_state_map(card)
    assert entity_ids(card) == [
        "sensor.thermostat_air_quality_index",
        "binary_sensor.climate_heating_active",
        "binary_sensor.climate_cooling_active",
    ]
    assert card["show"]["labels_secondary"] is False
    assert card["entities"][0]["line_width"] == 4
    assert card["entities"][0]["show_fill"] is False
    assert_hvac_activity_entities(card)


def test_air_quality_detail_graph_keeps_sensor_readings_without_hvac_overlays():
    assert_graph_detail_card("Air quality details", [
        "sensor.thermostat_air_quality_index",
        "sensor.thermostat_carbon_dioxide",
        "sensor.thermostat_vocs",
    ])
