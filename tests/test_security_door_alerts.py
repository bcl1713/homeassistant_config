from pathlib import Path

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "security_door_alerts.yaml"

CONTACTS = {
    "binary_sensor.entry_front_door": {"name": "Front Door", "tag_suffix": "front"},
    "binary_sensor.kitchen_back_door": {"name": "Back Door", "tag_suffix": "back"},
    "binary_sensor.garage_garage_interior_door": {
        "name": "Garage Interior Door",
        "tag_suffix": "garage-interior",
    },
}


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def automation_by_id(package, automation_id):
    for automation in package["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"automation {automation_id!r} not found")


def test_armed_security_contacts_include_exterior_and_garage_boundary_doors():
    package = load_package()
    contacts = package["homeassistant"]["customize"]["package.node_anchors"][
        "security_door_contacts"
    ]

    assert contacts == CONTACTS


def test_open_alert_is_immediate_armed_only_and_guest_mode_exempt():
    package = load_package()
    automation = automation_by_id(package, "armed_security_door_open_alert")

    assert automation["trigger"] == [
        {
            "platform": "state",
            "entity_id": list(CONTACTS),
            "from": "off",
            "to": "on",
        }
    ]
    assert automation["condition"] == [
        {
            "condition": "state",
            "entity_id": "input_boolean.mode_guest",
            "state": "off",
        },
        {
            "condition": "template",
            "value_template": (
                "{{ states('alarm_control_panel.home_alarm') in\n"
                "   ['armed_away', 'armed_night'] }}\n"
            ),
        },
    ]
    assert "for" not in automation["trigger"][0]
    assert automation["variables"]["security_mode_label"] == (
        "{{ 'away' if security_mode == 'armed_away' else 'night' }}"
    )
    assert "armed_night" in automation["condition"][1]["value_template"]


def test_open_alert_uses_distinct_critical_tags_and_one_bedroom_announcement():
    package = load_package()
    automation = automation_by_id(package, "armed_security_door_open_alert")
    notification = automation["action"][0]
    tts = automation["action"][1]

    assert notification["service"] == "notify.all_mobile_devices"
    assert notification["data"]["title"] == "Security Door Alert"
    assert notification["data"]["data"] == {
        "tag": "{{ notification_tag }}",
        "priority": "high",
        "ttl": 0,
        "critical": True,
    }
    assert "security-door-open-" in automation["variables"]["notification_tag"]
    assert "exterior-door-open-" not in automation["variables"]["notification_tag"]
    tag_template = Environment().from_string(automation["variables"]["notification_tag"])
    assert tag_template.render(
        door_contacts=CONTACTS,
        trigger={"entity_id": "binary_sensor.entry_front_door"},
        security_mode_label="away",
    ) == "security-door-open-front-away"
    assert "from: \"off\"" in PACKAGE.read_text()
    assert "while open do not re-announce" in PACKAGE.read_text()

    assert tts == {
        "action": "tts.speak",
        "target": {"entity_id": "tts.google_en_com"},
        "data": {
            "cache": True,
            "media_player_entity_id": "media_player.master_bedroom_display",
            "message": "{{ announcement }}",
        },
    }
    assert automation["mode"] == "parallel"
    assert automation["max"] == 3


def test_close_clears_only_matching_armed_security_tag_namespace():
    package = load_package()
    automation = automation_by_id(package, "armed_security_door_close_clear_alert")

    assert automation["trigger"] == [
        {
            "platform": "state",
            "entity_id": list(CONTACTS),
            "from": "on",
            "to": "off",
        }
    ]
    repeat = automation["action"][0]["repeat"]
    assert repeat["for_each"] == ["away", "night"]
    assert repeat["sequence"] == [
        {
            "service": "notify.all_mobile_devices",
            "data": {
                "message": "clear_notification",
                "data": {
                    "tag": "{{ 'security-door-open-' ~ door_contacts[trigger.entity_id]['tag_suffix'] ~ '-' ~ repeat.item }}"
                },
            },
        }
    ]
    assert "exterior-door-open-" not in str(repeat)
    assert automation["mode"] == "parallel"
    assert automation["max"] == 3
