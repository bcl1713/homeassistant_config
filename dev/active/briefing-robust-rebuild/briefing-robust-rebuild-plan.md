# Briefing Package Robust Rebuild Plan

**Last Updated:** 2025-11-07

## Executive Summary

The Home Assistant briefing system is an AI-powered daily briefing that collects data from multiple home systems, builds contextual prompts, and delivers personalized updates via mobile notifications and TTS. While architecturally sound, the current implementation is **fragile and broken** due to:

- **Missing entity dependencies** (Mealie calendars, travel time sensors, conversation agent misconfiguration)
- **Brittle timing-based synchronization** using arbitrary delays instead of proper async handling
- **Silent failure modes** with no error handling or validation
- **Duplicate definitions** causing conflicts (air quality sensor in two places)
- **No graceful degradation** when optional modules fail
- **Hard-coded entity IDs** vulnerable to device replacement

**Objective:** Rebuild the briefing system with a **resilient architecture** featuring:
- Entity validation and existence checking
- Graceful degradation when modules or integrations fail
- Proper async synchronization using `wait_template`
- Comprehensive error handling and logging
- Health monitoring and debug visibility
- Modular design allowing optional data sources

**Scope:** Complete rewrite of `packages/brief/` with backward compatibility maintained for key features (calendar events, weather/air quality, device health).

**Timeline:** 3-4 weeks (phased approach: foundation → architecture → refactor → testing)

---

## Current State Analysis

### Existing Architecture

**System Components:**
```
Trigger (time/calendar/event)
  ↓
script.daily_brief (main orchestrator)
  ↓
script.brief_build_prompt (context assembly)
  ↓
[8 parallel data collectors]
  │ ├─ Chores
  │ ├─ Appliances
  │ ├─ Calendar
  │ ├─ Garbage
  │ ├─ Meals (Mealie)
  │ ├─ Devices
  │ ├─ Commute (Travel time)
  │ └─ Air Quality
  ↓
[MQTT sensors collect results]
  ↓
Template builder assembles prompt
  ↓
conversation.chatgpt (AI processing)
  ↓
[Deliver via mobile + TTS]
```

**Files Involved:**
- `sensors.yaml` - 8 MQTT collectors + 1 template summary sensor
- `data_collectors.yaml` - 8 parallel collection scripts
- `template_builder.yaml` - Prompt assembly from collector data
- `notifications_updated.yaml` - Delivery mechanism
- `automations_updated.yaml` - 4 trigger automations

**Key Dependency Issues:**

| Entity | Status | Impact |
|--------|--------|--------|
| `conversation.chatgpt` | 🔴 Likely wrong ID | **CRITICAL** - AI won't work |
| `calendar.mealie_*` (3) | 🔴 Likely missing | Meal planning empty |
| `sensor.travel_time_to_*` (2) | 🔴 Likely missing | Commute times missing |
| `weather.forecast_home` | 🟡 Uncertain | Weather section empty |
| `media_player.display_kitchen` | 🟡 Uncertain | TTS won't work |
| Calendar labels (`brief`, `trash_calendar`) | 🔴 Likely unsupported | Calendar won't filter |
| MQTT topics | ✅ Assumed working | Air quality duplicated |

### Current Weaknesses

**1. Fragile Timing**
- 2-second arbitrary delay after parallel collectors (line 30, template_builder.yaml)
- 1-second delay before checking MQTT results (line 17, notifications_updated.yaml)
- No guarantee MQTT messages processed by then

**2. Silent Failures**
- Collectors fail silently if entities don't exist
- No validation of conversation agent availability
- No logging of which collectors succeeded/failed
- Missing sections just appear empty in prompt

**3. Hard-coded Dependencies**
- Long device-specific entity IDs: `binary_sensor.014030536224000994_dishcare_dishwasher_event_saltnearlyempty`
- No configuration file for customization
- Calendar label system may not work in all HA versions

**4. Duplicate Definitions**
- Air quality MQTT sensor defined in both:
  - `packages/brief/sensors.yaml` (incomplete)
  - `packages/air_quality.yaml` (complete)
- Creates merge conflicts and confusion

**5. Error Handling**
- No try/catch for conversation.process
- No fallback if AI API fails
- No retry logic for failed collectors
- No rate limiting on API calls

**6. Manual Trigger Design**
- Calendar event trigger (30 min before) uses poorly named automation
- Device tracker trigger is too noisy (triggers on ANY change)
- No deduplication of overlapping triggers

---

## Proposed Future State

### Architecture Principles

1. **Validation First** - Check entity existence before using
2. **Graceful Degradation** - Missing modules don't break the whole system
3. **Explicit Errors** - Failures are logged and reported, not silent
4. **Async-Safe** - Proper wait conditions instead of arbitrary delays
5. **Modular & Optional** - Each data source can be enabled/disabled
6. **Configuration-Driven** - Entity IDs externalized to config file
7. **Observable** - Health monitoring and debug dashboards

