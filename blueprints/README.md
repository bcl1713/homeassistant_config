# Home Assistant Blueprints

This directory contains reusable automation blueprints that can be imported into the Home Assistant UI and customized without editing YAML directly.

## Available Blueprints

### Automation Blueprints

| Blueprint           | Description                                                                                     |
|---------------------|-------------------------------------------------------------------------------------------------|
| `zwave_remote.yaml` | Universal Z-Wave remote control handler that supports multiple buttons with various press types |

## Using Blueprints

To use a blueprint:

1. In Home Assistant, go to **Configuration** → **Automations & Scenes**
2. Click the **Blueprints** tab
3. Click **Import Blueprint**
4. Enter the URL to the raw blueprint YAML file from this repository
5. Click **Preview Blueprint**
6. Click **Import Blueprint**

Once imported, you can create automations based on these blueprints by:

1. Going to **Configuration** → **Automations & Scenes**
2. Clicking **+ Add Automation**
3. Selecting **Use Blueprint**
4. Selecting the imported blueprint
5. Configuring the required inputs

## Creating New Blueprints

When adding a new blueprint:

1. Follow the naming convention: lowercase with underscores
2. Include comprehensive metadata in the `blueprint:` section
3. Document all inputs with clear descriptions
4. Test thoroughly before committing

Blueprint structure:

```yaml
blueprint:
  name: Descriptive Name
  description: >
    Detailed description of what this blueprint does and how to use it.
  domain: automation
  input:
    some_device:
      name: User-friendly Name
      description: What this input is for
      selector:
        device:
          integration: integration_name

# Blueprint implementation
trigger:
  - platform: state
    entity_id: !input some_device

action:
  - service: domain.service
    data:
      entity_id: !input some_device
```

See [DEVELOPMENT.md](../DEVELOPMENT.md) for detailed development guidelines.
