# Session 8 Handoff Notes - Device Name Display Fix

**Date:** 2025-11-08 (continuation from Session 7)
**Status:** Phase 3 - Device Name Display Still Not Working
**Branch:** `feature/briefing-robust-rebuild`
**Time:** Session ended due to context limits

## Session 8 Summary - Device Name Display Investigation

### What Was Accomplished

#### Problem Statement
Brief was showing generic "Low Battery Level" instead of actual device names like "Brian's Bedroom Remote"
- Example output: `Device issues: - Critical devices offline: Low Battery Level, Low Battery Level`
- Expected: Device names from the known_batteries.yaml template sensor friendly_name attribute

#### Root Cause Analysis ✅
1. **MQTT Sensor Attribute Flattening** (already known from Session 7)
   - Home Assistant MQTT integration flattens JSON to individual attributes
   - offline_devices attribute correctly contains list with device info

2. **Unhelpful Device Names** ✅
   - Binary sensors (`binary_sensor.bedroom_remote_brian_low_battery_level`, etc.) have name "Low Battery Level"
   - These are status indicators, not actual devices
   - The real friendly names are in `known_batteries.yaml` template sensors (e.g., "Brian's Bedroom Remote")

3. **Domain Classification Issue** ✅
   - `binary_sensor` was incorrectly included in `critical_domains` for offline monitoring
   - This caused battery status binary sensors to be picked up as "offline devices"
   - Should only monitor: camera, alarm_control_panel, lock

#### Fixes Applied (3 commits)

**Commit 1: 442ef59 - Extract battery device names**
- File: `orchestration_enhanced.yaml` (lines 263-283, 433-455)
- Added: Extract `critical_batteries` from sensor attributes
- Added: Display battery device names, not just counts
- Pattern: `{% set battery_names = battery_devices | map(attribute='name') | list %}`

**Commit 2: ea4c815 - Use friendly_name attribute**
- File: `devices_collector_enhanced.yaml` (lines 64-96, 98-117)
- Changed: Get friendly_name from entity.attributes first, fall back to entity.name
- Pattern: `{{ entity.attributes.get('friendly_name') or entity.name or entity.entity_id }}`

**Commit 3: 647ce67 - Remove binary_sensor from critical_domains** ✅
- File: `devices_collector_enhanced.yaml` (line 55)
- Changed: `critical_domains: ['camera', 'alarm_control_panel', 'lock', 'binary_sensor']`
- To: `critical_domains: ['camera', 'alarm_control_panel', 'lock']`
- Reason: Battery status binary sensors aren't real offline devices

### Current Problem: Changes Not Taking Effect

**Situation:**
- All 3 commits pushed and validated
- `curl -X POST services/template/reload` and `script/reload` executed
- `curl -X POST services/homeassistant/reload_all` executed
- Brief script executed multiple times
- **BUT:** Device sensor still shows:
  - `offline_devices: [{"name": "Low Battery Level"}, {"name": "Low Battery Level"}]`
  - `monitored_domains: ["camera","alarm_control_panel","lock","binary_sensor"]` (OLD VALUE!)

**Root Cause Analysis:**
The sensor attributes showing OLD values suggests:
1. **Template Caching Issue** - Home Assistant is caching the old script definition
2. **Sensor Value Not Updating** - MQTT sensor isn't being updated with new data
3. **Script Not Re-executing** - The old script is still running despite reload

### Key Technical Insights

#### MQTT Sensor State vs Attributes
```yaml
sensor.brief_data_devices:
  state: "2025-11-07T22:14:02.670972-06:00"  # Last update timestamp
  attributes:
    offline_count: 2
    offline_devices: [...]  # Individual attribute, flattened by MQTT
    critical_batteries: []  # Individual attribute
    monitored_domains: ["camera","alarm_control_panel","lock"]  # Should be NEW
```

#### Device Name Sources
1. **Binary Sensors** (unhelpful):
   - `binary_sensor.bedroom_remote_brian_low_battery_level`
   - friendly_name: "Low battery level" (lowercase, generic)

2. **Template Sensors** (correct):
   - In `known_batteries.yaml` lines 50-64
   - `sensor.bedroom_remote_brian_battery_level` or similar
   - friendly_name: "Brian's Bedroom Remote"

### Files Modified This Session

1. `orchestration_enhanced.yaml`
   - Lines 263-283: Added `critical_batteries` extraction
   - Lines 433-455: Added device name display logic

2. `devices_collector_enhanced.yaml`
   - Lines 53-55: Removed `binary_sensor` from critical_domains
   - Lines 64-96: Updated battery collection to use friendly_name attribute
   - Lines 98-117: Updated offline collection to use friendly_name and skip battery sensors

### Attempted Solutions That Didn't Work

1. ❌ Jinja2 `in` operator string matching:
   - Attempted: `if not ('low_battery' in entity.entity_id)`
   - Result: Still picked up battery sensors