### New Architecture

```
Startup
  ↓
[Health Check: Validate critical entities exist]
  ↓
Trigger (time/calendar/event)
  ↓
script.daily_brief
  ├─ Load configuration
  ├─ Validate enabled modules
  ├─ Parallel execution with timeout:
  │  ├─ [Chores - optional]
  │  ├─ [Calendar - required]
  │  ├─ [Weather/Air Quality - required]
  │  ├─ [Device Health - required]
  │  ├─ [Meals - optional]
  │  └─ [Commute - optional]
  ├─ Collect results (success or fallback)
  ├─ Assemble prompt (with present data)
  ├─ AI processing (with error handling)
  ├─ Delivery (mobile + TTS with fallback)
  └─ Log execution results
  ↓
Health monitoring updates
  ↓
Debug sensors updated
```

### Key Improvements

**1. Configuration File** (`brief_config.yaml`)
```yaml
brief:
  enabled_modules:
    calendar: true
    weather: true
    device_health: true
    chores: true
    meals: true
    commute: true
    appliances: false
    garbage: false

  entities:
    conversation_agent: "conversation.chatgpt"
    weather: "weather.forecast_home"
    media_player: "media_player.display_kitchen"

  calendars:
    events: "calendar.events"
    meals_breakfast: "calendar.mealie_breakfast"
    meals_lunch: "calendar.mealie_lunch"
    meals_dinner: "calendar.mealie_dinner"

  travel_time:
    brian: "sensor.travel_time_to_brian_s_work"
    hester: "sensor.travel_time_to_hester_s_work"

  timeout_seconds: 30
  max_retries: 2
```

**2. Validation System**
- Startup automation checks critical entities exist
- Creates `input_boolean.brief_is_ready` sensor
- Persistent notification if setup incomplete
- Health dashboard shows entity status

**3. Error Handling**
```yaml
# Each collector wrapped with error handling
- try:
    - call data collector
    - wait for MQTT result (max 15s)
  catch:
    - log error
    - set fallback value
    - mark collector failed
```

**4. Async Synchronization**
```yaml
# Instead of: delay: 2 seconds
# Use: wait for all MQTT sensors to update or timeout
- wait_template: "{{ states('sensor.brief_collector_status') == 'ready' }}"
  timeout: "{{ timeout }}"
  continue_on_timeout: true
```

**5. Health Monitoring**
- `sensor.brief_last_execution_time`
- `sensor.brief_collectors_status` (JSON with pass/fail per module)
- `sensor.brief_next_scheduled_execution`
- `input_boolean.brief_health_warning` (on failures)

**6. Graceful Degradation**
- Optional modules (meals, commute, chores) silently skip if missing
- Critical modules (calendar, weather, health) have fallback text
- Conversation still works even if 50% of data unavailable
- Missing modules noted in briefing ("Note: Meal planning unavailable")

---

## Implementation Phases

### Phase 1: Foundation & Validation (Week 1)
**Objective:** Establish entity validation and configuration system

#### 1.1 Create Configuration File (S)
- Create `packages/brief/config.yaml` with entity mappings
- Define timeout values and feature flags
- Document all required vs. optional dependencies
- **Acceptance:** Config file loads without errors, all entities mappable

#### 1.2 Build Entity Validator (M)
- Create `packages/brief/validator.yaml` with validation automation
- Check critical entities on startup (conversation agent, weather)
- Create `input_boolean.brief_validation_passed` sensor
- Persistent notification if setup incomplete
- **Acceptance:** System won't attempt briefing if critical entities missing

#### 1.3 Establish Health Monitoring (M)
- Create `packages/brief/health_monitoring.yaml`
- Define `sensor.brief_execution_status` (template)
- Define `sensor.brief_collectors_status` (JSON tracking)
- Define `sensor.brief_next_execution` (template)
- **Acceptance:** Health sensors populate correctly on each execution

#### 1.4 Fix Duplicate Air Quality Definition (S)
- Remove air quality MQTT sensor from `sensors.yaml`
- Keep only the version in `packages/air_quality.yaml`
- Update collector to reference correct sensor
- **Acceptance:** No duplicate MQTT sensor definitions

### Phase 2: Architecture Improvements (Week 2)
**Objective:** Replace timing-based sync with proper async, add error handling

#### 2.1 Refactor MQTT Sensor Architecture (M)
- Replace arbitrary delays with `wait_template` pattern
- Create helper script `script.brief_wait_for_collector` (retryable wait)
- Implement timeout handling with fallback values
- **Acceptance:** All collectors use wait_template, no arbitrary delays

