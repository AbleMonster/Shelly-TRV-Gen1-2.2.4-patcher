# Technical Details

This document describes the current technical implementation of the Shelly TRV Gen1 2.2.4 B2.2 firmware reconstruction performed by:

```text
patch_firmware_v2.0.py
```

The current patcher is fundamentally different from the historical v1.0 patcher.

The historical implementation applied two small experimental control-flow modifications directly to Stock 2.2.4.

The current v2.0 patcher instead performs a deterministic reconstruction:

```text
exact supported Stock 2.2.4
        |
        v
qualified B2.2 application
        |
        v
qualified B2.2 GBL
```

The objective is not to produce a functionally similar firmware.

The objective is to reproduce the exact qualified B2.2 artifacts byte-for-byte.

---

# Scope

B2.2 is the current observer-free integrated experimental firmware containing exactly nine selected qualified corrections:

```text
1. A1R including the A1 lifecycle correction
2. C-C Beacon-Recovery evidence correction
3. B2 bounded serialization
4. minimal MQTT PUBLISH guard
5. official Silicon Labs WF200 3.18.0
6. Calibration Restore Guard
7. P01 ownership-aware Battery-PA3 release
8. P02 bounded synchronous I2C timeout retirement
9. P03 WLAN-GPIO notification interrupt-mask correction
```

There is no implicit tenth correction.

B2.2 means:

```text
All Known Qualified Fixes
```

within the selected qualification scope.

It does **not** mean:

```text
all suspicious code paths ever identified
```

and it does not mean that the historical battery-drain root cause has been conclusively established.

---

# Not included in B2.2

The following experimental, diagnostic, deferred, or unqualified changes are not part of B2.2:

```text
periodic mDNS bypass
MIN80
D3 observer
PM52/cmd66 observer
additional diagnostic counters
additional diagnostic logging
FastPS experiments
P04
P05
P06
P07
P08
P10
P11
P12
P13
valve_min_percent correction
raw-ADC publication correction
raw TXDMA candidates
EM3 experiments
```

In particular, the historical periodic mDNS patch from `patch_firmware_v.1.0.py` is **not** part of B2.2.

Historical experiments using that patch remain valid as historical evidence but must not be described as part of the current B2.2 firmware.

---

# Supported firmware

Device:

```text
Shelly TRV Gen1
SHTRV-01
```

Supported Stock firmware:

```text
Version:
2.2.4

Build:
20240619-130912/v2.2.4@ee290818
```

Supported Stock GBL:

```text
Filename:
SHTRV-01_build_2.2.4.gbl

Size:
1,106,384 bytes

SHA256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

The patcher accepts only the specifically qualified Stock 2.2.4 input.

It does not search unknown firmware versions for similar instruction sequences and does not attempt heuristic relocation of the B2.2 correction set.

Unexpected input fails closed.

---

# Qualified B2.2 identities

## Application

```text
Filename:
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin

Size:
1,069,320 bytes

SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9

CRC32:
42657D97
```

## GBL

```text
Filename:
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl

Size:
1,126,156 bytes

SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

END CRC32:
52A97051

Whole-file CRC32 residue:
2144DF1C
```

These identities define the current qualified B2.2 build.

A different final application hash or GBL hash is a different firmware candidate and must not be silently treated as B2.2.

---

# Native Shelly firmware identity

B2.2 intentionally retains the original Shelly firmware identity:

```text
20240619-130912/v2.2.4@ee290818
```

No B2.2-specific research version is inserted into the normal Shelly firmware version string.

Consequently:

```text
/status
```

cannot uniquely distinguish B2.2 from Stock 2.2.4.

B2.2 is identified during construction and distribution by its exact artifact filename and cryptographic hashes.

---

# Patcher v2.0 reconstruction model

`patch_firmware_v2.0.py` is a standalone deterministic reconstruction tool.

It does not:

```text
download firmware
copy a finished B2.2 binary
copy a finished B2.2 GBL
embed the complete final firmware image
depend on the qualification reference directory at runtime
depend on the research directory at runtime
invent a new firmware variant
apply additional unqualified fixes
```

The patcher reconstructs B2.2 from the exact supported Stock 2.2.4 input.

The qualified Stock-to-B2.2 transformation is represented as approximately:

```text
1,404 exact authorized stock -> B2.2 byte runs
```

encoded as sparse transformation data with checked preimages.

This number must not be interpreted as 1,404 independent firmware defects or fixes.

B2.2 still contains exactly nine selected correction components.

The larger number of byte runs results from the compiled and integrated binary transformation required to reproduce the qualified application, including replacement code, relocated/integrated data and the WF200 firmware update.

---

# Reconstruction principle

For every authorized transformed region, the patcher verifies the expected Stock preimage before applying the corresponding transformation.

Conceptually:

```text
read Stock byte range
        |
        v
