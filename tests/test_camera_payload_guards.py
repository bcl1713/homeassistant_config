from pathlib import Path

import yaml
from jinja2.nativetypes import NativeEnvironment


ROOT = Path(__file__).resolve().parents[1]
CAMERAS_YAML = ROOT / "packages" / "cameras.yaml"


def load_camera_automation():
    data = yaml.safe_load(CAMERAS_YAML.read_text())
    for automation in data["automation"]:
        if automation.get("id") == "camera_notification_universal":
            return automation
    raise AssertionError("camera_notification_universal automation not found")


def render_native(template_string, context):
    env = NativeEnvironment(trim_blocks=True, lstrip_blocks=True)
    env.globals["is_state"] = lambda entity_id, state: context["state_map"].get(entity_id) == state
    template = env.from_string(template_string)
    return template.render(context)


def evaluate_camera_variables(payload, state_map=None):
    automation = load_camera_automation()
    variables = automation["action"][0]["variables"]
    context = {
        "trigger": {"payload_json": payload},
        "state_map": state_map or {},
    }

    evaluated = {}
    for key, template_string in variables.items():
        local_context = context | evaluated
        evaluated[key] = render_native(template_string, local_context)
    return evaluated


def evaluate_camera_condition(payload, state_map=None):
    automation = load_camera_automation()
    template_string = automation["condition"][0]["value_template"]
    rendered = render_native(
        template_string,
        {
            "trigger": {"payload_json": payload},
            "state_map": state_map or {},
        },
    )
    if isinstance(rendered, str):
        normalized = rendered.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    return rendered


def test_camera_condition_tolerates_missing_after_payload():
    result = evaluate_camera_condition({}, {"input_boolean.notification_camera_outdoor": "on"})

    assert result is False


def test_camera_variables_fallback_when_detection_payload_is_partial():
    payload = {
        "after": {
            "camera": "front_drive",
            "data": {},
        }
    }

    variables = evaluate_camera_variables(payload)

    assert variables["camera"] == "front_drive"
    assert variables["detections"] == []
    assert variables["id"] == "unknown"
    assert variables["objects"] == []
    assert variables["sub_labels"] == []
    assert variables["label"] == "Unknown"
    assert variables["review_id"] == "unknown"
    assert variables["start_time"] == 0
    assert variables["notification_tag"] == "frigate_unknown"


def test_camera_condition_tolerates_null_after_payload():
    result = evaluate_camera_condition(
        {"after": None},
        {"input_boolean.notification_camera_outdoor": "on"},
    )

    assert result is False


def test_camera_variables_fallback_when_after_data_is_null():
    payload = {
        "after": {
            "camera": "front_drive",
            "data": None,
        }
    }

    variables = evaluate_camera_variables(payload)

    assert variables["camera"] == "front_drive"
    assert variables["detections"] == []
    assert variables["id"] == "unknown"
    assert variables["objects"] == []
    assert variables["sub_labels"] == []
    assert variables["label"] == "Unknown"
    assert variables["review_id"] == "unknown"
    assert variables["start_time"] == 0
    assert variables["notification_tag"] == "frigate_unknown"


def test_camera_variables_preserve_valid_payload_behavior():
    payload = {
        "after": {
            "camera": "front_drive",
            "id": "review-123",
            "start_time": 1717420000,
            "data": {
                "detections": ["event-123"],
                "objects": ["person", "car"],
                "sub_labels": ["delivery"],
            },
        }
    }

    variables = evaluate_camera_variables(payload)

    assert variables["camera"] == "front_drive"
    assert variables["detections"] == ["event-123"]
    assert variables["id"] == "event-123"
    assert variables["objects"] == ["person", "car"]
    assert variables["sub_labels"] == ["delivery"]
    assert variables["label"] == "Person, Car"
    assert variables["review_id"] == "review-123"
    assert variables["start_time"] == 1717420000
    assert variables["notification_tag"] == "frigate_event-123"