#### 2.2 Add Error Handling Wrapper (M)
- Create `script.brief_safe_call_collector` wrapper
- Implements try/catch pattern using `continue_on_error`
- Logs failures to `sensor.brief_collector_errors`
- Sets fallback MQTT values on failure
- **Acceptance:** All collectors wrapped, errors logged, fallbacks applied

#### 2.3 Implement Async Conversation (M)
- Replace `conversation.process` direct call with wrapper
- Add error handling for API failures
- Implement retry logic (2 retries)
- Fallback to generic briefing text on failure
- **Acceptance:** AI failure doesn't crash system, fallback text used

#### 2.4 Refactor Parallel Collection (M)
- Update `script.brief_build_prompt` to call wrapped collectors
- Implement selective execution based on `brief_config.yaml`
- Return status object showing which collectors succeeded
- **Acceptance:** Collectors execute in parallel with proper error isolation

### Phase 3: Data Collector Refactoring (Week 2-3)
**Objective:** Fix broken collectors, add validation, implement graceful degradation

#### 3.1 Fix Calendar Event Collector (M)
- Remove dependency on `label_id` (replace with direct entity_id)
- Fix Mealie calendar references to use actual entity names
- Add validation: check calendar entity exists before calling
- Fallback: return empty list if calendar unavailable
- **Acceptance:** Calendar events collected or gracefully skipped

#### 3.2 Fix Travel Time Collector (M)
- Verify Waze integration setup or document required config
- Add entity existence check before reading
- Gracefully skip if sensors don't exist
- Fallback: empty string instead of error
- **Acceptance:** Travel time collected if available, skipped if not

#### 3.3 Fix Weather Collector (M)
- Verify weather entity name and attributes
- Add error handling for missing attributes
- Fallback: use generic "Weather data unavailable" message
- **Acceptance:** Weather integrated or gracefully skipped

#### 3.4 Standardize Collector Pattern (M)
- All collectors follow template pattern:
  1. Validate source entity exists
  2. Collect data with error handling
  3. Format for MQTT publish
  4. Publish with timestamp
  5. Set health status
- **Acceptance:** All 8 collectors follow identical error handling pattern

#### 3.5 Create Fallback Defaults (S)
- Define sensible fallback values for each module
- Empty list for calendar/meals/commute
- Generic text for weather/health
- Chores defaults to "No assignments"
- **Acceptance:** Briefing still works if all modules fail

### Phase 4: Testing & Documentation (Week 3-4)
**Objective:** Validate functionality, add monitoring, update documentation

#### 4.1 Unit Test Each Collector (M)
- Test with entity present (normal case)
- Test with entity missing (graceful degradation)
- Test with partial data (error handling)
- Test with timeout (fallback values)
- **Acceptance:** All collectors pass unit tests

#### 4.2 Integration Testing (M)
- Test full briefing flow end-to-end
- Test with various modules disabled
- Test with different time contexts (morning vs evening)
- Test notification delivery (mobile + TTS)
- **Acceptance:** Briefing works in all configuration combinations

#### 4.3 Create Health Dashboard (S)
- Add HA dashboard showing:
  - Last execution time
  - Collector status (pass/fail)
  - Next scheduled execution
  - Configuration status
  - Error logs (recent)
- **Acceptance:** Dashboard shows real-time system status

#### 4.4 Create Setup Guide (M)
- Document required entities and setup steps
- List optional integrations (Mealie, Waze)
- Provide configuration template
- Include troubleshooting section
- **Acceptance:** New user can set up briefing without code changes

#### 4.5 Migration Guide (S)
- Document how to migrate from old system
- List breaking changes (if any)
- Provide rollback procedure
- **Acceptance:** Existing setup can cleanly upgrade

### Phase 5: Optimization (Future)
**Objective:** Performance and reliability enhancements

#### 5.1 Response Caching
- Cache briefing text for 2 hours
- Only regenerate if data significantly changed
- Reduces API calls and improves reliability

#### 5.2 Rate Limiting
- Prevent multiple briefings within 15 minutes
- Per-person rate limiting
- API call budget tracking

#### 5.3 Advanced Monitoring
- Historical execution metrics
- Performance tracking per collector
- Automated alerts for patterns of failure

---

## Detailed Task Breakdown

See `briefing-robust-rebuild-tasks.md` for detailed task checklist with acceptance criteria.

---

## Risk Assessment & Mitigation

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|-----------|
| Mealie calendars don't exist | High | High | Make meals optional, skip gracefully, document setup |
| Conversation agent ID wrong | Critical | High | Validate on startup, provide alternative agent names |
| Travel time sensors missing | Medium | Medium | Make commute optional, graceful skip |
| MQTT broker failure | Medium | Low | Check MQTT connectivity, fallback to template sensors |
| API rate limiting | Low | Low | Implement rate limiting, cache responses |
| Breaking changes for users | High | Low | Detailed migration guide, rollback procedure |
| Timeout values too aggressive | Medium | Medium | Make timeout configurable, test in various scenarios |
| Entity name changes | Medium | Medium | Configuration file makes it easy to update |

