# Home Assistant Package Patterns

## Package Structure Overview

The packages pattern allows you to organize related automations, scripts, and entities into logical modules. Each package is a separate YAML file loaded by Home Assistant's configuration system.

### Configuration Loading
In `configuration.yaml`:
```yaml
packages: !include_dir_named packages
automation: !include_dir_merge_list automation
input_boolean: !include_dir_merge_named input_boolean
```

This loads all YAML files from the `packages/` directory, merging them into the main configuration.

## Package File Organization

### Typical Package Structure
```
packages/
├── presence.yaml
├── notifications.yaml
├── security_lights.yaml
├── weather.yaml
├── chores.yaml
├── light_groups.yaml
├── routines.yaml
├── remotes.yaml
├── device_health.yaml
├── garage_door_monitoring.yaml
├── towner_notifications.yaml
└── brief/
    ├── brief_main.yaml
    ├── brief_weather_data.yaml
    └── brief_context_collection.yaml
```

### Package File Naming
- Use descriptive names that match the functionality
- Separate words with underscores
- Create subdirectories for complex features (like `brief/`)
- Keep file names short but clear

## Package Content Patterns

### Basic Package Structure
Every package should follow this format:

```yaml
# ============================================================================
# Presence Detection System
# ============================================================================
#
# Purpose:
#   Manages home/away detection using multiple sensors and provides
#   aggregated presence state for other automations
#
# Main Entities:
#   - person.brian, person.hester: Mobile device tracking
#   - input_boolean.presence_override: Manual override
#   - automation: Triggered on state changes
#
# Integration Points:
#   - Used by: security_lights, device_health, notifications
#   - Dependencies: mobile_app integrations

# Input controls for manual override
input_boolean:
  presence_override:
    name: "Manual Presence Override"
    initial: off
    icon: mdi:toggle-switch

# Binary sensors for aggregated state
binary_sensor:
  - platform: template
    sensors:
      someone_home:
        friendly_name: "Someone Home"
        value_template: "{{ is_state('person.brian', 'home') or is_state('person.hester', 'home') }}"
        device_class: occupancy

      all_away:
        friendly_name: "Everyone Away"
        value_template: "{{ is_state('person.brian', 'not_home') and is_state('person.hester', 'not_home') }}"
        device_class: occupancy

# Automations triggered by presence changes
automation:
  - alias: "All left home: activate away mode"
    description: "When everyone leaves, enable away automations"
    trigger:
      - platform: state
        entity_id: binary_sensor.all_away
        to: "on"
    condition: []
    action:
      - service: automation.turn_on
        entity_id: group.away_automations

  - alias: "Someone arrived: deactivate away mode"
    description: "When anyone arrives, disable away automations"
    trigger:
      - platform: state
        entity_id: binary_sensor.someone_home
        to: "on"
    action:
      - service: automation.turn_off
        entity_id: group.away_automations

# Scripts for complex presence logic
script:
  check_presence_status:
    alias: "Check Current Presence Status"
    description: "Evaluate presence state and trigger appropriate automations"
    sequence:
      - service: script.notify_presence_change
        data:
          current_state: "{{ states('binary_sensor.someone_home') }}"
```

## Common Package Patterns

### 1. Notification Package
```yaml
# notifications.yaml

# ============================================================================
# Notification Management System
# ============================================================================
#
# Handles multi-device notifications across all mobile devices
# Provides grouping, tagging, and priority levels

input_boolean:
  notifications_enabled:
    name: "Notifications Enabled"
    initial: on
    icon: mdi:bell

input_select:
  notification_priority:
    name: "Notification Priority"
    options:
      - "Low"
      - "Normal"
      - "High"
      - "Critical"
    initial: "Normal"

script:
  notify_all_devices:
    alias: "Send notification to all devices"
    sequence:
      - service: notify.all_mobile_devices
        data:
          title: "{{ title }}"
          message: "{{ message }}"

automation:
  - alias: "Send notifications only when enabled"
    trigger: ...
    condition:
      - condition: state
        entity_id: input_boolean.notifications_enabled
        state: "on"
    action:
      - service: script.notify_all_devices
```

