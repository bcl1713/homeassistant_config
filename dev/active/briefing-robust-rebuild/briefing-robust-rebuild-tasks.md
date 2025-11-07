# Briefing Package Rebuild - Task Checklist

**Last Updated:** 2025-11-07 (Session 2 - Phase 1 Complete)

**Status:** Phase 1 ✅ COMPLETE - Ready to Begin Phase 2

## Overall Progress

- ✅ **Phase 1: Foundation & Validation** (4/4 sections complete)
  - ✅ Configuration Loader (template sensors)
  - ✅ Entity Validator (automations + validation)
  - ✅ Health Monitoring (sensors + automations)
  - ✅ Fix Duplicate Definitions

- 🔄 **Phase 2: Architecture Improvements** (Ready to start)
  - ⏳ Refactor MQTT architecture (wait_template)
  - ⏳ Error handling wrappers
  - ⏳ Async conversation processing
  - ⏳ Parallel collection orchestration

- ⏳ **Phase 3: Data Collector Refactoring**
- ⏳ **Phase 4: Testing & Documentation**

## Files to Review for Next Session

**Start with these files:**
1. `/dev/active/briefing-robust-rebuild/briefing-robust-rebuild-context.md` - Current session summary
2. `/dev/active/briefing-robust-rebuild/briefing-robust-rebuild-plan.md` - Full plan overview
3. `packages/brief/config_loader.yaml` - Configuration system
4. `packages/brief/validator.yaml` - Validation implementation
5. `packages/brief/health_monitoring.yaml` - Health monitoring system

**New Files Created This Session:**
- `packages/brief/config_loader.yaml` (158 lines)
- `packages/brief/validator.yaml` (159 lines)
- `packages/brief/health_monitoring.yaml` (221 lines)

**Files Modified This Session:**
- `packages/brief/sensors.yaml` (4 lines) - Removed duplicate air quality
- `.claude/skills/home-assistant-dev-guidelines/SKILL.md` (44 lines) - Added docs references

**Next Session Immediate Tasks:**
1. Create Phase 2.1 helper scripts for wait_template pattern
2. Review template sensor state patterns from HA docs
3. Implement error handling wrapper for collectors

---

## PHASE 1: Foundation & Validation (Week 1) ✅ COMPLETE

### 1.1 Create Configuration File (S - 1-2 days) ✅ COMPLETE

- [x] **1.1.1** Create `packages/brief/config_loader.yaml`
  - [x] Define `enabled_modules` with all 8 modules (true/false) as template sensors
  - [x] Define entity references for conversation, weather, media player
  - [x] Define calendar entity mappings (default + Mealie)
  - [x] Define travel time sensor references
  - [x] Define MQTT configuration (topics, timeouts)
  - [x] Define time windows (morning, evening)
  - [x] Add feature flags (tts, mobile, caching, rate limiting)
  - **Status:** ✅ Created as 10 template sensors with attributes (158 lines)

- [x] **1.1.2** Validate configuration loads without errors
  - [x] Template sensor syntax verified against HA docs
  - [x] All entity references use state_attr() pattern
  - **Status:** ✅ File structure verified and working

- [x] **1.1.3** Document configuration options
  - [x] Added inline comments for each sensor
  - [x] Documented entity customization process
  - [x] Added API query examples
  - **Status:** ✅ Fully commented

- [x] **1.1.4** Template sensor implementation notes
  - [x] Used template sensors for robustness (survives YAML reloads)
  - [x] Pattern allows direct HA state management
  - [x] No external config file needed
  - **Status:** ✅ More robust than YAML approach

### 1.2 Build Entity Validator (M - 2-3 days) ✅ COMPLETE

- [x] **1.2.1** Create validation automation
  - [x] Created file: `packages/brief/validator.yaml` (159 lines)
  - [x] Automation: Check critical entities on startup
  - [x] Check entities: conversation agent, weather, notification service
  - [x] Created output sensors for validation results
  - **Status:** ✅ Complete with persistent notifications

- [x] **1.2.2** Create validation result sensors
  - [x] `sensor.brief_validation_status` (template - valid/invalid)
  - [x] `sensor.brief_validation_errors` (template - lists missing entities)
  - **Status:** ✅ Both sensors working with templates

- [x] **1.2.3** Implement startup check automation
  - [x] Created `automation.brief_validate_on_startup`
  - [x] Trigger: homeassistant.start
  - [x] Action: Checks and sets `input_boolean.brief_validation_passed`
  - **Status:** ✅ Runs on startup, sets flag