**Overall Risk Level:** Medium (mostly due to missing integration setup, not code issues)

---

## Success Metrics

**Before:** System is broken, produces errors, references non-existent entities

**After:**
1. ✅ Briefing system generates daily without errors (100% success rate)
2. ✅ All critical modules (calendar, weather, health) deliver data
3. ✅ Optional modules gracefully skip if missing (no errors)
4. ✅ Health dashboard shows system status clearly
5. ✅ Setup documentation allows new users to configure without code changes
6. ✅ Failure modes are logged and visible, not silent
7. ✅ System tolerates entity name changes (config-driven)
8. ✅ Conversation API failures don't crash briefing (fallback text)

---

## Required Resources & Dependencies

### External Integrations
- **MQTT Broker** (assumed existing)
- **Conversation Agent** (ChatGPT or alternative)
- **Calendar Integration** (Google Calendar, Caldav, or local)
- **Weather Integration** (optional, provides weather data)
- **Mealie Integration** (optional, provides meal planning)
- **Waze/Google Travel** (optional, provides commute times)

### Home Assistant Components
- Home Assistant 2024.1+ (for `wait_template` stability)
- MQTT integration enabled
- Notification system configured
- TTS integration (optional, for kitchen display)

### Required HA Entities (Minimum)
- `conversation.chatgpt` (or alternative agent)
- `weather.forecast_home` (or similar)
- `notify.all_mobile_devices` (or similar)
- Chore input booleans (optional)
- Device health sensors (optional)

### Development Requirements
- Git access to repository
- SSH access to HA instance (for testing)
- .env file with HA_TOKEN and HAOS_IP
- Home Assistant running on 2024.1 or later

---

## Timeline Estimates

| Phase | Duration | Effort | Priority |
|-------|----------|--------|----------|
| Phase 1: Foundation | 3-4 days | Medium | P0 Critical |
| Phase 2: Architecture | 3-4 days | Medium | P0 Critical |
| Phase 3: Refactoring | 4-5 days | Large | P1 High |
| Phase 4: Testing | 3-4 days | Medium | P2 Medium |
| Phase 5: Optimization | 2-3 days (future) | Small | P3 Low |

**Total:** 13-20 days of work, estimated 3-4 weeks calendar time

**Quick Path (2 weeks):** Do Phase 1 + Phase 2 + minimal Phase 3 + integration testing only

---

## Dependencies & Blockers

### Must Complete First
1. Validate entity names via Home Assistant API (in progress)
2. Determine Mealie integration status (required for Phase 3.1)
3. Determine Waze integration status (required for Phase 3.2)
4. Verify conversation agent ID (required for Phase 2.3)

### External Dependencies
- Home Assistant version must support `wait_template` in scripts
- MQTT broker must be running and stable
- Calendar integration must be functional (for Phase 3.1 testing)

### Decision Points
1. Should chores be required or optional? (Current: optional)
2. Should appliances/garbage be removed? (Recommended: remove, not implemented)
3. Should Mealie be required or optional? (Current: optional)
4. What's the timeout tolerance? (Recommended: 30 seconds)

---

## Acceptance Criteria (Overall)

The briefing rebuild is complete when:

1. **Functional**
   - Daily briefing generates without errors (5 consecutive successful runs)
   - Mobile notifications deliver consistently
   - TTS delivery works (if enabled)
   - Conversation AI processing completes successfully

2. **Robust**
   - No silent failures (all errors logged)
   - Graceful degradation when modules missing
   - Validates entity existence on startup
   - Configuration externalized and customizable

3. **Observable**
   - Health dashboard shows real-time status
   - Collector success/failure logged
   - Error patterns visible in sensors
   - Easy to debug when issues arise

4. **Documented**
   - Setup guide for new installations
   - Migration guide for existing users
   - Troubleshooting documentation
   - Architecture documentation

5. **Tested**
   - All collectors pass unit tests
   - Integration tests pass for standard config
   - Tested with missing optional modules
   - Tested with alternative entity names

---

## Next Steps

1. **Immediate:** Validate entity names via Home Assistant API
2. **Week 1:** Complete Phase 1 (Foundation) tasks
3. **Week 2:** Complete Phase 2 (Architecture) tasks
4. **Week 2-3:** Complete Phase 3 (Refactoring) tasks
5. **Week 3-4:** Complete Phase 4 (Testing) tasks
6. **Week 4:** Deploy and monitor in production

See `briefing-robust-rebuild-tasks.md` for detailed task list.
