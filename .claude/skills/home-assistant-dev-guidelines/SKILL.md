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

## Critical Rule: Verify Syntax with Official Documentation

**BEFORE writing any Home Assistant YAML:**
1. Check official Home Assistant documentation for the specific component/integration
2. Verify YAML syntax and structure matches current HA version
3. Test syntax understanding by asking questions if unsure
4. Reference the exact documentation URL when writing code

**Official Documentation URLs:**
- Template Sensors: https://www.home-assistant.io/integrations/template/
- Scripts: https://www.home-assistant.io/docs/scripts/
- Automations: https://www.home-assistant.io/docs/automation/
- YAML: https://www.home-assistant.io/docs/configuration/yaml/
- Packages: https://www.home-assistant.io/docs/configuration/packages/
- Configuration: https://www.home-assistant.io/docs/configuration/
- Conditions: https://www.home-assistant.io/docs/automation/condition/

**API Documentation:**
- REST API: https://developers.home-assistant.io/docs/api/rest/
- WebSocket API: https://developers.home-assistant.io/docs/api/websocket/

**Never assume syntax.** If you're uncertain about YAML structure, attribute names, or patterns, fetch and read the documentation first.

**For Entity Validation:** Use the REST API `GET /api/states` endpoint to verify entity existence:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://YOUR_HA_IP:8123/api/states
```

## Key Resources

### Core Architecture
- **Packages Pattern**: Modular organization of related automations, scripts, and entities
  - https://www.home-assistant.io/docs/configuration/packages/
- **Configuration Loading**: YAML includes and package structure
  - https://www.home-assistant.io/docs/configuration/
- **Entity Management**: Finding and validating entity IDs
  - Use Developer Tools > States, or REST API GET /api/states

### Automation Development
- **Triggers**: Event, state, time-based triggers with templates
  - https://www.home-assistant.io/docs/automation/trigger/
- **Conditions**: State conditions, templates, and complex logic
  - https://www.home-assistant.io/docs/automation/condition/
- **Actions**: Service calls, script execution, notifications
  - https://www.home-assistant.io/docs/automation/action/

### Advanced Topics
- **Jinja2 Templates**: Dynamic values, filters, state access
  - https://www.home-assistant.io/docs/automation/templating/
- **Template Sensors**: State, attributes, availability
  - https://www.home-assistant.io/integrations/template/
- **Scripts**: Detailed syntax, response variables, variables
  - https://www.home-assistant.io/docs/scripts/
- **MQTT**: Sensors, switches, configuration
  - https://www.home-assistant.io/integrations/mqtt/
- **Security Integration**: Presence detection, security automations
- **Notification System**: Multi-device notifications, grouping
  - https://www.home-assistant.io/integrations/notify/
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
