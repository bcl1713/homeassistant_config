from datetime import datetime, timedelta
from pathlib import Path
import re

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
DEVICE_BATTERIES_YAML = ROOT / "packages" / "device_batteries.yaml"
DEVICE_CONNECTIVITY_YAML = ROOT / "packages" / "device_connectivity.yaml"
FIXED_NOW = datetime(2026, 6, 4, 12, 0, 0)


class Entity:
    def __init__(self, entity_id: str, state, name: str | None = None, attributes=None):
        self.entity_id = entity_id
        self.state = state
        self.name = name or entity_id
        self.attributes = attributes or {}


class StatesProxy:
    def __init__(self, entities, state_map=None):
        self._entities = list(entities)
        self._state_map = state_map or {}

    def __call__(self, entity_id):
        return self._state_map.get(entity_id)

    def __iter__(self):
        return iter(self._entities)

    def __getattr__(self, domain):
        prefix = f"{domain}."
        return [entity for entity in self._entities if entity.entity_id.startswith(prefix)]


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def package_sensor(package_path: Path, sensor_name: str):
    template_blocks = load_yaml(package_path)["template"]
    for block in template_blocks:
        for sensor in block.get("sensor", []):
            if sensor["name"] == sensor_name:
                return sensor
    raise AssertionError(f"sensor {sensor_name!r} not found in {package_path}")


def device_battery_sensor(sensor_name: str):
    return package_sensor(DEVICE_BATTERIES_YAML, sensor_name)


def device_connectivity_sensor(sensor_name: str):
    return package_sensor(DEVICE_CONNECTIVITY_YAML, sensor_name)


def render_template(template_string: str, *, entities=None, state_map=None, attr_map=None):
    env = Environment(trim_blocks=True, lstrip_blocks=True)
    env.filters["regex_match"] = lambda value, pattern: re.match(pattern, str(value)) is not None
    states = StatesProxy(entities or [], state_map=state_map)
    attr_map = attr_map or {}

    def as_timestamp(value):
        if isinstance(value, datetime):
            return value.timestamp()
        if value in (None, "", "unknown", "unavailable"):
            raise ValueError(f"invalid timestamp source: {value!r}")
        return datetime.fromisoformat(str(value)).timestamp()

    env.globals.update(
        states=states,
        as_timestamp=as_timestamp,
        now=lambda: FIXED_NOW,
        state_attr=lambda entity_id, attr: attr_map.get((entity_id, attr)),
    )
    return env.from_string(template_string).render()


def test_device_connectivity_zwave_problem_sensor_counts_non_healthy_nodes():
    sensor = device_connectivity_sensor("Device Connectivity Z-Wave Problems")
    rendered = render_template(
        sensor["state"],
        entities=[
            Entity("sensor.kitchen_node_status", "alive", "Kitchen Node Status"),
            Entity("sensor.window_node_status", "asleep", "Window Node Status"),
            Entity("sensor.office_node_status", "dead", "Office Node Status"),
            Entity("sensor.bedroom_node_status", "unknown", "Bedroom Node Status"),
            Entity("sensor.hallway_last_seen", FIXED_NOW.isoformat(), "Hallway Last Seen"),
        ],
    )

    assert rendered.strip() == "2"


def test_device_connectivity_stale_last_seen_sensor_ignores_invalid_values_and_flags_old_devices():
    sensor = device_connectivity_sensor("Device Connectivity Stale Last Seen")
    rendered = render_template(
        sensor["state"],
        entities=[
            Entity(
                "sensor.kitchen_porch_window_last_seen",
                (FIXED_NOW - timedelta(hours=30)).isoformat(),
                "Kitchen Porch Window Last Seen",
            ),
            Entity(
                "sensor.office_last_seen",
                (FIXED_NOW - timedelta(hours=6)).isoformat(),
                "Office Last Seen",
            ),
            Entity("sensor.guest_room_last_seen", "unknown", "Guest Room Last Seen"),
            Entity("sensor.zwave_gateway_node_status", "alive", "Z-Wave Gateway Node Status"),
        ],
        state_map={"input_number.device_connectivity_last_seen_threshold_hours": "24"},
    )

    assert rendered.strip() == "1"
    assert (
        render_template(
            sensor["attributes"]["stale_devices"],
            entities=[
                Entity(
                    "sensor.kitchen_porch_window_last_seen",
                    (FIXED_NOW - timedelta(hours=30)).isoformat(),
                    "Kitchen Porch Window Last Seen",
                )
            ],
            state_map={"input_number.device_connectivity_last_seen_threshold_hours": "24"},
        ).strip()
        == "Kitchen Porch Window Last Seen (30.0h)"
    )


