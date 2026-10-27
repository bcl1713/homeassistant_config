# #244 repair operator runbook

Repository fixes are **not live repair clearance**. No dashboard change, deploy,
reload/restart, registry deletion or physical device action is authorized by this
artifact. Obtain separate operator approval before any live step. Independent
exact-candidate review is required before integration/apply.

## Battery and package contract

- Seven active packages now place reusable YAML anchors at real consumers and
  inline single-use values. Complete resolved consumer fingerprints preserve
  all thresholds, contact maps, triggers, security conditions and actions.
- Keep existing battery wrapper names, unique IDs, percentage sources and history.
  `battery_health` and `cycle_count` were unused, unsupported metadata, not an
  integration contract. Do not copy those attributes into new examples.
- Charging is optional: remotes/Sally use their actual charging binary sensors;
  phones use their battery-state enums. `on`/`charging` is true;
  `off`/`discharging`/`not_charging`/`full` is false (full means not actively
  charging). Missing/unknown/unavailable/unrecognized sources yield `unknown`,
  not false. Front-door and master-bedroom charging are omitted as unsupported.
  Consumers must not treat the truthy string `unknown` as true; compare to true.
- Brian/Hester keep their existing level/state pairs. Before any `_2` switch,
  obtain sanitized entity-registry device IDs and config-entry IDs for both
  level/state entities, plus device/config-entry evidence identifying the intended
  current handset. Names, suffixes and differing percentages do not prove identity.
  Change both members only after that evidence is reviewed; no presence changes.
- Sally Direct is removed: repository search found only its definition; Jarvis's
  bounded read-only scalar scan of all stored `lovelace*` dashboards found neither
  its entity ID nor unique ID. Normal Sally still uses `sensor.sally_battery` and
  `binary_sensor.kitchen_kitchen_roomba_charging`; no replacement/count added.
  No recorder history or live registry cleanup. External consumers were not proven
  absent and are not claimed so. Inventory/double-count work remains #245;
  removing metadata does not repair the unknown master-bedroom percentage source
  or the hardcoded charging summary.

## Areas: candidate patch scope and identity gates

`244-areas.patch.json` is RFC 6902 against the **config object returned by
`lovelace/config`**, not a `.storage` envelope. It tests both exact preimages before
removing just these two obsolete hidden preferences:

- `/strategy/areas_options/dining_room/groups_options/climate/hidden/0` =
  `humidifier.thermostat`
- `/strategy/areas_options/garage/groups_options/security/hidden/0` =
  `lock.ratgdov25i_0cd7df_lock_remotes`

These are not control cards. All other values and working controls remain intact.
The patch intentionally will **not clear the whole Areas repair**. Remaining
candidates below are unvalidated suggestions, not approved replacements. Paths
are relative to `strategy/areas_options`:

| Exact preference path | Old reference | Candidate only / evidence gate |
| --- | --- | --- |
| `basement/groups_options/security/hidden/0` | `camera.birdseye` | `camera.system_birdseye`: prove same camera/feed and intended hiding |
| `dining_room/groups_options/climate/order/0` | `climate.thermostat_2` | `climate.thermostat`: prove device/config-entry identity and preserve order |
| `hallway/groups_options/security/hidden/0` | `camera.front_doorbell_main` | `camera.front_door_doorbell_camera_main`: prove same main feed |
| `hallway/groups_options/security/hidden/1` | `binary_sensor.front_doorbell_door_status` | `binary_sensor.front_door_doorbell_door_status`: prove same contact/device |
| `hallway/groups_options/security/hidden/2` | `camera.front_doorbell_sub` | `camera.front_door_doorbell_camera_sub`: prove same sub feed |
| `hallway/groups_options/security/order/0` | `camera.front_doorbell` | No validated candidate; identify original camera/feed and desired order |
| `kitchen/groups_options/others/order/0` | `vacuum.sally` | `vacuum.kitchen_roomba`: exists in audit, identity/preference still unverified |

Obtain a fresh config plus narrow sanitized device/config-entry evidence for any
proposed rename. Add only validated mappings in a separate reviewed patch; do not
blindly replace Spook suggestions, substitute the front-door lock for the garage
lock, or remove uncertain hiding/order preferences merely to silence repairs.

## Backup, offline preparation, supported apply and rollback

Do not edit `.storage` files. Use an operator's authorized browser session on the
Home Assistant origin; credentials stay in the browser, never in source/chat.
Treat downloaded config as private operator material; never commit it.

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

   Verify semantic diff is exactly those two list removals; review full preimage,
   not the synthetic test fixture. A failed `test` means drift: stop, obtain a fresh
   backup and re-review. The patch is deliberately not idempotent. Keep before,
   after, reviewed commit SHA and operator approval in private evidence storage.

3. In the same authorized console, load the reviewed candidate using a file picker:

   ```javascript
   const pickJson = () => new Promise((resolve, reject) => {
     const input = document.createElement('input'); input.type = 'file'; input.accept = '.json';
     input.onchange = async () => { try { resolve(JSON.parse(await input.files[0].text())); } catch (e) { reject(e); } };
     input.click();
   });
   const candidate = await pickJson(); // select areas-after-244.json
   const fresh = await hass.callWS({type: 'lovelace/config', url_path: 'dashboard-areas', force: true});
   if (JSON.stringify(fresh) !== JSON.stringify(original)) throw new Error('Dashboard changed: stop and re-review');
   // STOP here until the operator confirms the exact diff and apply approval.
   ```

   Only then save through the supported API, read back, and inspect Areas without
   actuating devices:

   ```javascript
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

After independent review/integration, obtain separate deploy/reload approval and
rollback to the previous source revision if authorized deployment regresses.
Only after authorized deploy and dashboard apply: read authenticated
`repairs/list_issues`, verify the exact ten targeted issues absent without
suppression/dismissal, ignored icon issue unchanged, no new repairs; compare
battery levels/charging to sources including unavailable states and existing IDs;
verify no added Sally count; inspect Areas cameras/climate/vacuum/security controls
without actuating them. Remaining identity-gated mappings/phone switches must not
be described as completed. Record partial clearance honestly.