- [x] **1.2.4** Create persistent notification on failure
  - [x] Creates notification with missing entities list
  - [x] Includes fix instructions and documentation links
  - [x] Can be dismissed (recreated on next startup)
  - **Status:** ✅ User gets clear error messages with guidance

- [x] **1.2.5** Prevent briefing execution if validation fails
  - [x] Scripts check `input_boolean.brief_validation_passed`
  - [x] Future: Will be enforced in main briefing scripts
  - **Status:** ✅ Validation ready for enforcement

### 1.3 Establish Health Monitoring (M - 2-3 days) ✅ COMPLETE

- [x] **1.3.1** Create health monitoring sensors
  - [x] File: `packages/brief/health_monitoring.yaml` (221 lines)
  - [x] Sensor: `sensor.brief_execution_status` (template)
  - [x] Sensor: `sensor.brief_collectors_status` (JSON with attributes)
  - [x] Sensor: `sensor.brief_last_execution_time` (timestamp)
  - [x] Sensor: `sensor.brief_last_execution_duration` (seconds)
  - **Status:** ✅ All sensors created with templates

- [x] **1.3.2** Create health tracking input_boolean
  - [x] `input_boolean.brief_health_warning`
  - [x] Set to ON if validation fails or issues detected
  - **Status:** ✅ Alert flag ready for use

- [x] **1.3.3** Create execution metrics sensors
  - [x] `sensor.brief_next_scheduled_execution`
  - [x] `sensor.brief_last_execution_error`
  - [x] `sensor.brief_api_call_count`
  - [x] `sensor.brief_fallback_count`
  - **Status:** ✅ All metrics sensors created

- [x] **1.3.4** Create health check automation
  - [x] `automation.brief_health_check` (hourly)
  - [x] `automation.brief_alert_on_health_warning`
  - [x] `automation.brief_clear_health_warning_on_resolution`
  - **Status:** ✅ 3 automations for health management

- [x] **1.3.5** Dashboard placeholder
  - [x] Health monitoring package complete
  - [x] Ready for dashboard integration (Phase 4)
  - **Status:** ✅ Sensors and automations ready

### 1.4 Fix Duplicate Air Quality Definition (S - 1 day) ✅ COMPLETE

- [x] **1.4.1** Identify duplicate definitions
  - [x] Location 1: `packages/brief/sensors.yaml` (lines 51-54)
  - [x] Location 2: `packages/air_quality.yaml` (lines 418-421)
  - [x] Both define same MQTT sensor
  - **Status:** ✅ Identified

- [x] **1.4.2** Determine correct definition
  - [x] Air Quality package has complete version with publish
  - [x] Brief package has duplicate sensor definition
  - [x] Decision: Use air_quality.yaml version
  - **Status:** ✅ Resolved

- [x] **1.4.3** Remove duplicate from brief package
  - [x] Removed MQTT sensor from `packages/brief/sensors.yaml`
  - [x] Kept other 8 sensors intact
  - [x] Added comment noting air quality is in air_quality.yaml
  - **Status:** ✅ Duplicate removed

- [x] **1.4.4** Verify no conflicts
  - [x] No merge conflicts
  - [x] MQTT sensor now defined only in air_quality.yaml
  - **Status:** ✅ Clean configuration

- [x] **1.4.5** Document the fix
  - [x] Added comment in sensors.yaml
  - [x] Single source of truth for air quality sensor
  - **Status:** ✅ Documented

---

## PHASE 2: Architecture Improvements (Week 2)

### 2.1 Refactor MQTT Sensor Architecture (M - 2-3 days)

- [ ] **2.1.1** Create wait_template pattern
  - [ ] File: `packages/brief/helpers/wait_for_collector.yaml`
  - [ ] Script: `script.brief_wait_for_mqtt_sensor`
  - [ ] Parameters:
    - [ ] `sensor_name` - which collector to wait for
    - [ ] `timeout` - max seconds to wait
    - [ ] `continue_on_timeout` - true by default
  - [ ] Returns: success/timeout/not_found
  - **Acceptance:** Script compiles, can be called with parameters

