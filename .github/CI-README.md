# Home Assistant Configuration CI

This directory contains GitHub Actions configuration for repository validation.

## Validation workflow

The active workflow is `.github/workflows/validate.yaml` and is named `Check`. It runs on pushes and pull requests.

The current job is:

1. **Home Assistant Core Configuration Check**
   - Checks out the repository.
   - Creates a dummy `SERVICE_ACCOUNT.json` with the fields required by `configuration.yaml`.
   - Creates `.storage/` for Home Assistant runtime expectations.
   - Runs `frenck/action-home-assistant@v1.4.1` with `version: stable`.

The workflow currently sets `continue-on-error: true` on the Home Assistant check step, so review the logs even when GitHub reports the job as non-blocking.

## Local validation

For configuration changes, prefer safe static checks first. If Docker and the required local context are available, a Home Assistant-style check can be run with:

```bash
docker run --rm -v "$(pwd):/config" homeassistant/home-assistant:stable hass -c /config --script check_config
```

For documentation-only changes, a package inventory check and Markdown review is usually the relevant validation.

## Secrets and generated files

The workflow uses dummy credential material only. Do not commit real Home Assistant secrets, `.storage/`, database files, generated exports, or service account credentials.

## Troubleshooting

If validation fails:

1. Read the workflow logs for the exact Home Assistant error.
2. Check changed YAML indentation, entity IDs, service names, and template syntax.
3. Confirm any newly referenced include files exist in the repository.
4. Confirm no live-only credential or runtime file was accidentally required by the change.
