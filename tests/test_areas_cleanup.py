"""Minimal synthetic config object, never a private storage/dashboard export."""
import copy
import json
from pathlib import Path

import jsonpatch
import pytest

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "docs/repairs/244-areas.patch.json"
# Explicit approved contract, independent of the shipped patch.
CHANGES = [
    ("basement/security/hidden/0", "camera.birdseye", "camera.system_birdseye"),
    ("dining_room/climate/order/0", "climate.thermostat_2", "climate.dining_room_thermostat"),
    ("dining_room/climate/hidden/0", "humidifier.thermostat", "humidifier.dining_room_humidistat"),
    ("hallway/security/hidden/0", "camera.front_doorbell_main", "camera.front_door_doorbell_camera_main"),
    ("hallway/security/hidden/1", "binary_sensor.front_doorbell_door_status", "binary_sensor.front_door_doorbell_door_status"),
    ("hallway/security/hidden/2", "camera.front_doorbell_sub", "camera.front_door_doorbell_camera_sub"),
    ("hallway/security/order/0", "camera.front_doorbell", "camera.front_door_doorbell_camera"),
    ("kitchen/others/order/0", "vacuum.sally", "vacuum.kitchen_roomba"),
    ("garage/security/hidden/0", "lock.ratgdov25i_0cd7df_lock_remotes", None),
]


def path(short):
    area, group, key, index = short.split("/")
    return f"/strategy/areas_options/{area}/groups_options/{group}/{key}/{index}"


def fixture():
    return {"strategy": {"type": "custom:area-strategy", "areas_options": {
        "basement": {"groups_options": {"security": {
            "hidden": ["camera.birdseye", "camera.keep_basement_hidden"],
        }}},
        "dining_room": {"groups_options": {"climate": {
            "hidden": ["humidifier.thermostat", "climate.thermostat", "climate.keep_hidden"],
            "order": ["climate.thermostat_2", "climate.keep_ordered"],
        }}},
        "garage": {"groups_options": {"security": {
            "hidden": ["lock.ratgdov25i_0cd7df_lock_remotes", "camera.keep_hidden"],
            "order": ["cover.garage_door"],
        }}},
        "hallway": {"groups_options": {"security": {
            "hidden": ["camera.front_doorbell_main", "binary_sensor.front_doorbell_door_status",
                       "camera.front_doorbell_sub", "camera.keep_hallway_hidden"],
            "order": ["camera.front_doorbell", "lock.keep_control"],
        }}},
        "kitchen": {"groups_options": {"others": {
            "order": ["vacuum.sally", "sensor.keep_ordered"],
        }}, "entities_options": {"sensor.dishwasher": {"hidden": True, "name": "Keep options"}}},
        "untouched": {"order": 7, "groups_options": {"lights": {"hidden": ["light.keep"]}}},
    }}, "views": [{"cards": [{"type": "button", "entity": "lock.keep_control"}]}]}


def test_patch_exactly_updates_all_nine_preferences_preserving_full_config():
    before = fixture()
    expected = copy.deepcopy(before)
    for short, _, replacement in CHANGES:
        area, group, key, index = short.split("/")
        values = expected["strategy"]["areas_options"][area]["groups_options"][group][key]
        if replacement is None:
            values.pop(int(index))
        else:
            values[int(index)] = replacement
    result = jsonpatch.apply_patch(before, json.loads(PATCH.read_text()))
    assert result == expected  # Full arrays, unrelated options and controls, not just membership.
    assert before == fixture()  # Unchanged private rollback preimage contract.


def test_patch_tests_all_exact_old_values_before_any_mutation():
    patch = json.loads(PATCH.read_text())
    assert patch[:9] == [{"op": "test", "path": path(short), "value": old}
                         for short, old, _ in CHANGES]
    assert patch[9:] == [dict(op="remove", path=path(short)) if new is None else
                        dict(op="replace", path=path(short), value=new)
                        for short, _, new in CHANGES]


@pytest.mark.parametrize("short,old,new", CHANGES)
def test_patch_refuses_each_drift_before_even_in_place_mutation(short, old, new):
    before = fixture()
    area, group, key, index = short.split("/")
    before["strategy"]["areas_options"][area]["groups_options"][group][key][int(index)] = "sensor.drift"
    saved = copy.deepcopy(before)
    with pytest.raises(jsonpatch.JsonPatchTestFailed):
        jsonpatch.apply_patch(before, json.loads(PATCH.read_text()), in_place=True)
    assert before == saved


def test_patch_refuses_second_apply_without_mutating_result():
    patch = json.loads(PATCH.read_text())
    after = jsonpatch.apply_patch(fixture(), patch)
    saved = copy.deepcopy(after)
    with pytest.raises(jsonpatch.JsonPatchTestFailed):
        jsonpatch.apply_patch(after, patch, in_place=True)
    assert after == saved
