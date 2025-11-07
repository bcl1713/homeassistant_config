# Home Assistant Development Guidelines

This skill provides comprehensive development guidance for Home Assistant configuration management using the packages pattern, Jinja2 templating, and automation best practices.

## When This Skill Activates

This skill activates when you're:
- Working on automations, scripts, or sensors
- Using Jinja2 templates or Home Assistant conditions
- Organizing code using packages
- Creating entities (input_boolean, sensors, etc.)
- Managing notifications or presence detection
- Working with Home Assistant YAML configuration

## Key Resources

### Core Architecture
- **Packages Pattern**: Modular organization of related automations, scripts, and entities
- **Configuration Loading**: YAML includes and package structure
- **Entity Management**: Naming conventions and organization

### Automation Development
- **Triggers**: Event, state, time-based triggers with templates
- **Conditions**: State conditions, templates, and complex logic
- **Actions**: Service calls, script execution, notifications

### Advanced Topics
- **Jinja2 Templates**: Dynamic values, filters, state access
- **Security Integration**: Presence detection, security automations
- **Notification System**: Multi-device notifications, grouping
- **Error Handling**: Safe template defaults, error prevention

## Development Standards

### YAML Formatting
- 2-space indentation (never tabs)
- Consistent quoting for strings containing special characters
- Alphabetical ordering within sections for consistency
- Clear, descriptive entity names with underscores

### Automation Best Practices
- Every automation must have a descriptive `alias` and `description`
- Use meaningful trigger, condition, and action organization
- Include comments for complex logic
- Template complex values instead of hardcoding

### Package Organization
- Group related functionality logically
- Use descriptive file names matching functionality
- One main purpose per package file
- Include header comment describing package purpose

### Entity Naming
- Format: `domain.descriptive_entity_name`
- Use underscores for spaces
- Be specific and meaningful
- Avoid abbreviations unless industry standard

## Common Patterns

### Automation Trigger Patterns
```yaml
automation:
  - alias: "Descriptive automation name"
    description: "What this automation does and why"
    trigger:
      # Single or multiple triggers
    condition: []
    action:
      # Sequence of actions
```

### Template Usage
```yaml
template:
  - sensor:
      name: "Sensor Name"
      unique_id: "unique_sensor_id"
      state: "{{ states('entity.name') }}"
```

### Input Boolean Controls
```yaml
input_boolean:
  feature_toggle:
    name: "Human Readable Name"
    initial: off
    icon: mdi:icon-name
```

## Integration Points

- **Automation Loading**: `automation: !include_dir_merge_list automation/`
- **Package Loading**: `packages: !include_dir_named packages/`
- **Input Boolean Loading**: `input_boolean: !include_dir_merge_named input_boolean/`
- **Notifications**: `notify.all_mobile_devices` and device-specific services

## Performance Considerations

- Use templates efficiently to minimize re-evaluation
- Avoid polling when event-based triggers are available
- Structure automations to fail fast on conditions
- Use input_boolean for state caching instead of template evaluation

---

Learn more: See resource files for detailed patterns and examples
