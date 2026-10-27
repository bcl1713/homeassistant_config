"""Synthetic preference-only fixture: never a private storage export."""
import copy
import json
from pathlib import Path

import jsonpatch
import pytest

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "docs/repairs/244-areas.patch.json"


def fixture():
    return {"strategy": {"type": "custom:area-strategy", "areas_options": {
        "dining_room": {"groups_options": {"climate": {
            "hidden": ["humidifier.thermostat", "climate.keep_hidden"],
            "order": ["climate.thermostat_2"],
        }}},
        "garage": {"groups_options": {"security": {
            "hidden": ["lock.ratgdov25i_0cd7df_lock_remotes", "camera.keep_hidden"],
        }}},
        "hallway": {"groups_options": {"security": {
            "hidden": ["camera.front_doorbell_main"], "order": ["camera.front_doorbell"],
        }}},
    }}, "views": [{"cards": [{"type": "button", "entity": "lock.keep_control"}]}]}


def test_patch_removes_only_two_obsolete_hidden_preferences():
    before = fixture()
    expected = copy.deepcopy(before)
    areas = expected["strategy"]["areas_options"]
    areas["dining_room"]["groups_options"]["climate"]["hidden"].pop(0)
    areas["garage"]["groups_options"]["security"]["hidden"].pop(0)
    result = jsonpatch.apply_patch(before, json.loads(PATCH.read_text()))
    assert result == expected
    assert before == fixture()  # usable unchanged rollback preimage


@pytest.mark.parametrize("area,group", [("dining_room", "climate"), ("garage", "security")])
def test_patch_refuses_drift_or_second_apply_without_mutating_preimage(area, group):
    before = fixture()
    before["strategy"]["areas_options"][area]["groups_options"][group]["hidden"].pop(0)
    saved = copy.deepcopy(before)
    with pytest.raises(jsonpatch.JsonPatchTestFailed):
        jsonpatch.apply_patch(before, json.loads(PATCH.read_text()))
    assert before == saved
