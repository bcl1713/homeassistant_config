# Home Assistant Packages

This directory contains modular packages that group related functionality. Each package is a self-contained YAML file that defines a specific feature set.

## Available Packages

### Core Functionality

| Package                | Description                                                |
|------------------------|------------------------------------------------------------|
| `cameras.yaml`         | Camera integration with motion detection and notifications |
| `presence.yaml`        | Presence detection and related automations                 |
| `security_lights.yaml` | Security-focused lighting automations                      |
| `weather.yaml`         | Weather data processing and event monitoring               |

### Daily Living

| Package             | Description                                   |
|---------------------|-----------------------------------------------|
| `chores.yaml`       | Household chore rotation and tracking system  |
| `light_groups.yaml` | Logical grouping of lights for easier control |
| `remotes.yaml`      | Z-Wave remote control configuration           |
| `routines.yaml`     | Common household routines (Good Night, etc.)  |

### Special Features

| Package                  | Description                                          |
|--------------------------|------------------------------------------------------|
| `brief/`                 | Daily briefing system with AI-generated home updates |
| `aircraft.yaml.disabled` | Aircraft tracking (currently disabled)               |
| `seasonal.yaml.disabled` | Seasonal automation features (currently disabled)    |

## Package Structure

Each package should follow this general structure:

```yaml
# packages/example.yaml
#
# Description of what this package does
#
# Features:
# - Feature 1
# - Feature 2

# Configuration
[configuration sections]

# Automations
automation:
  - alias: "Feature Automation"
    description: "Detailed description"
    trigger:
      [triggers]
    condition:
      [conditions]
    action:
      [actions]

# Scripts
script:
  feature_script:
    alias: "Feature Script"
    sequence:
      [sequence]

# Other components as needed
```

## Creating New Packages

When adding a new package:

1. Follow the naming convention: lowercase with underscores
2. Include a header comment with description and features
3. Group related entities and automations logically
4. Test thoroughly before committing

See [DEVELOPMENT.md](../DEVELOPMENT.md) for detailed development guidelines.
