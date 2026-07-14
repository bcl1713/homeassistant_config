from pathlib import Path

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "device_connectivity.yaml"
CRITICAL_DOOR_CONTACTS = {
    "binary_sensor.entry_front_door": "Front Door Contact",
    "binary_sensor.kitchen_back_door": "Back Door Contact",
    "binary_sensor.garage_garage_interior_door": "Garage Interior Door Contact",
}


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def sensor_by_name(package, sensor_name):
    for template_block in package["template"]:
        for sensor in template_block.get("sensor", []):
            if sensor["name"] == sensor_name:
                return sensor
    raise AssertionError(f"sensor {sensor_name!r} not found")


def render(template, state_map):
    environment = Environment(trim_blocks=True, lstrip_blocks=True)
    environment.globals["states"] = lambda entity_id: state_map.get(entity_id, "unknown")
    return environment.from_string(template).render()


def test_critical_door_contact_sensor_flags_only_unavailable_or_unknown_contacts():
    package = load_package()
    sensor = sensor_by_name(package, "Device Connectivity Critical Door Contact Problems")
    state_map = {
        "binary_sensor.entry_front_door": "off",
        "binary_sensor.kitchen_back_door": "unavailable",
        "binary_sensor.garage_garage_interior_door": "unknown",
    }

    assert all(entity_id in sensor["state"] for entity_id in CRITICAL_DOOR_CONTACTS)
    assert render(sensor["state"], state_map).strip() == "2"
    assert render(sensor["attributes"]["problem_contacts"], state_map).strip() == (
        "Back Door Contact (unavailable), Garage Interior Door Contact (unknown)"
    )


def test_door_contact_recovery_clears_the_problem_sensor_and_notification():
    package = load_package()
    sensor = sensor_by_name(package, "Device Connectivity Critical Door Contact Problems")
    alert = next(item for item in package["automation"] if item["id"] == "device_connectivity_issue_alert")
    reset = next(
        item for item in package["automation"] if item["id"] == "device_connectivity_issue_alert_reset"
    )
    recovered_states = {entity_id: "off" for entity_id in CRITICAL_DOOR_CONTACTS}

    assert render(sensor["state"], recovered_states).strip() == "0"
    assert render(sensor["attributes"]["problem_contacts"], recovered_states).strip() == "None"
    assert alert["trigger"][0]["for"] == {"minutes": 15}
    assert "door_contact_count" in alert["action"][1]["variables"]
    assert "door_contact_summary" in alert["action"][1]["variables"]
    assert alert["action"][2]["data"]["data"]["tag"] == "device-connectivity-alert"
    assert reset["action"][-1] == {
        "service": "notify.all_mobile_devices",
        "data": {"message": "clear_notification", "data": {"tag": "device-connectivity-alert"}},
    }


def test_connectivity_summary_consumes_critical_door_contact_problem_count():
    package = load_package()
    summary = sensor_by_name(package, "Device Connectivity Summary")

    assert "sensor.device_connectivity_critical_door_contact_problems" in summary["state"]
    assert (
        "sensor.device_connectivity_critical_door_contact_problems"
        in summary["attributes"]["critical_door_contact_problems"]
    )
