# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Workflow

### Issue Management
```bash
# Check existing issues before starting work
gh issue list

# Check existing labels before creating issues
gh label list

# Create new issue with appropriate labels
gh issue create --title "Feature Name" --body "Description..." --label "enhancement"
```

### Branch Management
```bash
# Start from latest main
git checkout main && git pull origin main

# Create feature branch
git checkout -b feature/descriptive-name
# Or for bug fixes
git checkout -b fix/descriptive-name

# Frequent commits for tracking
git add . && git commit -m "feat(scope): description"
```

### Pull Request Process
```bash
# Push branch after development
git push origin feature/feature-name

# Create PR to close issue
gh pr create --title "Feature: Add descriptive name" --body "Description and closes #ISSUE_NUMBER" --base main

# Merge after testing on HA machine
gh pr merge --squash
```

## Architecture Overview

This is a **Home Assistant configuration repository** organized using the packages pattern for modular functionality. The system manages a smart home with comprehensive automation, security, and notification capabilities.

### Core Structure

- **`packages/`** - Modular feature packages containing related automations, scripts, and entities
- **`configuration.yaml`** - Main configuration file that imports packages and core settings
- **`automation/`** - Additional automation files loaded via `!include_dir_merge_list`
- **`input_boolean/`** - Boolean switches for user control and automation state
- **`blueprints/`** - Reusable automation templates

### Key Packages

**Core Infrastructure:**
- `cameras.yaml` - Frigate camera integration with motion detection notifications
- `presence.yaml` - Presence detection and location-based automations  
- `notifications.yaml` - Multi-device notification system management
- `security_lights.yaml` - Security-focused lighting automations
- `weather.yaml` - Weather data processing and event monitoring

**Daily Living:**
- `chores.yaml` - Household chore rotation and tracking system
- `light_groups.yaml` - Logical grouping of lights for easier control
- `routines.yaml` - Common household routines (Good Night, morning wake-up, etc.)
- `remotes.yaml` - Z-Wave remote control configuration

**Advanced Features:**
- `brief/` - AI-powered daily briefing system with modular data collection
- `towner_notifications.yaml` - Zone-based notifications for specific areas
- `device_health.yaml` - Device monitoring and health checks
- `garage_door_monitoring.yaml` - Garage door state tracking and alerts

### Package Architecture Pattern

Each package follows a consistent structure:
```yaml
# Header comment describing purpose and features
automation:
  - alias: "Descriptive Name"
    description: "Clear purpose description"
    trigger: [triggers]
    condition: [conditions]  
    action: [actions]

script:
  script_name:
    alias: "Script Name"
    sequence: [steps]

# Additional components (sensors, input_boolean, etc.)
```

### Configuration Loading Strategy

The configuration uses Home Assistant's modular loading:
- `packages: !include_dir_named packages` - Loads all package files
- `automation: !include_dir_merge_list automation` - Merges automation files
- `input_boolean: !include_dir_merge_named input_boolean` - Loads boolean controls

### Notification System

Multi-device notifications configured in `configuration.yaml`:
- `notify.all_mobile_devices` - Group notification service for Brian and Hester's phones
- Individual mobile app services: `mobile_app_brian_phone`, `mobile_app_hester_phone`

### Development Standards

- **YAML Formatting**: 2-space indentation, consistent quoting
- **Entity Naming**: Descriptive names with underscores, domain prefixes
- **Package Organization**: Group related functionality, use meaningful file names
- **Automation Design**: Clear aliases, detailed descriptions, proper error handling
- **Template Usage**: Leverage Jinja2 templates for dynamic content and logic
- **Commit Strategy**: Frequent commits for each feature/change for tracking

### Testing Process

Development happens on this machine, testing on Home Assistant machine:
1. User pulls branches to HA machine for testing
2. Iterate based on testing feedback
3. Create PR when feature is complete and tested
4. Squash merge to main after approval

### Git Workflow

- Feature branches: `feature/descriptive-name`
- Bug fixes: `fix/descriptive-name` 
- Conventional commits with clear scope and description
- Frequent commits for tracking progress
- Pull requests required, squash merge to main
- Issues tracked via GitHub for feature planning

### Special Features

**Daily Briefing System (`packages/brief/`)**:
- Modular data collection from various home systems
- AI-generated briefings via MQTT integration
- Structured as subpackage with multiple YAML files

**Security Integration**:
- Frigate camera system with motion detection
- Zone-based notification system for different areas
- Security lighting responsive to presence and events

**Presence Detection**:
- Multiple presence sensors and zones
- Automated responses to home/away states
- Integration with lighting, security, and climate systems