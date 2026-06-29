from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIGURATION_YAML = ROOT / "configuration.yaml"
SHARED_INFRASTRUCTURE_YAML = ROOT / "packages" / "shared_infrastructure.yaml"
PACKAGES_DIR = ROOT / "packages"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def test_shared_infrastructure_owns_root_level_package_contracts():
    config_text = CONFIGURATION_YAML.read_text()
    shared = load_yaml(SHARED_INFRASTRUCTURE_YAML)

    assert "packages: !include_dir_named packages" in config_text
    assert "\nlovelace:" not in config_text
    assert "\nnotify:" not in config_text

    dashboards = shared["lovelace"]["dashboards"]
    assert dashboards["window-ventilation"]["filename"] == "dashboards/window_ventilation.yaml"
    assert dashboards["climate-control"]["filename"] == "dashboards/climate_control.yaml"

    notify_groups = shared["notify"]
    assert notify_groups == [
        {
            "platform": "group",
            "name": "all_mobile_devices",
            "services": [
                {"service": "mobile_app_brian_phone"},
                {"service": "mobile_app_hester_phone"},
            ],
        }
    ]


def test_shared_mobile_notify_consumers_have_documented_contract():
    shared_text = SHARED_INFRASTRUCTURE_YAML.read_text()
    consumers = sorted(
        package.relative_to(ROOT).as_posix()
        for package in PACKAGES_DIR.glob("*.yaml")
        if package != SHARED_INFRASTRUCTURE_YAML
        and "notify.all_mobile_devices" in package.read_text()
    )

    assert consumers
    for consumer in consumers:
        assert f"# - {consumer}" in shared_text
