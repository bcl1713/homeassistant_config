from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "exterior_door_monitoring.yaml"

CONTACTS = {
    "binary_sensor.entry_front_door": {
        "name": "Front Door",
        "tag": "exterior-door-open-front",
    },
    "binary_sensor.kitchen_back_door": {
        "name": "Back Door",
        "tag": "exterior-door-open-back",
    },
    "binary_sensor.garage_garage_interior_door": {
        "name": "Garage Interior Door",
        "tag": "exterior-door-open-garage-interior",
    },
}


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def automation_by_id(package, automation_id):
    for automation in package["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"automation {automation_id!r} not found")


def test_exterior_door_contacts_include_the_garage_interior_contact():
    package = load_package()
    contacts = package["homeassistant"]["customize"]["package.node_anchors"][
        "exterior_door_contacts"
    ]

    assert contacts == CONTACTS
    assert len({contact["tag"] for contact in contacts.values()}) == len(contacts)
    assert "immediate armed-security and secure-house workflows" in PACKAGE.read_text()


def test_open_alert_holds_for_two_continuous_minutes_and_cancels_on_early_close():
    package = load_package()
    automation = automation_by_id(package, "exterior_door_open_two_minute_alert")

    assert automation["trigger"] == [
        {
            "platform": "state",
            "entity_id": list(CONTACTS),
            "from": "off",
            "to": "on",
            "for": "00:02:00",
        }
    ]
    # A state trigger with `for` only fires after an uninterrupted off -> on
    # hold; returning to off before two minutes cancels the pending trigger.
    assert automation["variables"] == {"door_contacts": CONTACTS}
    assert automation["action"] == [
        {
            "service": "notify.all_mobile_devices",
            "data": {
                "title": "Exterior Door Alert",
                "message": (
                    "{{ door_contacts[trigger.entity_id]['name'] }} has been open for "
                    "2 minutes.\n"
                ),
                "data": {
                    "tag": "{{ door_contacts[trigger.entity_id]['tag'] }}"
                },
            },
        }
    ]
    assert automation["mode"] == "parallel"
    assert automation["max"] == 3


def test_close_clears_only_the_matching_tag_for_each_monitored_door():
    package = load_package()
    automation = automation_by_id(package, "exterior_door_close_clear_alert")

    assert automation["trigger"] == [
        {
            "platform": "state",
            "entity_id": list(CONTACTS),
            "from": "on",
            "to": "off",
        }
    ]
    assert automation["variables"] == {"door_contacts": CONTACTS}
    assert automation["action"] == [
        {
            "service": "notify.all_mobile_devices",
            "data": {
                "message": "clear_notification",
                "data": {
                    "tag": "{{ door_contacts[trigger.entity_id]['tag'] }}"
                },
            },
        }
    ]
    assert automation["mode"] == "parallel"
    assert automation["max"] == 3


def test_historical_brian_only_back_door_automation_is_not_present():
    notifications = (ROOT / "packages" / "notifications.yaml").read_text()

    assert "back_door_open_notification" not in notifications
    assert "back_door_close_clear_notification" not in notifications
    assert "notify.mobile_app_brian_phone" not in notifications
