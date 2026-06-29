from datetime import datetime, timedelta

from jinja2 import Environment

from climate_package_helpers import (
    CLIMATE_PACKAGE_NAMES,
    climate_package_text,
    load_climate_packages,
)


class MockState:
    def __init__(self, state, last_updated):
        self.state = state
        self.last_updated = last_updated


class MockStates:
    def __init__(self, states, updated_at, default_updated_at):
        self._states = states
        self._updated_at = updated_at
        self._default_updated_at = default_updated_at

    def __call__(self, entity_id):
        return self._states.get(entity_id, "unknown")

    def __contains__(self, entity_id):
        return entity_id in self._states

    def __getitem__(self, entity_id):
        return MockState(
            self._states[entity_id],
            self._updated_at.get(entity_id, self._default_updated_at),
        )


def as_timestamp(value, default=None):
    if value is None:
        return default
    if isinstance(value, datetime):
        return value.timestamp()
    return value


def render_ha_template(template, states, updated_at=None, now=None):
    now = now or datetime(2026, 6, 29, 15, 52, 35)
    env = Environment()
    env.globals.update(
        states=MockStates(states, updated_at or {}, now),
        now=lambda: now,
        as_timestamp=as_timestamp,
    )
    return env.from_string(template).render().strip()


def load_climate():
    return load_climate_packages()


def automation(automation_id):
    for item in load_climate()["automation"]:
        if item["id"] == automation_id:
            return item
    raise AssertionError(f"automation {automation_id!r} not found")


def binary_sensor(name):
    for block in load_climate()["template"]:
        for sensor in block.get("binary_sensor", []):
            if sensor["name"] == name:
                return sensor
    raise AssertionError(f"binary sensor {name!r} not found")


def template_block_for_binary_sensor(name):
    for block in load_climate()["template"]:
        for sensor in block.get("binary_sensor", []):
            if sensor["name"] == name:
                return block
    raise AssertionError(f"template block for binary sensor {name!r} not found")


SCHEDULE_SETPOINT_HELPERS = {
    "climate_heat_morning",
    "climate_heat_day",
    "climate_heat_bedtime",
    "climate_heat_sleep",
    "climate_heat_away",
    "climate_cool_morning",
    "climate_cool_day",
    "climate_cool_bedtime",
    "climate_cool_sleep",
    "climate_cool_away",
}


EXPECTED_CLIMATE_PACKAGES = {
    "climate_schedule.yaml",
    "climate_occupancy.yaml",
    "climate_extreme_heat.yaml",
    "climate_diagnostics.yaml",
}


def test_climate_control_is_split_into_responsibility_packages():
    assert EXPECTED_CLIMATE_PACKAGES.issubset(CLIMATE_PACKAGE_NAMES)
    assert "climate_control.yaml" not in CLIMATE_PACKAGE_NAMES

    package_text = climate_package_text()
    assert "Baseline climate schedule helpers" in package_text
    assert "Presence-aware climate behavior" in package_text
    assert "Extreme-heat climate overlay" in package_text
    assert "Dashboard-facing climate diagnostics" in package_text


def test_climate_schedule_setpoint_helpers_restore_last_ui_value():
    config = load_climate()

    for helper in SCHEDULE_SETPOINT_HELPERS:
        assert helper in config["input_number"]
        assert "initial" not in config["input_number"][helper]


def test_extreme_heat_helpers_are_configurable_in_fahrenheit():
    config = load_climate()

    threshold = config["input_number"]["climate_extreme_heat_threshold"]
    offset = config["input_number"]["climate_extreme_heat_precool_offset"]

    assert threshold["unit_of_measurement"] == "°F"
    assert threshold["initial"] == 95
    assert offset["unit_of_measurement"] == "°F"
    assert offset["min"] == 0
    assert offset["max"] == 2
    assert offset["initial"] == 1
    assert config["input_boolean"]["climate_extreme_heat_overlay_enabled"]["initial"] is True
    assert config["input_boolean"]["climate_extreme_heat_precool_active"]["initial"] is False
    assert "initial" not in config["input_boolean"]["climate_pre_arrival_recovery_active"]


