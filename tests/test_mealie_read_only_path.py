from pathlib import Path

import yaml
from jinja2 import Template
from jinja2.nativetypes import NativeEnvironment


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


def action_by_service(actions, service):
    for action in actions:
        if action.get("action") == service:
            return action
        for choice in action.get("choose", []):
            found = action_by_service(choice.get("sequence", []), service)
            if found:
                return found
        found = action_by_service(action.get("default", []), service)
        if found:
            return found
    return None


def variable_value(actions, name, matching_text=None):
    for action in actions:
        variables = action.get("variables", {})
        value = variables.get(name)
        if value is not None and (
            matching_text is None or matching_text in str(value)
        ):
            return value
        for choice in action.get("choose", []):
            found = variable_value(choice.get("sequence", []), name, matching_text)
            if found is not None:
                return found
        found = variable_value(action.get("default", []), name, matching_text)
        if found is not None:
            return found
    return None


def test_mealie_adapter_uses_bounded_get_requests_and_one_explicit_secret_backed_write_command():
    package = load_yaml(PACKAGE)
    commands = package["rest_command"]

    assert set(commands) == {
        "mealie_get_today",
        "mealie_get_range",
        "mealie_get_recipe",
        "mealie_mark_made",
    }
    for name in ("mealie_get_today", "mealie_get_range", "mealie_get_recipe"):
        command = commands[name]
        assert command["method"] == "GET"
        assert command["timeout"] == 15
        assert command["headers"]["Authorization"] == "!secret mealie_authorization_header"
        assert command["headers"]["Accept"] == "application/json"

    write = commands["mealie_mark_made"]
    assert write["url"] == "!secret mealie_mark_made_url"
    assert write["method"] == "PATCH"
    assert write["timeout"] == 15
    assert write["headers"] == {
        "Authorization": "!secret mealie_authorization_header",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    assert write["payload"] == '{"timestamp":"{{ mealie_made_timestamp }}"}'

    assert commands["mealie_get_today"]["url"] == "!secret mealie_today_url"
    assert commands["mealie_get_range"]["url"] == "!secret mealie_range_url"
    assert commands["mealie_get_recipe"]["url"] == "!secret mealie_recipe_url"

    package_text = PACKAGE.read_text()
    assert "POST" not in package_text
    assert "PUT" not in package_text
    assert "DELETE" not in package_text
    assert "Bearer " not in package_text
    assert "mealie_authorization_header" in package_text
    assert "rest_command.mealie_mark_made" not in automation_by_alias(
        package, "Refresh Meal Prep from Mealie"
    )["action"].__str__()


def test_dynamic_rest_command_urls_receive_explicit_nonempty_service_data():
    package = load_yaml(PACKAGE)
    refresh = automation_by_alias(package, "Refresh Meal Prep from Mealie")

    range_action = action_by_service(refresh["action"], "rest_command.mealie_get_range")
    recipe_action = action_by_service(refresh["action"], "rest_command.mealie_get_recipe")
    assert range_action is not None
    assert recipe_action is not None

    range_data = {
        key: Template(value).render(
            mealie_range_start="2026-07-24", mealie_range_end="2026-07-31"
        )
        for key, value in range_action["data"].items()
    }
    recipe_data = {
        key: Template(value).render(mealie_recipe_id="selected-recipe-id")
        for key, value in recipe_action["data"].items()
    }

    # These stand in for operator-owned secrets. Explicit service data is the
    # supported template context when rest_command renders those URLs.
    rendered_range_url = Template(
        "https://mealie.example/api/households/mealplans?start_date={{ mealie_range_start }}&end_date={{ mealie_range_end }}"
    ).render(**range_data)
    rendered_recipe_url = Template(
        "https://mealie.example/api/recipes/{{ mealie_recipe_id }}"
    ).render(**recipe_data)

    assert range_data == {
        "mealie_range_start": "2026-07-24",
        "mealie_range_end": "2026-07-31",
    }
    assert recipe_data == {"mealie_recipe_id": "selected-recipe-id"}
    assert "start_date=2026-07-24" in rendered_range_url
    assert "end_date=2026-07-31" in rendered_range_url
    assert rendered_recipe_url.endswith("/selected-recipe-id")


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


def test_unauthorized_and_422_responses_fail_closed_via_transport_path():
    package = load_yaml(PACKAGE)
    refresh = automation_by_alias(package, "Refresh Meal Prep from Mealie")
    transport_guard = next(
        choice["conditions"]
        for action in refresh["action"]
        for choice in action.get("choose", [])
        if choice["conditions"] == "{{ mealie_plan_status != 200 }}"
    )

    for status in (401, 422):
        assert Template(transport_guard).render(mealie_plan_status=status) == "True"

    text = PACKAGE.read_text()
    assert "Mealie request failed (HTTP {{ mealie_plan_status }})" in text
    assert "malformed Mealie meal-plan payload" in text
    assert "malformed Mealie recipe payload" in text


def test_range_pagination_envelope_normalizes_only_its_items_list():
    package = load_yaml(PACKAGE)
    refresh = automation_by_alias(package, "Refresh Meal Prep from Mealie")
    range_payload_template = variable_value(
        refresh["action"], "mealie_plan_payload", "mealie_range_response.content"
    )
    assert isinstance(range_payload_template, str)
    malformed_guard = next(
        choice["conditions"]
        for action in refresh["action"]
        for choice in action.get("choose", [])
        if choice["conditions"]
        == "{{ mealie_plan_payload is not sequence or mealie_plan_payload is string or mealie_plan_payload is mapping }}"
    )
    envelope = {
        "items": [{"recipeId": "selected-recipe-id", "entryType": "dinner"}],
        "next": None,
        "page": 1,
        "per_page": 10,
        "previous": None,
        "total": 1,
        "total_pages": 1,
    }

    normalized = NativeEnvironment().from_string(range_payload_template).render(
        mealie_range_response={"content": envelope}
    )

    assert normalized == envelope["items"]
    assert Template(malformed_guard).render(mealie_plan_payload=normalized) == "False"


def test_range_pagination_envelope_malformed_variants_fail_closed_or_follow_no_meal_path():
    package = load_yaml(PACKAGE)
    refresh = automation_by_alias(package, "Refresh Meal Prep from Mealie")
    range_payload_template = variable_value(
        refresh["action"], "mealie_plan_payload", "mealie_range_response.content"
    )
    assert isinstance(range_payload_template, str)
    malformed_guard = next(
        choice["conditions"]
        for action in refresh["action"]
        for choice in action.get("choose", [])
        if choice["conditions"]
        == "{{ mealie_plan_payload is not sequence or mealie_plan_payload is string or mealie_plan_payload is mapping }}"
    )
    normalizer = NativeEnvironment().from_string(range_payload_template)

    for payload in ({}, {"items": "not-a-list"}, {"items": {"recipeId": "x"}}):
        normalized = normalizer.render(mealie_range_response={"content": payload})
        assert Template(malformed_guard).render(mealie_plan_payload=normalized) == "True"

    assert normalizer.render(mealie_range_response={"content": {"items": []}}) == []


def test_normalized_recipe_output_is_bounded_and_populates_helper_seams():
    meal_prep = load_yaml(MEAL_PREP)
    helpers = meal_prep["input_text"]
    text = PACKAGE.read_text()

    assert helpers["meal_prep_recipe_summary"]["max"] == 160
    assert helpers["meal_prep_ingredient_context"]["max"] == 255
    for helper in (
        "meal_prep_recipe_prep_time",
        "meal_prep_recipe_cook_time",
        "meal_prep_recipe_total_time",
    ):
        assert helpers[helper]["max"] == 40
        assert f"input_text.{helper}" in text
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
