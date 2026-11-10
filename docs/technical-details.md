# Technical Details – Shelly TRV Gen1 B2.2 Beta

This document describes the technical implementation, qualified firmware corrections, and deterministic reconstruction of **B2.2 Beta** for the Shelly TRV Gen1 (`SHTRV-01`).

**Last updated:** November 9, 2026
**Patcher:** `patch_firmware_v2.0.py`
**Firmware:** B2.2 Beta
**Supported base:** Shelly TRV Gen1 Stock 2.2.4

> **Technical status**
>
> B2.2 integrates nine selected qualified correction components. Its application and OTA GBL are deterministically reconstructed from one exact Stock firmware image and verified byte-for-byte.
>
> Physical testing has exceeded six days without a recurrence of the previously documented severe battery depletion in the regular test fleet.
>
> **Known issue:** Unexpected automatic reboots have been observed on multiple B2.2 devices. Their cause remains unknown. Long-term stability and battery lifetime are not conclusively established.

## 1. Firmware Scope

B2.2 is an integrated, observer-free firmware build containing exactly nine selected correction components:

| ID | Correction |
|---|---|
| A1R | Host power-management lifecycle correction, including experimental A1 regression fix |
| C-C | Beacon-Recovery evidence validity |
| B2 | Bounded sleep-inhibit counter serialization |
| MQTT | Minimal PUBLISH input guard |
| WF200 | Official Silicon Labs radio firmware 3.18.0 |
| Calibration | Calibration Restore Guard |
| P01 | Ownership-aware Battery PA3 release |
| P02 | Bounded synchronous I2C timeout retirement |
| P03 | WLAN-GPIO notification interrupt-mask correction |

These components represent the **selected qualified correction set**, not every firmware issue identified during the broader investigation.

B2.2 does not include the historical periodic mDNS bypass, MIN80, D3 or PM52 observers, additional diagnostic logging, FastPS experiments, EM3 changes, or deferred P04+ candidates.

No implicit tenth correction is included.

The final firmware deliberately excludes diagnostic-only observer instrumentation.

## 2. Supported Firmware and Artifact Identity

### Supported Stock input

| Property | Value |
|---|---|
| Device | Shelly TRV Gen1 / SHTRV-01 |
| Firmware | Stock 2.2.4 |
| Build | `20240619-130912/v2.2.4@ee290818` |
| Filename | `SHTRV-01_build_2.2.4.gbl` |
| Size | 1,106,384 bytes |

**SHA-256:**

```text
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

The patcher accepts only this exact supported input. It does not search unknown firmware images for similar instruction patterns or relocate corrections heuristically.

### Qualified B2.2 application

| Property | Value |
|---|---|
| Filename | `SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin` |
| Size | 1,069,320 bytes |
| CRC32 | `42657D97` |

**SHA-256:**

```text
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9
```

### Qualified B2.2 OTA GBL

| Property | Value |
|---|---|
| Filename | `SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl` |
| Size | 1,126,156 bytes |
| END CRC32 | `52A97051` |
| Whole-file CRC32 residue | `2144DF1C` |

**SHA-256:**

```text
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c
```

The `EXPERIMENTAL` filenames remain unchanged for compatibility with the qualified reconstruction and OTA workflow. The current public release classification is **Beta**.

Changing either binary's contents would create a different firmware candidate requiring new validation.

### Native Shelly version

B2.2 retains the original firmware identity:

```text
20240619-130912/v2.2.4@ee290818
```

The `/status` endpoint therefore cannot, by itself, distinguish B2.2 from Stock 2.2.4.

## 3. Patcher v2.0 – Reconstruction Architecture

The historical v1.0 patcher applied two small control-flow modifications to Stock firmware.

Patcher v2.0 uses a fundamentally different approach:

```text
Verified Stock 2.2.4
        |
        v
Checked source preimages
        |
        v
Qualified transformations
        |
        v
B2.2 application reconstruction
        |
        v
Application identity validation
        |
        v
GBL reconstruction
        |
        v
GBL integrity validation
        |
        v