### 2. Security/Lighting Package
```yaml
# security_lights.yaml

# ============================================================================
# Security Lighting System
# ============================================================================
#
# Manages security lighting based on presence and motion detection
# Provides automatic turn-off and scene management

input_boolean:
  security_lights_enabled:
    name: "Security Lights"
    initial: on

automation:
  - alias: "Security: Turn on lights on motion when away"
    description: "Activate security lighting if motion detected while nobody home"
    trigger:
      - platform: state
        entity_id: binary_sensor.motion_detected_front
        to: "on"
    condition:
      - condition: state
        entity_id: binary_sensor.all_away
        state: "on"
      - condition: state
        entity_id: input_boolean.security_lights_enabled
        state: "on"
    action:
      - service: light.turn_on
        target:
          entity_id: group.security_lights
        data:
          brightness_pct: 100

  - alias: "Security: Turn off lights 5 min after motion clears"
    trigger:
      - platform: state
        entity_id: binary_sensor.motion_detected_front
        to: "off"
        for:
          minutes: 5
    action:
      - service: light.turn_off
        target:
          entity_id: group.security_lights
```

### 3. Complex Package with Submodules
For large features like the daily briefing system, organize into subdirectories:

```yaml
# packages/brief/brief_main.yaml
# ============================================================================
# Daily Briefing System - Main Coordinator
# ============================================================================
#
# Orchestrates daily briefing generation with modular data collection.
# Processes data from separate briefing modules and generates output.

input_boolean:
  briefing_enabled:
    name: "Daily Briefing"
    initial: on

input_number:
  briefing_hour:
    name: "Briefing Time"
    unit_of_measurement: "hours"
    min: 0
    max: 23
    initial: 6

automation:
  - alias: "Daily briefing: generate"
    trigger:
      - platform: time
        at: "06:30:00"
    action:
      - service: script.generate_daily_briefing

script:
  generate_daily_briefing:
    alias: "Generate Daily Briefing"
    sequence:
      - service: script.collect_briefing_weather
      - service: script.collect_briefing_context
      - service: script.send_briefing_to_mqtt

# packages/brief/brief_weather_data.yaml
# Specific weather data collection and formatting

# packages/brief/brief_context_collection.yaml
# Time-sensitive context and observations
```

## Best Practices

### 1. Meaningful Comments
Every package should start with a descriptive header:

```yaml
# ============================================================================
# Feature Name
# ============================================================================
#
# Multi-line description explaining:
#   - What this package does
#   - Why it exists
#   - How it integrates with other systems
#
# Main Entities:
#   - List key entities
#
# Dependencies:
#   - What other packages it needs
#
# Integration Points:
#   - What uses this package
```

### 2. Group Related Items
Keep automation, scripts, and entities that work together in the same file:

✅ **Good**: All presence-related automations together
```yaml
# packages/presence.yaml
binary_sensor:
  - platform: template
    sensors:
      someone_home: ...

automation:
  - alias: "Presence: Someone arrived"
    ...
  - alias: "Presence: Everyone left"
    ...

script:
  check_presence: ...
```

❌ **Bad**: Scattering related items across files

### 3. Use Input Helpers for Configuration
Allow users to control behavior without editing YAML:

```yaml
input_boolean:
  automation_enabled:    # Toggle entire feature
  notifications_enabled: # Toggle notifications

input_select:
  brightness_level:      # Choose brightness preset

input_number:
  timer_duration:        # Adjust timing
```

### 4. Consistent Entity Naming
Maintain naming conventions across packages:

```yaml
# Good - Clear prefix and description
binary_sensor.motion_detected_front_door
sensor.temperature_bedroom_main
light.bedroom_main
light.living_room_lamp

# Bad - Vague or inconsistent
binary_sensor.motion1
sensor.temp
light.light1
```

### 5. Automation Dependencies
Document which automations interact:

```yaml
automation:
  - alias: "Turn on light"
    action:
      - service: light.turn_on

  - alias: "Turn off light after 30 min"
    trigger:
      - platform: state
        entity_id: light.bedroom  # Depends on automation above
        to: "on"
        for:
          minutes: 30
    action:
      - service: light.turn_off
        entity_id: light.bedroom
```

## Testing Packages

### Validate Package Syntax
```bash
# Home Assistant validates on startup
# Check configuration before deployment
ha core check
```

### Debug Package Issues
1. Check Home Assistant logs for YAML errors
2. Use Developer Tools > States to verify entities exist
3. Monitor Developer Tools > Automations for execution
4. Use template editor to test Jinja2 expressions

### Package Modification Safety
When modifying a package:
1. Make changes incrementally
2. Test one automation at a time
3. Monitor logs for errors
4. Deploy to production safely using git branches
