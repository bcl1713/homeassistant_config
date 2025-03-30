# Home Assistant Configuration CI

This directory contains GitHub Actions workflows for continuous integration of the Home Assistant configuration.

## Validation Workflow

The `validate.yaml` workflow does the following:

1. Runs on every push to `main` branch and on pull requests that change YAML files
2. Validates the Home Assistant configuration using the official `hass --script check_config` command
3. Performs YAML linting using `yamllint` with custom rules
4. Adds comments to pull requests indicating success or failure

## Manual Validation

You can also run the validation workflow manually through the GitHub Actions UI.

## Local Validation

To validate your configuration locally before pushing, you can run:

```bash
# Install Home Assistant CLI if not already installed
pip install homeassistant

# Validate configuration
hass --script check_config --config .
```

## YAMLLint Configuration

The `.github/yamllint-config.yaml` file contains custom rules for YAML linting:

- Line length limit: 120 characters
- Indentation: 2 spaces
- Special handling for Home Assistant's truthy values
- Ignores certain directories and files

## Troubleshooting

If the validation fails:

1. Check the workflow logs for detailed error messages
2. Common issues include:
   - Indentation errors
   - Missing or incorrect entity references
   - Invalid service calls
   - Syntax errors in templates