Output readback verification
```

The objective is **exact binary reproduction**, not merely functional equivalence.

### Authorized transformations

The current reconstruction uses approximately **1,404 checked Stock-to-B2.2 byte transformation runs**.

Each authorized region is verified against its expected Stock preimage before transformation.

Unexpected source bytes cause the operation to abort.

These transformation runs include the integrated application changes, replacement code, relocation data, and updated WF200 firmware.

They must not be interpreted as 1,404 separate defects or corrections.

### Standalone operation

The distributed patcher requires only:

```text
patch_firmware_v2.0.py
target/SHTRV-01_build_2.2.4.gbl
```

It does not require Ghidra, REA, Codex, the research tree, a qualification build directory, or an already completed B2.2 firmware image at runtime.

An isolated standalone reconstruction successfully generated the exact qualified B2.2 artifacts.

### Fail-closed validation

Documented negative tests include:

- Modified Stock input
- Truncated GBL input
- Corrupt CRC or integrity data
- B2.2 supplied as input instead of Stock
- Modified expected preimage bytes
- Forced output-integrity mismatch

The patcher does not silently accept near-matches or partially reconstructed firmware.

After writing the generated files, the patcher reopens and verifies their identities.

The final v2.0 acceptance suite completed **18 automated tests successfully**.

Detailed test results are maintained in [Testing](../tests/README.md).

## 4. Correction A1R – Host Power-Management Lifecycle

Reverse engineering identified problematic lifecycle cases involving the host power-management implementation.

Relevant areas include:

- Final-sleep cleanup
- Wake-failure handling
- Timeout and cancellation behavior
- Late completion events
- Requested versus committed power-management state
- Completion races
- Independent inhibit ownership
- State settlement and handoff

An earlier experimental correction, A1, addressed selected lifecycle problems.

Subsequent qualification revealed a regression introduced by A1 itself.

### Experimental A1 regression

Five native request paths use power-state request `1` as a temporary override:

1. Physical button
2. HTTP `/psovrd`
3. Cloud `psovrd`
4. SSI `settings_sta`
5. OTA launcher

The intended behavior is conceptually:

```text
Selected policy: 3
        |
        v
Temporary request: 1
        |
        v
Temporary state: 1
        |
        v
Restore selected policy: 3
```

The experimental A1 implementation could incorrectly persist the temporary override as the selected policy:

```text
Selected / actual
      3 / 3
        |
        v
Temporary override
        |
        v
      1 / 1
```

This regression belonged to the experimental A1 correction.

**It must not be described as proof of an equivalent defect in Shelly's original Stock firmware.**

### A1R correction

A1R preserves the intended distinction between a temporary request and a persistent selected policy.

It corrects the experimental regression while retaining the qualified lifecycle corrections.

Qualification included **151 of 151 Thumb-level tests passing**, together with integration and retained-state testing.

## 5. Correction C-C – Beacon-Recovery Evidence Validity

Stock 2.2.4 includes a host-side Beacon-Recovery mechanism.

On affected devices, debug logs repeatedly reported:

```text
Beacon skip error! Attempt recovery
```

A typical observed recovery sequence involved switching to power-save state `1`, remaining serviced for approximately five seconds, and then restoring the connected power-save policy.

On affected devices, this sequence could recur approximately once per minute.

### Meaning of `real_beacon_skip`

The value exposed as `real_beacon_skip` is not a direct hardware setting specifying how many Wi-Fi beacons the WF200 skips.

The host derives the value from a cumulative WF200 beacon-receive counter.

Conceptually:

```c
P = previous cumulative beacon count;
C = current cumulative beacon count;

delta = C - P;
R = (uint8_t)(600 / delta);
```

The resulting value is cached and later used in the host recovery decision.

This calculation has several evidence-validity problems.

### C1a – Signed interpretation

The quotient is reduced to eight bits and later interpreted as signed.

For example:

```text
600 / 3 = 200

uint8_t: 0xC8 = 200
int8_t:  0xC8 = -56
```

A positive mathematical result can therefore enter the recovery decision as a negative signed value.

C-C corrects the selected signed-interpretation problem.

### C1b – Measurement-window validity

The fixed calculation:

```text
600 / delta
```

implicitly assumes a particular measurement relationship.

If expected measurement opportunities are skipped, the counter difference may cover a different effective interval.

The cumulative beacon counter may still be correct, while the derived control value is no longer valid for the assumed measurement window.

C-C addresses this measurement-validity problem.

### C2 – Stale Recovery evidence

Stock Recovery can clear the previous beacon-counter baseline while retaining a previously calculated recovery value.

Conceptually:

```text
Fresh qualifying measurement
        |
        v
Beacon Recovery
        |
        v
Previous counter baseline cleared
        |
        v
Cached recovery value retained
        |
        v
New baseline established
        |
        v
No fresh recovery value available yet
        |
        v
