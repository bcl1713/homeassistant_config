# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **Home Assistant configuration repository** organized using the packages pattern for modular functionality. The system manages a smart home with comprehensive automation, security, and notification capabilities.

## Development Workflow

### Standard Development Process

1. **Create feature branch**: `git checkout -b feature/descriptive-name`
2. **Make changes**: Edit YAML files in packages or other directories
3. **Commit frequently**: `git add . && git commit -m "feat: description"`
4. **Push for CI validation**: `git push origin feature/descriptive-name`
5. **Deploy to production for testing**: Deploy branch to Home Assistant
6. **Create PR**: After testing, create PR for review
7. **Merge**: Squash merge to main after approval

### Home Assistant Commands

```bash
# Deploy branch to production for testing
ssh root@$HAOS_IP "cd /config && git fetch origin && git checkout feature-branch && git pull origin feature-branch"

# Validate configuration
ssh root@$HAOS_IP "ha core check"

# Reload services (source .env first for API calls)
source .env && curl -X POST -H "Authorization: Bearer $HA_TOKEN" "http://$HAOS_IP:8123/api/services/automation/reload"
source .env && curl -X POST -H "Authorization: Bearer $HA_TOKEN" "http://$HAOS_IP:8123/api/services/script/reload"
source .env && curl -X POST -H "Authorization: Bearer $HA_TOKEN" "http://$HAOS_IP:8123/api/services/homeassistant/reload_all"

# Rollback to main if needed
ssh root@$HAOS_IP "cd /config && git checkout main && git pull origin main"

# Full restart (if needed)
ssh root@$HAOS_IP "ha core restart"
```

### GitHub Integration

```bash
# Issue management
gh issue list
gh issue create --title "Feature Name" --body "Description..." --label "enhancement"

# Pull request workflow
gh pr create --title "Feature: Description" --body "Closes #ISSUE_NUMBER" --base main
gh pr merge PR_NUMBER --squash
```

## Environment Setup

### Required Environment Variables (.env)

```bash
# Home Assistant connection
HAOS_IP=192.168.1.XXX
HAOS_USER=root
HA_TOKEN=your_long_lived_access_token_here

# Project paths
PROJECT_DIR=/home/USERNAME/Projects/homeassistant-dev/config
```

### Prerequisites

- Home Assistant OS instance with SSH access
- GitHub repository for HA configuration
- Home Assistant long-lived access token
- Modified export script on HAOS: `/config/scripts/export-ha-data-fixed.sh`

## Architecture Overview

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

### Branch Strategy

- Feature branches: `feature/descriptive-name`
- Bug fixes: `fix/descriptive-name`
- CI validation required before production testing
- Squash merge to main after testing

### Testing Workflow

1. **CI Validation**: Push triggers GitHub Actions validation
2. **Production Testing**: Deploy branch to Home Assistant for real-world testing
3. **Iterate**: Make changes based on testing feedback
4. **Finalize**: Create PR and merge after successful testing

### Special Features

**AI Context Generation**:

- Exports comprehensive HA state, entities, and configurations
- Generated via remote script execution on production instance
- Provides full context for AI-assisted development

**Safe Production Testing**:

- Git-based deployment to production HA instance
- Configuration validation before reload
- API-based reloads (no full restarts needed)
- Instant rollback capability

**CI Integration**:

- GitHub Actions validate configuration using HA container
- Creates dummy service account file for Google Assistant integration
- Continues on expected errors to allow deployment testing

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
