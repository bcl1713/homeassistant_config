from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SHARED_INFRASTRUCTURE = ROOT / "packages" / "shared_infrastructure.yaml"
DASHBOARD = ROOT / "dashboards" / "kitchen_prep.yaml"


def load_dashboard():
    return yaml.safe_load(DASHBOARD.read_text())


def load_shared_infrastructure():
    return yaml.safe_load(SHARED_INFRASTRUCTURE.read_text())


def iter_cards(cards):
    for card in cards:
        yield card
        if card.get("card"):
            yield from iter_cards([card["card"]])
        if card.get("cards"):
            yield from iter_cards(card["cards"])


def entity_refs(cards):
    refs = []
    for card in iter_cards(cards):
        if "entity" in card:
            refs.append(card["entity"])
        for row in card.get("entities", []):
            if isinstance(row, str):
                refs.append(row)
            elif isinstance(row, dict) and "entity" in row:
                refs.append(row["entity"])
    return refs


def markdown_by_title(cards, title):
    return next(card["content"] for card in cards if card.get("title") == title)


def test_kitchen_prep_dashboard_is_yaml_managed_and_hidden():
    dashboard_config = load_shared_infrastructure()["lovelace"]["dashboards"][
        "kitchen-prep"
    ]

    assert dashboard_config == {
        "mode": "yaml",
        "title": "Kitchen Prep",
        "icon": "mdi:chef-hat",
        "show_in_sidebar": False,
        "filename": "dashboards/kitchen_prep.yaml",
    }


def test_kitchen_prep_dashboard_presents_only_real_state_and_control_seams():
    dashboard = load_dashboard()
    cards = dashboard["views"][0]["cards"]
    refs = set(entity_refs(cards))

    assert dashboard["title"] == "Kitchen Prep"
    assert dashboard["views"][0]["path"] == "kitchen-prep"
    assert dashboard["views"][0]["badges"] == []
    assert refs == {
        "input_select.meal_prep_automatic_lead_time_policy",
        "sensor.meal_prep_automatic_start_time",
        "sensor.meal_prep_source_status",
        "sensor.meal_prep_session_state",
        "sensor.meal_prep_target_time",
    }

    dashboard_text = DASHBOARD.read_text()
    for entity_id in (
        "sensor.meal_prep_meal",
        "sensor.meal_prep_meal_type",
        "sensor.meal_prep_current_step",
        "sensor.meal_prep_next_step",
        "sensor.meal_prep_recipe_url",
        "sensor.meal_prep_recipe_reference",
    ):
        assert entity_id in dashboard_text

    assert "media_player.kitchen_display" in dashboard_text
    assert "media_player.display_kitchen" not in dashboard_text
    for script_id in (
        "script.meal_prep_start_preparation",
        "script.meal_prep_complete_current_step",
        "script.meal_prep_skip_current_step",
        "script.meal_prep_snooze_preparation",
        "script.meal_prep_finish_for_today",
        "script.meal_prep_show_dashboard",
        "script.meal_prep_clear_session",
    ):
        assert script_id in dashboard_text


def test_kitchen_prep_dashboard_is_concise_and_fail_closed_when_source_is_unavailable():
    cards = load_dashboard()["views"][0]["cards"]
    status = markdown_by_title(cards, "Meal status")
    current_step = markdown_by_title(cards, "Current step")
    next_step = markdown_by_title(cards, "Next step")
    recipe_context = markdown_by_title(cards, "Recipe context")

    assert "{% if source_status != 'ready' %}" in status
    assert "{% elif meal in ['none', 'unavailable', 'unknown'] %}" in status
    assert "No meal planned" in status
    assert "## {{ meal }}" in status
    for content in (current_step, next_step, recipe_context):
        assert "states('sensor.meal_prep_source_status') != 'ready'" in content
        assert "meal in ['none', 'unavailable', 'unknown']" in content

    assert "Meal source unavailable" in status
    assert "fresh, coherent snapshot" in status
    assert "states('sensor.meal_prep_meal')" in status
    assert "states('sensor.meal_prep_meal_type')" in status
    assert "states('sensor.meal_prep_target_time')" in status
    assert "states('input_select.meal_prep_automatic_lead_time_policy')" in status
    assert "states('sensor.meal_prep_automatic_start_time')" in status
    assert "duration_source" in status
    assert "state_attr('sensor.meal_prep_source_status', 'reason')" in status

    assert "## {{ states('sensor.meal_prep_current_step') }}" in current_step
    assert "No instruction is shown" in current_step
    assert "states('sensor.meal_prep_next_step')" in next_step
    assert "Timing / servings:" in recipe_context
    assert "Ingredients:" in recipe_context
    assert "sensor.meal_prep_recipe_summary" in recipe_context
    assert "sensor.meal_prep_ingredient_context" in recipe_context
    assert "full recipe" not in DASHBOARD.read_text().lower()


def test_kitchen_prep_dashboard_keeps_diagnostics_after_preparation_controls():
    cards = load_dashboard()["views"][0]["cards"]

    assert [card["title"] for card in cards] == [
        "Meal status",
        "Current step",
        "Next step",
        "Recipe context",
        "Preparation controls",
        "Source details",
    ]


def test_kitchen_prep_dashboard_buttons_call_only_real_manual_script_services():
    cards = load_dashboard()["views"][0]["cards"]
    control_card = next(card for card in cards if card.get("title") == "Preparation controls")
    buttons = control_card["cards"]

    assert control_card["type"] == "grid"
    assert [button["name"] for button in buttons] == [
        "Start",
        "Done",
        "Skip",
        "Snooze 30 min",
        "Finish today",
        "Show display",
        "Clear session",
    ]
    assert [button["tap_action"] for button in buttons] == [
        {"action": "perform-action", "perform_action": "script.meal_prep_start_preparation"},
        {"action": "perform-action", "perform_action": "script.meal_prep_complete_current_step"},
        {"action": "perform-action", "perform_action": "script.meal_prep_skip_current_step"},
        {
            "action": "perform-action",
            "perform_action": "script.meal_prep_snooze_preparation",
            "data": {"snooze_minutes": 30},
        },
        {"action": "perform-action", "perform_action": "script.meal_prep_finish_for_today"},
        {"action": "perform-action", "perform_action": "script.meal_prep_show_dashboard"},
        {"action": "perform-action", "perform_action": "script.meal_prep_clear_session"},
    ]
