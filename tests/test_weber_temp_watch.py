from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "weber_temp_watch.yaml"
PROBE_1 = "sensor.back_yard_weber_connect_hub_probe_1"
DERIVATIVE = "sensor.back_yard_weber_connect_hub_grill_temp_derivative"
PROBE_2 = "sensor.back_yard_weber_connect_hub_probe_2"
AUTOMATION_ID = "temp_weber_grill_temperature_watch"


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def automation_by_id(package, automation_id):
    for automation in package["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"automation {automation_id!r} not found")


def test_temp_weber_watch_uses_exact_threshold_crossing_triggers():
    automation = automation_by_id(load_package(), AUTOMATION_ID)

    assert automation["trigger"] == [
        {
            "platform": "numeric_state",
            "entity_id": PROBE_1,
            "above": 260,
            "id": "probe_1_above_260",
        },
        {
            "platform": "numeric_state",
            "entity_id": PROBE_1,
            "below": 240,
            "id": "probe_1_below_240",
        },
        {
            "platform": "numeric_state",
            "entity_id": DERIVATIVE,
            "above": 0.5,
            "id": "grill_temp_rising_fast",
        },
        {
            "platform": "numeric_state",
            "entity_id": DERIVATIVE,
            "below": -0.5,
            "id": "grill_temp_falling_fast",
        },
        {
            "platform": "numeric_state",
            "entity_id": PROBE_2,
            "above": 165,
            "for": "00:01:00",
            "id": "probe_2_above_165_for_one_minute",
        },
    ]


def test_temp_weber_watch_sends_one_templated_brian_notification_per_trigger():
    automation = automation_by_id(load_package(), AUTOMATION_ID)

    assert automation["alias"].startswith("TEMP")
    assert automation["mode"] == "single"
    assert "condition" not in automation
    assert automation["action"][0]["action"] == "notify.mobile_app_brian_phone"

    message = automation["action"][0]["data"]["message"]
    assert "conditions[trigger.id]" in message
    assert "states(trigger.entity_id)" in message
    assert "state_attr(trigger.entity_id, 'unit_of_measurement')" in message
    for trigger in automation["trigger"]:
        assert trigger["id"] in message
