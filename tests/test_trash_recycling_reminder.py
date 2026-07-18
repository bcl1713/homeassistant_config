from datetime import datetime, timedelta
from pathlib import Path

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "trash_recycling_reminder.yaml"
CALENDAR = "calendar.1112_limerick_rd_papillion"


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def automation_by_id(automation_id):
    for automation in load_package()["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"automation {automation_id!r} not found")


def render_collection_type(start_time, message, description, now):
    template = automation_by_id("trash_recycling_led_reminder_start")["variables"][
        "collection_type"
    ]
    attributes = {
        (CALENDAR, "start_time"): start_time,
        (CALENDAR, "message"): message,
        (CALENDAR, "description"): description,
    }
    environment = Environment(trim_blocks=True, lstrip_blocks=True)
    environment.globals.update(
        as_datetime=lambda value, default=None: datetime.fromisoformat(value)
        if value
        else default,
        as_local=lambda value: value,
        calendar_entity=CALENDAR,
        state_attr=lambda entity_id, attribute: attributes.get((entity_id, attribute)),
        now=lambda: now,
        timedelta=timedelta,
    )
    return environment.from_string(template).render().strip()


def test_collection_classifier_uses_tomorrows_actual_calendar_event_text():
    now = datetime(2026, 7, 19, 18, 0)

    assert render_collection_type(
        "2026-07-20 00:00:00", "Garbage", "Garbage", now
    ) == "garbage"
    assert render_collection_type(
        "2026-07-20 00:00:00", "Garbage and Recycling", "Garbage and Recycling", now
    ) == "garbage_recycling"
    assert render_collection_type(
        "2026-07-20 00:00:00", "Recycling", "Recycling", now
    ) == "none"
    assert render_collection_type(
        "2026-07-20 00:00:00", "Municipal holiday", "No collection", now
    ) == "none"
    assert render_collection_type(
        "2026-07-21 00:00:00", "Garbage", "Garbage", now
    ) == "none"


def test_start_automation_snapshots_and_sets_explicit_switch_style_targets():
    package = load_package()
    anchors = package["homeassistant"]["customize"]["package.node_anchors"]
    start = automation_by_id("trash_recycling_led_reminder_start")

    snapshot = anchors["trash_recycling_led_snapshot_entities"]
    mode_entities = anchors["trash_recycling_led_mode_entities"]
    color_entities = anchors["trash_recycling_led_color_entities"]
    brightness_entities = anchors["trash_recycling_led_brightness_entities"]

    assert len(mode_entities) == len(color_entities) == len(brightness_entities) == 14
    assert mode_entities[0] == "select.master_bathroom_master_bathroom_closet_led_indicator"
    assert color_entities[0] == "select.master_bathroom_master_bathroom_closet_led_indicator_color"
    assert brightness_entities[0] == "select.master_bathroom_master_bathroom_closet_led_indicator_brightness"
    assert set(snapshot) == set(mode_entities + color_entities + brightness_entities)
    assert all("door" not in entity and "window" not in entity for entity in snapshot)
    assert all("remote" not in entity for entity in snapshot)

    snapshot_action, mode_action, color_action, brightness_action, active_action = start[
        "action"
    ]
    assert snapshot_action["action"] == "scene.create"
    assert snapshot_action["data"]["scene_id"] == "trash_recycling_led_reminder_prior_settings"
    assert snapshot_action["data"]["snapshot_entities"] == snapshot
    assert mode_action["data"]["option"] == "Always on"
    assert mode_action["target"]["entity_id"] == mode_entities
    assert color_action["target"]["entity_id"] == color_entities
    assert color_action["data"]["option"] == "{{ reminder_color }}"
    assert brightness_action["data"]["option"] == "Bright (100%)"
    assert brightness_action["target"]["entity_id"] == brightness_entities
    assert active_action["target"]["entity_id"] == "input_boolean.trash_recycling_led_reminder_active"
    assert "presence" not in str(start).lower()


def test_restore_automation_restores_scene_at_midnight_only_after_a_reminder():
    restore = automation_by_id("trash_recycling_led_reminder_restore")

    assert restore["trigger"] == [{"platform": "time", "at": "00:00:00"}]
    assert restore["condition"] == [
        {
            "condition": "state",
            "entity_id": "input_boolean.trash_recycling_led_reminder_active",
            "state": "on",
        }
    ]
    assert restore["action"][0] == {
        "action": "scene.turn_on",
        "target": {"entity_id": "scene.trash_recycling_led_reminder_prior_settings"},
    }
    assert restore["action"][1]["action"] == "input_boolean.turn_off"
