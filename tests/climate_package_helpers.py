from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CLIMATE_PACKAGES = sorted((ROOT / "packages").glob("climate_*.yaml"))
CLIMATE_PACKAGE_NAMES = {path.name for path in CLIMATE_PACKAGES}


def merge_package(base, incoming):
    for key, value in (incoming or {}).items():
        if isinstance(value, dict):
            base.setdefault(key, {})
            merge_package(base[key], value)
        elif isinstance(value, list):
            base.setdefault(key, [])
            base[key].extend(value)
        else:
            base[key] = value
    return base


def load_climate_packages():
    merged = {}
    for path in CLIMATE_PACKAGES:
        merge_package(merged, yaml.safe_load(path.read_text()))
    return merged


def climate_package_text():
    return "\n".join(path.read_text() for path in CLIMATE_PACKAGES)