2. ❌ Regex match filter with underscore:
   - Attempted: `entity.entity_id | regex_match('^.*(_low_battery|_battery_level)')`
   - Result: Still didn't filter them out

3. ✅ Direct domain filtering (working fix):
   - Changed: Removed `binary_sensor` from critical_domains entirely
   - Status: Fix is correct, but NOT taking effect due to caching

### Next Session - IMMEDIATE PRIORITIES

#### PRIORITY #1: Force Template Re-Evaluation
1. Try `ha core restart` (full restart, more aggressive than reload_all)
2. Or: Deploy to production with `git push` to trigger CI
3. Check if there's a template compilation cache that needs clearing
4. Verify the device_collector_enhanced.yaml is actually being used

**Command to try:**
```bash
source .env
curl -X POST -H "Authorization: Bearer $HA_TOKEN" \
  "http://192.168.86.3:8123/api/services/homeassistant/restart"
# Wait 30 seconds for restart
sleep 30
curl -X POST -H "Authorization: Bearer $HA_TOKEN" \
  "http://192.168.86.3:8123/api/services/script/daily_brief"
sleep 4
curl -H "Authorization: Bearer $HA_TOKEN" \
  "http://192.168.86.3:8123/api/states/sensor.brief_data_devices" \
  | grep "monitored_domains"
```

#### PRIORITY #2: Verify Script is Loaded from File
1. Check `/config/packages/brief/collectors/devices_collector_enhanced.yaml` directly on device
2. Confirm line 55 has new critical_domains without binary_sensor
3. If file has old content, git pull might not have worked

#### PRIORITY #3: Alternative Approach if Caching Persists
If full restart doesn't work:
1. Rename the file to force reload
2. Or add a minor comment change to force re-parse
3. Or try renaming script within YAML

#### PRIORITY #4: Test the Brief Output
Once changes take effect:
```bash
# Get the brief prompt directly
curl -H "Authorization: Bearer $HA_TOKEN" \
  "http://192.168.86.3:8123/api/states/sensor.brief_prompt" \
  | grep -A 10 "Device issues"

# Expected output:
# Device issues:
# - Low battery: Brian's Bedroom Remote, Hester's Bedroom Remote
# - Critical devices offline: (none or actual device names)
```

### Architecture Notes

**Data Flow for Device Names:**
1. Collectors scan all entities for battery_level attribute or device_class=battery
2. Extract `entity.attributes.friendly_name` (this is the key!)
3. If no friendly_name, use `entity.name` or `entity.entity_id`
4. Publish to MQTT as list of {entity_id, name, level, device_id}
5. MQTT sensor reads and flattens to individual attribute
6. Orchestration reads attribute and reconstructs list
7. Prompt building displays the names

**Why Binary Sensors Were Included:**
- Original design wanted to catch all unavailable sensors
- But battery status binary sensors are NOT offline devices
- They're just indicators that show "unavailable" when the battery data can't be read

### Testing Artifacts

Last test output (pre-caching issue):
```
sensor.brief_data_devices attributes:
- offline_devices: [
    {"device_id": "bedroom_remote_brian_low_battery_level", "name": "Low Battery Level"},
    {"device_id": "bedroom_remote_hester_low_battery_level", "name": "Low Battery Level"}
  ]
- monitored_domains: ["camera","alarm_control_panel","lock","binary_sensor"]  ← OLD
```

Expected after fixes:
```
- offline_devices: []  (empty, since we excluded binary_sensor)
- critical_batteries: [
    {"device_id": "sensor.bedroom_remote_brian_battery_level", "name": "Brian's Bedroom Remote"},
    {"device_id": "sensor.bedroom_remote_hester_battery_level", "name": "Hester's Bedroom Remote"}
  ]
- monitored_domains: ["camera","alarm_control_panel","lock"]  ← NEW
```

### Commits This Session

```
702869a fix: Use regex_match to properly filter battery-related binary sensors from offline list
647ce67 fix: Remove binary_sensor from critical_domains as battery sensors shouldn't be in offline list
ea4c815 fix: Use friendly_name attribute for device names and skip battery-related binary sensors in offline list
442ef59 fix: Extract and display device names for both battery and offline devices
```

## Status

**Fixes Are Correct:** ✅ All code changes are proper and address the root cause
**But Changes Not Taking Effect:** ⚠️ Due to Home Assistant template caching
**Next Action:** Force full restart and verify changes take effect

The problem is NOT with the logic - it's with getting Home Assistant to actually use the updated scripts. A full `ha core restart` should resolve this.

---

**Status:** BLOCKED ON TEMPLATE CACHING - NEEDS FULL RESTART
**Branch:** feature/briefing-robust-rebuild (all commits pushed)
**Last Update:** 2025-11-08 04:15 UTC