verify expected preimage
        |
        +-- mismatch --> ABORT
        |
        v
apply qualified transformation
        |
        v
continue
```

The transformation therefore depends on known Stock content rather than blindly writing output bytes at offsets.

After all qualified transformations have been applied, the application is validated against the exact qualified B2.2 identity.

The GBL container is then rebuilt with the required application data and final integrity information.

---

# Why v2.0 is not a two-byte patcher

The historical v1.0 implementation modified two PROGRAM bytes and updated the GBL CRC.

That model is no longer applicable.

B2.2 contains:

- additional host-side correction logic,
- new helper code,
- lifecycle corrections,
- synchronization corrections,
- peripheral cleanup corrections,
- calibration correction logic,
- a minimal MQTT guard,
- the official WF200 3.18.0 firmware,
- associated integration changes.

The B2.2 application is therefore larger than the Stock application represented by the historical v1.0 workflow.

The old statement:

```text
exactly 6 bytes differ in the complete GBL
```

applies only to the historical v1.0 two-patch build.

It must not be used for B2.2.

---

# Correction 1 — A1R / host power-management lifecycle

Reverse engineering identified several problematic host power-management lifecycle cases involving areas such as:

```text
final-sleep cleanup
wake-failure handling
timeout versus cancellation
late completions
requested versus committed PM state
old-completion races
independent inhibit ownership
settlement / handoff
```

An earlier experimental correction called A1 was created for these lifecycle problems.

Subsequent qualification identified a regression introduced by A1 itself.

Five native request paths use power-state request `1` only as a temporary override:

```text
physical button
HTTP /psovrd
Cloud psovrd
SSI settings_sta
OTA launcher
```

The intended native behavior is conceptually:

```text
selected policy = 3
        |
temporary request = 1
        |
state 1 temporarily
        |
restore selected policy 3
```

The historical A1 implementation could incorrectly turn such a temporary override into a persistent selected state:

```text
3 / 3
  |
temporary override
  |
  v
1 / 1
```

That regression belonged to the experimental A1 implementation.

It must not be represented as proof of an equivalent Shelly Stock firmware defect.

A1R corrects this regression while retaining the qualified A1 lifecycle corrections.

A1R recognizes the verified temporary-return paths and preserves the distinction between:

```text
temporary request
```

and:

```text
persistent selected policy
```

A1R qualification included:

```text
151 / 151 Thumb-level tests PASS
```

together with integration and retained-state testing.

---

# Correction 2 — C-C Beacon-Recovery evidence validity

Stock 2.2.4 contains a recurring host-side Beacon Recovery mechanism.

A typical runtime sequence is:

```text
Beacon skip error! Attempt recovery
        |
        v
power-save state 1
        |
approximately five serviced seconds
        |
        v
restore connected power-save policy
```

On affected Stock devices this can recur approximately once per minute.

The investigation established that the host-side value historically exposed as:

```text
real_beacon_skip
```

is not a direct physical WF200 beacon-skip setting.

The host uses the cumulative WF200 beacon receive counter.

Conceptually:

```text
P = previous cumulative beacon counter
C = current cumulative beacon counter

delta = C - P
R = uint8_t(600 / delta)
```

`R` is cached and later used by the host recovery decision.

Three evidence-validity problems were identified.

## C1a — signed interpretation

The calculated quotient is reduced to an 8-bit value and later interpreted as signed.

For example:

```text
600 / 3 = 200
uint8    = 0xC8
int8     = -56
```

A mathematically positive calculated value can therefore enter a signed control domain with different semantics.

## C1b — measurement-window validity

The fixed:

```text
600 / delta
```

calculation assumes a measurement relationship that is not encoded together with the retained previous counter value.

If expected measurement opportunities are skipped, a later counter delta can cover a different effective time interval while still being interpreted using the same fixed constant.

The cumulative counter itself may remain correct while the resulting control evidence is no longer valid for the assumed measurement window.

## C2 — stale recovery evidence

Stock recovery can clear the previous counter baseline while retaining the previously calculated recovery value.

A possible sequence is:

```text
fresh qualifying R
        |
        v
