import ast
from pathlib import Path

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "device_connectivity.yaml"
PROTECTED_CONTACTS = ROOT / "packages" / "protected_contacts.yaml"


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def sensor_by_name(package, sensor_name):
    for template_block in package["template"]:
        for sensor in template_block.get("sensor", []):
            if sensor["name"] == sensor_name:
                return sensor
    raise AssertionError(f"sensor {sensor_name!r} not found")


def inventory_contacts():
    package = yaml.safe_load(PROTECTED_CONTACTS.read_text())
    inventory = sensor_by_name(package, "Protected Contact Inventory")
    rendered = Environment().from_string(inventory["attributes"]["contacts"]).render()
    return ast.literal_eval(rendered)


def render(template, state_map, contacts=None):
    environment = Environment(trim_blocks=True, lstrip_blocks=True)
    environment.globals.update(
        states=lambda entity_id: state_map.get(entity_id, "unknown"),
        state_attr=lambda entity_id, attribute: (
            contacts
            if (entity_id, attribute)
            == ("sensor.protected_contact_inventory", "contacts")
            else None
        ),
    )
    return environment.from_string(template).render()


def test_critical_contact_sensor_consumes_canonical_inventory_for_all_contact_health_states():
    package = load_package()
    sensor = sensor_by_name(package, "Device Connectivity Critical Contact Problems")
    contacts = inventory_contacts()
    state_map = {contact["entity_id"]: "off" for contact in contacts}
    state_map.update(
        {
            "binary_sensor.kitchen_back_door": "unavailable",
            "binary_sensor.porter_s_room_porter_s_window": "unknown",
            "binary_sensor.towner_s_room_towner_s_window": "unavailable",
        }
    )

    assert len(contacts) == 11
    assert "state_attr('sensor.protected_contact_inventory', 'contacts')" in sensor["state"]
    assert "state_attr('sensor.protected_contact_inventory', 'contacts')" in sensor["attributes"]["problem_contacts"]
    assert "binary_sensor." not in sensor["state"]
    assert "binary_sensor." not in sensor["attributes"]["problem_contacts"]
    assert render(sensor["state"], state_map, contacts).strip() == "3"
    assert render(sensor["attributes"]["problem_contacts"], state_map, contacts).strip() == (
        "Porter's Window (unknown), Towner's Window (unavailable), Back Door (unavailable)"
    )


def test_critical_contact_sensor_has_an_empty_inventory_fallback():
    package = load_package()
    sensor = sensor_by_name(package, "Device Connectivity Critical Contact Problems")

    assert render(sensor["state"], {}, None).strip() == "0"
    assert render(sensor["attributes"]["problem_contacts"], {}, None).strip() == "None"


def test_healthy_critical_contacts_clear_the_problem_sensor_and_notification():
    package = load_package()
    sensor = sensor_by_name(package, "Device Connectivity Critical Contact Problems")
    alert = next(item for item in package["automation"] if item["id"] == "device_connectivity_issue_alert")
    reset = next(
        item for item in package["automation"] if item["id"] == "device_connectivity_issue_alert_reset"
    )
    contacts = inventory_contacts()
    recovered_states = {contact["entity_id"]: "off" for contact in contacts}

    assert render(sensor["state"], recovered_states, contacts).strip() == "0"
    assert render(sensor["attributes"]["problem_contacts"], recovered_states, contacts).strip() == "None"
    assert alert["trigger"][0]["for"] == {"minutes": 15}
    assert "critical_contact_count" in alert["action"][1]["variables"]
    assert "critical_contact_summary" in alert["action"][1]["variables"]
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
    assert (
        "sensor.device_connectivity_critical_door_contact_problems"
        in summary["attributes"]["critical_contact_problems"]
    )
