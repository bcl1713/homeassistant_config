# Home Assistant Branching and Deployment Workflow

## Purpose

This repository does **not** have a separate Home Assistant staging environment. The live house is the only meaningful runtime, so the workflow should optimize for:

- safe changes,
- clear rollback points,
- honest branch semantics,
- and low process overhead.

The practical model is therefore:

- `dev` is the active trunk and normal deployment source,
- short-lived branches feed `dev`,
- deploys are tracked with tags,
- `main` is optional and should not be treated as the everyday source of truth.

## Branch Roles

### `dev`

Use `dev` as the default branch for ongoing work and routine live deployments.

`dev` should always be:

- valid enough to run `ha core check`,
- reviewed before merge when the change is non-trivial,
- and close to deployable.

### Short-lived working branches

Create branches from `dev` for changes that are risky, broad, or worth reviewing in isolation.

Recommended prefixes:

- `feature/...`
- `fix/...`
- `docs/...`
- `chore/...`

Examples:

- `feature/generic-prearrival-recovery`
- `fix/weather-forecast-refresh`
- `docs/deployment-workflow`

### `main`

`main` is optional.

If it is kept at all, it should mean **last explicitly blessed live baseline**, not “the place normal work merges.”

If `main` is not being actively promoted after successful live soak, do not rely on it for day-to-day branching or PR targeting.

## Default Change Flow

1. Start from the latest `dev`.
2. Create a focused branch for the change when the work is not trivial.
3. Make the change.
4. Run repo validation and any targeted tests.
5. Open a PR targeting `dev`.
6. Merge to `dev`.
7. Deploy `dev` to the live Home Assistant instance.
8. If the deploy is good, create a deploy tag on the deployed commit.

## When Direct Commits to `dev` Are Acceptable

Direct commits to `dev` are acceptable only for very small, low-risk changes such as:

- docs-only edits,
- comments,
- typo fixes,
- harmless dashboard polish,
- or mechanical cleanup with no behavior change.

If a change affects any of the following, use a branch and PR:

- presence,
- climate,
- security,
- alarms,
- notifications,
- automations with time/location triggers,
- or helpers/entities that other automations depend on.

## Validation Before Merge

Before merging to `dev`, prefer this order:

1. review the diff for accidental entity renames or YAML structure mistakes,
2. run repository tests relevant to the changed area,
3. run `ha core check` in a known-safe environment before a live restart,
4. confirm any UI/dashboard changes still reference valid entities.

A passing CI run is necessary but not magical. It only proves the specific checks you taught it to run, which is more than nothing and less than perfection.

## Live Deployment Procedure

For routine deployments, use this sequence on the Home Assistant host:

```bash
cd /config
git fetch origin --prune
git merge --ff-only origin/dev
ha core check
ha core restart
```

After restart, verify:

- Home Assistant Core is healthy,
- the expected entities/automations loaded,
- and the specific changed behavior is visible when practical.

## Deploy Tags

Every successful live deployment should get a tag on the deployed commit.

Recommended formats:

- `deploy-YYYY-MM-DD`
- `deploy-YYYY-MM-DD.N`
- `live-YYYY-MM-DD-feature-slug`

Examples:

- `deploy-2026-06-28`
- `deploy-2026-06-28.2`
- `live-2026-06-28-prearrival`

### Why tags matter

Tags provide:

- a clean rollback anchor,
- a human-readable live history,
- and a durable answer to “what commit is in the house right now?”

### Tagging example

```bash
git checkout dev
git pull origin dev
git tag -a deploy-2026-06-28 -m "Live Home Assistant deploy 2026-06-28"
git push origin deploy-2026-06-28
```

If the deploy came from a detached or remote-verified commit, tag that exact commit SHA instead of guessing.

## Rollback Procedure

If a deployment misbehaves:

1. identify the last known good deploy tag,
2. fast-forward is no longer the goal; check out the known good commit on `/config`,
3. run `ha core check`,
4. restart Home Assistant,
5. open a fix branch from current `dev` to correct the issue properly.

Example rollback shape:

```bash
cd /config
git fetch origin --tags --prune
git checkout <known-good-tag-or-sha>
ha core check
ha core restart
```

After emergency rollback, reconcile the repo deliberately rather than leaving the branch story to rot.

## Optional Role for `main`

If you want to keep `main`, use it only for one of these meanings:

### Option A: Last known good live baseline

After a successful deploy has soaked, fast-forward `main` to that commit.

This gives you:

- an easy “safe baseline” branch,
- simpler browsing for non-experimental state,
- and a branch-level rollback reference.

### Option B: Do not use `main`

If you are not going to maintain that promotion habit, leave `main` alone and rely on deploy tags instead.

That is cleaner than pretending `main` means something it plainly does not.

## Recommended Policy

For this repository today:

- **Use `dev` as the real trunk.**
- **Target PRs to `dev`.**
- **Use short-lived branches for risky work.**
- **Tag every successful live deployment.**
- **Treat `main` as optional until a real staging/promote model exists.**

## Quick Reference

### Start new work

```bash
git checkout dev
git pull origin dev
git checkout -b feature/descriptive-name
```

### Merge target

- open PRs against `dev`

### Deploy live

```bash
ssh root@<ha-host>
cd /config
git fetch origin --prune
git merge --ff-only origin/dev
ha core check
ha core restart
```

### Tag a good deploy

```bash
git tag -a deploy-YYYY-MM-DD -m "Live Home Assistant deploy"
git push origin deploy-YYYY-MM-DD
```