def test_device_connectivity_integration_problem_sensor_counts_unavailable_update_entities_only():
    sensor = device_connectivity_sensor("Device Connectivity Integration Problems")
    rendered = render_template(
        sensor["state"],
        entities=[
            Entity("update.home_assistant_core_update", "off", "Home Assistant Core Update"),
            Entity("update.z_wave_js_update", "unavailable", "Z-Wave JS Update"),
            Entity("update.matter_server_update", "unknown", "Matter Server Update"),
            Entity("sensor.random_last_seen", (FIXED_NOW - timedelta(hours=48)).isoformat(), "Random Last Seen"),
        ],
    )

    assert rendered.strip() == "2"


def test_battery_inventory_counts_attribute_and_device_class_batteries_once():
    sensor = device_battery_sensor("Real-time Battery Levels")
    entities = [
        Entity("binary_sensor.front_lock", "on", "Front Lock", {"battery_level": 14}),
        Entity("sensor.motion_battery", "27", "Motion Battery", {"device_class": "battery"}),
        Entity("sensor.battery_template_helper", "11", "Helper Battery", {"device_class": "battery"}),
        Entity("sensor.device_health_existing", "8", "Health Helper", {"device_class": "battery"}),
        Entity("sensor.temperature", "72", "Temperature"),
    ]
    state_map = {
        "input_number.device_health_critical_threshold": "15",
        "input_number.device_health_warning_threshold": "30",
        "input_number.device_health_low_threshold": "5",
    }

    assert render_template(sensor["state"], entities=entities, state_map=state_map).strip() == "2"
    assert render_template(
        sensor["attributes"]["critical_count"], entities=entities, state_map=state_map
    ).strip() == "1"
    assert render_template(
        sensor["attributes"]["warning_count"], entities=entities, state_map=state_map
    ).strip() == "1"
    assert render_template(
        sensor["attributes"]["critical_devices"], entities=entities, state_map=state_map
    ).strip() == "Front Lock (14%)"
    assert render_template(
        sensor["attributes"]["lowest_battery"], entities=entities, state_map=state_map
    ).strip() == "Front Lock: 14%"


def test_battery_summary_and_low_problem_sensor_consume_inventory_attributes():
    summary = device_battery_sensor("Device Health Battery Summary")
    low_problem = load_yaml(DEVICE_BATTERIES_YAML)["template"][1]["binary_sensor"][1]
    attr_map = {
        ("sensor.real_time_battery_levels", "critical_count"): "1",
        ("sensor.real_time_battery_levels", "warning_count"): "2",
        ("sensor.real_time_battery_levels", "lowest_battery"): "Front Lock: 14%",
        ("sensor.real_time_battery_levels", "low_count"): "1",
    }
    state_map = {"sensor.real_time_battery_levels": "4"}

    assert render_template(summary["state"], state_map=state_map, attr_map=attr_map).strip() == "4"
    assert render_template(
        summary["attributes"]["critical_count"], state_map=state_map, attr_map=attr_map
    ).strip() == "1"
    assert render_template(
        summary["attributes"]["warning_count"], state_map=state_map, attr_map=attr_map
    ).strip() == "2"
    assert render_template(low_problem["state"], state_map=state_map, attr_map=attr_map).strip() == "True"


def test_battery_alert_variables_do_not_rescan_all_entities():
    automations = load_yaml(DEVICE_BATTERIES_YAML)["automation"]
    low_alert = next(item for item in automations if item["id"] == "device_health_low_battery_alert")
    variables = low_alert["action"][0]["variables"]

    assert "state_attr('sensor.real_time_battery_levels', 'low_devices')" in variables["low_devices"]
    assert "state_attr('sensor.real_time_battery_levels', 'low_count')" in variables["device_count"]
    assert "for entity in states" not in variables["low_devices"]
    assert "for entity in states" not in variables["device_count"]
