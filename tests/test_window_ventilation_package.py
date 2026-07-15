import ast
from pathlib import Path

from jinja2 import Environment
import yaml


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "window_ventilation.yaml"
PROTECTED_CONTACTS_PACKAGE = ROOT / "packages" / "protected_contacts.yaml"


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def canonical_protected_contacts():
    package = yaml.safe_load(PROTECTED_CONTACTS_PACKAGE.read_text())
    inventory = next(
        sensor
        for block in package["template"]
        for sensor in block.get("sensor", [])
        if sensor["name"] == "Protected Contact Inventory"
    )
    rendered = Environment().from_string(inventory["attributes"]["contacts"]).render()
    return ast.literal_eval(rendered)


CANONICAL_PROTECTED_CONTACTS = canonical_protected_contacts()


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


def template_binary_sensor_by_name(package, name):
    for block in package["template"]:
        for sensor in block.get("binary_sensor", []):
            if sensor["name"] == name:
                return sensor
    raise AssertionError(f"template binary sensor {name!r} not found")


def automation_by_id(package, automation_id):
    for automation in package["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"automation {automation_id!r} not found")


def ha_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "on", "yes", "1", "enable", "enabled"}:
        return True
    if normalized in {"false", "off", "no", "0", "disable", "disabled"}:
        return False
    return default


def normalize_rendered(value):
    stripped = str(value).strip()
    lowered = stripped.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return stripped


class StatesProxy:
    def __init__(self, state_map):
        self._state_map = state_map

    def __call__(self, entity_id):
        return self._state_map.get(entity_id, "unknown")


def render_ha_template(template, *, state_map, attr_map=None):
    if not isinstance(template, str):
        return template
    attr_map = attr_map or {}
    env = Environment(trim_blocks=True, lstrip_blocks=True)
    env.filters["bool"] = ha_bool
    env.globals.update(
        states=StatesProxy(state_map),
        state_attr=lambda entity_id, attr: attr_map.get((entity_id, attr)),
        is_state=lambda entity_id, state: state_map.get(entity_id) == state,
    )
    return env.from_string(template).render().strip()


DEFAULT_VENTILATION_STATES = {
    "sensor.dining_room_thermostat_temperature": "72",
    "sensor.thermostat_humidity": "45",
    "sensor.window_ventilation_indoor_dew_point": "52",
    "sensor.weather_outdoor_temperature": "66",
    "sensor.weather_outdoor_dew_point": "50",
    "sensor.precipitation_forecast_next_hour": "0",
    "sensor.condition_forecast_next_hour": "sunny",
    "sensor.thermostat_carbon_dioxide": "700",
    "sensor.window_ventilation_co2_baseline": "650",
    "sensor.thermostat_vocs": "150",
    "sensor.window_ventilation_voc_baseline": "140",
    "sensor.air_quality_composite_status": "good",
    "sensor.air_quality_trend": "stable",
    "input_number.window_ventilation_cooler_delta": "3",
    "input_number.window_ventilation_max_outdoor_dew_point": "60",
    "input_number.window_ventilation_brief_purge_max_outdoor_temperature_delta": "5",
    "input_number.window_ventilation_brief_purge_max_outdoor_dew_point": "70",
    "input_number.window_ventilation_winter_threshold": "55",
    "input_number.window_ventilation_high_indoor_humidity": "58",
    "binary_sensor.kitchen_kitchen_porch_window": "off",
    "binary_sensor.kitchen_kitchen_sink_window": "off",
    "binary_sensor.living_room_living_room_window": "off",
    "binary_sensor.master_bedroom_brian_s_window": "off",
    "binary_sensor.master_bedroom_hester_s_window": "off",
    "binary_sensor.porter_s_room_porter_s_window": "off",
    "binary_sensor.towner_s_room_towner_s_window": "off",
    "binary_sensor.office_window": "off",
}


DEFAULT_VENTILATION_ATTRS = {
    ("climate.dining_room_thermostat", "hvac_action"): "idle",
    ("climate.dining_room_thermostat", "current_temperature"): 72,
    ("climate.dining_room_thermostat", "current_humidity"): 45,
    ("sensor.protected_contact_inventory", "contacts"): CANONICAL_PROTECTED_CONTACTS,
}


