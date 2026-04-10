# Briefing Package Rebuild - Context & Dependencies

**Last Updated:** 2025-11-07 (Session 2 - Implementation in Progress)

## Session 2 Summary (Current)

### Completed in This Session
1. ✅ **Phase 1: Foundation & Validation** - COMPLETE
   - Created `packages/brief/config_loader.yaml` - 10 template sensors for configuration
   - Created `packages/brief/validator.yaml` - Entity validation automation + persistent notifications
   - Created `packages/brief/health_monitoring.yaml` - Health tracking and execution metrics
   - Fixed duplicate air quality MQTT sensor in `packages/brief/sensors.yaml`
   - Updated `home-assistant-dev-guidelines` skill with documentation references

2. ✅ **Updated Skill** - Added documentation URLs and API references
   - Added critical rule: Verify syntax with official documentation before writing YAML
   - Added REST API and WebSocket API documentation links
   - Added entity validation examples using API

### Key Decisions Made This Session
1. **Configuration Storage:** Used template sensors with attributes instead of YAML config file
   - Reason: More robust - stored in HA state, accessible via `state_attr()`, survives YAML reloads
   - Pattern: `sensor.brief_config_*` with attributes for each setting
   - Verified syntax against: https://www.home-assistant.io/integrations/template/

2. **Validation Approach:** Used automation + template sensors instead of custom script
   - Reason: Follows HA patterns, uses native automations and conditions
   - Checks entities on startup and revalidates on config changes
   - Creates persistent notifications with detailed error messages

3. **Health Monitoring:** Created dedicated package with 8+ sensors + 3 automations
   - Tracks execution status, timestamps, collector status, errors
   - Alerts system when validation fails
   - Provides metrics for optimization (API calls, fallback usage)

### Files Modified/Created
- ✅ `packages/brief/config_loader.yaml` (158 lines) - NEW
- ✅ `packages/brief/validator.yaml` (159 lines) - NEW
- ✅ `packages/brief/health_monitoring.yaml` (221 lines) - NEW
- ✅ `packages/brief/sensors.yaml` (4 lines modified) - Removed duplicate air quality sensor
- ✅ `.claude/skills/home-assistant-dev-guidelines/SKILL.md` (44 lines added) - Documentation refs

### Commits This Session
1. `chore: update home-assistant-dev-guidelines with documentation references`
2. `feat: add configuration loader for briefing system`
3. `feat: add entity validator for briefing system`
4. `feat: add health monitoring for briefing system`
5. `fix: remove duplicate air quality MQTT sensor definition`

### Home Assistant API/Documentation Verified
- ✅ Template Sensors: https://www.home-assistant.io/integrations/template/
- ✅ Scripts: https://www.home-assistant.io/docs/scripts/
- ✅ Automations: https://www.home-assistant.io/docs/automation/
- ✅ Automation Actions: https://www.home-assistant.io/docs/automation/action/
- ✅ Automation Conditions: https://www.home-assistant.io/docs/automation/condition/
- ✅ Persistent Notifications: https://www.home-assistant.io/integrations/persistent_notification/
- ✅ REST API: https://developers.home-assistant.io/docs/api/rest/
- ✅ Configuration: https://www.home-assistant.io/docs/configuration/

### Next Session: Phase 2 - Architecture Improvements
Phase 2 focuses on replacing brittle timing-based sync with proper async patterns:
- Phase 2.1: Refactor MQTT sensor architecture (use wait_template instead of delays)
- Phase 2.2: Add error handling wrapper scripts
- Phase 2.3: Implement async conversation processing with retries
- Phase 2.4: Refactor parallel collection orchestration

Current branch: `feature/briefing-robust-rebuild`
Current status: Ready to begin Phase 2.1

**Last Updated:** 2025-11-07

## Key Files & Structure

### Current Implementation Files
```
packages/brief/
├── sensors.yaml                    # 9 MQTT/template sensors
├── data_collectors.yaml            # 8 collection scripts (broken)
├── template_builder.yaml           # Prompt assembly (fragile timing)
├── notifications_updated.yaml      # Delivery mechanism
├── automations_updated.yaml        # 4 trigger automations
└── README.md                       # Empty
```