Old value remains eligible for evaluation
```

This can extend a transient event into a recurring Recovery episode.

The recurrence is not necessarily permanent until reboot: a later valid measurement can replace the stale value and allow the episode to end.

### C-C behavior

C-C corrects the selected C1a, C1b and C2 issues.

It **does not globally disable Beacon Recovery**.

Recovery remains possible when evidence is:

```text
Fresh
  +
Valid
  +
Qualifying
```

This differs from the historical v1.0 unconditional Beacon-Recovery bypass.

The individual electrical contribution of this correction to overall battery consumption has not been isolated.

## 6. Correction B2 – Bounded Sleep-Inhibit Serialization

The host uses a shared reference counter designated B2 in the investigation.

Its purpose is to track owners that require the host to remain at an EM1-capable sleep level.

Conceptually:

```text
B2 = 0 → no EM1 owner
B2 = 1 → one EM1 owner
B2 = 2 → two EM1 owners
```

Reverse engineering identified inconsistent serialization of read-modify-write operations on this counter.

### Example: phantom contribution

Consider the following sequence:

```text
Initial B2 = 1

Task A reads B2 = 1

Task A is preempted

Task B releases its contribution:
B2: 1 → 0

Task A resumes and stores
an increment based on stale data:
B2: 0 → 2
```

Only one legitimate owner remains, but the counter contains two contributions.

After the remaining real owner releases:

```text
B2: 2 → 1
```

A phantom contribution remains.

The host may therefore remain limited to EM1 when it could otherwise enter a deeper sleep state.

The opposite race can remove a legitimate contribution and potentially allow deeper sleep too early.

### B2 correction

B2.2 adds bounded serialization using **saved-PRIMASK semantics** around the relevant counter operations.

The previous interrupt state is preserved rather than blindly enabling interrupts after the critical section.

The correction does not introduce a new EM3 policy.

## 7. Correction MQTT – Minimal PUBLISH Guard

B2.2 includes a minimal guard on the relevant MQTT PUBLISH input path.

The guard was selected because a concrete malformed-input failure was demonstrated and the bounded correction was qualified.

Qualification included **258 of 258 target/parser/worker tests passing**.

The public battery-drain documentation intentionally excludes sensitive reproduction details from the separate MQTT security investigation.

The existence of this correction does not imply that remote code execution, arbitrary memory writes, or a complete MQTT parser compromise have been demonstrated.

It is a narrowly scoped correction rather than a complete MQTT parser redesign.

## 8. Correction WF200 – Official Silicon Labs 3.18.0

Stock Shelly TRV 2.2.4 uses:

| Component | Stock version |
|---|---|
| Shelly host FMAC | 3.7.0 |
| WF200 radio firmware | 3.16.1 |

B2.2 retains the Shelly FMAC integration and updates the radio firmware to the official **Silicon Labs WF200 3.18.0**.

The later firmware includes an official power-save-related correction for a condition in which the radio can fail to sleep after a power-save mode change.

The updated radio firmware was integrated into the Shelly application, including the required relocation and validation work.

Physical hardware testing demonstrated successful operation of:

```text
FMAC 3.7.0
    +
WF200 3.18.0
```

including WF200 initialization, WLAN scanning, association, DHCP, cloud connectivity, and connected power-save operation.

This demonstrates functional compatibility under the tested conditions.

**WF200 3.18.0 alone has not been proven to resolve the historical Shelly TRV battery drain.**

## 9. Correction Calibration Restore Guard

A concrete calibration-state defect was identified in the restore path.

A queued restore operation could complete successfully and then immediately schedule itself again.

Conceptually:

```text
Queued calibration restore
        |
        v
Successful completion
        |
        v
Restore scheduling logic
        |
        v
Same operation queued again
```

B2.2 adds a guard that prevents the selected self-requeue condition while preserving the intended calibration workflow.

Qualification included native execution paths, scalar state combinations, queue and countdown behavior, and negative test cases.

## 10. Correction P01 – Battery PA3 Resource Release

The battery ADC implementation uses PA3 as part of its measurement resource lifecycle.

A timeout path could return without correctly releasing PA3.

A later successful measurement could repair the state, but the timeout path itself did not perform complete resource cleanup.

B2.2 introduces an ownership-aware release that corrects the selected condition without indiscriminately releasing resources owned elsewhere.

The electrical current contribution of the original defect has **not** been directly measured.

A demonstrated resource-lifecycle defect is not equivalent to a demonstrated quantitative battery-drain contribution.

## 11. Correction P02 – Bounded Synchronous I2C Timeout Retirement

The analyzed synchronous I2C/display timeout path could return with an unfinished transaction and retained interrupt-related resources.

Conceptually:

```text
Timeout
   |
   v
