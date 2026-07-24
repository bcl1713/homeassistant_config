from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "mealie_read_only.yaml"
MEAL_PREP = ROOT / "packages" / "meal_prep.yaml"
DASHBOARD = ROOT / "dashboards" / "kitchen_prep.yaml"
PACKAGE_README = ROOT / "packages" / "README.md"


def load_yaml(path):
    class SecretLoader(yaml.SafeLoader):
        pass

    SecretLoader.add_constructor(
        "!secret", lambda loader, node: f"!secret {loader.construct_scalar(node)}"
    )
    return yaml.load(path.read_text(), Loader=SecretLoader)


def automation_by_alias(package, alias):
    return next(item for item in package["automation"] if item["alias"] == alias)


def test_mealie_read_path_has_only_bounded_get_requests_with_secret_backed_wiring():
    package = load_yaml(PACKAGE)
    commands = package["rest_command"]

    assert set(commands) == {
        "mealie_get_today",
        "mealie_get_range",
        "mealie_get_recipe",
    }
    for command in commands.values():
        assert command["method"] == "GET"
        assert command["timeout"] == 15
        assert command["headers"]["Authorization"] == "!secret mealie_authorization_header"
        assert command["headers"]["Accept"] == "application/json"

    assert commands["mealie_get_today"]["url"] == "!secret mealie_today_url"
    assert commands["mealie_get_range"]["url"] == "!secret mealie_range_url"
    assert commands["mealie_get_recipe"]["url"] == "!secret mealie_recipe_url"

    package_text = PACKAGE.read_text()
    assert "POST" not in package_text
    assert "PUT" not in package_text
    assert "PATCH" not in package_text
    assert "DELETE" not in package_text
    assert "Bearer " not in package_text
    assert "mealie_authorization_header" in package_text


def test_refresh_uses_today_then_bounded_range_and_camel_case_fields_only():
    package = load_yaml(PACKAGE)
    refresh = automation_by_alias(package, "Refresh Meal Prep from Mealie")
    text = PACKAGE.read_text()

    assert refresh["mode"] == "single"
    assert {trigger["platform"] for trigger in refresh["trigger"]} == {
        "homeassistant",
        "time_pattern",
    }
    assert any(trigger.get("minutes") == "/15" for trigger in refresh["trigger"])
    assert "rest_command.mealie_get_today" in text
    assert "rest_command.mealie_get_range" in text
    assert "rest_command.mealie_get_recipe" in text
    assert "mealie_range_start" in text
    assert "mealie_range_end" in text
    for field in (
        "entryType",
        "recipeId",
        "prepTime",
        "cookTime",
        "totalTime",
        "recipeIngredient",
        "recipeInstructions",
    ):
        assert field in text
    # The adapter's local variables may use snake case, but source payload
    # access must remain the verified camelCase contract above.
    assert ".recipe_id" not in text
    assert ".entry_type" not in text
    assert ".prep_time" not in text
    assert ".recipe_ingredient" not in text


def test_refresh_has_explicit_idle_missing_link_transport_and_malformed_payload_paths():
    text = PACKAGE.read_text()

    for status, reason in (
        ("ready", "no meal planned"),
        ("unavailable", "meal plan entry has no recipeId"),
        ("unavailable", "Mealie request failed"),
        ("unavailable", "malformed Mealie recipe payload"),
    ):
        assert status in text
        assert reason in text

    # A fresh previous snapshot can be retained only with a visible cached reason;
    # otherwise failures must fail closed rather than look freshly fetched.
    assert "using fresh cached snapshot after Mealie request failure" in text
    assert "10800" in text
    assert "input_text.meal_prep_source_status" in text
    assert "input_datetime.meal_prep_source_updated_at" in text


def test_normalized_recipe_output_is_bounded_and_populates_helper_seams():
    meal_prep = load_yaml(MEAL_PREP)
    helpers = meal_prep["input_text"]
    text = PACKAGE.read_text()

    assert helpers["meal_prep_recipe_summary"]["max"] == 160
    assert helpers["meal_prep_ingredient_context"]["max"] == 255
    assert "input_text.meal_prep_recipe_summary" in text
    assert "input_text.meal_prep_ingredient_context" in text
    assert "[:6]" in text
    assert "truncate(255" in text
    assert "truncate(160" in text
    assert "steps[1]" in text

    for sensor in ("Meal Prep Recipe Summary", "Meal Prep Ingredient Context"):
        assert any(
            item.get("name") == sensor
            for block in meal_prep["template"]
            for item in block.get("sensor", [])
        )


def test_dashboard_and_docs_only_show_new_recipe_context_when_source_is_fresh():
    dashboard_text = DASHBOARD.read_text()
    docs = PACKAGE_README.read_text()

    assert "sensor.meal_prep_recipe_summary" in dashboard_text
    assert "sensor.meal_prep_ingredient_context" in dashboard_text
    assert "deferred to the read-only Mealie normalizer" not in dashboard_text
    assert "mealie_read_only.yaml" in docs
    assert "mealie_authorization_header" in docs
    assert "15-minute" in docs
    assert "fresh cached snapshot" in docs