### New Files to Create
```
packages/brief/
├── config.yaml                     # Configuration file (entity mappings)
├── validator.yaml                  # Startup validation automation
├── health_monitoring.yaml          # Health tracking sensors/automations
├── helpers/
│   ├── wait_for_collector.yaml    # Async wait helper script
│   ├── safe_call_collector.yaml   # Error handling wrapper
│   └── conversation_wrapper.yaml  # AI processing with error handling
├── collectors/
│   ├── calendar.yaml              # Fixed calendar collector
│   ├── weather.yaml               # Fixed weather collector
│   ├── devices.yaml               # Fixed device health collector
│   ├── meals.yaml                 # Fixed meals collector
│   ├── commute.yaml               # Fixed commute collector
│   └── legacy/
│       ├── chores.yaml            # Original chores (may deprecate)
│       ├── appliances.yaml        # Original appliances (may remove)
│       └── garbage.yaml           # Original garbage (may remove)
└── README.md                       # Setup guide
```

## Architecture Decisions

### 1. Configuration-Driven Design
**Decision:** Use external YAML config file instead of hardcoding entity names

**Rationale:**
- Allows users to customize entity names without code changes
- Supports multiple HA instances with different entity names
- Makes it easy to enable/disable modules
- Clear documentation of all dependencies

**File:** `packages/brief/config.yaml`

### 2. Optional Modules with Graceful Skip
**Decision:** Make all modules except calendar/weather/health optional

**Rationale:**
- Users may not have all integrations installed
- Missing modules shouldn't break the whole system
- Optional modules skip silently when unavailable
- Fallback text used for critical modules

**Modules:**
- **Required:** Calendar, Weather/Air Quality, Device Health
- **Optional:** Mealie, Commute, Chores, Appliances, Garbage

### 3. Async Pattern with Wait Templates
**Decision:** Replace arbitrary 2-second delays with `wait_template`

**Rationale:**
- More reliable than timing-based synchronization
- Respects different MQTT broker performance
- Timeout handling prevents infinite waits
- Observable - can see what we're waiting for

**Pattern:**
```yaml
- wait_template: "{{ state_attr('sensor.brief_collector_status', 'chores_complete') == true }}"
  timeout: "{{ config.timeout_seconds }}"
  continue_on_timeout: true
```

### 4. Collector Wrapper Functions
**Decision:** Create wrapper scripts for error handling and retries

**Rationale:**
- Standardizes error handling across all collectors
- Centralizes retry logic
- Makes testing easier
- Visible logging of failures

**Scripts:**
- `script.brief_safe_call_collector` - Generic wrapper
- `script.brief_wait_for_collector` - MQTT wait helper
- `script.brief_call_conversation` - AI with error handling

### 5. Health Monitoring & Observability
**Decision:** Create comprehensive health tracking sensors

**Rationale:**
- Users can see what's working and what's broken
- Enables debugging without logs
- Supports automated alerts
- Foundation for optimization (caching, rate limiting)

**Sensors:**
- `sensor.brief_execution_status` - Last run status
- `sensor.brief_collectors_status` - Per-collector results (JSON)
- `sensor.brief_last_execution_time` - When it last ran
- `sensor.brief_next_execution` - When it's scheduled
- `input_boolean.brief_health_warning` - Alert flag

### 6. MQTT vs. Template-Based State
**Decision:** Continue using MQTT for collector results but add template fallback

**Rationale:**
- MQTT is already working for 8 data sources
- Template sensors can aggregate results
- Hybrid approach provides flexibility
- Easy to debug MQTT topics

**Pattern:**
- Data collectors → MQTT topics → MQTT sensors → Template builders
- Can read from either MQTT sensors or trigger script directly

## Integration Points

### Home Assistant Services Called
1. **`conversation.process`** - AI processing (with error handling)
   - Entity: `conversation.chatgpt` (verify ID correct)
   - Input: Built prompt text
   - Output: AI-generated briefing text

2. **`notify.all_mobile_devices`** - Mobile notification delivery
   - Title: "Daily Briefing"
   - Message: AI-generated text

3. **`tts.speak`** - TTS delivery (optional)
   - Entity: `media_player.display_kitchen`
   - Message: AI-generated text or fallback

4. **`mqtt.publish`** - Data collector results
   - Topics: `home/brief/data/{module}`
   - Payload: JSON formatted collector results

5. **`calendar.get_events`** - Calendar event retrieval (fixed)
   - Entities: Calendar entities (no more label_id)
   - Parameters: Time window (tomorrow for morning briefing, today for evening)

### External Dependencies
1. **MQTT Broker**
   - Publish: `home/brief/data/chores`, `weather`, `calendar`, etc.
   - Subscribe: `home/ai/response` (AI response)