Transaction not fully retired
   |
   v
Interrupt-related state retained
   |
   v
Incomplete cleanup
```

B2.2 adds a bounded retirement path that completes the selected cleanup without introducing an unbounded wait.

The qualified P02 helper occupies the recorded application range:

```text
[0x104740, 0x1047C8)
```

## 12. Correction P03 – WLAN-GPIO Interrupt Mask

A WLAN-GPIO notification disable path passed the numeric value `10` to an interface expecting a bit mask.

The actual mask semantics therefore differed from the intended interrupt selection.

This could leave an intended interrupt source enabled while incorrectly affecting other mask bits.

B2.2 corrects the interrupt-mask semantics.

The qualified P03 correction occupies:

```text
[0x104840, 0x104854)
```

## 13. Qualified Integration Regions

The B2.2 qualification records identify these application regions:

| Component | Application range |
|---|---|
| P02 helper | `[0x104740, 0x1047C8)` |
| P03 | `[0x104840, 0x104854)` |
| P01 | `[0x104880, 0x1048BC)` |
| Calibration Restore Guard | `[0x1050F4, 0x105108)` |

These are selected qualified integration regions, not a complete inventory of every Stock-to-B2.2 byte difference.

The definitive application identity is the complete SHA-256 hash.

## 14. Observer-Free Design

B2.2 intentionally omits diagnostic-only instrumentation used in earlier research.

This includes the PM52/cmd66 observer, D3 observer, and additional temporary debug counters.

Only the runtime memory required by the selected integrated correction set, including A1R lifecycle handling, remains.

The objective is to evaluate the correction set without observer-specific changes that could influence long-term runtime behavior.

## 15. Physical Runtime and Battery Evaluation

### Initial canary

B2.2 successfully completed physical OTA installation, application boot, WF200 3.18.0 initialization, WLAN association, DHCP, calibration, connected power-save operation, and cloud connectivity.

The initial approximately 29-hour canary showed no additional unexpected reboot or reconnect during that period.

### Fleet rollout

The regular hardware test fleet was deployed on **November 2, 2026, at approximately 18:55 local time**.

The November 9 evaluation covered approximately **6.46 days** after deployment.

The regular B2.2 fleet consists of:

```text
TRV .11
TRV .61
TRV .71
TRV .77
TRV .88
TRV .97
```

TRV .234 is excluded because it is running Stock firmware for separate MQTT security testing.

TRV .61 was recharged during the observation period, so its battery history must be split at that event.

### Battery observations

The historical Shelly Cloud data includes multiple original-firmware episodes in which the displayed battery percentage fell from approximately 95% to 0% within roughly 5.8–6.5 days.

No comparable rapid depletion was observed in the regular B2.2 fleet during the first six days.

Four devices showed these voltage changes between available snapshots from November 3 and November 9:

| Device | Initial voltage | Final voltage | Change |
|---|---:|---:|---:|
| .71 | 3.507 V | 3.487 V | −20 mV |
| .77 | 3.801 V | 3.782 V | −19 mV |
| .88 | 4.051 V | 4.029 V | −22 mV |
| .97 | 3.737 V | 3.721 V | −16 mV |

These measurements span approximately 5.4 days of available voltage snapshots.

The results are encouraging but do not represent direct current or accumulated-energy measurements.

There is no simultaneous matched Stock control group. The historical Stock data also uses firmware-reported battery percentages, rather than the same voltage-based methodology throughout.

Therefore, the current data does not establish a quantified battery-life improvement or identify the definitive historical root cause.

For the detailed test record, see [Testing](../tests/README.md).

## 16. Known Reliability Issue – Unexpected Reboots

During B2.2 fleet testing, several devices restarted automatically without manual intervention.

Recorded reboot-counter changes from November 3 to November 9 were:

| Device | Initial | Latest | Change |
|---|---:|---:|---:|
| .11 | 2 | 6 | +4 |
| .61 | 2 | 3 | +1 |
| .71 | 1 | 65 | +64 |
| .77 | 1 | 6 | +5 |
| .88 | 1 | 2 | +1 |
| .97 | 1 | 1 | 0 |

The unusually large counter change on .71 must not automatically be interpreted as 64 distinct confirmed reset events.

Uptime data confirms at least one restart, but the counter semantics and actual reset history require investigation.

The current available diagnostic snapshots do not establish whether the cause involves a Watchdog timeout, CPU exception, software reset, power-related reset, or a separate counter anomaly.

### Reset investigation priorities

Future static and runtime investigation should examine:

1. EFM32 reset-cause acquisition and retention, including `RMU_RSTCAUSE`.
2. Watchdog initialization, configuration, and feed paths.
3. Sleep-entry and wake-up sequencing.
4. Reboot-counter persistence and update semantics.
5. Interactions between the integrated B2.2 corrections and existing host firmware behavior.

The reset issue is not assigned to a specific correction without direct evidence.

**Beta status is maintained with this issue openly documented.**

## 17. Historical and Deferred Work

### Historical v1.0 patcher

The earlier `patch_firmware_v.1.0.py` implemented a different experimental firmware consisting of a Beacon-Recovery bypass and a periodic mDNS restart bypass.

This was not the current B2.2 correction set.

Historical output identities must not be used to verify current B2.2 artifacts.

### Historical mDNS findings

Earlier packet captures demonstrated that the selected periodic connected-state mDNS restart activity could be suppressed.

Longer-term observations also demonstrated that suppressing this activity did not by itself prevent poor battery runtime or recurring Beacon Recovery.

Consequently, the historical mDNS bypass is not included in B2.2.

### Deferred candidates

Additional findings excluded from the current qualified set include:

- P04 motor-timeout movement accounting
- `valve_min_percent` mixed-unit issue
- Raw ADC transient publication
- Raw TXDMA candidates
- Other peripheral candidates
- EM3 and FastPS experiments

Exclusion does not necessarily mean that a finding is invalid.

It means the finding was not selected for this qualified firmware build.

Any future integrated correction would require a new firmware identity and independent qualification.

## 18. Test and Evidence Boundaries

The project distinguishes the following evidence levels:

```text
Static reverse engineering
          !=
