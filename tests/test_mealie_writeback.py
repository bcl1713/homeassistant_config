from pathlib import Path

import yaml
from jinja2 import Environment
from jinja2.nativetypes import NativeEnvironment


ROOT = Path(__file__).resolve().parents[1]
MEAL_PREP = ROOT / "packages" / "meal_prep.yaml"
MEALIE = ROOT / "packages" / "mealie_read_only.yaml"
DASHBOARD = ROOT / "dashboards" / "kitchen_prep.yaml"
PACKAGE_README = ROOT / "packages" / "README.md"


VALID_RECIPE_ID = "42b5c097-3900-4d27-a0d2-832cb3c3dc36"
IDENTITY = f"2026-07-24|{VALID_RECIPE_ID}"
TIMESTAMP = "2026-07-24T18:30:00+00:00"


def load_yaml(path):
    class SecretLoader(yaml.SafeLoader):
        pass

    SecretLoader.add_constructor(
        "!secret", lambda loader, node: f"!secret {loader.construct_scalar(node)}"
    )
    return yaml.load(path.read_text(), Loader=SecretLoader)


def script_services(node):
    services = []

    if isinstance(node, dict):
        if "action" in node:
            services.append(node["action"])
        for value in node.values():
            services.extend(script_services(value))
    elif isinstance(node, list):
        for item in node:
            services.extend(script_services(item))
    return services


def condition_templates(node):
    templates = []

    if isinstance(node, dict):
        if "conditions" in node:
            templates.append(node["conditions"])
        for value in node.values():
            templates.extend(condition_templates(value))
    elif isinstance(node, list):
        for item in node:
            templates.extend(condition_templates(item))
    return templates


def sequence_for_condition(node, condition):
    if isinstance(node, dict):
        for choice in node.get("choose", []):
            if choice.get("conditions") == condition:
                return choice["sequence"]
        for value in node.values():
            found = sequence_for_condition(value, condition)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = sequence_for_condition(item, condition)
            if found is not None:
                return found
    return None


def set_values(sequence):
    return [
        action["data"]["value"]
        for action in sequence
        if action.get("action") == "input_text.set_value"
    ]


def render(template, **context):
    environment = Environment(trim_blocks=True, lstrip_blocks=True)
    environment.globals["is_state"] = context.pop("is_state")
    environment.globals["states"] = context.pop("states")
    return environment.from_string(template).render(**context).strip()


def test_writeback_is_disabled_by_default_and_finish_today_stays_local_only():
    package = load_yaml(MEAL_PREP)
    script = package["script"]["meal_prep_mark_made_in_mealie"]
    finish = package["script"]["meal_prep_finish_for_today"]

    assert "initial" not in package["input_boolean"]["meal_prep_mealie_writeback_enabled"]
    assert script["mode"] == "single"
    assert script["fields"]["confirm"]["required"] is True
    assert "rest_command" not in str(finish["sequence"])
    assert "mealie_mark_made" not in str(finish["sequence"])

    disabled_condition = next(
        condition
        for condition in condition_templates(script["sequence"])
        if "meal_prep_mealie_writeback_enabled" in condition
    )
    assert render(
        disabled_condition,
        is_state=lambda entity_id, state: entity_id.endswith("writeback_enabled")
        and state == "on"
        and False,
        states=lambda _: "",
    ) == "True"
    assert set_values(sequence_for_condition(script["sequence"], disabled_condition)) == [
        "disabled",
        "Mealie write-back is disabled",
    ]


def test_writeback_uses_verified_patch_contract_only_from_the_explicit_script():
    mealie = load_yaml(MEALIE)
    script = load_yaml(MEAL_PREP)["script"]["meal_prep_mark_made_in_mealie"]
    command = mealie["rest_command"]["mealie_mark_made"]

    assert command["method"] == "PATCH"
    assert command["url"] == "!secret mealie_mark_made_url"
    assert command["payload"] == '{"timestamp":"{{ mealie_made_timestamp }}"}'
    assert command["headers"]["Content-Type"] == "application/json"
    assert script_services(script["sequence"]).count("rest_command.mealie_mark_made") == 1
    assert "rest_command.mealie_mark_made" not in str(
        next(
            automation
            for automation in mealie["automation"]
            if automation["alias"] == "Refresh Meal Prep from Mealie"
        )["action"]
    )


