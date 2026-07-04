# Contributing Guide

Thank you for helping improve this Home Assistant configuration. This repository is a live smart-home configuration, so changes should be small, reviewable, and validated before they are proposed for integration.

## Before starting

1. Read `DEVELOPMENT.md` for the detailed workflow and implementation standards.
2. Check existing GitHub issues at https://github.com/bcl1713/homeassistant_config/issues.
3. Comment on the issue you plan to work on, or create one if the change is not already tracked.
4. Work only in the repository checkout unless a task explicitly authorizes live Home Assistant changes.

## Branch and pull-request flow

The normal integration branch is `dev`. Do not branch from `main` for ordinary feature, fix, automation, or documentation work.

```bash
git fetch origin
git checkout dev
git pull origin dev
git checkout -b docs/short-description
```

Use focused branch names:

- `feature/descriptive-name` for new user-facing behavior.
- `fix/descriptive-name` for bug fixes.
- `docs/descriptive-name` for documentation-only changes.
- `chore/descriptive-name` for maintenance.

Open pull requests against `dev`:

```bash
gh pr create --base dev --title "docs: update package documentation" --body "Summary..."
```

`main` is reserved for the established release gate. Do not self-merge to `main`.

## Development standards

- Use the existing package structure instead of adding unrelated logic to `configuration.yaml`.
- Use 2-space YAML indentation.
- Follow existing entity, helper, script, and automation naming conventions.
- Add comments for complex templates or non-obvious automation logic.
- Keep package boundaries clear; cross-cutting notifier/dashboard contracts belong in `packages/shared_infrastructure.yaml`.
- Do not commit secrets, `.storage/`, generated exports, runtime databases, or credential files.

## Testing and validation

Before opening a pull request:

1. Review the diff for accidental entity renames, indentation mistakes, unrelated refactors, and secret leakage.
2. Run the most relevant local validation available for the change.
3. For documentation-only changes, verify package inventories and links by inspection or script.
4. For Home Assistant configuration changes, prefer safe static validation first. Run a full Home Assistant config check only when a known-safe local command/environment is available.
5. Do not reload or restart the live Home Assistant host unless the task explicitly authorizes it and includes the intended rollback/safety path.

## Commit messages

Use conventional commits:

```text
<type>(<scope>): <description>

[optional body]
```

Examples:

- `feat(security): add camera motion notifications`
- `fix(climate): preserve thermostat band gap`
- `docs(packages): refresh active package inventory`

Common types are `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, and `ci`.

## Pull request checklist

A good PR should include:

- A concise summary of what changed.
- The issue number, when applicable.
- Validation performed.
- Any live Home Assistant actions intentionally not performed.
- Documentation impact, especially when packages, dashboards, helpers, or operator workflows change.

Wait for the reviewer gate and the established integration flow before merge.
