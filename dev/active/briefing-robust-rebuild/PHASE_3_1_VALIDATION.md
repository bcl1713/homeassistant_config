# Phase 3.1: Entity Validation - Complete Implementation

**Date:** 2025-11-07
**Status:** Complete
**Branch:** `feature/briefing-robust-rebuild`

## What Was Completed

### Phase 3.1: Entity Validation & Graceful Degradation ✅

Created 6 new enhanced collector scripts with comprehensive entity validation and error handling:

#### 1. **Entity Validation Helper** (`helpers/validate_entities.yaml`)
- `script.brief_validate_entity` - Validates single entity exists
- `script.brief_validate_collector_entities` - Validates all entities for a module
- Maps each module to its required and optional entities
- Returns validation status with list of missing entities
- Supports parallel validation (max 10 concurrent)

#### 2. **Enhanced Chores Collector** (`collectors/chores_collector_enhanced.yaml`)
- Validates all 5 required chores entities before collection
- Checks:
  - binary_sensor.time_is_weekend
  - input_select.chore_dishwasher_assignee
  - input_boolean.chore_dishwasher_completed
  - input_select.chore_bathroom_assignee
  - input_boolean.chore_bathroom_completed
- Graceful fallback if any entity missing
- Publishes validation_status to MQTT
- Honors configuration-driven enabled flag

#### 3. **Enhanced Appliances Collector** (`collectors/appliances_collector_enhanced.yaml`)
- Validates primary entity: sensor.dishwasher_state (required)
- Optional entities for maintenance (salt/rinse aid sensors)
- Graceful degradation if maintenance sensors missing
- Returns sensor availability status in MQTT payload
- Properly disabled by default (matches config_loader)

#### 4. **Enhanced Commute Collector** (`collectors/commute_collector_enhanced.yaml`)
- Context-aware validation (only checks when weekday morning)
- Both travel time sensors optional (graceful degradation)
- Returns validation_status: success/partial/failed
- Lists available and missing sensors in MQTT payload
- Handles weekend/evening gracefully (not relevant)

#### 5. **Enhanced Meals Collector** (`collectors/meals_collector_enhanced.yaml`)
- Validates up to 3 meal calendar entities
- Tries to get each calendar separately (handles missing independently)
- Returns which calendars are available/missing
- Collects whatever meals are available
- Falls back gracefully if all calendars missing

#### 6. **Enhanced Devices Collector** (`collectors/devices_collector_enhanced.yaml`)
- Gathers battery levels (auto-discovers, no entity required)
- Monitors offline devices in critical domains
- Uses configurable battery threshold from input_number
- Falls back to parameter default if input_number missing
- Returns monitoring configuration in MQTT payload

## Entity Requirements by Module

### Chores (5 required, 0 optional)
```yaml
Required:
  - binary_sensor.time_is_weekend
  - input_select.chore_dishwasher_assignee
  - input_boolean.chore_dishwasher_completed
  - input_select.chore_bathroom_assignee
  - input_boolean.chore_bathroom_completed
```

### Appliances (1 required, 4 optional)
```yaml
Required:
  - sensor.dishwasher_state

Optional:
  - binary_sensor.014030536224000994_dishcare_dishwasher_event_saltnearlyempty
  - binary_sensor.014030536224000994_dishcare_dishwasher_event_saltempty
  - binary_sensor.014030536224000994_dishcare_dishwasher_event_rinseaidnearlyempty
  - binary_sensor.014030536224000994_dishcare_dishwasher_event_rinseaidempty
```

### Meals (3 required, 0 optional)
```yaml
Required:
  - calendar.mealie_breakfast
  - calendar.mealie_lunch
  - calendar.mealie_dinner
```

### Commute (2 optional, 0 required)
```yaml
Optional (both):
  - sensor.travel_time_to_brian_s_work
  - sensor.travel_time_to_hester_s_work
```

### Devices (0 required, 0 optional)
```yaml
Auto-discovers:
  - All entities with battery_level attribute
  - All sensors with device_class: battery
  - All entities in [camera, alarm_control_panel, lock, binary_sensor] with unavailable state

Configurable:
  - input_number.device_health_critical_threshold (battery alert level)
```

## Validation Behavior

### Success Case (All entities present)
```
Entity Check: ✓ Found
Response: validation_status = "success"
Action: Publish full data to MQTT
```

### Partial Failure (Some optional missing)
```
Entity Check: ✓ Found (required), ✗ Not found (optional)
Response: validation_status = "partial"
Action: Publish available data + error message
Example: Appliances without maintenance sensors
```

### Complete Failure (Required missing)
```
Entity Check: ✗ Not found
Response: validation_status = "failed"
Action: Publish fallback text from config_loader
Also: Publish validation error to home/brief/validation/{module}
```

### Disabled Module
```
Config Check: Module disabled in config_loader
Response: validation_status = "disabled"
Action: Publish empty data structure
```

## MQTT Validation Error Topics

When validation fails, error details published to:
```
home/brief/validation/{module}
```

Example error payload:
```json
{
  "timestamp": "2025-11-07T12:34:56+00:00",
  "status": "validation_error",
  "missing_entities": ["sensor.dishwasher_state"],
  "help": "Check entity ID in Developer Tools > States"
}
```

## Configuration Integration

All enhanced collectors now use config_loader values:

```yaml
# Module enabled/disabled
state_attr('sensor.brief_config_modules', '{module}')

# Fallback text
state_attr('sensor.brief_config_fallback_text', '{module}')

# MQTT topic
state_attr('sensor.brief_config_mqtt', '{module}')

# Timeouts
state_attr('sensor.brief_config_timeouts', 'collector_timeout')

# Battery threshold (devices only)
states('input_number.device_health_critical_threshold')
```

