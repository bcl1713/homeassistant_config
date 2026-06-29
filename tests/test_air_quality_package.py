from pathlib import Path

from jinja2 import Environment
import yaml


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "air_quality.yaml"


class MockStates:
    def __init__(self, states):
        self._states = states

    def __call__(self, entity_id):
        return self._states.get(entity_id, "unknown")


def render_ha_template(template, states):
    env = Environment()
    env.globals.update(states=MockStates(states))
    return env.from_string(template).render().strip()


def load_package():
    return yaml.safe_load(PACKAGE.read_text())


def template_sensor(name):
    for block in load_package()["template"]:
        for sensor in block.get("sensor", []):
            if sensor["name"] == name:
                return sensor
    raise AssertionError(f"sensor {name!r} not found")


def test_air_quality_trend_uses_real_statistics_baselines():
    package = load_package()
    statistic_sensors = package["sensor"]

    assert {
        sensor["entity_id"] for sensor in statistic_sensors
    } == {
        "sensor.thermostat_air_quality_index",
        "sensor.thermostat_carbon_dioxide",
        "sensor.thermostat_vocs",
    }
    assert all(sensor["platform"] == "statistics" for sensor in statistic_sensors)
    assert all(sensor["state_characteristic"] == "mean" for sensor in statistic_sensors)
    assert all(sensor["max_age"] == {"hours": 1} for sensor in statistic_sensors)
    assert all(sensor["sampling_size"] == 240 for sensor in statistic_sensors)

    trend = template_sensor("Air Quality Trend")
    trend_text = trend["state"] + str(trend["attributes"])
    assert "sensor.air_quality_aqi_1h_mean" in trend_text
    assert "sensor.air_quality_co2_1h_mean" in trend_text
    assert "sensor.air_quality_voc_1h_mean" in trend_text
    assert "sensero.thermostat_vocs" not in trend_text
    assert "state_attr('sensor.air_quality_composite_status'" not in trend_text
    assert trend["attributes"]["comparison_basis"] == (
        "Current readings minus 1-hour statistics mean"
    )


def test_air_quality_trend_reports_worsening_from_statistics_mean():
    trend = template_sensor("Air Quality Trend")

    assert render_ha_template(
        trend["state"],
        {
            "sensor.thermostat_air_quality_index": "71",
            "sensor.thermostat_carbon_dioxide": "920",
            "sensor.thermostat_vocs": "330",
            "sensor.air_quality_aqi_1h_mean": "60",
            "sensor.air_quality_co2_1h_mean": "820",
            "sensor.air_quality_voc_1h_mean": "225",
        },
    ) == "worsening"


def test_air_quality_trend_reports_improving_from_statistics_mean():
    trend = template_sensor("Air Quality Trend")

    assert render_ha_template(
        trend["state"],
        {
            "sensor.thermostat_air_quality_index": "49",
            "sensor.thermostat_carbon_dioxide": "690",
            "sensor.thermostat_vocs": "175",
            "sensor.air_quality_aqi_1h_mean": "60",
            "sensor.air_quality_co2_1h_mean": "790",
            "sensor.air_quality_voc_1h_mean": "280",
        },
    ) == "improving"


def test_air_quality_trend_reports_stable_within_thresholds():
    trend = template_sensor("Air Quality Trend")

    assert render_ha_template(
        trend["state"],
        {
            "sensor.thermostat_air_quality_index": "59",
            "sensor.thermostat_carbon_dioxide": "889",
            "sensor.thermostat_vocs": "349",
            "sensor.air_quality_aqi_1h_mean": "60",
            "sensor.air_quality_co2_1h_mean": "790",
            "sensor.air_quality_voc_1h_mean": "250",
        },
    ) == "stable"
