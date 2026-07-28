from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "master_bedroom_closet_light.yaml"
DOOR_SENSOR = "binary_sensor.master_bathroom_master_bedroom_closet"
CLOSET_LIGHT = "light.master_bathroom_master_bathroom_closet"


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def automation_by_id(package, automation_id):
    for automation in package["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"automation {automation_id!r} not found")


def assert_direct_state_transition(automation, *, state, service):
    assert automation["trigger"] == [
        {
            "platform": "state",
            "entity_id": DOOR_SENSOR,
            "to": state,
        }
    ]
    assert automation["action"] == [
        {
            "service": service,
            "target": {"entity_id": CLOSET_LIGHT},
        }
    ]
    assert "condition" not in automation
    assert "delay" not in str(automation["action"])
    assert automation["mode"] == "single"


def test_opening_closet_door_turns_on_exact_closet_light():
    automation = automation_by_id(load_package(), "master_bedroom_closet_light_on_open")

    assert_direct_state_transition(automation, state="on", service="light.turn_on")


def test_closing_closet_door_turns_off_exact_closet_light():
    automation = automation_by_id(load_package(), "master_bedroom_closet_light_off_close")

    assert_direct_state_transition(automation, state="off", service="light.turn_off")
