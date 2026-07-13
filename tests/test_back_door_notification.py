from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
NOTIFICATIONS = ROOT / "packages" / "notifications.yaml"
BACK_DOOR_ENTITY = "binary_sensor.kitchen_back_door"
BACK_DOOR_TAG = "back-door-open"
BRIAN_NOTIFIER = "notify.mobile_app_brian_phone"


def automation_by_id(automation_id):
    package = yaml.safe_load(NOTIFICATIONS.read_text())
    for automation in package["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"automation {automation_id!r} not found")


def test_back_door_open_notification_is_brian_only_and_tagged():
    automation = automation_by_id("back_door_open_notification")

    assert automation["trigger"] == [
        {
            "platform": "state",
            "entity_id": BACK_DOOR_ENTITY,
            "from": "off",
            "to": "on",
        }
    ]
    assert automation["action"] == [
        {
            "service": BRIAN_NOTIFIER,
            "data": {
                "title": "Back Door",
                "message": "Back door opened.",
                "data": {"tag": BACK_DOOR_TAG},
            },
        }
    ]
    assert automation["mode"] == "single"


def test_back_door_close_clears_the_matching_brian_notification():
    automation = automation_by_id("back_door_close_clear_notification")

    assert automation["trigger"] == [
        {
            "platform": "state",
            "entity_id": BACK_DOOR_ENTITY,
            "from": "on",
            "to": "off",
        }
    ]
    assert automation["action"] == [
        {
            "service": BRIAN_NOTIFIER,
            "data": {
                "message": "clear_notification",
                "data": {"tag": BACK_DOOR_TAG},
            },
        }
    ]
    assert automation["mode"] == "single"