2. **Conversation Agent**
   - Must be configured: `conversation.chatgpt` (or alternative)
   - Must have API key/credentials configured

3. **Calendar Integration**
   - Google Calendar, Caldav, or local calendar
   - Must have calendar entities created

4. **Weather Integration**
   - Built-in weather or custom integration
   - Must have `weather.forecast_home` or similar

5. **Optional: Mealie Integration**
   - For meal planning
   - Requires: `calendar.mealie_breakfast`, `mealie_lunch`, `mealie_dinner`

6. **Optional: Waze Integration**
   - For commute times
   - Requires: Travel time sensors for each person

## Broken Dependencies (Current)

### Critical Blockers
1. **`conversation.chatgpt`** ID may be wrong
   - Check actual agent ID: `ha api GET /api/conversation/agent/info`
   - May be `conversation.chatgpt_homeassistant`, `conversation.openai`, etc.

2. **Mealie Calendars** may not exist
   - References: `calendar.mealie_breakfast`, `mealie_lunch`, `mealie_dinner`
   - May need to create these in Mealie integration

3. **Calendar Labels** may not work
   - Uses `label_id: brief` and `label_id: trash_calendar`
   - HA may not support labels in this version
   - Should use `entity_id` directly instead

### Validation Required
1. **Travel Time Sensors**
   - `sensor.travel_time_to_brian_s_work`
   - `sensor.travel_time_to_hester_s_work`
   - Requires Waze integration or Google Travel integration

2. **Weather Entity**
   - `weather.forecast_home` expected
   - May be different name: `weather.openweather`, etc.

3. **Media Player**
   - `media_player.display_kitchen` for TTS
   - May be different name or missing

4. **Dishwasher Sensors**
   - References long device-specific IDs
   - May break if device replaced

5. **Duplicate Air Quality**
   - MQTT sensor defined in TWO places:
     - `packages/brief/sensors.yaml` (incomplete)
     - `packages/air_quality.yaml` (complete)
   - Must consolidate to one definition

## Data Flow Mapping

### Current (Broken) Flow
```
[6:45 AM / 5:30 PM / Calendar Event / Device Change Trigger]
                    ↓
         script.daily_brief
                    ↓
       script.brief_build_prompt
       (parallel execution)
                    ↓
    [8 collectors publish to MQTT]
                    ↓
  [Arbitrary 2-second delay]
                    ↓
   [Template reads MQTT sensors]
   [Builds context prompt]
                    ↓
    conversation.chatgpt
    (may fail silently!)
                    ↓
     [Mobile notification]
     [TTS notification]
```

### Proposed (Robust) Flow
```
[6:45 AM / 5:30 PM / Calendar Event / Device Change Trigger]
                    ↓
   [Check if already running (debounce)]
                    ↓
         script.daily_brief
                    ├─ Load config
                    ├─ Validate critical entities exist
                    ├─ Log execution start
                    ↓
   script.brief_build_prompt (wrapped with error handling)
   (parallel execution with timeout)
                    ├─ For each enabled module:
                    │  ├─ Call collector with wrapper
                    │  ├─ Wait for MQTT result (max 15s)
                    │  ├─ Log success/failure
                    │  ├─ Use fallback on failure
                    │  └─ Add to prompt
                    └─ Return assembled prompt
                    ↓
   script.brief_call_conversation (with error handling)
   (AI processing with retry logic)
                    ├─ Try conversation.process
                    ├─ On failure: retry (2x)
                    ├─ On final failure: use fallback text
                    └─ Return briefing text
                    ↓
   script.brief_deliver (with error handling)
                    ├─ Mobile notification
                    ├─ TTS notification (if enabled)
                    └─ Log delivery result
                    ↓
   [Update health sensors]
   [Log execution complete]
```

## Configuration File Structure