def evaluate_window_ventilation(state_overrides=None, attr_overrides=None):
    package = load_package()
    context = template_sensor_by_name(package, "Window Ventilation Decision Context")
    recommendation = template_sensor_by_name(
        package, "Window Ventilation Recommendation"
    )
    reason = template_sensor_by_name(package, "Window Ventilation Reason")

    state_map = DEFAULT_VENTILATION_STATES | (state_overrides or {})
    attr_map = DEFAULT_VENTILATION_ATTRS | (attr_overrides or {})
    context_state = render_ha_template(
        context["state"], state_map=state_map, attr_map=attr_map
    )
    state_map["sensor.window_ventilation_decision_context"] = context_state

    context_attrs = {}
    for name, template in context["attributes"].items():
        context_attrs[name] = normalize_rendered(
            render_ha_template(template, state_map=state_map, attr_map=attr_map)
        )
    for name, value in context_attrs.items():
        attr_map[("sensor.window_ventilation_decision_context", name)] = value

    recommendation_state = render_ha_template(
        recommendation["state"], state_map=state_map, attr_map=attr_map
    )
    state_map["sensor.window_ventilation_recommendation"] = recommendation_state
    recommendation_attrs = {}
    for name, template in recommendation["attributes"].items():
        if isinstance(template, str) and ("{{" in template or "{%" in template):
            recommendation_attrs[name] = normalize_rendered(
                render_ha_template(template, state_map=state_map, attr_map=attr_map)
            )
        else:
            recommendation_attrs[name] = template
    for name, value in recommendation_attrs.items():
        attr_map[("sensor.window_ventilation_recommendation", name)] = value

    reason_state = render_ha_template(reason["state"], state_map=state_map, attr_map=attr_map)
    return {
        "context_state": context_state,
        "context_attrs": context_attrs,
        "recommendation_state": recommendation_state,
        "recommendation_attrs": recommendation_attrs,
        "reason_state": reason_state,
    }


def test_window_ventilation_required_entities_are_defined():
    package = load_package()

    assert "Window Ventilation Indoor Dew Point" in sensor_names(package)
    assert "Window Ventilation Decision Context" in sensor_names(package)
    assert "Window Ventilation Open Window Summary" in sensor_names(package)
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
    assert "Window HVAC Open Warning" in binary_names


def test_window_hvac_open_warning_only_matches_open_windows_while_hvac_runs():
    package = load_package()
    guard = template_binary_sensor_by_name(package, "Window HVAC Open Warning")

    state_map = DEFAULT_VENTILATION_STATES | {
        "binary_sensor.kitchen_kitchen_porch_window": "on",
        "binary_sensor.office_window": "on",
    }
    heating_attrs = DEFAULT_VENTILATION_ATTRS | {
        ("climate.dining_room_thermostat", "hvac_action"): "heating"
    }
    cooling_attrs = DEFAULT_VENTILATION_ATTRS | {
        ("climate.dining_room_thermostat", "hvac_action"): "cooling"
    }

    assert render_ha_template(guard["state"], state_map=state_map, attr_map=heating_attrs) == "True"
    assert render_ha_template(guard["state"], state_map=state_map, attr_map=cooling_attrs) == "True"
    assert (
        render_ha_template(
            guard["state"], state_map=state_map, attr_map=DEFAULT_VENTILATION_ATTRS
        )
        == "False"
    )
    assert (
        render_ha_template(
            guard["state"],
            state_map=DEFAULT_VENTILATION_STATES,
            attr_map=heating_attrs,
        )
        == "False"
    )
    assert (
        render_ha_template(
            guard["attributes"]["open_windows"],
            state_map=state_map,
            attr_map=heating_attrs,
        )
        == "Kitchen Porch Window, Office Window"
    )
    assert (
        render_ha_template(
            guard["attributes"]["open_window_count"],
            state_map=state_map,
            attr_map=heating_attrs,
        )
        == "2"
    )


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

    summary = template_sensor_by_name(package, "Window Ventilation Open Window Summary")
    assert summary["unique_id"] == "window_ventilation_open_window_summary"
    assert "sensor.window_ventilation_decision_context" in str(summary)

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

    for contact_attribute in ("open_window_count", "open_window_names"):
        assert contact_attribute in context["attributes"]
        assert contact_attribute in recommendation["attributes"]

    assert "sensor.protected_contact_inventory" in context_text
    assert "contact.category == 'window'" in context_text
    assert "contact.name" in context_text
    assert "friendly_name" not in context_text
    assert "binary_sensor.kitchen_kitchen_porch_window" not in PACKAGE.read_text()
    assert "binary_sensor.office_window" not in PACKAGE.read_text()
    assert "open_window_count > 0" in reason_text
    assert "Close {{ open_window_names }}" in reason_text

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