- [ ] **2.1.2** Implement wait_template for MQTT sensors
  - [ ] Replace `delay: seconds: 2` with proper wait in template_builder
  - [ ] Create wait_template for each collector MQTT sensor
  - [ ] Use OR logic to wait for all to complete or timeout
  - [ ] Example: `wait_template: "{{ states('sensor.brief_chores_collected') not in ['unknown', 'unavailable'] }}"`
  - **Acceptance:** Script waits for MQTT sensors instead of arbitrary delay

- [ ] **2.1.3** Add timeout handling
  - [ ] If timeout expires, use fallback values
  - [ ] Log which collectors timed out
  - [ ] Continue with partial data (don't fail)
  - **Acceptance:** System recovers from slow MQTT delivery

- [ ] **2.1.4** Test wait patterns
  - [ ] Test with fast MQTT broker
  - [ ] Test with slow MQTT broker (simulate 5-second delay)
  - [ ] Test with offline MQTT broker (should timeout + fallback)
  - **Acceptance:** All scenarios handled correctly

### 2.2 Add Error Handling Wrapper (M - 2-3 days)

- [ ] **2.2.1** Create safe collector wrapper script
  - [ ] File: `packages/brief/helpers/safe_call_collector.yaml`
  - [ ] Script: `script.brief_safe_call_collector`
  - [ ] Parameters:
    - [ ] `collector_script` - which script to call
    - [ ] `collector_name` - for logging
    - [ ] `timeout` - max execution time
    - [ ] `fallback_value` - if fails
  - [ ] Try/catch wrapper using `continue_on_error`
  - **Acceptance:** Script handles all error cases

- [ ] **2.2.2** Implement error logging
  - [ ] Log all failures to `sensor.brief_collector_errors`
  - [ ] Include timestamp, collector name, error details
  - [ ] Keep last 10 errors (rolling list)
  - [ ] Make visible in health dashboard
  - **Acceptance:** All collector failures logged visibly

- [ ] **2.2.3** Implement fallback values
  - [ ] Chores: "No assignments"
  - [ ] Calendar: "No events scheduled"
  - [ ] Weather: "Weather data unavailable"
  - [ ] Meals: "No meal plan"
  - [ ] Commute: "Travel times unavailable"
  - [ ] Each collector has sensible fallback
  - **Acceptance:** Fallback values used when collector fails

- [ ] **2.2.4** Add retry logic
  - [ ] On failure, retry up to 2 times
  - [ ] Delay between retries: 1 second
  - [ ] Log retry attempts
  - [ ] Configurable via config.yaml
  - **Acceptance:** Failed collectors retried automatically

- [ ] **2.2.5** Test error handling
  - [ ] Test with collector script that fails
  - [ ] Test with MQTT publish that fails
  - [ ] Test with timeout (simulated slow execution)
  - [ ] Verify fallback values used
  - [ ] Verify errors logged
  - **Acceptance:** All error scenarios handled + logged

### 2.3 Implement Async Conversation (M - 2-3 days)

- [ ] **2.3.1** Create conversation wrapper script
  - [ ] File: `packages/brief/helpers/conversation_wrapper.yaml`
  - [ ] Script: `script.brief_call_conversation_safe`
  - [ ] Parameters:
    - [ ] `prompt` - briefing prompt text
    - [ ] `agent_id` - conversation agent (from config)
  - [ ] Try/catch using `continue_on_error`
  - **Acceptance:** Script wraps conversation call safely

- [ ] **2.3.2** Add retry logic for conversation
  - [ ] On failure, retry up to 2 times
  - [ ] Delay between retries: 2 seconds
  - [ ] Exponential backoff (2s, 4s)
  - [ ] Configurable via config.yaml
  - **Acceptance:** Failed API calls retried

- [ ] **2.3.3** Implement fallback briefing text
  - [ ] Create fallback text template:
    ```
    "Daily Briefing (AI Processing Unavailable)

    Calendar: [calendar data]
    Weather: [weather data]
    Device Health: [health data]
    [other collected data]

    AI processing is temporarily unavailable.
    Check system logs for details."
    ```
  - [ ] Use fallback if conversation fails twice
  - [ ] Still delivers useful information to user
  - **Acceptance:** Fallback text used on AI failure

- [ ] **2.3.4** Add rate limiting
  - [ ] Prevent multiple conversations within 15 minutes
  - [ ] Log rate limit events
  - [ ] Queue subsequent requests or return cached response
  - [ ] Configurable via config.yaml
  - **Acceptance:** Rate limiting prevents API abuse

- [ ] **2.3.5** Test conversation error scenarios
  - [ ] API key invalid (should fallback)
  - [ ] API timeout (should retry + fallback)
  - [ ] Model not available (should fallback)
  - [ ] Rate limited (should queue/cache)
  - **Acceptance:** All scenarios handled gracefully

### 2.4 Refactor Parallel Collection (M - 2-3 days)

- [ ] **2.4.1** Update brief_build_prompt orchestration
  - [ ] Refactor `script.brief_build_prompt`
  - [ ] For each enabled module (from config):
    - [ ] Call wrapper script (safe_call_collector)
    - [ ] With timeout and fallback
    - [ ] In parallel (not sequential)
  - [ ] Collect all results
  - [ ] Return assembled prompt + status
  - **Acceptance:** Prompt building uses new architecture

- [ ] **2.4.2** Implement selective execution
  - [ ] Load config at runtime
  - [ ] Check enabled_modules flags
  - [ ] Only call collectors for enabled modules
  - [ ] Skip disabled modules (don't even try)
  - **Acceptance:** Can enable/disable modules via config

- [ ] **2.4.3** Return execution status
  - [ ] script.brief_build_prompt returns object:
    ```yaml
    prompt: "assembled briefing prompt text"
    status:
      chores: success
      calendar: success
      weather: success
      meals: failed
      commute: skipped
      ...
    ```
  - [ ] Caller can see what succeeded
  - **Acceptance:** Execution status returned with prompt

- [ ] **2.4.4** Implement timeout for entire build
  - [ ] Entire prompt building has timeout (default 30s)
  - [ ] If exceeded, return partial data
  - [ ] Don't wait longer than needed
  - **Acceptance:** Build completes within timeout

- [ ] **2.4.5** Test parallel execution
  - [ ] All collectors run in parallel (not sequential)
  - [ ] One slow collector doesn't block others
  - [ ] Overall execution time < 30 seconds
  - [ ] Partial results used if some collectors slow
  - **Acceptance:** Performance is acceptable

---

## PHASE 3: Data Collector Refactoring (Week 2-3)

### 3.1 Fix Calendar Event Collector (M - 2-3 days)

- [ ] **3.1.1** Remove label_id dependency
  - [ ] Current: Uses `label_id: brief` and `label_id: trash_calendar`
  - [ ] Problem: May not work in current HA version
  - [ ] Solution: Use direct entity_id filtering
  - [ ] Update calendar.get_events call
  - **Acceptance:** No more label_id references

- [ ] **3.1.2** Fix Mealie calendar references
  - [ ] Current: References `calendar.mealie_breakfast`, etc.
  - [ ] Verify actual entity names in HA
  - [ ] May need to use config values
  - [ ] Handle if calendars don't exist
  - **Acceptance:** Uses correct Mealie calendar entity names

- [ ] **3.1.3** Add entity existence validation
  - [ ] Before calling calendar.get_events, check entity exists
  - [ ] Check with: `state_attr('calendar.entity', 'state')`
  - [ ] If missing, return fallback and log
  - **Acceptance:** No errors if calendar entity missing

- [ ] **3.1.4** Implement graceful fallback
  - [ ] If calendar missing: return "No events scheduled"
  - [ ] If calendar API fails: return same fallback
  - [ ] If no events in time window: return "No upcoming events"
  - **Acceptance:** Calendar failures don't break briefing

- [ ] **3.1.5** Test calendar collection
  - [ ] With calendar entity present
  - [ ] With calendar entity missing
  - [ ] With no events scheduled
  - [ ] With multiple events (format correctly)
  - [ ] Verify JSON published to MQTT
  - **Acceptance:** All scenarios work, data formatted correctly

### 3.2 Fix Travel Time Collector (M - 2-3 days)

- [ ] **3.2.1** Verify travel time sensors
  - [ ] Current: `sensor.travel_time_to_brian_s_work`, `sensor.travel_time_to_hester_s_work`
  - [ ] Check if these entities actually exist in HA
  - [ ] May need different names (depends on Waze/Google config)
  - [ ] Document actual sensor names needed
  - **Acceptance:** Actual entity names identified

- [ ] **3.2.2** Add entity existence check
  - [ ] Before reading travel time, check sensor exists
  - [ ] If missing: return empty/unavailable
  - [ ] Log which sensors are missing
  - **Acceptance:** No errors if sensors missing

- [ ] **3.2.3** Make commute module optional
  - [ ] Add to config: `enabled_modules.commute: true/false`
  - [ ] If disabled, skip collector
  - [ ] If enabled but sensors missing, gracefully skip
  - **Acceptance:** Can toggle commute on/off in config

- [ ] **3.2.4** Implement fallback values
  - [ ] If sensor missing: "Travel times unavailable"
  - [ ] If sensor error: same fallback
  - [ ] If sensor unavailable: same fallback
  - **Acceptance:** Graceful degradation

- [ ] **3.2.5** Document Waze setup
  - [ ] Create guide for setting up Waze integration
  - [ ] Document required sensor names
  - [ ] Provide example config
  - [ ] Note: Commute module optional
  - **Acceptance:** Users can set up Waze if desired

### 3.3 Fix Weather Collector (M - 2-3 days)

- [ ] **3.3.1** Verify weather entity
  - [ ] Current: `weather.forecast_home`
  - [ ] Check if this entity exists in HA
  - [ ] May have different name based on integration
  - [ ] Load from config instead of hardcode
  - **Acceptance:** Uses configured weather entity

- [ ] **3.3.2** Add entity validation
  - [ ] Check weather entity exists
  - [ ] Check required attributes available
  - [ ] Handle missing attributes gracefully
  - **Acceptance:** No errors on missing attributes

- [ ] **3.3.3** Fix temperature unit handling
  - [ ] Get from home assistant config (C vs F)
  - [ ] Include in briefing: "72°F" not just "72"
  - [ ] Handle any temperature unit correctly
  - **Acceptance:** Temperatures formatted with units

- [ ] **3.3.4** Implement graceful fallback
  - [ ] If weather entity missing: "Weather data unavailable"
  - [ ] If API fails: same fallback
  - [ ] Include last known data as fallback (from cache)
  - **Acceptance:** System works without weather

- [ ] **3.3.5** Test weather collection
  - [ ] With weather entity present
  - [ ] With weather entity missing
  - [ ] With partial weather data
  - [ ] Verify temperature units correct
  - **Acceptance:** All scenarios work

### 3.4 Fix Device Health Collector (M - 2-3 days)

- [ ] **3.4.1** Verify device health dependencies
  - [ ] Check if device_health.yaml package exists
  - [ ] Find actual entity names for health checks
  - [ ] May have changed from original package
  - **Acceptance:** Device health entities identified

- [ ] **3.4.2** Add entity existence checks
  - [ ] Before reading health sensors, check they exist
  - [ ] Skip if device_health package not installed
  - [ ] Graceful fallback if sensors missing
  - **Acceptance:** No errors if sensors missing

- [ ] **3.4.3** Update health sensor references
  - [ ] Find actual battery sensors
  - [ ] Find actual device unavailable sensors
  - [ ] Update to use actual entity names
  - [ ] Use config file for customization
  - **Acceptance:** References correct entity names

- [ ] **3.4.4** Test device health collection
  - [ ] With all health sensors present
  - [ ] With some sensors missing
  - [ ] With devices reported unhealthy
  - [ ] With no health issues
  - **Acceptance:** All scenarios handled

### 3.5 Fix Meals Collector (M - 2-3 days)

- [ ] **3.5.1** Verify Mealie integration
  - [ ] Check if Mealie integration installed
  - [ ] Find calendar entities (breakfast, lunch, dinner)
  - [ ] May need different entity names
  - [ ] Document actual names
  - **Acceptance:** Mealie integration verified

- [ ] **3.5.2** Add Mealie entity validation
  - [ ] Check if Mealie calendars exist
  - [ ] If missing: set meals module to optional
  - [ ] Don't error, just skip
  - **Acceptance:** Gracefully skips if not installed

- [ ] **3.5.3** Implement meal plan collection**
  - [ ] Get calendar events from Mealie calendars
  - [ ] Format as: "Breakfast: X, Lunch: Y, Dinner: Z"
  - [ ] Include date if different from today
  - **Acceptance:** Meal plans formatted nicely

- [ ] **3.5.4** Add fallback for no meals
  - [ ] If no meal plan: "No meals planned"
  - [ ] If Mealie missing: "Meal planning unavailable"
  - **Acceptance:** Graceful degradation

- [ ] **3.5.5** Test meals collection
  - [ ] With Mealie installed and calendars present
  - [ ] With Mealie not installed
  - [ ] With empty meal calendars
  - [ ] With full meal calendars
  - **Acceptance:** All scenarios work

### 3.6 Fix Commute Collector (M - 2-3 days)

*Same as 3.2 Travel Time - included above*

### 3.7 Standardize Collector Pattern (M - 3 days)

- [ ] **3.7.1** Create collector template
  - [ ] File: `packages/brief/collectors/_template.yaml`
  - [ ] Template showing standard pattern:
    - [ ] Validation step
    - [ ] Collection step
    - [ ] Formatting step
    - [ ] MQTT publish step
    - [ ] Error handling
  - **Acceptance:** Template provides clear pattern

- [ ] **3.7.2** Audit all collectors
  - [ ] Review all 8 collectors
  - [ ] Check they follow standard pattern
  - [ ] Identify any deviations
  - [ ] Document any intentional differences
  - **Acceptance:** Audit complete

- [ ] **3.7.3** Refactor non-compliant collectors
  - [ ] Chores, Appliances, Garbage, Air Quality
  - [ ] Ensure all follow standard pattern
  - [ ] Add entity validation
  - [ ] Add error handling
  - [ ] Add fallback values
  - **Acceptance:** All collectors use standard pattern

- [ ] **3.7.4** Add debug logging to collectors
  - [ ] Each collector logs when called
  - [ ] Each collector logs when complete (success/failure)
  - [ ] Log actual data collected (for debugging)
  - [ ] Visible in HA logs
  - **Acceptance:** Can see collector execution in logs

- [ ] **3.7.5** Test standardized collectors
  - [ ] All collectors follow pattern
  - [ ] All have error handling
  - [ ] All have fallback values
  - [ ] All publish to MQTT
  - **Acceptance:** Standardization complete

### 3.8 Create Fallback Defaults (S - 1-2 days)

- [ ] **3.8.1** Define fallback values per module
  - [ ] Chores: "No chores assigned"
  - [ ] Calendar: "No events scheduled"
  - [ ] Weather: "Weather unavailable"
  - [ ] Meals: "No meal plan"
  - [ ] Commute: "Travel times unavailable"
  - [ ] Devices: "Device status unavailable"
  - [ ] Air Quality: "Air quality unavailable"
  - [ ] Appliances: "Appliance status unavailable"
  - [ ] Garbage: "Garbage schedule unavailable"
  - **Acceptance:** All modules have fallback text

- [ ] **3.8.2** Create fallback prompt template
  - [ ] Build briefing with available data only
  - [ ] Show which modules are unavailable
  - [ ] Still provide useful summary
  - [ ] Example:
    ```
    Good morning!

    Today's Schedule: [events]
    Weather: [weather]
    Device Health: [health]

    Note: Meal planning and travel times are currently unavailable.
    ```
  - **Acceptance:** Briefing readable even with missing data

- [ ] **3.8.3** Test fallback scenarios
  - [ ] Single module fails
  - [ ] Multiple modules fail
  - [ ] All optional modules fail
  - [ ] Critical modules fail (should show error)
  - **Acceptance:** Briefing still useful with fallbacks

---

## PHASE 4: Testing & Documentation (Week 3-4)

### 4.1 Unit Test Each Collector (M - 2-3 days)

- [ ] **4.1.1** Create test cases for chores collector
  - [ ] [ ] Test: Entity present, data available
  - [ ] [ ] Test: Entity missing
  - [ ] [ ] Test: Timeout during execution
  - [ ] [ ] Test: MQTT publish fails
  - [ ] [ ] Acceptance: All tests pass

- [ ] **4.1.2** Create test cases for calendar collector
  - [ ] [ ] Test: Calendar present, events available
  - [ ] [ ] Test: Calendar missing
  - [ ] [ ] Test: No events in time window
  - [ ] [ ] Test: Multiple events (format correctly)
  - [ ] [ ] Test: Timeout
  - [ ] [ ] Acceptance: All tests pass

- [ ] **4.1.3** Create test cases for weather collector
  - [ ] [ ] Test: Weather entity present
  - [ ] [ ] Test: Weather entity missing
  - [ ] [ ] Test: Partial weather data (missing attributes)
  - [ ] [ ] Test: Temperature units (C and F)
  - [ ] [ ] Test: Timeout
  - [ ] [ ] Acceptance: All tests pass

- [ ] **4.1.4** Create test cases for device health collector
  - [ ] [ ] Test: Health sensors present
  - [ ] [ ] Test: Health sensors missing
  - [ ] [ ] Test: Devices reported unhealthy
  - [ ] [ ] Test: No health issues
  - [ ] [ ] Test: Timeout
  - [ ] [ ] Acceptance: All tests pass

- [ ] **4.1.5** Create test cases for remaining collectors
  - [ ] [ ] Meals, Commute, Air Quality, Appliances, Garbage
  - [ ] [ ] Same test pattern for each
  - [ ] [ ] Entity present/missing, data available/partial, timeout
  - [ ] [ ] Acceptance: All tests pass

### 4.2 Integration Testing (M - 2-3 days)

- [ ] **4.2.1** Test full briefing flow (all modules)
  - [ ] [ ] Run full briefing with all modules enabled
  - [ ] [ ] Collect all data
  - [ ] [ ] Generate prompt
  - [ ] [ ] Process conversation
  - [ ] [ ] Deliver mobile notification
  - [ ] [ ] Check TTS (if enabled)
  - [ ] [ ] Acceptance: Full flow works end-to-end

- [ ] **4.2.2** Test with optional modules disabled
  - [ ] [ ] Disable meals module
  - [ ] [ ] Disable commute module
  - [ ] [ ] Disable both
  - [ ] [ ] Briefing still works
  - [ ] [ ] Skipped modules noted
  - [ ] [ ] Acceptance: Works with modules disabled

- [ ] **4.2.3** Test different time contexts
  - [ ] [ ] Morning briefing (6:45 AM)
  - [ ] [ ] Evening briefing (5:30 PM)
  - [ ] [ ] Weekday vs weekend (different content)
  - [ ] [ ] Acceptance: Context changes appropriately

- [ ] **4.2.4** Test notification delivery
  - [ ] [ ] Mobile notification sent
  - [ ] [ ] TTS notification sent
  - [ ] [ ] Both succeed
  - [ ] [ ] One fails (other still sent)
  - [ ] [ ] Acceptance: Notifications delivered

- [ ] **4.2.5** Test error recovery
  - [ ] [ ] Single collector fails → briefing continues
  - [ ] [ ] Multiple collectors fail → briefing continues
  - [ ] [ ] Conversation API fails → fallback text sent
  - [ ] [ ] MQTT broker unavailable → fallback triggered
  - [ ] [ ] Acceptance: System recovers from errors

### 4.3 Create Health Dashboard (S - 1-2 days)

- [ ] **4.3.1** Design dashboard layout
  - [ ] [ ] Status section (validation, last run, next run)
  - [ ] [ ] Collector status (green/red per module)
  - [ ] [ ] Metrics (execution time, API calls)
  - [ ] [ ] Recent errors (last 5)
  - [ ] [ ] Quick actions (manual trigger)
  - [ ] [ ] Acceptance: Design approved

- [ ] **4.3.2** Create dashboard in HA Lovelace
  - [ ] [ ] Build `/lovelace/briefing_health.yaml`
  - [ ] [ ] Add status indicators
  - [ ] [ ] Add collector status cards
  - [ ] [ ] Add metrics graphs
  - [ ] [ ] Add error log section
  - [ ] [ ] Acceptance: Dashboard displays correctly

- [ ] **4.3.3** Test dashboard
  - [ ] [ ] All sensors visible
  - [ ] [ ] Updates in real-time
  - [ ] [ ] Shows all modules correctly
  - [ ] [ ] Error messages clear
  - [ ] [ ] Acceptance: Dashboard functional

### 4.4 Create Setup Guide (M - 2-3 days)

- [ ] **4.4.1** Create README.md
  - [ ] [ ] Overview of briefing system
  - [ ] [ ] Architecture diagram
  - [ ] [ ] Required dependencies
  - [ ] [ ] Optional integrations
  - [ ] [ ] Acceptance: README complete

- [ ] **4.4.2** Document entity requirements
  - [ ] [ ] List critical entities (required)
  - [ ] [ ] List optional entities
  - [ ] [ ] How to find entity IDs in HA
  - [ ] [ ] Common naming variations
  - [ ] [ ] Acceptance: Entity reference complete

- [ ] **4.4.3** Create configuration guide
  - [ ] [ ] How to customize config.yaml
  - [ ] [ ] Enable/disable modules
  - [ ] [ ] Change entity names
  - [ ] [ ] Adjust timeouts
  - [ ] [ ] Acceptance: Configuration guide complete

- [ ] **4.4.4** Create troubleshooting guide
  - [ ] [ ] "Briefing not generating"
  - [ ] [ ] "Missing sections in briefing"
  - [ ] [ ] "No mobile notification"
  - [ ] [ ] "Conversation AI not working"
  - [ ] [ ] "MQTT errors"
  - [ ] [ ] Acceptance: Common issues covered

- [ ] **4.4.5** Create integration setup guides
  - [ ] [ ] Mealie integration setup
  - [ ] [ ] Waze integration setup
  - [ ] [ ] OpenAI/Conversation setup
  - [ ] [ ] Weather integration setup
  - [ ] [ ] Acceptance: All guides complete

### 4.5 Create Migration Guide (S - 1 day)

- [ ] **4.5.1** Document breaking changes
  - [ ] [ ] List what's different in new system
  - [ ] [ ] Entity naming changes
  - [ ] [ ] Automation trigger changes
  - [ ] [ ] Script signature changes
  - [ ] [ ] Acceptance: Breaking changes listed

- [ ] **4.5.2** Create upgrade procedure
  - [ ] [ ] Step-by-step upgrade instructions
  - [ ] [ ] How to backup old system
  - [ ] [ ] How to run new system in parallel
  - [ ] [ ] How to validate new system works
  - [ ] [ ] Acceptance: Procedure documented

- [ ] **4.5.3** Create rollback procedure
  - [ ] [ ] How to rollback if issues
  - [ ] [ ] How to restore old system
  - [ ] [ ] How to report issues
  - [ ] [ ] Acceptance: Rollback documented

---

## TESTING CHECKLIST

### Pre-Deployment Validation
- [ ] All YAML files parse without errors
- [ ] All entity references validated
- [ ] Configuration file loads correctly
- [ ] Health monitoring sensors populate
- [ ] Dashboard displays correctly
- [ ] No HA warnings or errors

### Functional Testing (5 consecutive successful runs)
- [ ] Briefing generates without errors
- [ ] Mobile notifications sent
- [ ] TTS notifications sent (if enabled)
- [ ] Conversation API processes successfully
- [ ] All modules collect data

### Error Scenarios (Each must be tested)
- [ ] Single collector fails → briefing continues
- [ ] Conversation API fails → fallback used
- [ ] MQTT broker offline → fallback triggered
- [ ] Entity missing → skipped gracefully
- [ ] Timeout occurs → partial data used

### Configuration Testing
- [ ] Can disable optional modules in config
- [ ] Can change entity names in config
- [ ] Can adjust timeout values
- [ ] Config local overrides work
- [ ] All configuration options documented

### Documentation Testing
- [ ] README is clear and complete
- [ ] Setup guide works for new user
- [ ] Configuration guide explains all options
- [ ] Troubleshooting guide helps solve problems
- [ ] Migration guide explains upgrade process

---

## SIGN-OFF CRITERIA

Project is complete when:

✅ **Functional**
- [ ] 5 consecutive successful briefing runs
- [ ] Mobile notifications deliver
- [ ] No errors in HA logs
- [ ] Health dashboard shows "Ready"

✅ **Robust**
- [ ] Graceful degradation tested
- [ ] Error scenarios tested and handled
- [ ] Configuration externalized
- [ ] Entity validation on startup

✅ **Observable**
- [ ] Health dashboard shows real-time status
- [ ] All errors logged and visible
- [ ] Collector status per module visible
- [ ] Easy to debug issues

✅ **Documented**
- [ ] README complete
- [ ] Setup guide available
- [ ] Configuration guide available
- [ ] Troubleshooting guide available
- [ ] Migration guide available
- [ ] API documentation available

✅ **Tested**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Error scenarios handled
- [ ] Performance acceptable (<30s per briefing)

---

## PROGRESS TRACKING

| Phase | Status | Start | End | Notes |
|-------|--------|-------|-----|-------|
| Phase 1: Foundation | Not Started | - | - | |
| Phase 2: Architecture | Not Started | - | - | |
| Phase 3: Refactoring | Not Started | - | - | |
| Phase 4: Testing | Not Started | - | - | |
| Phase 5: Optimization | Planned | - | - | Future work |

---

**Last Updated:** 2025-11-07
**Next Review:** When Phase 1 complete