Recovery
        |
        v
previous counter baseline cleared
cached R retained
        |
        v
next sampling event establishes a new baseline
        |
        v
no new R calculated yet
        |
        v
old R remains available for evaluation
```

This can extend a transient qualifying event into a longer recurring recovery episode.

The recurrence is metastable, not necessarily permanent until reboot.

A later valid fresh measurement can replace the stale value and allow the device to leave the episode without rebooting.

## C-C behavior

C-C corrects the C1a, C1b and C2 evidence-validity problems.

It does **not** globally disable Beacon Recovery.

Recovery remains possible when evidence is:

```text
fresh
+
valid
+
qualifying
```

This distinction is important.

B2.2 therefore does not implement the historical v1.0 unconditional Beacon-Recovery bypass.

---

# Correction 3 — B2 bounded serialization

The host contains a shared reference counter referred to during the investigation as B2.

B2 represents owners requiring the host to remain at an EM1-capable sleep level.

Conceptually:

```text
B2 = 0 -> no EM1 owner
B2 = 1 -> one owner
B2 = 2 -> two owners
```

Reverse engineering found inconsistent serialization of read-modify-write operations on this counter.

A task could be preempted between load and store while another context updated the same counter.

This permits lost-update behavior.

Example phantom contribution:

```text
B2 = 1

Task A:
load B2 = 1

preempt

Task B:
release
1 -> 0

Task A resumes:
store stale increment
B2 -> 2
```

Only one legitimate owner remains, but the counter now contains two contributions.

After that real owner releases:

```text
2 -> 1
```

a phantom contribution remains.

The consequence can be:

```text
EM1 allowed
instead of
EM2
```

The inverse race can also lose a legitimate contribution and allow deeper sleep too early.

B2.2 uses bounded serialization with saved-PRIMASK semantics around the relevant shared-counter operations.

The correction preserves the previous interrupt state rather than blindly enabling interrupts after the protected operation.

No EM3 policy change is introduced by this correction.

---

# Correction 4 — minimal MQTT PUBLISH guard

B2.2 contains a minimal guard on the relevant MQTT PUBLISH input path.

This correction is included because a concrete malformed-input failure was demonstrated and a bounded guard was qualified.

The public battery-drain patcher documentation intentionally does not reproduce security-sensitive exploit or disclosure details.

Those details belong to the separate responsible-disclosure workflow.

The B2.2 guard is deliberately minimal and does not imply:

```text
remote code execution demonstrated
arbitrary write demonstrated
complete MQTT parser redesign
```

Qualification of the selected guard included:

```text
258 / 258 target/parser/worker tests PASS
```

---

# Correction 5 — official Silicon Labs WF200 3.18.0

Stock Shelly TRV 2.2.4 uses:

```text
Shelly FMAC:
3.7.0

WF200 radio firmware:
3.16.1
```

B2.2 retains the Shelly host FMAC integration while replacing the radio firmware with the official Silicon Labs:

```text
WF200 3.18.0
```

The later Silicon Labs release contains a power-save related correction for a condition in which the device can fail to sleep after a power-save mode change.

The official WF200 3.18.0 firmware was integrated into the Shelly application and qualified for correct relocation and runtime initialization.

Hardware testing established successful operation of:

```text
FMAC 3.7.0
+
WF200 3.18.0
```

including:

```text
WF200 initialization
WLAN scan
association
DHCP
cloud connectivity
connected power save
normal TRV operation
```

This establishes compatibility of the integrated radio firmware under the tested conditions.

It does **not** establish that WF200 3.18.0 alone fixes the historical Shelly TRV battery drain.

---

# Correction 6 — Calibration Restore Guard

A concrete calibration-state defect was identified in the restore path.

A queued successful restore could immediately enqueue itself again.

Conceptually:

```text
queued restore
        |
        v
successful completion
        |
        v
restore scheduling path
        |
        v