def test_extreme_heat_day_uses_weather_owned_high_temperature_helper():
    sensor = binary_sensor("Climate Extreme Heat Day")
    state = sensor["state"]
    availability = sensor["availability"]
    attrs = sensor["attributes"]

    assert "states('sensor.temperature_forecast_high_today')" in availability
    assert "states('sensor.temperature_forecast_high_today')" in state
    assert "input_number.climate_extreme_heat_threshold" in state
    assert "state_attr('sensor.weather_daily_forecast'" not in state
    assert "forecast[:2]" not in state
    assert "period.temperature" not in state
    assert attrs["forecast_source"] == "sensor.temperature_forecast_high_today"
    assert "weather-owned helper" in attrs["forecast_unit_assumption"]


def test_precool_apply_is_bounded_occupied_and_one_shot():
    item = automation("climate_extreme_heat_precool_apply")
    text = climate_package_text()

    assert {trigger.get("id") for trigger in item["trigger"]} == {
        "overlay_window_start",
        "hot_day_detected",
        "guest_mode_enabled",
    }
    assert any(trigger.get("at") == "13:00:00" for trigger in item["trigger"])
    assert "before: \"18:00:00\"" in text
    assert "binary_sensor.climate_extreme_heat_day" in text
    assert "input_boolean.climate_extreme_heat_precool_active" in text
    assert "state: \"off\"" in text
    assert "zone.home" in text
    assert "input_boolean.mode_guest" in text
    assert "day - offset" in text
    assert "input_boolean.turn_on" in text
    assert "packages/climate_extreme_heat.yaml" in text


def test_precool_apply_rearms_for_guest_mode_without_return_home_race():
    item = automation("climate_extreme_heat_precool_apply")

    guest_enabled = next(
        trigger for trigger in item["trigger"] if trigger.get("id") == "guest_mode_enabled"
    )

    assert "return_home" not in {trigger.get("id") for trigger in item["trigger"]}
    assert guest_enabled == {
        "platform": "state",
        "entity_id": "input_boolean.mode_guest",
        "to": "on",
        "id": "guest_mode_enabled",
    }
    assert any(
        condition.get("entity_id") == "input_boolean.climate_extreme_heat_precool_active"
        and condition.get("state") == "off"
        for condition in item["condition"]
    )


def test_return_home_deactivate_applies_extreme_heat_overlay_before_day_restore():
    apply = automation("climate_extreme_heat_precool_apply")
    deactivate = automation("climate_away_mode_deactivate")
    extreme_heat_branch = deactivate["action"][1]["choose"][1]
    daytime_branch = deactivate["action"][1]["choose"][2]

    assert not any(
        trigger.get("entity_id") == "zone.home" for trigger in apply["trigger"]
    )
    assert deactivate["trigger"] == [
        {"platform": "numeric_state", "entity_id": "zone.home", "above": 0}
    ]
    assert any(
        condition.get("entity_id") == "input_boolean.climate_extreme_heat_overlay_enabled"
        and condition.get("state") == "on"
        for condition in extreme_heat_branch["conditions"]
    )
    assert any(
        condition.get("entity_id") == "binary_sensor.climate_extreme_heat_day"
        and condition.get("state") == "on"
        for condition in extreme_heat_branch["conditions"]
    )
    assert any(
        condition.get("condition") == "time"
        and condition.get("after") == "12:59:00"
        and condition.get("before") == "18:00:00"
        for condition in extreme_heat_branch["conditions"]
    )

    set_temperature_steps = [
        step
        for step in extreme_heat_branch["sequence"]
        if step.get("service") == "climate.set_temperature"
    ]
    assert len(set_temperature_steps) == 1
    assert "day - offset" in set_temperature_steps[0]["data"]["target_temp_high"]
    assert any(
        step.get("service") == "input_boolean.turn_on"
        and step.get("target", {}).get("entity_id")
        == "input_boolean.climate_extreme_heat_precool_active"
        for step in extreme_heat_branch["sequence"]
    )
    assert daytime_branch["conditions"] == [
        {"condition": "time", "after": "09:00:00", "before": "21:00:00"}
    ]


def test_precool_prearrival_helpers_use_person_level_proximity_abstractions():
    config = load_climate()
    text = climate_package_text()

    assert config["input_number"]["climate_precool_arrival_distance_ft"]["initial"] == 30000
    assert config["input_number"]["climate_precool_arrival_signal_max_age"]["initial"] == 20

    sensor = binary_sensor("Climate Pre-arrival Expected")
    state = sensor["state"]
    assert "person.brian" in state
    assert "person.hester" in state
    assert "sensor.home_brian_distance" in state
    assert "sensor.home_hester_direction_of_travel" in state
    assert "device_tracker" not in state
    assert "direction == 'towards'" in state
    assert "last_updated" in state
    assert "direction_age" not in state
    assert "climate_precool_arrival_distance_ft" in state
    assert sensor["attributes"]["eligible_people"] == "Brian, Hester"
    assert "To add another climate pre-arrival person" in text


