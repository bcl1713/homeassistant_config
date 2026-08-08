from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIGURATION_YAML = ROOT / "configuration.yaml"
PACKAGES_DIRECTORY = ROOT / "packages"
VALIDATION_WORKFLOW = ROOT / ".github" / "workflows" / "validate.yaml"


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


def test_validation_workflow_has_non_secret_placeholders_for_package_secrets():
    package_secret_references = {
        match.group(1)
        for package in PACKAGES_DIRECTORY.glob("*.yaml")
        for match in re.finditer(r"!secret\s+([a-z0-9_]+)", package.read_text())
    }
    workflow_text = VALIDATION_WORKFLOW.read_text()
    fixture_text = workflow_text.split("cat > secrets.yaml <<'EOF'\n", 1)[1].split("\n          EOF", 1)[0]
    fixture_secret_names = set(re.findall(r"^\s*([a-z0-9_]+):", fixture_text, re.MULTILINE))

    assert package_secret_references == fixture_secret_names
    assert "mealie_today_url" in fixture_secret_names
    assert "continue-on-error" not in workflow_text
