# Home Assistant Configuration

![Home Assistant Logo](https://brands.home-assistant.io/_/home_assistant/logo.png)

This repository contains my personal Home Assistant configuration, providing automated control and monitoring of my smart home.

## Overview

This Home Assistant configuration provides a comprehensive smart home automation system with the following features:

- **Security and Monitoring**: Camera integrations, motion detection alerts, and alarm system management
- **Lighting Control**: Automated lighting based on presence, time of day, and security events
- **Routine Automation**: Good night routines, morning wake-up sequences, and presence-based automations
- **Notification System**: Multi-device alerts for critical events and daily briefings
- **Weather Integration**: Automated responses to weather conditions
- **Chore Management**: Tracking and rotation of household responsibilities

## Directory Structure

```
/
├── automation/               # Individual automation files
├── blueprints/              # Reusable automation blueprints
├── input_boolean/           # Boolean switch definitions
├── packages/                # Feature-specific configuration packages
│   ├── brief/              # Daily briefing system
│   ├── cameras.yaml        # Camera configuration
│   ├── chores.yaml         # Chore management
│   └── ...                 # Other feature packages
├── scenes.yaml              # Defined scenes
├── configuration.yaml       # Main configuration file
└── recorder.yaml            # Database recording settings
```

## Packages

This configuration uses Home Assistant's packages feature to organize functionality into discrete modules:

- **cameras.yaml**: Camera integration with motion detection and notifications
- **chores.yaml**: Household chore rotation and tracking system
- **light_groups.yaml**: Logical grouping of lights for easier control
- **presence.yaml**: Presence detection and related automations
- **remotes.yaml**: Z-Wave remote control configuration
- **routines.yaml**: Common household routines (Good Night, etc.)
- **security_lights.yaml**: Security-focused lighting automations
- **weather.yaml**: Weather data processing and event monitoring

## Getting Started

To use this configuration as a template:

1. Install Home Assistant using your preferred method
2. Clone this repository to your configuration directory
3. Update the configuration to match your devices and preferences
4. Restart Home Assistant to apply changes

## Development

Please see [DEVELOPMENT.md](DEVELOPMENT.md) for contribution guidelines, development workflows, and coding standards.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