def test_precool_prearrival_qualifies_fresh_distance_with_stable_towards_direction():
    sensor = binary_sensor("Climate Pre-arrival Expected")
    current_time = datetime(2026, 6, 29, 15, 52, 35)
    states = {
        "person.brian": "not_home",
        "person.hester": "home",
        "sensor.home_brian_distance": "285",
        "sensor.home_brian_direction_of_travel": "towards",
        "sensor.home_hester_distance": "12000",
        "sensor.home_hester_direction_of_travel": "away_from",
        "input_number.climate_precool_arrival_distance_ft": "30000",
        "input_number.climate_precool_arrival_signal_max_age": "20",
    }
    updated_at = {
        "sensor.home_brian_distance": current_time - timedelta(minutes=1),
        # Proximity direction may remain the same for a whole trip, so Home
        # Assistant may not advance last_updated for this entity while fresh
        # distance updates continue proving the inbound signal is current.
        "sensor.home_brian_direction_of_travel": current_time - timedelta(hours=1),
    }

    assert render_ha_template(sensor["state"], states, updated_at, current_time) == "True"
    assert render_ha_template(
        sensor["attributes"]["expected_people"], states, updated_at, current_time
    ) == "Brian"


def test_precool_prearrival_rejects_stale_distance_even_if_direction_is_towards():
    sensor = binary_sensor("Climate Pre-arrival Expected")
    current_time = datetime(2026, 6, 29, 15, 52, 35)
    states = {
        "person.brian": "not_home",
        "person.hester": "home",
        "sensor.home_brian_distance": "285",
        "sensor.home_brian_direction_of_travel": "towards",
        "sensor.home_hester_distance": "12000",
        "sensor.home_hester_direction_of_travel": "away_from",
        "input_number.climate_precool_arrival_distance_ft": "30000",
        "input_number.climate_precool_arrival_signal_max_age": "20",
    }
    updated_at = {
        "sensor.home_brian_distance": current_time - timedelta(minutes=21),
        "sensor.home_brian_direction_of_travel": current_time,
    }

    assert render_ha_template(sensor["state"], states, updated_at, current_time) == "False"


def test_precool_prearrival_template_has_explicit_update_triggers():
    block = template_block_for_binary_sensor("Climate Pre-arrival Expected")
    triggers = block["trigger"]

    state_trigger = next(
        trigger for trigger in triggers if trigger.get("id") == "prearrival_input_changed"
    )
    triggered_entities = set(state_trigger["entity_id"])

    assert state_trigger["platform"] == "state"
    assert {
        "person.brian",
        "person.hester",
        "sensor.home_brian_distance",
        "sensor.home_brian_direction_of_travel",
        "sensor.home_hester_distance",
        "sensor.home_hester_direction_of_travel",
        "input_number.climate_precool_arrival_distance_ft",
        "input_number.climate_precool_arrival_signal_max_age",
    }.issubset(triggered_entities)
    assert any(
        trigger.get("platform") == "homeassistant" and trigger.get("event") == "start"
        for trigger in triggers
    )
    assert any(
        trigger.get("platform") == "time_pattern" and trigger.get("minutes") == "/1"
        for trigger in triggers
    )


def test_generic_prearrival_apply_can_start_from_debounced_expectation():
    item = automation("climate_pre_arrival_recovery_apply")

    prearrival_trigger = next(
        trigger for trigger in item["trigger"] if trigger.get("id") == "prearrival_expected"
    )
    assert prearrival_trigger == {
        "platform": "state",
        "entity_id": "binary_sensor.climate_pre_arrival_expected",
        "to": "on",
        "for": {"minutes": 2},
        "id": "prearrival_expected",
    }

    condition_text = str(item["condition"])
    assert "binary_sensor.climate_pre_arrival_expected" in condition_text
    assert "zone.home" in condition_text
    assert "input_boolean.mode_guest" in condition_text
    assert "input_boolean.climate_pre_arrival_recovery_active" in condition_text

    services = str(item["action"])
    assert "input_number.climate_cool_day" in services
    assert "input_number.climate_heat_day" in services
    assert "binary_sensor.climate_extreme_heat_day" in services
    assert "day - offset" in services
    assert "input_boolean.climate_pre_arrival_recovery_active" in services


