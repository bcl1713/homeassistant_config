# Home Assistant Automation Patterns

## Basic Automation Structure

Every automation should follow this structure:

```yaml
automation:
  - alias: "Descriptive automation name"
    description: "Clear explanation of what this automation does"
    trigger: [...]
    condition: [...]
    action: [...]
```

## Common Trigger Patterns

### State Change Trigger
```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.motion_detected
    to: "on"
```

### Time-based Trigger
```yaml
trigger:
  - platform: time
    at: "06:30:00"  # Sunrise for morning routine
```

### Event Trigger
```yaml
trigger:
  - platform: event
    event_type: zwave.scene_activated
    event_data:
      entity_id: zwave.z_wave_device
      scene_id: 1
```

### Multiple Triggers
```yaml
trigger:
  - platform: state
    entity_id: sensor.temperature
    condition: "{{ trigger.to_state.state | float > 25 }}"
  - platform: numeric_state
    entity_id: sensor.humidity
    above: 70
```

## Condition Patterns

### State Condition
```yaml
condition:
  - condition: state
    entity_id: binary_sensor.presence
    state: "on"
```

### Numeric Condition
```yaml
condition:
  - condition: numeric_state
    entity_id: sensor.temperature
    above: 20
    below: 25
```

### Template Condition
```yaml
condition:
  - condition: template
    value_template: "{{ states('sensor.time') >= '19:00' }}"
```

### Combined Conditions
```yaml
condition: # All conditions must be true (AND)
  - condition: state
    entity_id: input_boolean.notifications_enabled
    state: "on"
  - condition: numeric_state
    entity_id: sensor.battery_level
    below: 20
```

## Action Patterns

### Service Call
```yaml
action:
  - service: light.turn_on
    target:
      entity_id: light.bedroom
    data:
      brightness: 100
      color_temp: 3000
```

### Call Script
```yaml
action:
  - service: script.morning_routine
```

### Send Notification
```yaml
action:
  - service: notify.all_mobile_devices
    data:
      title: "Notification Title"
      message: "Notification message with {{ variable }} substitution"
      data:
        tag: "unique_tag"
        group: "notifications"
```

### Conditional Actions
```yaml
action:
  - choose:
      - conditions: "{{ states('sensor.temperature') | float > 25 }}"
        sequence:
          - service: climate.set_temperature
            data:
              temperature: 22
      - conditions: "{{ states('sensor.temperature') | float < 15 }}"
        sequence:
          - service: climate.set_temperature
            data:
              temperature: 20
    default:
      - service: climate.set_temperature
        data:
          temperature: 19
```

### Delay and Wait
```yaml
action:
  - delay:
      seconds: 30
  - wait_template: "{{ states('binary_sensor.door') == 'off' }}"
    timeout:
      seconds: 300
```

## Template Best Practices

### Accessing States
```yaml
# Get state value
{{ states('light.bedroom') }}

# Get state with default
{{ states('sensor.missing', 'unknown') }}

# Get attributes
{{ state_attr('light.bedroom', 'brightness') }}

# With defaults
{{ state_attr('sensor.unknown', 'temperature', 0) | float(0) }}
```

### Filters and Calculations
```yaml
# Type conversion
{{ states('sensor.temperature') | float(0) }}
{{ states('sensor.count') | int(0) }}

# Comparisons
{{ states('light.bedroom') == 'on' }}
{{ states('sensor.battery') | int > 50 }}

# Rounding
{{ (states('sensor.temperature') | float) | round(1) }}

# List operations
{{ expand('light.living_room_lights') | selectattr('state','eq','on') | list | length }}
```

### Safe Defaults
```yaml
# Always provide defaults to prevent errors
{{ states('sensor.possibly_missing') | default('unknown') }}
{{ state_attr('light.bedroom', 'brightness') | default(0) }}

# Type-safe conversions
{{ states('sensor.temp') | float(0) + 5 }}
{{ (states('sensor.battery') | int(0)) % 2 }}
```

## Error Prevention

### Common Mistakes to Avoid

❌ **Don't**: Access undefined entities without defaults
```yaml
# BAD - Will error if sensor doesn't exist
{{ states('sensor.missing') | float }}
```

✅ **Do**: Use defaults in templates
```yaml
# GOOD
{{ states('sensor.missing') | float(0) }}
```

❌ **Don't**: Forget quotes around dynamic values
```yaml
# BAD
service: notify.{{ device_name }}
```

✅ **Do**: Quote service names
```yaml
# GOOD
service: "notify.{{ device_name }}"
```

❌ **Don't**: Hardcode values that should be configurable
```yaml
# BAD
action:
  - service: light.turn_on
    data:
      brightness: 255
```

✅ **Do**: Use input_boolean for toggles and sensors for dynamic values
```yaml
# GOOD
condition:
  - condition: state
    entity_id: input_boolean.automation_enabled
    state: "on"
```

## Automation Organization

### Group Related Automations
Create separate automation files for related functionality:
- `packages/presence.yaml` - Presence detection and location-based automations
- `packages/notifications.yaml` - All notification-related automations
- `packages/security_lights.yaml` - Security lighting automations
- `packages/routines.yaml` - Daily routines and schedules

### Name Automations Clearly
```yaml
alias: "Bedroom: Turn off light on last person leaving"
description: "When the last person leaves home, turn off bedroom light"

alias: "Mobile: Send battery low notification"
description: "Alert when any mobile device battery drops below 20%"

alias: "Security: Arm alarm when all present entities away"
description: "Automatically arm security system 5 minutes after everyone leaves"
```

## Testing Automations

### Manual Trigger Testing
Use the Developer Tools > Automations page to:
1. Verify automation syntax
2. Manually trigger automations
3. Check action execution
4. Review logs for errors

### Real-world Testing
After deployment:
1. Monitor automation execution in logs
2. Verify notifications arrive correctly
3. Check that service calls execute as expected
4. Watch for template errors in system logs
