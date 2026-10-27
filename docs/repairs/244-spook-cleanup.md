# #244 repair operator runbook

Repository fixes are **not live repair clearance**. No dashboard change, deploy,
reload/restart, registry deletion or physical device action is authorized by this
artifact. Obtain separate operator approval before any live step. Independent
exact-candidate review is required before integration/apply.

## Battery and package contract

- Seven active packages now place reusable YAML anchors at real consumers and
  inline single-use values. Complete resolved consumer fingerprints preserve
  all thresholds, contact maps, triggers, security conditions and actions.
- Keep existing battery wrapper names, unique IDs and history; only Brian/Hester
  percentage and charging sources change together to the verified current handset.
  `battery_health` and `cycle_count` were unused, unsupported metadata, not an
  integration contract. Do not copy those attributes into new examples.
- Charging is optional: remotes/Sally use their actual charging binary sensors;
  phones use their battery-state enums. `on`/`charging` is true;
  `off`/`discharging`/`not_charging`/`full` is false (full means not actively
  charging). Missing/unknown/unavailable/unrecognized sources yield `unknown`,
  not false. Front-door and master-bedroom charging are omitted as unsupported.
  Consumers must not treat the truthy string `unknown` as true; compare to true.
- Brian/Hester now use `sensor.<person>_phone_battery_level_2` and
  `sensor.<person>_phone_battery_state_2` together, including source metadata.
  Fresh private Oct 27 evidence verifies each pair shares the intended Google
  Pixel 10 Pro XL device/config entry, is enabled/loaded and updated Oct 27; old
  Samsung pairs last updated Oct 25. No fallback to the stale handset when the
  current phone is missing/unavailable. Other wrappers, presence, names and IDs
  remain unchanged. Identity IDs and raw state attributes must stay private.
- Sally Direct is removed: repository search found only its definition; Jarvis's
  bounded read-only scalar scan of all stored `lovelace*` dashboards found neither
  its entity ID nor unique ID. Normal Sally still uses `sensor.sally_battery` and
  `binary_sensor.kitchen_kitchen_roomba_charging`; no replacement/count added.
  No recorder history or live registry cleanup. External consumers were not proven
  absent and are not claimed so. Inventory/double-count work remains #245;
  removing metadata does not repair the unknown master-bedroom percentage source
  or the hardcoded charging summary.

## Areas: complete identity-validated candidate

`244-areas.patch.json` is RFC 6902 against the **config object returned by
`lovelace/config`**, not a `.storage` envelope. All nine exact old-value `test`
operations precede any mutation: eight in-place replacements and one obsolete
hidden-preference removal. Paths below are relative to `strategy/areas_options`:

| Exact preference path | Old reference | Approved replacement / action |
| --- | --- | --- |
| `basement/groups_options/security/hidden/0` | `camera.birdseye` | `camera.system_birdseye` (Frigate Birdseye) |
| `dining_room/groups_options/climate/order/0` | `climate.thermostat_2` | `climate.dining_room_thermostat` (ecobee) |
| `dining_room/groups_options/climate/hidden/0` | `humidifier.thermostat` | `humidifier.dining_room_humidistat` (same ecobee; keep hidden) |
| `hallway/groups_options/security/hidden/0` | `camera.front_doorbell_main` | `camera.front_door_doorbell_camera_main` (Dahua main) |
| `hallway/groups_options/security/hidden/1` | `binary_sensor.front_doorbell_door_status` | `binary_sensor.front_door_doorbell_door_status` (same Dahua, user-disabled; keep hidden) |
| `hallway/groups_options/security/hidden/2` | `camera.front_doorbell_sub` | `camera.front_door_doorbell_camera_sub` (Dahua sub) |
| `hallway/groups_options/security/order/0` | `camera.front_doorbell` | `camera.front_door_doorbell_camera` (Frigate, NOT Dahua) |
| `kitchen/groups_options/others/order/0` | `vacuum.sally` | `vacuum.kitchen_roomba` (Sally device identity) |
| `garage/groups_options/security/hidden/0` | `lock.ratgdov25i_0cd7df_lock_remotes` | Remove obsolete preference only; no lock substitution |

Fresh private evidence resolves the prior identity gates. The disabled HomeKit
`climate.thermostat` is NOT the ordered thermostat replacement; preserve its
existing hidden preference. Preserve all unrelated preferences, full list order
and indexes (except the intentional garage removal), dishwasher options and the
working garage cover. The ratgdo remote-lock entity is user-disabled; neither
enable it nor replace this stale preference with the front-door lock.