Qualified component correction
          !=
Exact integrated reconstruction
          !=
Successful OTA installation
          !=
Physical hardware operation
          !=
Long-term firmware stability
          !=
Quantified battery-life improvement
          !=
Historically proven drain root cause
```

The original and generated firmware identities, reconstruction tests, component qualification, and physical runtime observations establish different properties.

They must not be treated as interchangeable proof.

In particular:

- A firmware defect is not automatically a proven cause of the historical battery drain.
- A qualified correction does not automatically establish measured energy savings.
- A valid firmware hash does not establish stable runtime behavior.
- A successful hardware boot does not establish long-term stability.
- A current Beacon-Recovery counter of zero does not prove that no recovery occurred during the entire observation period.
- A low short-term voltage decline does not establish a guaranteed battery lifetime.

These distinctions remain important even when initial results are positive.

## 19. Current Technical Assessment

As of November 9, 2026, the following are supported by the documented evidence:

| Area | Assessment |
|---|---|
| Exact supported Stock input | Confirmed |
| Nine selected correction components | Qualified |
| Deterministic reconstruction | Confirmed |
| Application byte identity | Confirmed |
| GBL byte identity | Confirmed |
| Fail-closed validation | Confirmed |
| Standalone patcher operation | Confirmed |
| Automated patcher tests | 18 passed |
| Physical installation and boot | Confirmed |
| WF200 3.18.0 hardware integration | Confirmed |
| WLAN, DHCP, cloud, calibration | Demonstrated |
| Initial six-day battery evaluation | Completed |
| Historical Stock-like severe battery drain | Not observed during initial B2.2 fleet test |
| Unexpected automatic reboots | Observed; unresolved |
| Long-term firmware stability | Not proven |
| Quantified battery-life improvement | Not established |
| Complete historical battery-drain root cause | Not conclusively established |

## Conclusion

B2.2 Beta integrates nine selected qualified firmware corrections and can be reconstructed deterministically from one exact supported Shelly TRV Gen1 Stock 2.2.4 image.

The generated application and OTA GBL match their qualified references byte-for-byte.

Physical testing has demonstrated normal operation of the integrated firmware, including the updated WF200 radio firmware.

The first six-day fleet evaluation shows encouraging battery behavior, with no recurrence of the historical severe rapid-depletion condition in the regular test devices.

However, unexpected automatic reboots remain unresolved, and neither long-term battery lifetime nor the complete historical battery-drain root cause has been conclusively established.

**B2.2 is therefore classified as Beta, with the identified reliability limitation explicitly documented.**
