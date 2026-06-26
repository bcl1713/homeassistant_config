from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIGURATION = ROOT / "configuration.yaml"
DASHBOARD = ROOT / "dashboards" / "window_ventilation.yaml"


def load_dashboard():
    return yaml.safe_load(DASHBOARD.read_text())


def entity_refs(cards):
    refs = []
    for card in cards:
        if "entity" in card:
            refs.append(card["entity"])
        for row in card.get("entities", []):
            if isinstance(row, str):
                refs.append(row)
            elif isinstance(row, dict) and "entity" in row:
                refs.append(row["entity"])
    return refs


def test_window_ventilation_dashboard_is_yaml_managed_and_hidden():
    config_text = CONFIGURATION.read_text()

    assert "lovelace:" in config_text
    assert "window-ventilation:" in config_text
    assert "mode: yaml" in config_text
    assert "filename: dashboards/window_ventilation.yaml" in config_text
    assert "show_in_sidebar: false" in config_text


def test_window_ventilation_dashboard_surfaces_required_context():
    dashboard = load_dashboard()
    cards = dashboard["views"][0]["cards"]
    refs = set(entity_refs(cards))
    markdown = "\n".join(
        card.get("content", "") for card in cards if card.get("type") == "markdown"
    )

    assert dashboard["title"] == "Ventilation Advisor"
    assert dashboard["views"][0]["path"] == "ventilation-advisor"

    required_entities = {
        "input_boolean.window_ventilation_advisor_enabled",
        "sensor.window_ventilation_recommendation",
        "sensor.window_ventilation_reason",
        "binary_sensor.window_ventilation_favorable",
        "binary_sensor.window_ventilation_unfavorable",
        "sensor.dining_room_thermostat_temperature",
        "sensor.thermostat_humidity",
        "sensor.window_ventilation_indoor_dew_point",
        "sensor.weather_outdoor_temperature",
        "sensor.weather_outdoor_humidity",
        "sensor.weather_outdoor_dew_point",
        "sensor.precipitation_forecast_next_hour",
        "sensor.condition_forecast_next_hour",
        "climate.dining_room_thermostat",
        "sensor.thermostat_carbon_dioxide",
        "sensor.window_ventilation_co2_baseline",
        "sensor.thermostat_vocs",
        "sensor.window_ventilation_voc_baseline",
        "input_number.window_ventilation_cooler_delta",
        "input_number.window_ventilation_max_outdoor_dew_point",
        "input_number.window_ventilation_winter_threshold",
        "input_number.window_ventilation_high_indoor_humidity",
    }
    assert required_entities <= refs
    assert "state_attr('sensor.window_ventilation_recommendation', 'mode')" in markdown
    assert "advisory-only" in markdown

    attribute_rows = [
        row
        for card in cards
        for row in card.get("entities", [])
        if isinstance(row, dict) and row.get("type") == "attribute"
    ]
    assert {row["attribute"] for row in attribute_rows} >= {
        "mode",
        "hvac_action",
        "hvac_mode",
    }

    assert any(
        row.get("entity") == "sensor.precipitation_forecast_next_hour"
        and row.get("name") == "Rain probability next hour"
        for card in cards
        for row in card.get("entities", [])
        if isinstance(row, dict)
    )
    assert not any(
        row.get("entity") == "weather.forecast_home"
        for card in cards
        for row in card.get("entities", [])
        if isinstance(row, dict)
    )
