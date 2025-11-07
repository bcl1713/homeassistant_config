# Jinja2 Templates and Entity Management

## Jinja2 Template Fundamentals

### Basic State Access
```yaml
# Simple state access
{{ states('light.bedroom') }}

# Access with fallback
{{ states('sensor.temperature', 'unknown') }}

# Attribute access
{{ state_attr('light.bedroom', 'brightness') }}

# Complete object
{{ states.light.bedroom }}
```

### Type Conversions and Filters

#### String Operations
```yaml
# Lowercase and uppercase
{{ states('input_text.name') | lower }}
{{ states('input_text.name') | upper }}

# Capitalize
{{ states('input_text.name') | capitalize }}

# Replace values
{{ states('sensor.status') | replace('unavailable', 'Unknown') }}

# String length
{{ states('input_text.message') | length }}
```

#### Numeric Operations
```yaml
# Convert to float with default
{{ states('sensor.temperature') | float(0) }}

# Convert to int with default
{{ states('sensor.count') | int(0) }}

# Math operations
{{ (states('sensor.temperature') | float(0)) + 5 }}
{{ (states('sensor.value') | float(0)) * 1.5 }}
{{ (states('sensor.value') | float(0)) | round(2) }}

# Absolute value
{{ states('sensor.value') | float(0) | abs }}

# Min/Max
{{ [states('sensor.temp1') | float(0), states('sensor.temp2') | float(0)] | min }}
{{ [states('sensor.temp1') | float(0), states('sensor.temp2') | float(0)] | max }}
```

#### List Operations
```yaml
# List manipulation
{{ expand('group.all_lights') }}
{{ expand('light.living_room_lights') | length }}

# Selecting from list
{{ expand('light.all_lights') | selectattr('state', 'eq', 'on') | list }}
{{ expand('light.all_lights') | rejectattr('state', 'eq', 'unavailable') | list }}

# Count lights that are on
{{ expand('light.living_room_lights') | selectattr('state', 'eq', 'on') | list | length }}

# Map to attributes
{{ expand('device_tracker.all_devices') | map(attribute='state') | list }}
```

#### Boolean Logic
```yaml
# Simple conditions
{{ states('light.bedroom') == 'on' }}
{{ states('binary_sensor.motion') == 'on' }}

# Comparisons
{{ states('sensor.temperature') | float > 25 }}
{{ states('sensor.battery') | int < 20 }}

# Multiple conditions (AND)
{{ states('light.bedroom') == 'on' and states('binary_sensor.motion') == 'on' }}

# Multiple conditions (OR)
{{ states('light.bedroom') == 'on' or states('light.living_room') == 'on' }}

# NOT condition
{{ not (states('binary_sensor.motion') == 'on') }}
{{ states('light.bedroom') != 'on' }}

# In operator
{{ states('sensor.status') in ['on', 'active', 'running'] }}
```

### Advanced Template Patterns

#### Datetime Operations
```yaml
# Current time (use trigger.now for automations)
{{ now().hour }}
{{ now().minute }}
{{ now().strftime('%H:%M') }}

# Time comparison
{{ now().hour > 19 }}
{{ now().hour < 6 }}

# Check if in time range
{{ (now().hour > 9) and (now().hour < 17) }}

# Day of week (0 = Monday)
{{ now().weekday() }}
{{ now().isoweekday() }}  # 1 = Monday, 7 = Sunday
```

#### Conditional Template Values
```yaml
# Simple if-then-else
{{ 'On' if states('light.bedroom') == 'on' else 'Off' }}

# Complex conditions
{{ 'Hot' if (states('sensor.temperature') | float(0)) > 25 else 'Cold' if (states('sensor.temperature') | float(0)) < 15 else 'Comfortable' }}

# Ternary with state
{{ 'Battery Low' if (states('sensor.battery') | int(0)) < 20 else 'OK' }}
```

#### Entity Lookup and Grouping
```yaml
# All devices in group
{% set devices = expand('group.all_lights') %}
{{ devices | length }} lights in group

# Devices with specific state
{% set on_lights = expand('light.all_lights') | selectattr('state', 'eq', 'on') | list %}
{{ on_lights | length }} lights are on

# Friendly names
{% set lights = expand('light.living_room_lights') %}
{% for light in lights %}
  {{ light.attributes.friendly_name }}
{% endfor %}
```