def test_valid_success_requires_matching_recipe_response_and_records_only_bounded_state():
    package = load_yaml(MEAL_PREP)
    script = package["script"]["meal_prep_mark_made_in_mealie"]
    success_condition = next(
        condition
        for condition in condition_templates(script["sequence"])
        if "mealie_write_status == 200" in condition
    )
    environment = NativeEnvironment(trim_blocks=True, lstrip_blocks=True)
    rendered = environment.from_string(success_condition).render(
        mealie_write_status=200,
        mealie_write_content={"id": VALID_RECIPE_ID},
        recipe_reference=VALID_RECIPE_ID,
    )
    wrong_recipe = environment.from_string(success_condition).render(
        mealie_write_status=200,
        mealie_write_content={"id": "00000000-0000-4000-8000-000000000000"},
        recipe_reference=VALID_RECIPE_ID,
    )

    assert rendered is True
    assert wrong_recipe is False
    assert set_values(sequence_for_condition(script["sequence"], success_condition)) == [
        "{{ meal_prep_identity }}",
        "success",
        "Marked made in Mealie",
    ]
    assert "mealie_write_content" not in str(package["input_text"])
    assert "mealie_mark_made_url" not in str(package["input_text"])


def test_retry_reuses_stable_pending_identity_and_timestamp_before_the_patch():
    script = load_yaml(MEAL_PREP)["script"]["meal_prep_mark_made_in_mealie"]
    text = str(script["sequence"])
    services = script_services(script["sequence"])

    assert "meal_prep_mealie_write_pending_key" in text
    assert "meal_prep_mealie_write_pending_timestamp" in text
    assert "mealie_made_timestamp" in text
    assert "states('input_text.meal_prep_mealie_write_pending_key') == meal_prep_identity" in text
    assert services.index("rest_command.mealie_mark_made") > services.index(
        "input_text.set_value"
    )


def test_duplicate_and_failure_paths_fail_closed_without_marking_success():
    script = load_yaml(MEAL_PREP)["script"]["meal_prep_mark_made_in_mealie"]
    conditions = condition_templates(script["sequence"])

    expected = {
        "{{ states('input_text.meal_prep_mealie_marked_key') == meal_prep_identity }}": (
            "duplicate",
            "This recipe is already marked made for today",
        ),
        "{{ mealie_write_status in [401, 403] }}": (
            "unauthorized",
            "Mealie write-back was not authorized",
        ),
        "{{ mealie_write_status == 409 }}": (
            "duplicate",
            "Mealie rejected the write as a duplicate",
        ),
        "{{ mealie_write_status in [404, 405, 501] }}": (
            "unsupported",
            "Mealie write-back endpoint is unavailable",
        ),
        "{{ mealie_write_status in [408, 504] }}": (
            "timeout",
            "Mealie write-back timed out; retry is safe",
        ),
        "{{ mealie_write_status == 0 }}": (
            "unavailable",
            "Mealie write-back was unavailable; retry is safe",
        ),
    }

    for condition, values in expected.items():
        assert condition in conditions
        assert tuple(set_values(sequence_for_condition(script["sequence"], condition))) == values

    assert "failed" in str(script["sequence"])
    assert "Mealie write-back response was malformed or unsuccessful" in str(script["sequence"])
    assert "mealie_write_status == 200" in str(script["sequence"])


def test_unconfirmed_or_malformed_requests_cannot_reach_the_patch_action():
    script = load_yaml(MEAL_PREP)["script"]["meal_prep_mark_made_in_mealie"]
    conditions = condition_templates(script["sequence"])

    unconfirmed = "{{ confirm | default(false) | bool == false }}"
    malformed = next(
        condition for condition in conditions if "regex_match" in condition
    )
    assert set_values(sequence_for_condition(script["sequence"], unconfirmed)) == [
        "unconfirmed",
        "Mealie write-back was not confirmed",
    ]
    assert "[1-5]" in malformed
    assert "sensor.meal_prep_source_status" in malformed
    assert "fresh linked recipe" in str(sequence_for_condition(script["sequence"], malformed))


def test_dashboard_requires_confirmation_and_documents_the_opt_in_and_disable_path():
    dashboard = yaml.safe_load(DASHBOARD.read_text())
    buttons = next(
        card["cards"]
        for card in dashboard["views"][0]["cards"]
        if card.get("title") == "Preparation controls"
    )
    write_button = next(button for button in buttons if button["name"] == "Mark made in Mealie")
    docs = PACKAGE_README.read_text()

    assert write_button["tap_action"] == {
        "action": "perform-action",
        "perform_action": "script.meal_prep_mark_made_in_mealie",
        "data": {"confirm": True},
        "confirmation": {
            "text": "Set this linked recipe's Last made timestamp in Mealie? Finish today stays local-only."
        },
    }
    assert "input_boolean.meal_prep_mealie_writeback_enabled" in docs
    assert "PATCH /api/recipes/{slug}/last-made" in docs
    assert "To disable the feature immediately" in docs
