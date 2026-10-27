"""Resolved consumer fingerprints from base 94af9d2 (only fake bucket removed).

Real YAML parsing resolves every alias, covering all nested security conditions,
contact maps, triggers, actions and defaults, not just selected anchor values.
"""
import hashlib
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
BASE_CONSUMERS = {
    "device_batteries": "06ba1a3be706e0f02e146a6d68cac67e2107626f9fc5c730a749c306c0d25eb7",
    "weather": "2e2132711becbd71908043fa8b3b3b4619498dbaa033dabdd54e2065cea898d6",
    "garage_door_monitoring": "e99e73f4d12397914935833f1964c58bf2f7d282fb79413f7c9c72a3fc7a9863",
    "security_door_alerts": "33e06b088b1310bb8c32249859c5e8e89388342711e2b6e841b46d971a101917",
    "exterior_door_monitoring": "95bf61e899476be5a7ba660ca2097b57914725566e34cb25f1da08024ca61a35",
    "trash_recycling_reminder": "6d87faec2e3ab9023c26503681c36a0ca527f156d8f7e991c59a281473534a80",
    "air_quality": "70f9f86a8f0e7c1d8958033e59e1a93219c590c38a32a4d0a8f0f69bc0169ad1",
}


@pytest.mark.parametrize("name,expected", BASE_CONSUMERS.items())
def test_no_fictional_customization_and_complete_consumer_equivalence(name, expected):
    package = yaml.safe_load((ROOT / "packages" / f"{name}.yaml").read_text())
    assert "package.node_anchors" not in package.get("homeassistant", {}).get("customize", {})
    actual = hashlib.sha256(json.dumps(package, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    assert actual == expected