```yaml
# packages/brief/config.yaml

brief:
  # Feature toggles
  enabled_modules:
    calendar: true           # Required
    weather: true            # Required
    device_health: true      # Required
    meals: true              # Optional
    commute: true            # Optional
    chores: false            # Deprecated
    appliances: false        # Deprecated
    garbage: false           # Deprecated

  # Timeout handling
  timeout_seconds: 30        # Max wait for collectors
  max_retries: 2             # Conversation API retries
  retry_delay_ms: 1000       # Delay between retries

  # Entity references
  entities:
    conversation_agent: "conversation.chatgpt"
    weather: "weather.forecast_home"
    media_player: "media_player.display_kitchen"
    notification_service: "notify.all_mobile_devices"

  # Calendar entities
  calendars:
    default: "calendar.events"
    meals_breakfast: "calendar.mealie_breakfast"
    meals_lunch: "calendar.mealie_lunch"
    meals_dinner: "calendar.mealie_dinner"

  # Travel time sensors (optional)
  travel_time:
    brian: "sensor.travel_time_to_brian_s_work"
    hester: "sensor.travel_time_to_hester_s_work"

  # MQTT configuration
  mqtt:
    base_topic: "home/brief"
    response_topic: "home/ai/response"
    timeout_seconds: 5

  # Time windows
  time_windows:
    morning:
      start_hour: 6
      end_hour: 12
    evening:
      start_hour: 17
      end_hour: 21

  # Feature flags
  features:
    tts_enabled: true        # Send to kitchen display
    mobile_enabled: true     # Send to phones
    caching_enabled: false   # Future optimization
    rate_limiting_enabled: false  # Future optimization
```

## Testing Strategy

### Unit Tests (Per Collector)
```yaml
Test Scenarios:
- Entity present & responsive (normal case)
- Entity missing (should use fallback)
- Entity returns error (should handle gracefully)
- Collector timeout (should use fallback)
- Partial data available (should use partial data)
```

### Integration Tests
```yaml
Test Scenarios:
- Full briefing with all modules enabled
- Briefing with optional modules disabled
- Briefing with different time contexts (morning/evening/weekend)
- Briefing with calendar events (30 min trigger)
- Conversation API failure → fallback text
- MQTT broker unavailable → template sensor fallback
- Mobile notification delivery
- TTS notification delivery
```

### Deployment Tests
```yaml
Test Scenarios:
- Deploy to production HA instance
- Run 5 consecutive briefings without error
- Verify mobile notifications received
- Verify TTS output (if enabled)
- Check health sensors populated correctly
- Run with various entity names (config customization)
```

## Migration Path

### From Old System to New
1. **Keep both systems running** during transition
2. **Run new briefing** on alternate schedule (test schedule)
3. **Compare outputs** with old system
4. **Once stable**, switch production to new system
5. **Keep old system** as fallback for 1 week
6. **Remove old system** after validation

### Rollback Procedure
If new system breaks in production:
1. Switch back to old system (temporarily)
2. Revert code changes
3. Reload automations/scripts
4. Verify briefings resume
5. Debug and fix issues offline

## Documentation Requirements

### For Users
1. Setup guide - how to configure briefing
2. Entity reference - which entities are required/optional
3. Configuration guide - how to customize entity names
4. Troubleshooting - common issues and fixes

### For Developers
1. Architecture overview - how system works
2. Collector development guide - how to add new collectors
3. Testing guide - how to test changes
4. API reference - all exposed scripts/sensors

### For Operations
1. Health monitoring guide - what sensors mean
2. Debugging guide - how to troubleshoot failures
3. Performance optimization guide - caching, rate limiting
4. Upgrade guide - how to upgrade safely

## Success Criteria

**Old System Problems:**
- ❌ References non-existent entities (Mealie, travel time, conversation agent)
- ❌ Silent failures (missing sections in briefing)
- ❌ Brittle timing (arbitrary 2-second delays)
- ❌ No error handling (API failures crash system)
- ❌ No observability (can't see what's working)

**New System Solutions:**
- ✅ Validates all entities on startup
- ✅ Gracefully skips missing optional modules
- ✅ Uses proper async synchronization
- ✅ Error handling at each step
- ✅ Health dashboard shows system status
- ✅ Comprehensive logging for debugging
- ✅ Configuration-driven (easy to customize)
- ✅ Modular (can add/remove features easily)

## Technical Constraints

### Home Assistant Version
- Minimum: HA 2024.1 (for `wait_template` in scripts)
- Recommended: HA 2024.6+ (latest bug fixes)

### MQTT Requirements
- MQTT broker must be accessible
- Message retention preferred (not required)
- QoS 1 or 2 for data topics

### API Rate Limits
- OpenAI conversation: ~3-5 requests per minute (default)
- Need rate limiting if running briefings very frequently
- Caching can reduce API calls significantly

### Performance Targets
- Full briefing generation: < 30 seconds
- Mobile notification delivery: < 5 seconds
- TTS generation: < 10 seconds (depends on TTS service)
- Health sensor updates: < 2 seconds
