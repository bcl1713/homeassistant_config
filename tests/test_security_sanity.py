from pathlib import Path

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
SECURITY = ROOT / "packages" / "security_sanity.yaml"
ROUTINES = ROOT / "packages" / "routines.yaml"
PRESENCE = ROOT / "packages" / "presence.yaml"
SECURITY_DOOR_CONTACTS = {
    "binary_sensor.entry_front_door": "Front Door",
    "binary_sensor.kitchen_back_door": "Back Door",
    "binary_sensor.garage_garage_interior_door": "Garage Interior Door",
}


def load_yaml(path):
    return yaml.safe_load(path.read_text())


def automation_by_id(package, automation_id):
    for automation in package["automation"]:
        if automation["id"] == automation_id:
            return automation
    raise AssertionError(f"automation {automation_id!r} not found")


def script_step_services(script):
    return [step.get("service") for step in script["sequence"] if isinstance(step, dict)]


def render_template(template, state_map, **variables):
    environment = Environment()
    environment.globals["is_state"] = lambda entity_id, state: (
        state_map.get(entity_id) == state
    )
    return environment.from_string(template).render(**variables).strip()


def test_secure_house_away_context_waits_for_front_door_to_settle_before_reading_state():
    package = load_yaml(SECURITY)
    script = package["script"]["secure_house_sanity_check"]
    settle_step = script["sequence"][0]
    variables_step = script["sequence"][1]

    assert "choose" in settle_step
    settle_choice = settle_step["choose"][0]
    assert settle_choice["conditions"] == [
        {
            "condition": "template",
            "value_template": (
                "{{ (check_context | default('night')) == 'away' and\n"
                "   not is_state('lock.front_door', 'locked') }}\n"
            ),
        }
    ]
    assert settle_choice["sequence"] == [
        {
            "wait_template": "{{ is_state('lock.front_door', 'locked') }}",
            "timeout": "00:00:45",
            "continue_on_timeout": True,
        }
    ]
    assert "variables" in variables_step
    assert variables_step["variables"]["front_door_state"] == (
        "{{ states('lock.front_door') }}"
    )


def test_secure_house_sanity_script_aggregates_and_stays_notify_first():
    package = load_yaml(SECURITY)
    script = package["script"]["secure_house_sanity_check"]
    text = SECURITY.read_text()

    assert script["mode"] == "parallel"
    assert "check_context" in script["fields"]
    assert "lock.front_door" in text
    assert "cover.garage_door" in text
    assert "alarm_control_panel.home_alarm" in text
    assert "security_door_contacts" in text
    assert "open_security_contact_count" in text
    assert "findings.items | join" in text
    assert "mismatch_count | int > 0" in text
    assert "1 if front_door_state != 'locked' else 0" in text
    assert "continue_on_timeout: true" in text
    assert "Guest Mode is on" in text

    services = script_step_services(script)
    assert "notify.all_mobile_devices" in text
    assert "lock.lock" not in services
    assert "cover.close_cover" not in services
    assert "alarm_control_panel.alarm_arm_night" not in services
    assert "alarm_control_panel.alarm_arm_away" not in services


def test_secure_house_sanity_lists_open_security_contacts_in_one_findings_summary():
    package = load_yaml(SECURITY)
    variables = package["script"]["secure_house_sanity_check"]["sequence"][1][
        "variables"
    ]
    secure_states = {
        "binary_sensor.entry_front_door": "off",
        "binary_sensor.kitchen_back_door": "off",
        "binary_sensor.garage_garage_interior_door": "off",
    }
    open_contact_states = {
        **secure_states,
        "binary_sensor.kitchen_back_door": "on",
        "binary_sensor.garage_garage_interior_door": "on",
    }
    finding_variables = {
        "front_door_state": "locked",
        "garage_door_state": "closed",
        "alarm_state": "armed_night",
        "expected_alarm_state": "armed_night",
        "expected_alarm_label": "night",
        "security_door_contacts": SECURITY_DOOR_CONTACTS,
    }

    assert variables["security_door_contacts"] == SECURITY_DOOR_CONTACTS
    assert render_template(
        variables["open_security_contact_count"], secure_states, **finding_variables
    ) == "0"
    assert render_template(
        variables["security_findings"], secure_states, **finding_variables
    ) == ""
    assert render_template(
        variables["open_security_contact_count"],
        open_contact_states,
        **finding_variables,
    ) == "2"
    findings = render_template(
        variables["security_findings"], open_contact_states, **finding_variables
    )
    assert "Back Door contact is open." in findings
    assert "Garage Interior Door contact is open." in findings
    assert "Front Door contact is open." not in findings
    assert render_template(
        variables["mismatch_count"],
        open_contact_states,
        open_security_contact_count=2,
        **finding_variables,
    ) == "2"


def test_secure_house_actions_require_explicit_notification_events():
    package = load_yaml(SECURITY)
    automation = automation_by_id(package, "secure_house_notification_actions")
    text = SECURITY.read_text()

    assert {trigger["event_data"]["action"] for trigger in automation["trigger"]} == {
        "secure_house_lock_front_door",
        "secure_house_close_garage",
        "secure_house_arm_night",
        "secure_house_arm_away",
        "secure_house_acknowledge",
    }
    assert "binary_sensor.garage_door_obstruction" in text
    assert "lock.lock" in text
    assert "cover.close_cover" in text
    assert "alarm_control_panel.alarm_arm_night" in text
    assert "alarm_control_panel.alarm_arm_away" in text


def test_good_night_invokes_secure_house_check_after_routine_sequence():
    package = load_yaml(ROUTINES)
    sequence = package["script"]["good_night"]["sequence"]

    assert sequence[-2] == {"delay": "00:00:15"}
    assert sequence[-1] == {
        "service": "script.secure_house_sanity_check",
        "data": {"check_context": "night"},
    }


def test_everyone_left_invokes_same_secure_house_check():
    package = load_yaml(PRESENCE)
    automation = automation_by_id(package, "presence_everyone_left")

    assert automation["condition"] == [
        {
            "condition": "state",
            "entity_id": "input_boolean.mode_guest",
            "state": "off",
        }
    ]
    assert automation["action"][-2] == {"delay": "00:00:15"}
    assert automation["action"][-1] == {
        "service": "script.secure_house_sanity_check",
        "data": {"check_context": "away"},
    }
