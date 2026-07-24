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


def test_kitchen_prep_dashboard_presents_only_real_read_only_state_seams():
    dashboard = load_dashboard()
    cards = dashboard["views"][0]["cards"]
    refs = set(entity_refs(cards))

    assert dashboard["title"] == "Kitchen Prep"
    assert dashboard["views"][0]["path"] == "kitchen-prep"
    assert dashboard["views"][0]["badges"] == []
    assert refs == {
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
    assert "service:" not in dashboard_text
    assert "script." not in dashboard_text


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
    assert "state_attr('sensor.meal_prep_source_status', 'reason')" in status

    assert "## {{ states('sensor.meal_prep_current_step') }}" in current_step
    assert "No instruction is shown" in current_step
    assert "states('sensor.meal_prep_next_step')" in next_step
    assert "Prep time, cook time, servings, and concise ingredient context" in recipe_context
    assert "deferred to the read-only Mealie normalizer in #209" in recipe_context
    assert "full recipe" not in DASHBOARD.read_text().lower()


def test_kitchen_prep_dashboard_defers_controls_to_the_owner_card_without_dangling_services():
    dashboard_text = DASHBOARD.read_text()

    assert "#210 owns the stable Start, Done, Skip, Snooze, and Finish script" in dashboard_text
    assert "Do not add buttons until that card supplies real services." in dashboard_text
    assert "type: button" not in dashboard_text
    assert "tap_action:" not in dashboard_text
