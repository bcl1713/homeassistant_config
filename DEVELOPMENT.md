# Home Assistant Development Guide

This guide documents the safe development workflow for this Home Assistant configuration repository. The repository is treated as source-controlled infrastructure: make changes in Git, validate locally where possible, open a pull request to `dev`, and let the reviewer/integration gate decide when changes advance.

## Development workflow

### 1. Plan the change

- Check existing GitHub issues before starting new work.
- Create or update an issue for non-trivial changes.
- Identify the owning package, dashboard, script, blueprint, or root include before editing.
- Keep live Home Assistant side effects out of normal development unless a task explicitly authorizes them.

### 2. Branch from `dev`

Always start ordinary work from the latest `dev` branch:

```bash
git fetch origin
git checkout dev
git pull origin dev
```

Create a focused branch:

```bash
git checkout -b feature/descriptive-name
git checkout -b fix/descriptive-name
git checkout -b docs/descriptive-name
git checkout -b chore/descriptive-name
```

Target pull requests at `dev`. Do not merge automation or configuration changes directly to `main`; `main` is reserved for the established release gate.

### 3. Understand repository structure

`configuration.yaml` intentionally stays small and delegates most behavior to includes:

- `homeassistant.packages: !include_dir_named packages` loads feature packages.
- `automation: !include_dir_merge_list automation` loads standalone automations.
- `input_boolean: !include_dir_merge_named input_boolean` loads helper modes.
- `scene: !include scenes.yaml` loads scenes.
- `recorder: !include recorder.yaml` and `logbook: !include logbook.yaml` keep history/logging configuration separate.

Feature packages live in `packages/`. Shared package-level contracts live in `packages/shared_infrastructure.yaml`, currently including `notify.all_mobile_devices` and YAML Lovelace dashboard registration.

Dedicated operator dashboards live in `dashboards/` and are registered by shared infrastructure. ESPHome device YAML lives in `esphome/`. Utility scripts live in `scripts/`.

### 4. Package design standards

- Keep related helpers, templates, scripts, and automations in the owning feature package.
- Do not add unrelated feature logic directly to `configuration.yaml`.
- Put shared notifier/dashboard/root-level contracts in `shared_infrastructure.yaml` rather than redefining them in feature packages.
- Split complex domains by responsibility. The climate subsystem is the current example:
  - `climate_schedule.yaml` owns baseline setpoints and schedule application.
  - `climate_occupancy.yaml` owns away, return-home, and pre-arrival behavior.
  - `climate_extreme_heat.yaml` owns hot-day/pre-cool overlay behavior.
  - `climate_diagnostics.yaml` owns read-only dashboard diagnostics.
- Update `packages/README.md` whenever an active `packages/*.yaml` file is added, renamed, removed, enabled, or disabled.

### 5. YAML and automation standards

- Use 2-space YAML indentation.
- Keep lines reasonably short and readable.
- Prefer descriptive entity, helper, script, and automation names.
- Add comments for complex templates or safety-sensitive behavior.
- Use helper entities for user-tunable thresholds and enable flags.
- Choose Home Assistant automation modes deliberately (`single`, `restart`, `queued`, `parallel`).
- Add timeouts to waits where an automation could otherwise hang.
- Avoid broad refactors while making a focused behavior or documentation change.

### 6. Dashboards and operator views

- Put dedicated YAML dashboards under `dashboards/`.
- Register YAML dashboards from `packages/shared_infrastructure.yaml`.
- Keep dashboard-facing diagnostic sensors in the package that owns the data.
- Document new operator views in `README.md` and any feature-specific package documentation.

Current YAML dashboards:

- `dashboards/climate_control.yaml` for climate operations and diagnostics.
- `dashboards/window_ventilation.yaml` for advisory ventilation recommendations.

### 7. Notifications

Use `notify.all_mobile_devices` for household-wide mobile fan-out unless the package has a deliberate narrower target. The shared notify group is defined in `packages/shared_infrastructure.yaml` so feature packages can consume a stable contract.

Notification-heavy packages should clearly document enable flags, thresholds, action identifiers, and reset behavior inside the package or package README entry.

### 8. Testing and validation

Before considering a change complete:

1. Review the diff for accidental entity renames, formatting-only churn, unrelated edits, and secrets.
2. Parse or lint changed YAML where practical.
3. Run repository tests when they cover the changed area.
4. For documentation-only changes, verify package/documentation inventories by script or manual checklist.
5. Run a Home Assistant config check only when the task or environment provides a known-safe local command. Do not assume access to the live instance is safe.
6. Do not reload or restart the live Home Assistant host as part of routine development unless explicitly authorized.

The GitHub workflow in `.github/workflows/validate.yaml` prepares dummy credential material and runs a Home Assistant Core configuration check using `frenck/action-home-assistant`.

### 9. Commit guidelines

Use conventional commits:

```text
<type>(<scope>): <description>

[optional body]
```

Common types:

- `feat`: new automation or user-facing behavior
- `fix`: bug fix
- `docs`: documentation changes
- `test`: tests or validation fixtures
- `refactor`: restructuring without intended behavior change
- `chore`: maintenance
- `ci`: workflow or validation changes

Examples:

```text
feat(security): add camera motion notifications
fix(climate): preserve thermostat band gap
docs(packages): refresh active package inventory
```

### 10. Pull requests and integration

1. Stage only the files needed for the change.
2. Commit with a conventional commit message.
3. Push the branch.
4. Open a pull request against `dev`:

   ```bash
   gh pr create --base dev --title "docs: refresh repository documentation" --body "Summary..."
   ```

5. Include a summary, validation performed, linked issue, and documentation impact.
6. Wait for review and address feedback.
7. Do not self-merge to `main`.

## Troubleshooting notes

- If validation fails, read the failing workflow/test output before editing.
- Check sibling packages for the same pattern before fixing a repeated issue in only one place.
- If a change depends on live runtime state, record the assumption and avoid making live changes without explicit authorization.
- If a package rename/addition changes operator expectations, update README/package/dashboard documentation in the same PR.
