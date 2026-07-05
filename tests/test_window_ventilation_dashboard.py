from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SHARED_INFRASTRUCTURE = ROOT / "packages" / "shared_infrastructure.yaml"
DASHBOARD = ROOT / "dashboards" / "window_ventilation.yaml"


def load_dashboard():
    return yaml.safe_load(DASHBOARD.read_text())


def load_shared_infrastructure():
    return yaml.safe_load(SHARED_INFRASTRUCTURE.read_text())


def entity_refs(cards):
    refs = []
    for card in cards:
        if "entity" in card:
            refs.append(card["entity"])
        if "card" in card:
            refs.extend(entity_refs([card["card"]]))
        for row in card.get("entities", []):
            if isinstance(row, str):
                refs.append(row)
            elif isinstance(row, dict) and "entity" in row:
                refs.append(row["entity"])
    return refs


def test_window_ventilation_dashboard_is_yaml_managed_and_hidden():
    dashboard_config = load_shared_infrastructure()["lovelace"]["dashboards"][
        "window-ventilation"
    ]

    assert dashboard_config["mode"] == "yaml"
    assert dashboard_config["filename"] == "dashboards/window_ventilation.yaml"
    assert dashboard_config["show_in_sidebar"] is False


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
        "binary_sensor.window_ventilation_brief_purge",
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
        "input_number.window_ventilation_brief_purge_max_outdoor_temperature_delta",
        "input_number.window_ventilation_brief_purge_max_outdoor_dew_point",
        "input_number.window_ventilation_winter_threshold",
        "input_number.window_ventilation_high_indoor_humidity",
    }
    assert required_entities <= refs
    assert "state_attr('sensor.window_ventilation_recommendation', 'mode')" in markdown
    assert "advisory-only" in markdown
    assert "Brief stale-air purge" in markdown
    assert "This is not ordinary comfort ventilation" in markdown
    assert "Open Briefly" not in markdown

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


def test_window_ventilation_dashboard_separates_brief_purge_from_comfort_open():
    dashboard = load_dashboard()
    cards = dashboard["views"][0]["cards"]
    markdown = "\n".join(
        card.get("content", "") for card in cards if card.get("type") == "markdown"
    )

    status_card = next(card for card in cards if card.get("title") == "Advisor status")
    status_names = {
        row["entity"]: row["name"]
        for row in status_card["entities"]
        if isinstance(row, dict) and "entity" in row and "name" in row
    }
    brief_purge_card = next(
        card
        for card in cards
        if card.get("type") == "conditional"
        and card.get("card", {}).get("title") == "Brief purge guardrails"
    )

    assert "'open': 'Open for comfort ventilation'" in markdown
    assert "'open_briefly': 'Brief stale-air purge'" in markdown
    assert "'brief_purge': 'Bounded stale-air purge'" in markdown
    assert "not ordinary comfort ventilation" in markdown
    assert status_names["binary_sensor.window_ventilation_favorable"] == (
        "Comfort ventilation favorable"
    )
    assert status_names["binary_sensor.window_ventilation_brief_purge"] == (
        "Bounded stale-air purge active"
    )
    assert brief_purge_card["conditions"] == [
        {
            "entity": "sensor.window_ventilation_recommendation",
            "state": "open_briefly",
        }
    ]
    assert "not a comfort ventilation recommendation" in brief_purge_card["card"][
        "content"
    ]
    assert "5-10 minutes" in brief_purge_card["card"]["content"]