same work immediately queued again
```

B2.2 adds a Calibration Restore Guard that prevents the qualified self-requeue condition while preserving the intended calibration workflow.

Qualification covered native paths, scalar state combinations, queue behavior, countdown behavior and negative cases.

---

# Correction 7 — P01 Battery-PA3 release

The battery ADC path uses PA3 as part of the measurement resource lifecycle.

A timeout path could return without correctly releasing PA3.

A later successful measurement could repair the state, but this means the timeout path itself did not have complete resource cleanup.

B2.2 adds an ownership-aware release.

The correction is intended to release PA3 when the affected path owns the resource while avoiding an unrelated release of state owned elsewhere.

The electrical current contribution of the original defect has not been directly measured.

Therefore:

```text
resource-lifecycle defect proven
```

does not imply:

```text
quantitative battery-drain contribution proven
```

---

# Correction 8 — P02 bounded synchronous I2C timeout retirement

The analyzed synchronous I2C/display timeout path could return with state equivalent to:

```text
transaction unfinished
interrupt enable state retained
no complete abort / retirement
```

This leaves the peripheral transaction lifecycle incompletely retired.

B2.2 adds a bounded timeout-retirement path.

The correction is designed to complete the required shutdown/retirement work without introducing an unbounded wait.

Qualified helper code occupies the application range recorded by the B2.2 build evidence as:

```text
[0x104740, 0x1047C8)
```

---

# Correction 9 — P03 WLAN-GPIO interrupt-mask correction

A WLAN GPIO notification disable path passed:

```text
decimal 10
```

to an interface that expects a bit mask.

The value therefore had mask semantics different from the intended interrupt selection.

This could leave an intended interrupt source active while affecting other mask bits incorrectly.

B2.2 corrects the interrupt-mask operation.

The qualified correction occupies the application range recorded by the B2.2 build evidence as:

```text
[0x104840, 0x104854)
```

---

# Additional qualified B2.2 code regions

The B2.2 build evidence records additional integrated correction regions:

```text
P02 helper:
[0x104740, 0x1047C8)

P03:
[0x104840, 0x104854)

P01:
[0x104880, 0x1048BC)

Calibration Restore Guard:
[0x1050F4, 0x105108)
```

These ranges describe qualified B2.2 application regions.

They must not be interpreted as the complete Stock-to-B2.2 difference set.

The final B2.2 application identity is defined by the complete application hash.

---

# Observer-free design

B2.2 is intentionally observer-free.

It does not contain the diagnostic PM52/cmd66 observer used in earlier research builds.

It also does not contain the D3 observer or other diagnostic-only instrumentation.

The B2.2 build retains only the RAM required by the selected A1/A1R lifecycle implementation.

No observer RAM region is part of the final B2.2 candidate.

This matters because long-term runtime testing should evaluate the integrated correction set without the additional diagnostic observer.

---

# Patcher input validation

Before reconstruction proceeds, the patcher validates the supplied Stock firmware.

The validation boundary includes the exact supported input identity and the expected structure needed by the reconstruction logic.

At minimum, the supported Stock image is pinned by:

```text
Filename:
SHTRV-01_build_2.2.4.gbl

Size:
1,106,384 bytes

SHA256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

The patcher also validates expected preimage material before applying authorized transformations.

A firmware file that merely reports version `2.2.4` is not sufficient.

The exact supported binary identity is required.

---

# Fail-closed behavior

The v2.0 patcher is deliberately fail-closed.

Failure conditions tested during qualification include:

```text
modified Stock input
truncated GBL input
corrupted CRC / integrity
B2.2 supplied as input instead of Stock
modified expected preimage data
forced output-integrity mismatch
```

The patcher must not continue by guessing, relocating, or partially applying the correction set.

Conceptually:

```text
unexpected input
        |
        v
validation failure
        |
        v
NO firmware output accepted as B2.2
```

---

# Application reconstruction

The patcher applies the qualified Stock-to-B2.2 transformation to the supported application data.

After reconstruction, the resulting application must match:

```text
Size:
1,069,320 bytes

SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9

CRC32:
42657D97
```

A byte-level transformation can be considered successful only if the complete resulting application matches this identity.

Passing individual local preimage checks is not sufficient.

---

# GBL reconstruction

After the B2.2 application has been reconstructed, the patcher rebuilds the required GBL PROGRAM content and final END checksum.

