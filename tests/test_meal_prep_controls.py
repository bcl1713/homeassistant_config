import re
from pathlib import Path

import yaml
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "meal_prep.yaml"
MEALIE = ROOT / "packages" / "mealie_read_only.yaml"


def load_yaml(path):
    class HomeAssistantLoader(yaml.SafeLoader):
        pass

    HomeAssistantLoader.add_constructor(
        "!secret", lambda loader, node: f"!secret {loader.construct_scalar(node)}"
    )
    return yaml.load(path.read_text(), Loader=HomeAssistantLoader)


def load_package():
    return load_yaml(PACKAGE)


def script_services(script):
    services = []

    def walk(node):
        if isinstance(node, dict):
            if "action" in node:
                services.append(node["action"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(script["sequence"])
    return services


def condition_templates(script):
    return [
        item["value_template"]
        for item in script["sequence"]
        if item.get("condition") == "template"
    ]


def render_recipe_guard(script, recipe_reference):
    variables = script["sequence"][0]["variables"]
    guard = condition_templates(script)[0]
    environment = Environment(trim_blocks=True, lstrip_blocks=True)
    environment.filters["regex_replace"] = lambda value, find, replace: re.sub(
        find, replace, value
    )
    environment.globals["states"] = lambda entity_id: {
        "sensor.meal_prep_recipe_reference": recipe_reference
    }.get(entity_id, "unknown")

    normalized_reference = environment.from_string(variables["recipe_reference"]).render()
    return environment.from_string(guard).render(
        recipe_reference=normalized_reference
    ).strip()


def test_start_preparation_has_a_stable_manual_script_seam():
    script = load_package()["script"]["meal_prep_start_preparation"]

    assert script["alias"] == "Kitchen Prep: Start preparation"
    assert script["mode"] == "single"
    assert "sensor.meal_prep_source_status" in str(script["sequence"])
    assert "sensor.meal_prep_meal" in str(script["sequence"])
    assert "input_boolean.turn_on" in script_services(script)


def test_all_required_manual_control_scripts_are_stable_and_non_automatic():
    scripts = load_package()["script"]

    assert set(scripts) == {
        "meal_prep_start_preparation",
        "meal_prep_complete_current_step",
        "meal_prep_skip_current_step",
        "meal_prep_snooze_preparation",
        "meal_prep_finish_for_today",
        "meal_prep_mark_made_in_mealie",
        "meal_prep_show_dashboard",
        "meal_prep_clear_session",
    }
    assert all(script["mode"] == "single" for script in scripts.values())
    assert all("trigger" not in script for script in scripts.values())
    assert "automation" not in load_package()


def test_start_resets_only_new_session_identity_and_reactivation_keeps_progress():
    script = load_package()["script"]["meal_prep_start_preparation"]
    text = str(script["sequence"])

    assert "input_text.meal_prep_session_key" in text
    assert "input_boolean.meal_prep_done" in text
    assert "input_text.meal_prep_snooze_until" in text
    assert "input_text.meal_prep_last_skipped_step" in text
    assert "!= meal_prep_identity" in text
    assert script_services(script).count("input_boolean.turn_on") == 1


def test_state_changing_controls_reject_invalid_recipe_references_before_identity_or_mutation():
    scripts = load_package()["script"]
    state_changing_scripts = (
        "meal_prep_start_preparation",
        "meal_prep_complete_current_step",
        "meal_prep_skip_current_step",
        "meal_prep_snooze_preparation",
        "meal_prep_finish_for_today",
    )

    for script_name in state_changing_scripts:
        script = scripts[script_name]

        assert list(script["sequence"][0]["variables"]) == ["recipe_reference"]
        assert "meal_prep_identity" in script["sequence"][2]["variables"]
        assert render_recipe_guard(script, "recipe-123") == "True"
        for invalid_reference in (
            "",
            "none",
            "unknown",
            "unavailable",
            "recipe reference",  # ASCII space
            "recipe\t123",  # tab
            "recipe\n123",  # newline
            "recipe\r123",  # carriage return
            "recipe\u00a0123",  # non-breaking space
            "recipe|123",
        ):
            assert render_recipe_guard(script, invalid_reference) == "False", (
                script_name,
                invalid_reference,
            )


def test_done_advances_only_a_valid_active_matching_session_once():
    script = load_package()["script"]["meal_prep_complete_current_step"]
    condition = condition_templates(script)[1]
    actions = script_services(script)

    assert "sensor.meal_prep_source_status" in condition
    assert "input_boolean.meal_prep_active" in condition
    assert "input_text.meal_prep_session_key" in condition
    assert "next_step not in ['none', 'unavailable', 'unknown']" in condition
    assert actions == [
        "input_text.set_value",
        "input_text.set_value",
        "input_text.set_value",
    ]
    assert "value: \"{{ next_step }}\"" in PACKAGE.read_text()


def test_skip_records_a_bounded_deliberate_skip_without_claiming_completion():
    script = load_package()["script"]["meal_prep_skip_current_step"]
    actions = script_services(script)

    assert actions == [
        "input_text.set_value",
        "input_text.set_value",
        "input_text.set_value",
        "input_text.set_value",
    ]
    assert "input_text.meal_prep_last_skipped_step" in str(script["sequence"])
    assert "input_boolean.turn_on" not in actions
    assert "input_boolean.meal_prep_done" not in str(script["sequence"])


def test_snooze_is_bounded_and_persistent_until_its_future_timestamp_expires():
    script = load_package()["script"]["meal_prep_snooze_preparation"]

    assert script["fields"]["snooze_minutes"]["selector"]["number"] == {
        "min": 5,
        "max": 60,
        "step": 5,
        "unit_of_measurement": "min",
    }
    assert "bounded_snooze_minutes" in str(script["sequence"])
    assert "input_text.meal_prep_snooze_until" in str(script["sequence"])
    assert "timedelta(minutes=bounded_snooze_minutes | int)" in str(script["sequence"])


def test_finish_and_clear_are_local_persistent_state_transitions():
    scripts = load_package()["script"]
    finish_services = script_services(scripts["meal_prep_finish_for_today"])
    clear_services = script_services(scripts["meal_prep_clear_session"])

    assert finish_services == [
        "input_boolean.turn_off",
        "input_boolean.turn_on",
        "input_text.set_value",
        "input_text.set_value",
    ]
    assert clear_services == ["input_boolean.turn_off", "input_text.set_value"]
    clear_text = str(scripts["meal_prep_clear_session"]["sequence"])
    assert "input_text.meal_prep_session_key" in clear_text
    assert "input_text.meal_prep_last_skipped_step" in clear_text
    assert "input_text.meal_prep_meal_title" not in clear_text


def test_show_dashboard_targets_the_registered_kitchen_display_view():
    script = load_package()["script"]["meal_prep_show_dashboard"]

    wake_display = script["sequence"][0]
    assert wake_display["choose"][0]["conditions"] == [
        {
            "condition": "state",
            "entity_id": "media_player.kitchen_display",
            "state": "off",
        }
    ]
    wake_sequence = wake_display["choose"][0]["sequence"]
    assert wake_sequence[0] == {
        "action": "media_player.turn_on",
        "target": {"entity_id": "media_player.kitchen_display"},
    }
    assert wake_sequence[1] == {
        "wait_template": "{{ not is_state('media_player.kitchen_display', 'off') }}",
        "timeout": "00:00:15",
        "continue_on_timeout": False,
    }
    assert wake_sequence[2] == {"delay": "00:00:02"}

    assert script_services(script) == [
        "media_player.turn_on",
        "cast.show_lovelace_view",
    ]
    action = script["sequence"][-1]
    assert action["target"]["entity_id"] == "media_player.kitchen_display"
    assert action["data"] == {
        "dashboard_path": "kitchen-prep",
        "view_path": "kitchen-prep",
    }


def test_refresh_preserves_active_matching_manual_progress_but_can_seed_new_meals():
    mealie = load_yaml(MEALIE)
    text = MEALIE.read_text()

    assert "mealie_preserve_manual_progress" in text
    assert "input_text.meal_prep_session_key" in text
    assert "not mealie_preserve_manual_progress" in text
    assert "mealie_session_key" in text
    assert "input_text.meal_prep_current_step" in text
    assert "input_text.meal_prep_next_step" in text
    assert "input_text.meal_prep_remaining_steps" in text
    assert "values.parts | join('\\u001f')" in text
    assert "input_boolean.meal_prep_done" not in text
    assert "input_boolean.turn_on" not in str(mealie)


def test_advance_uses_a_bounded_persistent_remaining_step_queue():
    helpers = load_package()["input_text"]
    done = load_package()["script"]["meal_prep_complete_current_step"]

    assert helpers["meal_prep_remaining_steps"]["max"] == 255
    assert "input_text.meal_prep_remaining_steps" in str(done["sequence"])
    assert ".split('\\\\u001f')" in str(done["sequence"])


def test_new_persistent_helpers_have_no_initial_values():
    helpers = load_package()["input_text"]

    for helper in (
        "meal_prep_session_key",
        "meal_prep_last_skipped_step",
        "meal_prep_remaining_steps",
    ):
        assert helpers[helper]["max"] == 255
        assert "initial" not in helpers[helper]
