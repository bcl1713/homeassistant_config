from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIGURATION_YAML = ROOT / "configuration.yaml"


def test_legacy_http_configuration_is_commented_and_ui_migration_is_documented():
    config_text = CONFIGURATION_YAML.read_text()
    root = yaml.compose(config_text)
    top_level_keys = [key.value for key, _ in root.value]

    assert "http" not in top_level_keys
    assert "google_assistant" in top_level_keys
    assert "# Legacy HTTP configuration migrated to Settings -> System -> Network." in config_text
    assert "# http:" in config_text
    assert "#   use_x_forwarded_for: true" in config_text
    assert "#   trusted_proxies:" in config_text
    assert "#     Interim issue #93 fix: trust only the current server-VLAN CIDR until" in config_text
    assert "#     Cloudflare tunnel traffic is bound to a single stable proxy IP." in config_text
    assert "#     - 10.10.50.0/24" in config_text
