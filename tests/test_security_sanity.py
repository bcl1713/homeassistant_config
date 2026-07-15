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


class State:
    def __init__(self, entity_id, state, name, device_class=None):
        self.entity_id = entity_id
        self.state = state
        self.name = name
        self.attributes = {}
        if device_class is not None:
            self.attributes["device_class"] = device_class


class States:
    def __init__(self, state_map, binary_sensors):
        self.state_map = state_map
        self.binary_sensor = binary_sensors

    def __call__(self, entity_id):
        return self.state_map.get(entity_id, "unknown")


def render_template(template, state_map, *, binary_sensors=None, **variables):
    states = States(state_map, binary_sensors or [])
    environment = Environment(trim_blocks=True, lstrip_blocks=True)
    environment.globals.update(
        states=states,
        is_state=lambda entity_id, expected: states(entity_id) == expected,
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
    assert "open_window_contact_count" in text
    assert "attributes.device_class', 'eq', 'window'" in text
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
        open_window_contact_count=0,
        **finding_variables,
    ) == "2"


def test_secure_house_sanity_reports_open_windows_by_friendly_name():
    package = load_yaml(SECURITY)
    variables = package["script"]["secure_house_sanity_check"]["sequence"][1][
        "variables"
    ]
    state_map = {
        **{entity_id: "off" for entity_id in SECURITY_DOOR_CONTACTS},
    }
    binary_sensors = [
        State("binary_sensor.kitchen_window", "on", "Kitchen Window", "window"),
        State("binary_sensor.back_door", "on", "Back Door", "door"),
        State("binary_sensor.bedroom_window", "off", "Bedroom Window", "window"),
    ]
    finding_variables = {
        "front_door_state": "locked",
        "garage_door_state": "closed",
        "alarm_state": "armed_night",
        "expected_alarm_state": "armed_night",
        "expected_alarm_label": "night",
        "security_door_contacts": SECURITY_DOOR_CONTACTS,
    }

    open_window_contact_count = render_template(
        variables["open_window_contact_count"],
        state_map,
        binary_sensors=binary_sensors,
    )
    findings = render_template(
        variables["security_findings"],
        state_map,
        binary_sensors=binary_sensors,
        **finding_variables,
    )

    assert open_window_contact_count == "1"
    assert findings == "Kitchen Window is open."
    assert render_template(
        variables["mismatch_count"],
        state_map,
        open_security_contact_count=0,
        open_window_contact_count=open_window_contact_count,
        **finding_variables,
    ) == "1"


def test_secure_house_sanity_has_no_findings_when_all_items_are_secure():
    package = load_yaml(SECURITY)
    variables = package["script"]["secure_house_sanity_check"]["sequence"][1][
        "variables"
    ]
    state_map = {
        **{entity_id: "off" for entity_id in SECURITY_DOOR_CONTACTS},
    }
    closed_window = [
        State("binary_sensor.kitchen_window", "off", "Kitchen Window", "window")
    ]
    finding_variables = {
        "front_door_state": "locked",
        "garage_door_state": "closed",
        "alarm_state": "armed_away",
        "expected_alarm_state": "armed_away",
        "expected_alarm_label": "away",
        "security_door_contacts": SECURITY_DOOR_CONTACTS,
    }

    open_window_contact_count = render_template(
        variables["open_window_contact_count"],
        state_map,
        binary_sensors=closed_window,
    )
    findings = render_template(
        variables["security_findings"],
        state_map,
        binary_sensors=closed_window,
        **finding_variables,
    )

    assert open_window_contact_count == "0"
    assert findings == ""
    assert render_template(
        variables["mismatch_count"],
        state_map,
        open_security_contact_count=0,
        open_window_contact_count=open_window_contact_count,
        **finding_variables,
    ) == "0"


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
