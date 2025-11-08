# Next Steps - Session 9

## Immediate Action (First 5 minutes)

### Step 1: Full Restart Home Assistant
```bash
source .env
curl -X POST -H "Authorization: Bearer $HA_TOKEN" \
  "http://192.168.86.3:8123/api/services/homeassistant/restart"
```
Wait 30 seconds for restart to complete.

### Step 2: Verify Changes Loaded
Check that the new critical_domains is being used:
```bash
source .env
curl -s -X POST -H "Authorization: Bearer $HA_TOKEN" \
  "http://192.168.86.3:8123/api/services/script/daily_brief" > /dev/null
sleep 4
curl -s -H "Authorization: Bearer $HA_TOKEN" \
  "http://192.168.86.3:8123/api/states/sensor.brief_data_devices" \
  | grep -o '"monitored_domains":\[[^]]*\]'
```

**Expected output:** `"monitored_domains":["camera","alarm_control_panel","lock"]`
**Old (bad) output:** `"monitored_domains":["camera","alarm_control_panel","lock","binary_sensor"]`

### Step 3: Check Device Names in Brief
```bash
source .env
curl -s -H "Authorization: Bearer $HA_TOKEN" \
  "http://192.168.86.3:8123/api/states/sensor.brief_prompt" \
  | python3 -c "import sys,json; l=[x for x in sys.stdin];
                 d=json.loads(l[-1] if l else '{}');
                 print(d['attributes']['prompt'])" | grep -A 5 "Device"
```

**Expected:** Device names like "Brian's Bedroom Remote" instead of "Low Battery Level"

## If Full Restart Doesn't Work

### Option A: Check File Content on Device
```bash
source .env
ssh root@192.168.86.3 "grep 'critical_domains' /config/packages/brief/collectors/devices_collector_enhanced.yaml"
```

Should show: `critical_domains: ['camera', 'alarm_control_panel', 'lock']`

### Option B: Force Template Re-parse
Edit the file to add a comment and force re-parse:
```bash
# Add a comment change to line 55
nano packages/brief/collectors/devices_collector_enhanced.yaml
# Add space or change comment
# Then: reload
```

### Option C: Check Git Status on Device
```bash
source .env
ssh root@192.168.86.3 "cd /config && git status"
```

Verify the branch is feature/briefing-robust-rebuild and has latest commits.

## Success Criteria

✅ Brief shows actual device names (e.g., "Brian's Bedroom Remote")
✅ No more "Low Battery Level" entries
✅ Offline devices section is empty (since we only have battery status sensors offline)
✅ Brief mentions battery devices like: "Low battery: Brian's Bedroom Remote, Hester's Bedroom Remote"

## Files Changed Summary

- `packages/brief/orchestration_enhanced.yaml` - Extract and display battery names
- `packages/brief/collectors/devices_collector_enhanced.yaml` - Use friendly_name, remove binary_sensor

## Key Insight for This Issue

**The problem was NOT logic errors** - it was Home Assistant's template caching system not recognizing the file changes. A full service restart should force re-compilation of all YAML templates.

---

**Estimated Time:** 5-10 minutes for full restart + testing
**Risk Level:** Low - only service restart, no data loss
**Rollback Plan:** If issues occur, switch back to `main` branch
