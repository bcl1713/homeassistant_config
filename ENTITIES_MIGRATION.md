# Entity Naming Standardization - Complete Mapping

This document provides a comprehensive mapping between current entity IDs and their standardized replacements.

## Table of Contents
- [Input Booleans](#input-booleans)
- [Lights](#lights)
- [Sensors](#sensors)
- [Binary Sensors](#binary-sensors)
- [Scripts](#scripts)
- [Automations](#automations)
- [Media Players](#media-players)
- [Input Selects](#input-selects)

## Input Booleans

| Current Entity ID | Standardized Entity ID | Friendly Name |
|-------------------|------------------------|---------------|
| input_boolean.guest_mode | input_boolean.mode_guest | Guest Mode |
| input_boolean.camera_notifications_indoor | input_boolean.notification_camera_indoor | Indoor Camera Notifications |
| input_boolean.camera_notifications_outdoor | input_boolean.notification_camera_outdoor | Outdoor Camera Notifications |
| input_boolean.chore_dishwasher_completed | input_boolean.chore_dishwasher_completed | Dishwasher - Completed Today |
| input_boolean.chore_bathroom_completed | input_boolean.chore_bathroom_completed | Bathroom - Completed This Weekend |
| input_boolean.brian_lamp_dimming | input_boolean.dimming_lamp_brian | Brian's Lamp Dimming Active |
| input_boolean.hester_lamp_dimming | input_boolean.dimming_lamp_hester | Hester's Lamp Dimming Active |
| input_boolean.front_lights_auto_off | input_boolean.auto_off_lights_front | Front Lights Auto Off |
| input_boolean.back_lights_auto_off | input_boolean.auto_off_lights_back | Back Lights Auto Off |
| input_boolean.doorbell_lights_auto_off | input_boolean.auto_off_lights_doorbell | Doorbell Lights Auto Off |
| input_boolean.camera_notifications | input_boolean.notification_camera | Camera Notifications |

## Lights

| Current Entity ID | Standardized Entity ID | Friendly Name |
|-------------------|------------------------|---------------|
| light.living_room_center | light.living_room_ceiling_center | Living Room Ceiling Center |
| light.living_room_left | light.living_room_ceiling_left | Living Room Ceiling Left |
| light.living_room_right | light.living_room_ceiling_right | Living Room Ceiling Right |
| light.brian_s_table_lamp | light.bedroom_table_lamp_brian | Brian's Bedside Lamp |
| light.hester_s_table_lamp | light.bedroom_table_lamp_hester | Hester's Bedside Lamp |
| light.towners_room_light | light.bedroom_towner_ceiling | Towner's Room Ceiling |
| light.towners_bed_lights | light.bedroom_towner_led | Towner's LED Lights |
| light.dimmer | light.bedroom_porter_ceiling | Porter's Room Ceiling |
| light.hallway_entry | light.hallway_entry | Hallway Entry |
| light.hallway_corridor | light.hallway_corridor | Hallway Corridor |
| light.hallway_lamp | light.hallway_lamp | Hallway Lamp |
| light.kitchen_fan | light.kitchen_ceiling_fan | Kitchen Fan Light |
| light.kitchen_bar_lights | light.kitchen_bar | Kitchen Bar Lights |
| light.kitchen_counter_lights | light.kitchen_counter | Kitchen Counter Lights |
| light.dining_room_table_light | light.dining_room_table | Dining Room Table Light |
| light.back_yard | light.outdoor_backyard | Back Yard Light |
| light.front_yard_lights | light.outdoor_front_yard | Front Yard Lights |
| light.outdoor_plug_light | light.outdoor_plugin | Outdoor Plugin Light |
| light.christmas_tree | light.seasonal_christmas_tree | Christmas Tree |
| light.front_doorbell_ring_light | light.doorbell_front_ring | Front Doorbell Ring Light |
| light.front_doorbell_infrared | light.doorbell_front_infrared | Front Doorbell Infrared |
| light.ratgdov25i_0cd7df_light | light.garage_door_light | Garage Door Light |

## Light Groups

| Current Entity ID | Standardized Entity ID | Friendly Name |
|-------------------|------------------------|---------------|
| light.entry_lights | light.group_entry | Entry Lights |
| light.downstairs_lights | light.group_downstairs | Downstairs Lights |
| light.after_dark_entry_lights | light.group_entry_after_dark | After Dark Entry Lights |
| light.outside_lights | light.group_outdoor | Outside Lights |

## Sensors

| Current Entity ID | Standardized Entity ID | Friendly Name |
|-------------------|------------------------|---------------|
| sensor.living_room_all_count | sensor.camera_living_room_all_count | Living Room All Count |
| sensor.front_doorbell_person_count | sensor.camera_doorbell_front_person_count | Front Doorbell Person Count |
| sensor.front_drive_all_count | sensor.camera_front_drive_all_count | Front Drive All Count |
| sensor.front_drive_person_count | sensor.camera_front_drive_person_count | Front Drive Person Count |
| sensor.living_room_person_count | sensor.camera_living_room_person_count | Living Room Person Count |
| sensor.front_drive_bus_count | sensor.camera_front_drive_bus_count | Front Drive Bus Count |
| sensor.back_door_all_count | sensor.camera_backyard_all_count | Back Yard All Count |
| sensor.back_door_person_count | sensor.camera_backyard_person_count | Back Yard Person Count |
| sensor.front_doorbell_all_count | sensor.camera_doorbell_front_all_count | Front Doorbell All Count |
| sensor.weather_last_updated | sensor.weather_last_updated | Weather Last Updated |
| sensor.condition_forecast_next_hour | sensor.weather_forecast_condition_next_hour | Condition Forecast Next Hour |
| sensor.condition_forecast_today | sensor.weather_forecast_condition_today | Condition Forecast Today |
| sensor.precipitation_forecast_next_hour | sensor.weather_forecast_precipitation_next_hour | Precipitation Forecast Next Hour |
| sensor.temperature_forecast_high_today | sensor.weather_forecast_temperature_high_today | Temperature Forecast High Today |
| sensor.chores_summary | sensor.chores_summary | Chores Summary |
| sensor.dishwasher_state | sensor.appliance_dishwasher_state | Bosch Dishwasher - Operation State |

## Binary Sensors

| Current Entity ID | Standardized Entity ID | Friendly Name |
|-------------------|------------------------|---------------|
| binary_sensor.is_weekend | binary_sensor.time_is_weekend | Is Weekend |
| binary_sensor.front_doorbell_person_occupancy | binary_sensor.camera_doorbell_front_person_occupancy | Front Doorbell Person Occupancy |
| binary_sensor.front_drive_all_occupancy | binary_sensor.camera_front_drive_all_occupancy | Front Drive All Occupancy |
| binary_sensor.front_drive_person_occupancy | binary_sensor.camera_front_drive_person_occupancy | Front Drive Person Occupancy |
| binary_sensor.living_room_camera_person_occupancy | binary_sensor.camera_living_room_person_occupancy | Living Room Camera Person Occupancy |
| binary_sensor.front_drive_bus_occupancy | binary_sensor.camera_front_drive_bus_occupancy | Front Drive Bus Occupancy |
| binary_sensor.back_door_all_occupancy | binary_sensor.camera_backyard_all_occupancy | Back Yard All Occupancy |
| binary_sensor.back_door_person_occupancy | binary_sensor.camera_backyard_person_occupancy | Back Yard Person Occupancy |
| binary_sensor.front_doorbell_all_occupancy | binary_sensor.camera_doorbell_front_all_occupancy | Front Doorbell All Occupancy |
| binary_sensor.back_door_motion | binary_sensor.camera_backyard_motion | Back Yard Motion |
| binary_sensor.front_drive_motion | binary_sensor.camera_front_drive_motion | Front Drive Motion |
| binary_sensor.living_room_camera_motion | binary_sensor.camera_living_room_motion | Living Room Camera Motion |
| binary_sensor.front_doorbell_motion | binary_sensor.camera_doorbell_front_motion | Front Doorbell Motion |
| binary_sensor.front_doorbell_button_pressed | binary_sensor.doorbell_front_button_pressed | Front Doorbell Button Pressed |
| binary_sensor.thermostat_occupancy | binary_sensor.climate_thermostat_occupancy | Thermostat Occupancy |
| binary_sensor.master_bedroom_occupancy | binary_sensor.climate_bedroom_master_occupancy | Master Bedroom Occupancy |

## Scripts

| Current Entity ID | Standardized Entity ID | Friendly Name |
|-------------------|------------------------|---------------|
| script.show_chores | script.chores_show | Show Chores |
| script.daily_brief | script.notification_daily_brief | Enhanced Daily Status Brief |
| script.lamp_dim_sequence | script.light_dim_sequence | Lamp Dim Sequence |
| script.good_night | script.routine_good_night | Good Night Routine |

## Automations

| Current Alias | Standardized Alias | Description |
|---------------|-------------------|-------------|
| Universal Camera Notification | camera_notification_universal | Notify tracked objects |
| Doorbell Button Press | doorbell_button_press_notification | Notify on doorbell press |
| Reset Daily Chores | chore_reset_daily | Reset daily chores at midnight |
| Reset Weekly Chores | chore_reset_weekly | Reset weekly chores on Monday |
| Morning Wake Detection | mode_morning_wake_detection | Transition to home mode in morning |
| Everyone Left | presence_everyone_left | Handle when everyone has left home |
| Someone Came Home | presence_someone_returned | Handle when someone returns home |
| Handle Home Alarm Armed Away | alarm_handle_armed_away | Actions when alarm is armed away |
| Handle Home Alarm Armed Night | alarm_handle_armed_night | Actions when alarm is armed night |
| Handle Home Alarm Armed Home | alarm_handle_armed_home | Actions when alarm is armed home |
| Welcome Home Light Control | light_welcome_home | Turn on entry lights on return |
| Security Lighting - Person Detection | security_lighting_person_detection | Manage lights based on detection |
| Turn on the Front Yard Lights at Dusk | light_front_yard_at_dusk | Dusk lighting automation |
| Notify me if it is going to rain soon | notification_rain_forecast | Rain forecast notification |
| Weather Data Refresh | weather_data_refresh | Update weather data |
| Morning Brief Trigger | notification_brief_morning | Trigger brief in the morning |
| Evening Brief Trigger | notification_brief_evening | Trigger brief in the evening |
| Calendar Update Brief Trigger | notification_brief_calendar | Trigger brief on calendar events |
| Significant Changes Brief Trigger | notification_brief_significant_changes | Trigger brief on significant changes |
| Bus Detected On School Days | notification_bus_detection | Notify when school bus is detected |

## Media Players

| Current Entity ID | Standardized Entity ID | Friendly Name |
|-------------------|------------------------|---------------|
| media_player.living_room_tv | media_player.tv_living_room | Living Room TV |
| media_player.master_bedroom_tv | media_player.tv_bedroom_master | Master Bedroom TV |
| media_player.kitchen_display | media_player.display_kitchen | Kitchen Display |
| media_player.living_room_speaker | media_player.speaker_living_room | Living Room Speaker |
| media_player.music_room_speaker | media_player.speaker_music_room | Music Room Speaker |
| media_player.master_bathroom | media_player.speaker_bathroom_master | Master Bathroom Speaker |
| media_player.porter_s_room_speaker | media_player.speaker_bedroom_porter | Porter's Room Speaker |
| media_player.towner_s_room_speaker | media_player.speaker_bedroom_towner | Towner's Room Speaker |
| media_player.all_speakers | media_player.group_all_speakers | All Speakers |

## Input Selects

| Current Entity ID | Standardized Entity ID | Friendly Name |
|-------------------|------------------------|---------------|
| input_select.chore_dishwasher_assignee | input_select.chore_dishwasher_assignee | Dishwasher Duty |
| input_select.chore_bathroom_assignee | input_select.chore_bathroom_assignee | Bathroom Duty |

## Implementation Considerations

1. **Entities Created by Integrations**
   - Some entities may be created automatically by integrations and cannot be renamed easily
   - For these, create template sensors with standardized names that mirror the original entities

2. **Entity Registry Updates**
   - Use the `homeassistant.update_entity_id` service for entities that can be renamed
   - This preserves entity history and relationships

3. **Configuration File Updates**
   - Update all relevant YAML files to reference the new entity IDs
   - Use compatibility templates during transition

4. **Testing Priority**
   - Test critical automations after each batch of renames
   - Focus on security and core functionality first