def test_window_ventilation_favorable_conditions_still_recommend_open():
    result = evaluate_window_ventilation()

    assert result["context_state"] == "ready"
    assert result["context_attrs"]["mild_open"] is True
    assert result["context_attrs"]["brief_purge"] is False
    assert result["recommendation_state"] == "open"
    assert result["recommendation_attrs"]["mode"] == "comfort"
    assert "Recommendation: consider opening windows." in result["reason_state"]
    assert "short purge" not in result["reason_state"]
    assert "Briefly open" not in result["reason_state"]


def test_window_ventilation_severe_stale_air_can_recommend_bounded_brief_purge():
    result = evaluate_window_ventilation(
        {
            "sensor.weather_outdoor_temperature": "75",
            "sensor.weather_outdoor_dew_point": "65",
            "sensor.thermostat_carbon_dioxide": "1600",
            "sensor.window_ventilation_co2_baseline": "1000",
            "sensor.air_quality_composite_status": "poor",
            "sensor.air_quality_trend": "worsening",
        }
    )

    assert result["context_state"] == "ready"
    assert result["context_attrs"]["outdoor_cooler"] is False
    assert result["context_attrs"]["outdoor_drier"] is False
    assert result["context_attrs"]["severe_stale_air_reason"] is True
    assert result["context_attrs"]["brief_purge_outdoor_temperature_ok"] is True
    assert result["context_attrs"]["brief_purge_outdoor_dew_point_ok"] is True
    assert result["context_attrs"]["brief_purge"] is True
    assert result["recommendation_state"] == "open_briefly"
    assert result["recommendation_state"] != "open"
    assert result["recommendation_attrs"]["mode"] == "brief_purge"
    assert "Recommendation: consider briefly opening windows for a short purge" in result["reason_state"]
    assert "bounded compromise limits" in result["reason_state"]


def test_window_ventilation_brief_purge_requires_bounded_outdoor_limits():
    too_warm = evaluate_window_ventilation(
        {
            "sensor.weather_outdoor_temperature": "78",
            "sensor.weather_outdoor_dew_point": "65",
            "sensor.thermostat_carbon_dioxide": "1600",
            "sensor.window_ventilation_co2_baseline": "1000",
            "sensor.air_quality_composite_status": "poor",
            "sensor.air_quality_trend": "worsening",
        }
    )
    too_humid = evaluate_window_ventilation(
        {
            "sensor.weather_outdoor_temperature": "75",
            "sensor.weather_outdoor_dew_point": "71",
            "sensor.thermostat_carbon_dioxide": "1600",
            "sensor.window_ventilation_co2_baseline": "1000",
            "sensor.air_quality_composite_status": "poor",
            "sensor.air_quality_trend": "worsening",
        }
    )

    assert too_warm["context_attrs"]["severe_stale_air_reason"] is True
    assert too_warm["context_attrs"]["brief_purge_outdoor_temperature_ok"] is False
    assert too_warm["context_attrs"]["brief_purge_outdoor_dew_point_ok"] is True
    assert too_warm["context_attrs"]["brief_purge"] is False
    assert too_warm["recommendation_state"] != "open_briefly"
    assert too_warm["recommendation_state"] != "open"

    assert too_humid["context_attrs"]["severe_stale_air_reason"] is True
    assert too_humid["context_attrs"]["brief_purge_outdoor_temperature_ok"] is True
    assert too_humid["context_attrs"]["brief_purge_outdoor_dew_point_ok"] is False
    assert too_humid["context_attrs"]["brief_purge"] is False
    assert too_humid["recommendation_state"] != "open_briefly"
    assert too_humid["recommendation_state"] != "open"