The resulting GBL must match:

```text
Size:
1,126,156 bytes

SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

END CRC32:
52A97051

Whole-file CRC32 residue:
2144DF1C
```

The final GBL identity is an independent acceptance condition.

A correct application embedded into an incorrectly rebuilt container must not be accepted.

---

# Output readback verification

The patcher does not treat a successful file write as sufficient.

After writing the generated artifacts, it reopens and verifies the written output.

This protects against errors occurring between:

```text
validated in-memory result
```

and:

```text
actual file stored on disk
```

The final application and GBL identities must still match after readback.

---

# Deterministic reconstruction verification

The reconstructed v2.0 output was independently compared with the qualified B2.2 reference artifacts.

Application:

```text
generated SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9

reference SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9

byte-for-byte comparison:
IDENTICAL
```

GBL:

```text
generated SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

reference SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

byte-for-byte comparison:
IDENTICAL
```

This establishes deterministic reproduction of the qualified B2.2 artifacts.

---

# Standalone dependency test

The final patcher was also tested in isolation.

The test directory contained only:

```text
patch_firmware_v2.0.py
target/SHTRV-01_build_2.2.4.gbl
```

The reconstruction succeeded and generated the exact expected B2.2 application and GBL identities.

This confirms that runtime reconstruction does not depend on:

```text
reference/
research/
qualification build trees
Codex
REA
Ghidra
freeze scripts
reference B2.2 binaries
```

The qualification environment was used to derive and verify the reconstruction recipe.

It is not required to run the final patcher.

---

# Automated patcher tests

The v2.0 patcher test suite currently contains:

```text
18 tests
```

The suite includes positive reconstruction and fail-closed negative cases.

Current result:

```text
Ran 18 tests

OK
```

Some negative tests intentionally trigger an error message such as an output-hash mismatch.

Such an expected rejection message is not a suite failure when the final test result is:

```text
OK
```

---

# B2.2 qualification coverage

The B2.2 build qualification included component-level and integration testing.

Recorded qualification coverage includes:

```text
A1R:
151 / 151

C-C:
512 + 10000 cases

B2:
2060 + 102
plus mixed/preemption cases

MQTT:
258 cases

Calibration Restore Guard:
68 native
66535 scalar
104 queue
30 countdown
plus negative tests

P01:
128 + 6

P02:
90 + 480

P03:
128 native

motor / B2 / P01 interaction:
10 + 30

sleep / PA8:
48

battery / OTA / boot:
10002 + 2 + 4 + 3

interfaces / flows:
10 interactions
13 flow groups
```

The build process additionally established:

```text
multiple clean application constructions identical
GBL constructions byte-identical
zero unexplained application differences
zero unexplained container differences
observer absence verified
```

These results establish strong offline qualification of the selected B2.2 build.

---

# Physical runtime validation

B2.2 has subsequently been installed on physical Shelly TRV Gen1 hardware.

The initial hardware canary successfully demonstrated the complete operational chain:

```text
OTA
        |
        v
cold reboot
        |
        v
Shelly 2.2.4 application boot
        |
        v
FMAC 3.7.0
        |
        v
WF200 3.18.0 initialization
        |
        v
WLAN scan / association
        |
        v
DHCP
        |
        v
calibration
        |
        v
connected power save
        |
        v
cloud connectivity
```

After approximately 29 hours, the initial canary showed:

```text
reboot counter:       1
reconnect counter:    1
beacon error counter: 0
desired beacon skip:  20
real beacon skip:     21
battery display:      99 %
voltage:              approximately 4.027 V
```

No unexpected additional reboot or reconnect was observed in that period.

The hardware test was subsequently expanded to the active test fleet on 2026-11-02.

B2.2 is therefore no longer an offline-only firmware candidate.

---

# Current hardware qualification boundary

Physical runtime success establishes that B2.2 can:

```text
boot on real hardware
initialize WF200 3.18.0
associate with WLAN
obtain DHCP configuration
operate connected power save
connect to the cloud
perform normal TRV operation
```

It does not yet establish:

```text
indefinite long-term stability
restored original battery lifetime
quantified battery-life improvement
the sole historical battery-drain root cause
the primary historical battery-drain root cause
```

Long-term fleet observation remains in progress.

---

