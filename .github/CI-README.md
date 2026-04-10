# Home Assistant Configuration CI

This directory contains GitHub Actions workflows for continuous integration of the Home Assistant configuration.

## Validation Workflow

The `validate.yaml` workflow consists of three separate jobs:

1. **YAML Linting**: Checks the syntax and style of all YAML files in the repository
2. **Home Assistant Config Check**: Validates Home Assistant configuration using a container-based approach
3. **Notify Results**: Adds comments to pull requests indicating success or failure

The workflow runs on every push to `main` branch and on pull requests that change YAML files. You can also trigger it manually through the GitHub Actions UI.

## How it Works

### YAML Linting
This job uses `yamllint` with custom rules defined in `.github/yamllint-config.yaml` to check for:
- Proper indentation (2 spaces)
- Line length (max 120 characters)
- Home Assistant specific truthy values
- Other YAML syntax rules

### Home Assistant Config Check
This job:
1. Creates dummy files for sensitive information (SERVICE_ACCOUNT.json, secrets.yaml)
2. Uses a dedicated Home Assistant container to validate the configuration
3. Reports validation errors without requiring actual credentials

## Local Validation

To validate your configuration locally before pushing, you can run:

```bash
# Using the Home Assistant CLI
hass --script check_config --config .

# Using Docker (more similar to the CI environment)
docker run --rm -v $(pwd):/config homeassistant/home-assistant:stable hass -c /config --script check_config
```

## YAMLLint Configuration

The `.github/yamllint-config.yaml` file contains custom rules optimized for Home Assistant configuration:

- Line length limit: 120 characters
- Indentation: 2 spaces
- Special handling for Home Assistant's truthy values
- Ignores directories like `.storage/`, `themes/`, and `blueprints/`

## Handling Secrets

The workflow creates dummy versions of:
- SERVICE_ACCOUNT.json
- secrets.yaml (if used)

This allows validation without exposing sensitive information in the repository.

## Troubleshooting

If validation fails:

1. Check the workflow logs for detailed error messages
2. Common issues include:
   - Indentation errors
   - Missing or incorrect entity references
   - Invalid service calls
   - Syntax errors in templates
   - References to missing files or secrets
