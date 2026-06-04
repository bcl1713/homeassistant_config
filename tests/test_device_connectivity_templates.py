from datetime import datetime, timedelta
from pathlib import Path

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
DEVICE_HEALTH_YAML = ROOT / "packages" / "device_health.yaml"
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


def device_health_sensor(sensor_name: str):
    template_blocks = load_yaml(DEVICE_HEALTH_YAML)["template"]
    for block in template_blocks:
        for sensor in block.get("sensor", []):
            if sensor["name"] == sensor_name:
                return sensor
    raise AssertionError(f"device health sensor {sensor_name!r} not found")


def render_template(template_string: str, *, entities=None, state_map=None):
    env = Environment(trim_blocks=True, lstrip_blocks=True)
    states = StatesProxy(entities or [], state_map=state_map)

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
        state_attr=lambda entity_id, attr: None,
    )
    return env.from_string(template_string).render()


def test_device_connectivity_zwave_problem_sensor_counts_non_healthy_nodes():
    sensor = device_health_sensor("Device Connectivity Z-Wave Problems")
    rendered = render_template(
        sensor["state"],
        entities=[
            Entity("sensor.kitchen_node_status", "alive", "Kitchen Node Status"),
            Entity("sensor.office_node_status", "dead", "Office Node Status"),
            Entity("sensor.bedroom_node_status", "unknown", "Bedroom Node Status"),
            Entity("sensor.hallway_last_seen", FIXED_NOW.isoformat(), "Hallway Last Seen"),
        ],
    )

    assert rendered.strip() == "2"


def test_device_connectivity_stale_last_seen_sensor_ignores_invalid_values_and_flags_old_devices():
    sensor = device_health_sensor("Device Connectivity Stale Last Seen")
    rendered = render_template(
        sensor["state"],
        entities=[
            Entity(
                "sensor.front_door_last_seen",
                (FIXED_NOW - timedelta(hours=30)).isoformat(),
                "Front Door Last Seen",
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


def test_device_connectivity_integration_problem_sensor_counts_unavailable_update_entities_only():
    sensor = device_health_sensor("Device Connectivity Integration Problems")
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