def test_precool_restore_cancels_abandoned_prearrival_to_away_targets():
    item = automation("climate_pre_arrival_recovery_restore")
    text = climate_package_text()

    abandoned = next(
        trigger for trigger in item["trigger"] if trigger.get("id") == "prearrival_cleared"
    )
    assert abandoned == {
        "platform": "state",
        "entity_id": "binary_sensor.climate_pre_arrival_expected",
        "to": "off",
        "for": {"minutes": 10},
        "id": "prearrival_cleared",
    }
    assert "prearrival_cleared" in text
    assert "input_number.climate_cool_away" in text
    assert "input_number.climate_heat_away" in text
    assert "input_boolean.turn_off" in text
    assert "states('input_number.climate_cool_day')" in text
    assert "states('input_number.climate_heat_day')" in text


def test_precool_restore_overlay_end_restores_away_prearrival_targets():
    item = automation("climate_extreme_heat_precool_restore")
    away_branch = item["action"][1]["choose"][0]
    conditions = away_branch["conditions"]
    sequence = away_branch["sequence"]

    trigger_condition = next(
        condition for condition in conditions if condition.get("condition") == "template"
    )
    assert "overlay_window_end" in trigger_condition["value_template"]
    assert "overlay_disabled" in trigger_condition["value_template"]
    assert "climate_disabled" in trigger_condition["value_template"]
    assert "prearrival_cleared" not in trigger_condition["value_template"]
    assert any(
        condition.get("condition") == "numeric_state"
        and condition.get("entity_id") == "zone.home"
        and condition.get("below") == 1
        for condition in conditions
    )
    assert any(
        condition.get("entity_id") == "input_boolean.mode_guest"
        and condition.get("state") == "off"
        for condition in conditions
    )
    assert not any(
        condition.get("entity_id") == "input_boolean.climate_automation_enabled"
        for condition in conditions
    )
    assert any(
        "input_number.climate_cool_away" in step.get("data", {}).get("target_temp_high", "")
        and "input_number.climate_heat_away" in step.get("data", {}).get("target_temp_low", "")
        for step in sequence
        if step.get("service") == "climate.set_temperature"
    )


def test_restart_resync_runs_on_start_only_when_occupied_or_guest_and_stale():
    item = automation("climate_restart_occupied_resync")
    text = climate_package_text()

    assert item["trigger"] == [
        {"platform": "homeassistant", "event": "start", "id": "ha_start"}
    ]
    assert any(
        condition.get("entity_id") == "input_boolean.climate_automation_enabled"
        and condition.get("state") == "on"
        for condition in item["condition"]
    )
    occupancy_condition = next(
        condition for condition in item["condition"] if condition.get("condition") == "or"
    )
    assert {
        (condition.get("condition"), condition.get("entity_id"), condition.get("above"), condition.get("state"))
        for condition in occupancy_condition["conditions"]
    } == {
        ("numeric_state", "zone.home", 0, None),
        ("state", "input_boolean.mode_guest", None, "on"),
    }
    stale_guard = next(
        condition for condition in item["condition"] if condition.get("condition") == "template"
    )
    assert "target_temp_high" in stale_guard["value_template"]
    assert "target_temp_low" in stale_guard["value_template"]
    assert "states('climate.dining_room_thermostat') != 'heat_cool'" in stale_guard["value_template"]
    assert "climate_cool_away" not in text.split("id: climate_restart_occupied_resync", 1)[1]


def test_restart_resync_selects_current_occupied_schedule_and_overlay():
    item = automation("climate_restart_occupied_resync")
    branches = item["action"][1]["choose"]
    branch_text = [str(branch) for branch in branches]
    default_text = str(item["action"][1]["default"])

    assert len(branches) == 4
    assert "climate_cool_morning" in branch_text[0]
    assert "climate_heat_morning" in branch_text[0]
    assert "binary_sensor.climate_extreme_heat_day" in branch_text[1]
    assert "day - offset" in branch_text[1]
    assert "input_boolean.climate_extreme_heat_precool_active" in branch_text[1]
    assert "climate_cool_day" in branch_text[2]
    assert "climate_heat_day" in branch_text[2]
    assert "climate_cool_bedtime" in branch_text[3]
    assert "climate_heat_bedtime" in branch_text[3]
    assert "climate_cool_sleep" in default_text
    assert "climate_heat_sleep" in default_text