## Error Handling Patterns

### Pattern 1: Required Entity Missing
```yaml
- if:
    - condition: template
      value_template: "{{ entity_state not in ['unknown', 'unavailable'] }}"
  then:
    - # Collect data
  else:
    - # Publish error and fallback
```

### Pattern 2: Optional Entity Missing
```yaml
- if:
    - condition: template
      value_template: "{{ has_optional_entity }}"
  then:
    - # Include in payload
  else:
    - # Omit from payload
```

### Pattern 3: Context-Aware Validation
```yaml
- if:
    - condition: template
      value_template: "{{ is_relevant_time }}"
  then:
    - # Validate entities only when relevant
  else:
    - # Skip validation, return not-relevant
```

## Files Created

```
packages/brief/helpers/validate_entities.yaml          (95 lines)
packages/brief/collectors/chores_collector_enhanced.yaml      (135 lines)
packages/brief/collectors/appliances_collector_enhanced.yaml  (160 lines)
packages/brief/collectors/commute_collector_enhanced.yaml     (200 lines)
packages/brief/collectors/meals_collector_enhanced.yaml       (230 lines)
packages/brief/collectors/devices_collector_enhanced.yaml     (180 lines)
```

**Total: 1000 lines of enhanced, validated collector code**

## Key Improvements Over Original

| Aspect | Original | Phase 3.1 | Improvement |
|--------|----------|-----------|-------------|
| Entity Validation | None | Complete | Prevents silent failures |
| Missing Entity Handling | Silent failure | Graceful fallback | Users see error |
| Optional Entities | Not supported | Partial collection | Collects what's available |
| Config Integration | Hard-coded | Dynamic from config_loader | Flexible deployment |
| Error Visibility | Hidden | MQTT + validation topic | Full observability |
| Fallback Text | None | From config_loader | Consistent messaging |
| Logging | None | Validation errors published | Debuggable |

## Testing the Enhanced Collectors

### Test 1: All Entities Present (Success Case)
```bash
# Run briefing with all entities available
# Expected: validation_status = "success"
# Verify: Full data published to MQTT topic
```

### Test 2: Missing Required Entity (Failure)
```bash
# Temporarily disable/rename required entity
# Run enhanced collector
# Expected: validation_status = "failed"
# Verify: Error published to home/brief/validation/{module}
# Verify: Fallback text in MQTT payload
```

### Test 3: Missing Optional Entity (Partial)
```bash
# Temporarily disable optional entity (e.g., appliance maintenance sensor)
# Run enhanced collector
# Expected: validation_status = "partial"
# Verify: Available data still published
# Verify: Missing fields documented
```

### Test 4: Disabled Module (Config-Driven)
```bash
# Set state_attr('sensor.brief_config_modules', 'chores', false)
# Run enhanced collector
# Expected: validation_status = "disabled"
# Verify: Empty/minimal MQTT payload published
```

### Test 5: API Validation
```bash
# Use REST API to check entity state before collector runs
curl -H "Authorization: Bearer $HA_TOKEN" \
  http://homeassistant:8123/api/states/sensor.dishwasher_state
# Expected: { "state": "...", "attributes": {...} }
```

## Next Steps (Phase 3.2)

Phase 3.2 will refactor the main orchestration script to:
1. Check configuration before running each collector
2. Skip disabled modules entirely
3. Call enhanced collectors instead of originals
4. Update health sensors with validation results
5. Aggregate validation errors for UI display

## Documentation References

All code verified against:
- **Scripts:** https://www.home-assistant.io/docs/scripts/
- **State Template:** https://www.home-assistant.io/docs/configuration/templating/#states
- **Conditions:** https://www.home-assistant.io/docs/automation/condition/template/
- **REST API:** https://developers.home-assistant.io/docs/api/rest/
- **MQTT:** https://www.home-assistant.io/integrations/mqtt/

## Rollback Strategy

If enhanced collectors cause issues:
1. Keep original collectors intact (in `data_collectors.yaml`)
2. Enhanced versions in separate `collectors/` subdirectory
3. Update `script.brief_build_prompt` to use either version
4. Can revert to originals by changing service names

## Common Issues & Solutions

### Issue: Entity always returns "unknown"
**Solution:** Verify entity ID in Developer Tools > States. Use REST API:
```bash
curl -H "Authorization: Bearer $HA_TOKEN" \
  "http://homeassistant:8123/api/states/entity.id"
```

### Issue: Validation status stuck at "failed"
**Solution:** Check MQTT validation topic for error details:
```bash
# Monitor validation errors
mosquitto_sub -h mqtt-broker -t "home/brief/validation/+"
```

### Issue: Collector not respecting config_loader
**Solution:** Verify config sensors are loaded:
```bash
# Check config_loader sensors exist
curl -H "Authorization: Bearer $HA_TOKEN" \
  "http://homeassistant:8123/api/states/sensor.brief_config_modules"
```

## Summary

Phase 3.1 implements comprehensive entity validation for all collectors with:
- ✅ Pre-collection entity checks
- ✅ Graceful fallback for missing entities
- ✅ Configuration-driven module enable/disable
- ✅ Validation error reporting
- ✅ Partial collection support (optional entities)
- ✅ Context-aware validation (only when relevant)
- ✅ Full observability through MQTT topics

Ready for Phase 3.2: Configuration-driven orchestration.