#### Safe Template Defaults
```yaml
# All of these prevent errors if entities don't exist
{{ states('sensor.missing') | default('unknown') }}
{{ state_attr('sensor.missing', 'unit') | default('N/A') }}
{{ (states('sensor.missing') | float(0)) }}
{{ (states('sensor.missing') | int(-1)) }}

# Complex expressions with safe defaults
{{ [states('sensor.temp1') | float(0), states('sensor.temp2') | float(0)] | max }}
```

## Entity Organization

### Input Boolean (Toggle Controls)
Use for binary state that should persist:

```yaml
input_boolean:
  automations_enabled:
    name: "Enable All Automations"
    initial: on
    icon: mdi:dip-switch

  notifications_enabled:
    name: "Enable Notifications"
    initial: on
    icon: mdi:bell

  guest_mode:
    name: "Guest Mode Active"
    initial: off
    icon: mdi:account-multiple
```

### Input Select (Multi-choice Controls)
```yaml
input_select:
  climate_mode:
    name: "Climate Mode"
    options:
      - "Away"
      - "Home"
      - "Sleep"
    initial: "Home"
    icon: mdi:thermostat

  automation_mode:
    name: "Automation Level"
    options:
      - "Full Automation"
      - "Semi-Auto"
      - "Manual"
    initial: "Full Automation"
```

### Input Number (Numeric Controls)
```yaml
input_number:
  temperature_offset:
    name: "Temperature Offset"
    unit_of_measurement: "°C"
    min: -5
    max: 5
    step: 0.1
    icon: mdi:thermometer

  brightness_level:
    name: "Default Brightness"
    unit_of_measurement: "%"
    min: 0
    max: 100
    step: 5
    icon: mdi:brightness-6
```

### Input Text (Text Storage)
```yaml
input_text:
  notification_message:
    name: "Custom Notification"
    max: 255
    icon: mdi:message

  location_name:
    name: "Current Location"
    max: 50
    icon: mdi:map-marker
```

## Naming Conventions

### Entity IDs
Format: `domain.descriptive_name_with_underscores`

✅ **Good Examples:**
```yaml
input_boolean.automations_enabled
binary_sensor.motion_detected_living_room
sensor.temperature_bedroom
light.bedroom_main
light.living_room_floor_lamp
automation.bedroom_motion_detected
script.morning_routine
```

❌ **Bad Examples:**
```yaml
input_boolean.auto  # Too vague
binary_sensor.sensor1  # Not descriptive
sensor.temp  # Ambiguous location
light.light1  # Generic name
```

### Friendly Names
Use human-readable names in friendly_name attributes:

```yaml
# Good
name: "Living Room Temperature"
name: "Bedroom Main Light"
name: "Presence Detected - Front Door"

# Bad
name: "temp"
name: "light1"
name: "event"
```

## Package Organization

### Group Related Entities
Keep entities together by functionality:

**packages/presence.yaml**
```yaml
input_boolean:
  home_mode:
    name: "Home Mode"

binary_sensor:
  - platform: template
    sensors:
      someone_home:
        value_template: "{{ is_state('person.brian', 'home') or is_state('person.hester', 'home') }}"

automation:
  - alias: "Home mode on when anyone arrives"
    trigger: ...
```

**packages/security_lights.yaml**
```yaml
input_boolean:
  security_lights_enabled:
    name: "Security Lights"

automation:
  - alias: "Turn on security lights on motion"
    trigger: ...
  - alias: "Turn off security lights when clear"
    trigger: ...
```

### Configuration Comments
Always include context in package headers:

```yaml
# Presence Detection System
#
# Manages home/away state using multiple presence sensors.
# Triggers security and comfort automations based on occupancy.
#
# Main entities:
#   - person.brian, person.hester: Primary presence tracking
#   - binary_sensor.someone_home: Aggregated presence state
#   - input_boolean.home_mode: Override for presence logic

input_boolean:
  home_mode: ...
```