The Dahua contact remains user-disabled. Preserving its hiding under the current
registered ID is intentional, not an instruction to enable it: Spook's Lovelace
repair uses `async_get_all_entity_ids`, which unions **all entity-registry IDs**
with state-machine IDs without filtering `disabled_by`. A registered disabled
entity is therefore known even without live state. Sources, inspected at commit
`bf426cd7e0dd990460bb955344aae9db299f36b2`:
[registry membership](https://github.com/frenck/spook/blob/bf426cd7e0dd990460bb955344aae9db299f36b2/custom_components/spook/entity_filtering.py)
and [Lovelace repair](https://github.com/frenck/spook/blob/bf426cd7e0dd990460bb955344aae9db299f36b2/custom_components/spook/ectoplasms/lovelace/repairs/unknown_entity_references.py).
This source inspection is not a live installed-version or repair-clearance test.

## Backup, offline preparation, supported apply and rollback

Do not edit `.storage` files. Use an operator's authorized browser session on the
Home Assistant origin; credentials stay in the browser, never in source/chat.
Treat downloaded config as private operator material; never commit it. The supplied
Oct 27 preimage was validated offline on Forge, including the complete actual
config, not just a synthetic fixture. It is not authorization to save and does not
replace a fresh backup/drift comparison at apply time. Keep backups/candidates
mode 600 in a private directory, outside Git; never print raw exports or camera
state attributes (they may contain access tokens).

1. After explicit approval, open Areas, then browser developer console. Capture
   its config through the supported WebSocket API and download an exact backup:

   ```javascript
   const hass = document.querySelector('home-assistant').hass;
   const original = await hass.callWS({type: 'lovelace/config', url_path: 'dashboard-areas', force: true});
   const download = (name, value) => {
     const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], {type: 'application/json'}));
     const a = document.createElement('a'); a.href = url; a.download = name; a.click();
     setTimeout(() => URL.revokeObjectURL(url), 1000);
   };
   download('areas-before-244.json', original);
   ```

2. On an authorized offline workstation (or isolated Forge directory), install
   `jsonpatch` in a disposable virtual environment. With backup and reviewed patch
   available, create candidate **without overwriting the backup**:

   ```bash
   python -m venv .venv-244
   .venv-244/bin/python -m pip install jsonpatch==1.38
   .venv-244/bin/python -c 'import json,jsonpatch; from pathlib import Path; before=json.loads(Path("areas-before-244.json").read_text()); patch=json.loads(Path("docs/repairs/244-areas.patch.json").read_text()); after=jsonpatch.apply_patch(before,patch); f=open("areas-after-244.json","x"); json.dump(after,f,indent=2); f.close()'
   diff -u areas-before-244.json areas-after-244.json
   ```

   Privately review the exact diff: precisely the eight replacements and one
   garage hidden removal in the table, with full-array order and unrelated
   settings unchanged, including hidden disabled `climate.thermostat`, dishwasher
   options and garage cover. Review the actual full preimage, not the synthetic
   fixture. Do not publish this diff. A failed `test` means drift: stop, obtain a fresh
   backup and re-review. The patch is deliberately not idempotent. Keep before,
   after, reviewed commit SHA and operator approval in private evidence storage.

3. In the same authorized console, load the reviewed candidate using a file picker:

   ```javascript
   const pickJson = () => new Promise((resolve, reject) => {
     const input = document.createElement('input'); input.type = 'file'; input.accept = '.json';
     input.onchange = async () => { try { resolve(JSON.parse(await input.files[0].text())); } catch (e) { reject(e); } };
     input.click();
   });
   const reviewedBefore = await pickJson(); // select exact areas-before-244.json
   const candidate = await pickJson(); // select reviewed areas-after-244.json
   const fresh = await hass.callWS({type: 'lovelace/config', url_path: 'dashboard-areas', force: true});
   if (JSON.stringify(fresh) !== JSON.stringify(reviewedBefore)) throw new Error('Dashboard changed: stop and re-review');
   // STOP here until the operator confirms the exact diff and apply approval.
   ```

   Only after separate explicit dashboard-apply approval, repeat the **whole
   config** comparison immediately before save (not just the nine old-value tests).
   Re-review any drift, even in an unrelated option. Coordinate an exclusive edit
   window: this API has no atomic compare-and-swap. Save through the supported API,
   read back, and inspect Areas without actuating devices:

   ```javascript
   const latest = await hass.callWS({type: 'lovelace/config', url_path: 'dashboard-areas', force: true});
   if (JSON.stringify(latest) !== JSON.stringify(reviewedBefore)) throw new Error('Dashboard changed: stop and re-review');
   await hass.callWS({type: 'lovelace/config/save', url_path: 'dashboard-areas', config: candidate});
   const saved = await hass.callWS({type: 'lovelace/config', url_path: 'dashboard-areas', force: true});
   if (JSON.stringify(saved) !== JSON.stringify(candidate)) throw new Error('Readback mismatch: investigate');
   ```

4. Rollback, if needed and separately authorized: in the same session use
   `original`; after a session loss use `await pickJson()` to load
   `areas-before-244.json` into a new `rollback` variable. Fetch current config,
   ensure no intervening operator changes (otherwise reconcile before overwriting),
   then `await hass.callWS({type:'lovelace/config/save', url_path:'dashboard-areas',
   config: original})` (or `rollback`). Read back with `force:true`, compare to the
   backup, and visually confirm original preferences. Never reconstruct rollback
   by guessed reverse renames.

## Verification and live clearance gates

Forge-only repository checks: install `-r requirements-test.txt`,
then `python -m pytest -q`; focus `tests/test_spook_anchor_consumers.py`,
`tests/test_known_batteries.py`, `tests/test_areas_cleanup.py` and existing security,
exterior-door and trash-reminder tests. Config validation follows
`.github/workflows/validate.yaml` / `frenck/action-home-assistant@v1.4.1` with dummy
secrets/service account, stable Core, isolated filesystem and network disabled.
A parser/config pass does not prove live device identity, UI behavior or repairs.

After independent exact-candidate review/integration, obtain separate package
**deploy/reload approval**; dashboard **apply approval** is a separate decision.
If deployment regresses, roll back to the previous source revision and use the
authorized reload path. Do not delete/rename wrappers to roll back source changes.

Only after authorized deploy and dashboard apply, read authenticated
`repairs/list_issues` and verify **all ten** targeted repairs absent without
suppression/dismissal. Use the fresh baseline IDs (hash suffixes may change on a
later baseline); verify each check, not just a reduced issue count:

| Check | Target repair (Spook) | Live acceptance |
| --- | --- | --- |
| 1 | `unknown_customized_entities_unknown_customized_entities_8e62b2be` | Anchor/customization repair absent; resolved package consumers unchanged |
| 2 | `lovelace_unknown_entity_references_dashboard-areas_6e3773cb` | Areas repair absent; cameras/climate/vacuum/security render with reviewed preferences, disabled contact still disabled, garage cover and dishwasher options unchanged |
| 3 | `template_unknown_entity_references_sensor.kitchen_roomba_battery_direct_583272b1` | Sally Direct repair absent, no replacement/double-count sensor, normal Sally retained |
| 4 | `template_unknown_attribute_references_sensor.master_bedroom_remote_hester_battery_80024d80` | Hester remote repair absent; supported binary charging/percentage match sources, unknown remains unknown |
| 5 | `template_unknown_attribute_references_sensor.master_bedroom_remote_brian_battery_09e360c0` | Brian remote repair absent; supported binary charging/percentage match sources, unknown remains unknown |
| 6 | `template_unknown_attribute_references_sensor.hester_phone_battery_c9703735` | Hester phone repair absent; existing wrapper ID/history, current `_2` pair only, no stale fallback, honest unknown/charging semantics |
| 7 | `template_unknown_attribute_references_sensor.brian_phone_battery_9ae2d1c2` | Brian phone repair absent; existing wrapper ID/history, current `_2` pair only, no stale fallback, honest unknown/charging semantics |
| 8 | `template_unknown_attribute_references_sensor.towner_phone_battery_45e53297` | Towner repair absent; unchanged source pair and honest enum charging/unknown behavior |
| 9 | `template_unknown_attribute_references_sensor.front_door_lock_battery_56004a5a` | Front-door battery repair absent; percentage source/ID retained, unsupported charging omitted |
| 10 | `template_unknown_attribute_references_sensor.kitchen_roomba_battery_f7f40878` | Normal Sally repair absent; percentage and binary charging match actual sources, unknown remains unknown |

Keep ignored `unknown_icons_unknown_icons_93da16ce` unchanged and verify no new
repairs. Compare source/wrapper values read-only; include naturally observed
unavailable/missing cases or record those runtime cases as pending, never disable
devices to manufacture them. Inspect controls without actuating locks, covers,
climate or vacuum. Record private before/after readbacks and honest partial
clearance if any check is pending. Offline evidence and this runbook do not claim
any live repair has cleared.