# Battery interpretation

The Shelly battery percentage displayed by the firmware is not a coulomb counter.

Static analysis showed that the displayed percentage is derived from the measured/cached battery voltage.

This means the displayed percentage can:

```text
rise without charging
fall non-linearly
differ between batteries at similar state of charge
```

For short-term battery comparisons, voltage is therefore generally more informative than percentage alone.

Neither value directly measures instantaneous or accumulated current consumption.

---

# Firmware defect versus battery causation

A central interpretation rule for this project is:

```text
firmware defect
!=
battery-drain root cause
```

Likewise:

```text
qualified correction
!=
measured energy saving
```

and:

```text
successful B2.2 runtime
!=
long-term battery-life improvement proven
```

Several concrete firmware defects have been demonstrated and corrected in B2.2.

Their individual and combined quantitative contribution to the historical battery drain has not yet been fully measured.

---

# Deferred findings

Several additional findings were intentionally excluded from B2.2 because they were not part of the selected qualified correction set.

Examples include:

```text
P04 motor-timeout movement-accounting issue
valve_min_percent mixed-unit issue
raw ADC transient publication
raw TXDMA candidates
additional peripheral candidates
EM3 changes
FastPS diagnostic ideas
```

Exclusion does not necessarily mean that a finding is invalid.

It means that the finding was not selected as part of the current qualified B2.2 firmware.

A future correction must be qualified separately and would create a new firmware candidate with a new application and GBL identity.

---

# Historical mDNS work

Earlier project versions investigated recurring connected-state mDNS responder restart behavior.

Historical testing demonstrated that the periodic restart could be suppressed without globally disabling mDNS.

However, longer-term testing also demonstrated that removing the targeted periodic mDNS restart did not by itself prevent poor battery runtime or the Beacon-Recovery behavior.

For this reason, and because B2.2 contains only the selected qualified correction set, the historical mDNS bypass is not included in B2.2.

Historical mDNS evidence remains part of the research history.

It must not be represented as a current B2.2 correction.

---

# Historical v1.0 patcher

`patch_firmware_v.1.0.py` is a historical implementation.

It produced the earlier combined experimental firmware based on:

```text
Beacon-Recovery bypass
+
periodic mDNS restart bypass
```

That implementation and its output identities are not the current patching workflow.

Historical v1.0 values such as:

```text
SHTRV-01_2.2.4_beacon_mdns_patch.gbl

SHA256:
7adbb31d6b7faa8b9290d7b3436af45d42af9c3602a7195cafab774ded84ac61

CRC32:
BAEB8265
```

must not be used to validate B2.2.

The current expected B2.2 GBL is:

```text
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl

SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

END CRC32:
52A97051
```

---

# Reproducibility summary

Current supported input:

```text
Device:
Shelly TRV Gen1 / SHTRV-01

Firmware:
20240619-130912/v2.2.4@ee290818

Stock GBL:
SHTRV-01_build_2.2.4.gbl

Size:
1,106,384 bytes

SHA256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

Current reconstruction tool:

```text
patch_firmware_v2.0.py
```

Expected application:

```text
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin

Size:
1,069,320 bytes

SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9

CRC32:
42657D97
```

Expected GBL:

```text
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl

Size:
1,126,156 bytes

SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

END CRC32:
52A97051

Whole-file CRC32 residue:
2144DF1C
```

Successful reconstruction requires the generated application and GBL to match these exact identities.

---

# Current technical conclusion

The current evidence establishes:

```text
exact supported Stock input identified

nine selected B2.2 corrections qualified

deterministic Stock -> B2.2 reconstruction implemented

fail-closed input/preimage/output validation implemented

generated B2.2 application byte-identical to qualified reference

generated B2.2 GBL byte-identical to qualified reference

standalone patcher operation verified

B2.2 physical boot and basic runtime operation verified

WF200 3.18.0 physical integration verified
```

The current evidence does **not** establish:

```text
historical battery-drain root cause conclusively proven

B2.2 guaranteed to eliminate historical battery drain

long-term battery-life improvement quantified

indefinite long-term stability proven

B2.2 suitable as an official production release
```

These boundaries are intentional.

The current firmware status is:

```text
B2.2 EXPERIMENTAL

physical runtime testing:
in progress

long-term battery validation:
in progress
```