def test_window_ventilation_rain_and_hvac_suppress_brief_purge_recommendations():
    severe_stale_air = {
        "sensor.weather_outdoor_temperature": "75",
        "sensor.weather_outdoor_dew_point": "65",
        "sensor.thermostat_carbon_dioxide": "1600",
        "sensor.window_ventilation_co2_baseline": "1000",
        "sensor.air_quality_composite_status": "poor",
        "sensor.air_quality_trend": "worsening",
    }
    rainy = evaluate_window_ventilation(
        severe_stale_air | {"sensor.precipitation_forecast_next_hour": "30"}
    )
    hvac = evaluate_window_ventilation(
        severe_stale_air,
        {("climate.dining_room_thermostat", "hvac_action"): "cooling"},
    )

    assert rainy["context_attrs"]["severe_stale_air_reason"] is True
    assert rainy["context_attrs"]["brief_purge"] is False
    assert rainy["recommendation_state"] == "close"
    assert "rain or mixed precipitation" in rainy["reason_state"]
    assert "short purge" not in rainy["reason_state"]

    assert hvac["context_attrs"]["severe_stale_air_reason"] is True
    assert hvac["context_attrs"]["brief_purge"] is False
    assert hvac["recommendation_state"] == "close"
    assert "HVAC is currently cooling" in hvac["reason_state"]
    assert "short purge" not in hvac["reason_state"]


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


def test_window_ventilation_contact_context_names_open_windows_without_false_opens():
    open_window = "binary_sensor.kitchen_kitchen_porch_window"
    friendly_name = "Kitchen Porch Window"
    all_contacts_closed = {
        contact["entity_id"]: "off" for contact in CANONICAL_PROTECTED_CONTACTS
    }

    all_closed = evaluate_window_ventilation(
        all_contacts_closed | {"sensor.precipitation_forecast_next_hour": "30"}
    )
    one_open = evaluate_window_ventilation(
        all_contacts_closed | {
            "sensor.precipitation_forecast_next_hour": "30",
            open_window: "on",
        }
    )

    assert all_closed["context_attrs"]["open_window_count"] == "0"
    assert all_closed["context_attrs"]["open_window_names"] == ""
    assert "Keep windows closed:" in all_closed["reason_state"]
    assert friendly_name not in all_closed["reason_state"]

    assert one_open["context_attrs"]["open_window_count"] == "1"
    assert one_open["context_attrs"]["open_window_names"] == friendly_name
    assert one_open["recommendation_attrs"]["open_window_count"] == "1"
    assert one_open["recommendation_attrs"]["open_window_names"] == friendly_name
    assert f"Close {friendly_name}:" in one_open["reason_state"]


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


def test_window_hvac_open_warning_has_configurable_hold_and_separate_tagged_clear():
    package = load_package()
    warning = automation_by_id(package, "window_hvac_open_warning")
    clear = automation_by_id(package, "window_hvac_open_warning_clear")

    assert package["input_number"]["window_hvac_open_warning_hold_minutes"] == {
        "name": "Window HVAC Open Warning Hold Time",
        "min": 1,
        "max": 120,
        "step": 1,
        "unit_of_measurement": "min",
        "icon": "mdi:timer-outline",
        "initial": 10,
    }
    assert warning["trigger"] == [
        {
            "platform": "state",
            "entity_id": "binary_sensor.window_hvac_open_warning",
            "to": "on",
            "for": {
                "minutes": "{{ states('input_number.window_hvac_open_warning_hold_minutes') | int(10) }}"
            },
        }
    ]
    assert warning["action"][-1]["service"] == "notify.all_mobile_devices"
    warning_text = str(warning)
    assert "Windows Open While Heating" in warning_text
    assert "Windows Open While Cooling" in warning_text
    assert "open_windows" in warning_text
    assert "window-hvac-open-warning" in warning_text
    assert "climate.set_" not in warning_text

    assert clear["trigger"] == [
        {
            "platform": "state",
            "entity_id": "binary_sensor.window_hvac_open_warning",
            "from": "on",
            "to": "off",
        }
    ]
    assert clear["action"] == [
        {
            "service": "notify.all_mobile_devices",
            "data": {
                "message": "clear_notification",
                "data": {"tag": "window-hvac-open-warning"},
            },
        }
    ]
    assert "two-minute" not in str(clear)
    assert "security" not in str(clear)
