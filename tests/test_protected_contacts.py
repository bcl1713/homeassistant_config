import ast
from pathlib import Path

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "protected_contacts.yaml"


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def sensor_by_name(package, name):
    for block in package["template"]:
        for sensor in block.get("sensor", []):
            if sensor["name"] == name:
                return sensor
    raise AssertionError(f"sensor {name!r} not found")


def inventory_contacts(package):
    inventory = sensor_by_name(package, "Protected Contact Inventory")
    rendered = Environment().from_string(inventory["attributes"]["contacts"]).render()
    return ast.literal_eval(rendered)


def render(template, contacts, state_map):
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
    return environment.from_string(template).render().strip()


def all_closed(contacts):
    return {contact["entity_id"]: "off" for contact in contacts}


def test_protected_contact_inventory_is_the_single_canonical_roster():
    package = load_package()
    inventory = sensor_by_name(package, "Protected Contact Inventory")
    contacts = inventory_contacts(package)

    assert inventory["unique_id"] == "protected_contact_inventory"
    assert len(contacts) == 11
    assert inventory["attributes"]["window_count"] == 8
    assert inventory["attributes"]["security_boundary_door_count"] == 3
    assert {contact["category"] for contact in contacts} == {
        "window",
        "security_boundary_door",
    }
    assert {contact["entity_id"] for contact in contacts} == {
        "binary_sensor.kitchen_kitchen_porch_window",
        "binary_sensor.kitchen_kitchen_sink_window",
        "binary_sensor.living_room_living_room_window",
        "binary_sensor.master_bedroom_brian_s_window",
        "binary_sensor.master_bedroom_hester_s_window",
        "binary_sensor.porter_s_room_porter_s_window",
        "binary_sensor.towner_s_room_towner_s_window",
        "binary_sensor.office_window",
        "binary_sensor.entry_front_door",
        "binary_sensor.kitchen_back_door",
        "binary_sensor.garage_garage_interior_door",
    }


def test_protected_contact_summary_reports_all_closed_without_false_open_or_health_status():
    package = load_package()
    summary = sensor_by_name(package, "Protected Contact Summary")
    contacts = inventory_contacts(package)
    states = all_closed(contacts)

    assert render(summary["state"], contacts, states) == "0"
    assert render(summary["attributes"]["status"], contacts, states) == "closed"
    assert render(summary["attributes"]["open_contacts"], contacts, states) == "None"
    assert render(summary["attributes"]["open_windows"], contacts, states) == "None"
    assert (
        render(summary["attributes"]["open_security_boundary_doors"], contacts, states)
        == "None"
    )
    assert render(summary["attributes"]["unavailable_count"], contacts, states) == "0"
    assert render(summary["attributes"]["unknown_count"], contacts, states) == "0"


def test_protected_contact_summary_reports_one_open_contact_with_name_and_category():
    package = load_package()
    summary = sensor_by_name(package, "Protected Contact Summary")
    contacts = inventory_contacts(package)
    states = all_closed(contacts)
    states["binary_sensor.office_window"] = "on"

    assert render(summary["state"], contacts, states) == "1"
    assert render(summary["attributes"]["status"], contacts, states) == "open"
    assert render(summary["attributes"]["open_contacts"], contacts, states) == "Office Window"
    assert render(summary["attributes"]["open_windows"], contacts, states) == "Office Window"
    assert (
        render(summary["attributes"]["open_security_boundary_doors"], contacts, states)
        == "None"
    )


def test_protected_contact_summary_distinguishes_unavailable_and_unknown_from_closed():
    package = load_package()
    summary = sensor_by_name(package, "Protected Contact Summary")
    contacts = inventory_contacts(package)
    states = all_closed(contacts)
    states["binary_sensor.kitchen_kitchen_sink_window"] = "unavailable"
    states["binary_sensor.kitchen_back_door"] = "unknown"

    assert render(summary["state"], contacts, states) == "0"
    assert render(summary["attributes"]["status"], contacts, states) == "degraded"
    assert render(summary["attributes"]["unavailable_count"], contacts, states) == "1"
    assert (
        render(summary["attributes"]["unavailable_contacts"], contacts, states)
        == "Kitchen Sink Window"
    )
    assert render(summary["attributes"]["unknown_count"], contacts, states) == "1"
    assert (
        render(summary["attributes"]["unknown_contacts"], contacts, states)
        == "Back Door"
    )


def test_protected_contact_summary_is_read_only_and_references_the_inventory_seam():
    package = load_package()
    summary = sensor_by_name(package, "Protected Contact Summary")

    assert "automation" not in package
    assert "script" not in package
    assert summary["attributes"]["inventory_entity"] == "sensor.protected_contact_inventory"
    assert "sensor.protected_contact_inventory" in summary["state"]
    assert "sensor.protected_contact_inventory" in str(summary["attributes"])
    assert "binary_sensor.office_window" not in str(summary)
