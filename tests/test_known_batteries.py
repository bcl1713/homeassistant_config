"""Exercise shipped templates with HA-style state lookup; never source attributes."""
from pathlib import Path

import pytest
import yaml
from jinja2.nativetypes import NativeEnvironment

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "battery_hester_remote": ("sensor.bedroom_remote_hester_battery_level", "binary_sensor.bedroom_remote_hester_battery_is_charging", "binary"),
    "battery_brian_remote": ("sensor.bedroom_remote_brian_battery_level", "binary_sensor.bedroom_remote_brian_battery_is_charging", "binary"),
    "battery_hester_phone": ("sensor.hester_phone_battery_level", "sensor.hester_phone_battery_state", "phone"),
    "battery_brian_phone": ("sensor.brian_phone_battery_level", "sensor.brian_phone_battery_state", "phone"),
    "battery_towner_phone": ("sensor.tk_galaxy_a16_battery_level", "sensor.tk_galaxy_a16_battery_state", "phone"),
    "battery_front_door": ("sensor.front_door_battery", None, None),
    "battery_master_bedroom_sensor": ("sensor.master_bedroom_battery", None, None),
    "battery_sally_vacuum": ("sensor.sally_battery", "binary_sensor.kitchen_kitchen_roomba_charging", "binary"),
}


def sensors():
    package = yaml.safe_load((ROOT / "packages/known_batteries.yaml").read_text())
    return {sensor["unique_id"]: sensor for sensor in package["template"][0]["sensor"]}


def render(template, values):
    env = NativeEnvironment()
    env.globals["states"] = lambda entity: values.get(entity, "unknown")
    # Deliberately no state_attr: absent source attributes must never be queried.
    return env.from_string(template).render()


@pytest.mark.parametrize("uid", SOURCES)
@pytest.mark.parametrize("value", [0, 28, 83.0, 100, "unknown", "unavailable", None])
def test_useful_ids_and_percentage_passthrough(uid, value):
    sensor = sensors()[uid]
    source, _, _ = SOURCES[uid]
    assert sensor["attributes"]["entity_id"] == source
    assert sensor["device_class"] == "battery"
    assert sensor["unit_of_measurement"] == "%"
    values = {} if value is None else {source: value}
    assert render(sensor["state"], values) == ("unknown" if value is None else value)


@pytest.mark.parametrize("uid", SOURCES)
def test_unsupported_unused_metadata_is_absent(uid):
    attributes = sensors()[uid]["attributes"]
    assert "battery_health" not in attributes
    assert "cycle_count" not in attributes
    if SOURCES[uid][1] is None:
        assert "is_charging" not in attributes


@pytest.mark.parametrize("uid", [uid for uid, (_, charging, _) in SOURCES.items() if charging])
@pytest.mark.parametrize("value", [None, "unknown", "unavailable", "unexpected", "on", "off", "charging", "discharging", "not_charging", "full"])
def test_supported_charging_distinguishes_false_from_unknown(uid, value):
    _, source, kind = SOURCES[uid]
    known = {"on": True, "off": False} if kind == "binary" else {
        "charging": True, "discharging": False, "not_charging": False, "full": False,
    }
    expected = known.get(value, "unknown")
    actual = render(sensors()[uid]["attributes"]["is_charging"], {} if value is None else {source: value})
    assert actual == expected
    assert type(actual) is type(expected)


def test_unused_sally_direct_is_retired_without_replacement_count():
    assert set(sensors()) == set(SOURCES)
    assert len([s for s in sensors().values() if "Sally" in s["name"]]) == 1
    assert sensors()["battery_sally_vacuum"]["state"] == "{{ states('sensor.sally_battery') }}"
