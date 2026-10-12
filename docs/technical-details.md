# Technical Details

This document describes the technical implementation of the two firmware
modifications applied by this project and the validation performed by:

```text
patch_firmware_v.1.0.py
```

The current patcher applies two independent modifications to the supported
Shelly TRV 2.2.4 firmware:

- **Patch A:** bypass of the recurring beacon-skip recovery path
- **Patch B:** bypass of the periodic connected-state mDNS responder restart

Both modifications are applied to the same main PROGRAM block.

Detailed reverse-engineering research, firmware comparisons, runtime logs,
packet captures and the investigation that led to these modifications are
maintained in the separate research repository.

This document intentionally describes only the firmware build and exact patch
implemented by this project.

It is not intended as general documentation for other Shelly firmware versions
or as a general description of the GBL format.

---

## Supported firmware

Device:

```text
Shelly TRV (SHTRV-01)
```

Firmware:

```text
Version: 2.2.4
Build:   20240619-130912/v2.2.4@ee290818
```

Original GBL size:

```text
1,106,384 bytes
```

Original GBL SHA-256:

```text
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

Original GBL CRC32:

```text
0xDC7BAB58
```

Original main PROGRAM SHA-256:

```text
4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c
```

Only this specifically analyzed firmware image is accepted by the patcher.

The patcher does not attempt to locate equivalent instructions in unknown
firmware versions.

---

# Patch A — Beacon-skip recovery bypass

## Observed behavior

Firmware 2.2.4 was observed repeatedly producing the runtime sequence:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip N)
```

Under affected conditions this sequence could recur approximately once per
minute.

Reverse engineering showed that this recovery behavior is separate from the
normal RSSI-dependent beacon-skip selection mechanism.

Patch A bypasses the additional recovery block while leaving the normal
RSSI-dependent beacon-skip selection code intact.

---

## Normal beacon-skip selection

Analysis of the supported firmware showed the following desired beacon-skip
selection:

```text
RSSI >= -69 dBm        -> beacon skip 20
RSSI -79 .. -70 dBm    -> beacon skip 15
RSSI < -79 dBm         -> beacon skip 10
```

Equivalent threshold behavior was also found in older firmware examined during
the investigation.

Patch A does not modify:

- these RSSI thresholds,
- the desired beacon-skip calculation,
- normal entry into powersave state 3,
- the configured skip value selected from RSSI.

The patch targets only the additional recovery path.

---

## Beacon statistics and recovery condition

Further reverse engineering established that firmware 2.2.4 obtains beacon
statistics from the WLAN subsystem using command:

```text
0x66
```

The returned data includes values corresponding to:

```text
beacon_rx_count
missed
tbtt_diff
```

The firmware derives the value used by the recovery logic from the change in
the cumulative beacon receive counter.

The relevant calculation is equivalent to:

```text
600 / (current_beacon_rx_count - previous_beacon_rx_count)
```

The result is truncated to its low byte and is subsequently read as a signed
8-bit value by the recovery-condition code.

This detail is important because the recovery condition is therefore not
simply a direct test of the desired RSSI-based beacon-skip setting.

The value involved in the recovery path and the configured desired
beacon-skip value are separate quantities.

---

## Recovery-path condition

The relevant firmware sequence contains:

```asm
0001E1B6  21 4B        ldr      r3,[...]
0001E1B8  93 F9 00 30  ldrsb.w  r3,[r3,#0]
0001E1BC  00 2B        cmp      r3,#0
0001E1BE  36 D0        beq      0x0001E22E

0001E1C0  1E 4B        ldr      r3,[...]
0001E1C2  93 F9 00 30  ldrsb.w  r3,[r3,#0]
0001E1C6  02 2B        cmp      r3,#2
0001E1C8  31 DC        bgt      0x0001E22E
```

The additional recovery block follows this conditional branch.

Because the value is loaded with a signed-byte load, the relevant control flow
is effectively:

```text
value == 0   -> continue without recovery
value <= 2   -> recovery path, except zero
value > 2    -> continue without recovery
```

This includes negative signed-byte values.

The binary-analysis result therefore establishes that the recovery predicate
is effectively:

```text
value != 0 && value <= 2
```

for the signed value used at this point in the firmware.

---

## Beacon recovery behavior

When the recovery path is entered, the firmware requests:

```text
powersave state 1
```

Analysis of the WLAN power-management path indicates that this state
corresponds to an active/always-on WLAN power-management mode.

During the observed recovery sequence, the firmware remains in this state for
approximately five seconds.

It then restores the previously selected or deferred power state, normally:

```text
powersave state 3 (skip N)
```

with the current desired RSSI-dependent beacon-skip value.

The recovery path therefore temporarily changes WLAN power-management behavior.

No explicit transmit-power increase was identified in the analyzed recovery
path.

The recovery sequence also does not inherently imply a full Wi-Fi scan,
reconnect, DHCP exchange or cloud reconnect.

The energy impact of the repeated state-1 interval is plausible but has not
been quantitatively measured by this project.

---

## Patch A instruction

Relevant instruction offset in PROGRAM #1:

```text
0x0001E1C8
```

Original instruction:

```asm
31 DC    bgt 0x0001E22E
```

Patched instruction:

```asm
31 E0    b 0x0001E22E
```

The original conditional branch is replaced with an unconditional branch to
the same existing destination.

Execution therefore always continues at:

```text
0x0001E22E
```

instead of being able to fall through into the additional recovery block.

The destination code itself is not modified.

---

## Patch A byte modification

The Thumb instruction is two bytes long:

```text
Original: 31 DC
Patched : 31 E0
```

Only the second byte changes.

PROGRAM #1 offset:

```text
0x0001E1C9
```

Modification:

```text
DC -> E0
```

Corresponding GBL file offset:

```text
0x0002471D
```

---

## Patch A context

Original bytes around the instruction:

```text
0x0001E1B8:
93 F9 00 30 00 2B 36 D0 1E 4B 93 F9 00 30 02 2B

0x0001E1C8:
31 DC 07 F1 14 03 18 46 54 F0 BC FB F8 62 EC F7
```

After Patch A:

```text
0x0001E1C8:
31 E0 07 F1 14 03 ...
```

---

# Patch B — Periodic mDNS restart bypass

## Observed behavior

Firmware comparison and runtime packet capture identified recurring mDNS
activity that differs between firmware versions.

Observed runtime behavior included approximately:

```text
Firmware 2.1.0   -> no recurring mDNS traffic observed during the capture
Firmware 2.1.3   -> recurring mDNS activity approximately every 60 seconds
Firmware 2.2.4   -> recurring mDNS activity approximately every 180 seconds
```

These values describe the documented finite packet-capture windows.

Absence of packets from firmware 2.1.0 during that finite observation period
does not prove that the firmware can never emit mDNS traffic.

Static analysis of firmware 2.2.4 identified the recurring connected-state
call responsible for the approximately 180-second activity.

---

## Periodic scheduling path

The relevant firmware logic is serviced by the firmware's minute-based
maintenance path.

A firmware-seconds dispatcher invokes the minute routine when the relevant
time value reaches a minute boundary.

The minute routine increments an internal counter.

Firmware 2.2.4 then performs a modulo-three test on this counter.

The resulting behavior is approximately:

```text
minute 1 -> no periodic mDNS restart
minute 2 -> no periodic mDNS restart
minute 3 -> connected-state mDNS restart
```

and then repeats.

The observed approximately 180-second interval is therefore not implemented as
a dedicated independent 180-second timer.

It results from an every-third-invocation condition inside the minute
maintenance path.

Depending on scheduling and missed boundaries, observed packet timing does not
need to be exactly 180.000 seconds.

---

## mDNS restart function

Reverse engineering identified the relevant restart-equivalent function at:

```text
0x0003D6C8
```

Its behavior is consistent with restarting the mDNS responder state.

The function:

- resets responder probe state,
- returns the responder to probing,
- schedules the probing callback,
- eventually results in normal mDNS probe and announcement traffic.

The probing sequence uses the existing mDNS implementation and UDP port:

```text
5353
```

The function itself is not removed or modified by Patch B.

---

## Other mDNS restart callers

The mDNS restart-equivalent function has multiple callers.

The periodic connected-state caller targeted by Patch B is only one of them.

Other analyzed call sites include paths associated with:

- button-release behavior,
- network-interface addition,
- service addition,
- successful connection establishment.

Patch B does not modify those callers.

This distinction is important:

> Patch B does not disable mDNS.

It bypasses only the recurring connected-state restart call identified in the
periodic maintenance path.

Normal initialization and event-driven mDNS functionality remain outside the
modified call site.

---

## Patch B control flow

The relevant periodic code contains a conditional branch at:

```text
0x0001E0F0
```

Original instruction:

```text
02 D0
```

This is a conditional branch to:

```text
0x0001E0F8
```

When the original condition does not branch, execution continues through the
periodic mDNS restart call.

The restart call itself occurs at:

```text
0x0001E0F4
```

and calls:

```text
0x0003D6C8
```

The continuation begins at:

```text
0x0001E0F8
```

Patch B replaces the conditional branch with an unconditional branch to the
same continuation.

---

## Patch B instruction

Relevant instruction offset in PROGRAM #1:

```text
0x0001E0F0
```

Original:

```text
02 D0
```

Patched:

```text
02 E0
```

The instruction therefore changes from a conditional branch to an
unconditional branch.

The target remains:

```text
0x0001E0F8
```

The result is that execution always skips the periodic restart call at:

```text
0x0001E0F4
```

---

## Patch B byte modification

The instruction is two bytes long:

```text
Original: 02 D0
Patched : 02 E0
```

Only the second byte changes.

PROGRAM #1 offset:

```text
0x0001E0F1
```

Modification:

```text
D0 -> E0
```

Corresponding GBL file offset:

```text
0x00024645
```

---

## Patch B context

Original instruction window:

```text
02 D0 29 48 1F F0 E8 FA 12 4B
```

Patched instruction window:

```text
02 E0 29 48 1F F0 E8 FA 12 4B
```

The bypassed call begins at:

```text
0x0001E0F4
```

with bytes:

```text
1F F0 E8 FA
```

The continuation at:

```text
0x0001E0F8
```

begins with:

```text
12 4B
```

The call instruction itself is deliberately left unchanged.

Only the preceding control-flow branch is modified.

---

# Relationship between Patch A and Patch B

Patch A and Patch B affect two different firmware paths.

Patch A targets:

```text
beacon statistics
        |
        v
derived recovery value
        |
        v
recovery predicate
        |
        v
temporary powersave state 1
```

Patch B targets:

```text
minute maintenance
        |
        v
modulo-three condition
        |
        v
periodic mDNS responder restart
        |
        v
mDNS probes / announcement
```

The two patches are located close to each other in the main PROGRAM image, but
their targeted runtime behaviors are distinct.

Runtime testing provides additional evidence for this separation.

A physical device running **Patch B only** showed:

```text
periodic mDNS traffic:    not observed in the monitored capture
beacon recovery sequence: still observed repeatedly
```

The beacon recovery continued approximately once per minute even though the
targeted periodic mDNS activity was no longer observed.

This occurred even with relatively strong Wi-Fi signal conditions around:

```text
-58 to -59 dBm
```

and normal desired beacon skip:

```text
20
```

Under the tested conditions, the periodic mDNS restart was therefore not
required for the observed beacon-recovery behavior.

This does not prove that the two mechanisms can never interact indirectly
under any possible runtime condition.

---

# GBL container

The supported original firmware is stored in a GBL container.

For this specific image, the parsed container contains six tags:

```text
#1  HEADER
    ID             : 0x03A617EB
    Tag offset     : 0x00000000
    Payload length : 8 bytes

#2  APPLICATION_INFO
    ID             : 0xF40A0AF4
    Tag offset     : 0x00000010
    Payload length : 28 bytes

#3  BOOTLOADER
    ID             : 0xF50909F5
    Tag offset     : 0x00000034
    Payload length : 25,868 bytes

#4  PROGRAM
    ID             : 0xFD0303FD
    Tag offset     : 0x00006548
    Payload length : 1,049,552 bytes

#5  PROGRAM
    ID             : 0xFD0303FD
    Tag offset     : 0x00106920
    Payload length : 30,876 bytes

#6  END
    ID             : 0xFC0404FC
    Tag offset     : 0x0010E1C4
    Payload length : 4 bytes
```

The patcher validates this exact expected structure before modifying the
firmware.

---

# PROGRAM blocks

The supported GBL contains two PROGRAM tags.

Each PROGRAM payload contains a four-byte flash address followed by the program
data.

## PROGRAM #1

Flash start:

```text
0x00000000
```

Flash end:

```text
0x001003CB
```

Program data size:

```text
1,049,548 bytes
```

GBL program-data range:

```text
0x00006554 - 0x0010691F
```

Original PROGRAM #1 SHA-256:

```text
4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c
```

Both Patch A and Patch B are located in PROGRAM #1.

---

## PROGRAM #2

Flash start:

```text
0x00130A98
```

Flash end:

```text
0x0013832F
```

Program data size:

```text
30,872 bytes
```

GBL program-data range:

```text
0x0010692C - 0x0010E1C3
```

PROGRAM #2 SHA-256:

```text
662bd549f050ab81a120d3daa07646652c38880b9d2bfa988ff6bee7f731e33e
```

PROGRAM #2 is not modified.

The patcher verifies that it remains unchanged when rebuilding the GBL.

---

# Address mapping

PROGRAM #1 begins at flash address:

```text
0x00000000
```

and its actual program data begins at GBL file offset:

```text
0x00006554
```

Because PROGRAM #1 is mapped to flash address zero, its PROGRAM offsets and
flash addresses are numerically identical.

---

## Patch B address mapping

PROGRAM offset:

```text
0x0001E0F1
```

Flash address:

```text
0x0001E0F1
```

GBL calculation:

```text
0x00006554 + 0x0001E0F1 = 0x00024645
```

Complete mapping:

```text
PROGRAM offset : 0x0001E0F1
Flash address  : 0x0001E0F1
GBL file offset: 0x00024645
```

Modification:

```text
D0 -> E0
```

---

## Patch A address mapping

PROGRAM offset:

```text
0x0001E1C9
```

Flash address:

```text
0x0001E1C9
```

GBL calculation:

```text
0x00006554 + 0x0001E1C9 = 0x0002471D
```

Complete mapping:

```text
PROGRAM offset : 0x0001E1C9
Flash address  : 0x0001E1C9
GBL file offset: 0x0002471D
```

Modification:

```text
DC -> E0
```

---

# GBL handling

The patcher does not construct a firmware image from scratch.

It:

1. locates the fixed original firmware in `target/`,
2. reads the original GBL,
3. validates the complete original file identity,
4. parses the expected GBL tag structure,
5. validates the original GBL CRC32,
6. identifies the expected PROGRAM blocks,
7. validates PROGRAM #1,
8. validates both original patch instructions,
9. validates both original patch bytes,
10. applies Patch B in memory,
11. applies Patch A in memory,
12. validates both resulting instructions,
13. validates the resulting PROGRAM #1 SHA-256,
14. verifies that PROGRAM #2 remains unchanged,
15. reinserts the modified PROGRAM #1 data into a copy of the original GBL,
16. recalculates the GBL CRC32,
17. validates the rebuilt GBL,
18. verifies the exact expected original-to-patched byte differences,
19. verifies the final GBL SHA-256,
20. writes the result only after validation succeeds,
21. reads the written output back and verifies it again.

Unrelated firmware data is expected to remain unchanged.

---

# CRC32

The original GBL contains the stored CRC32:

```text
0xDC7BAB58
```

For this firmware, CRC32 is calculated over the GBL data from:

```text
0x00000000
```

through:

```text
0x0010E1CB
```

inclusive.

The four stored CRC bytes occupy:

```text
0x0010E1CC - 0x0010E1CF
```

The CRC32 calculated over the original file matches the stored value:

```text
Calculated: 0xDC7BAB58
Stored    : 0xDC7BAB58
```

After applying both program modifications, the expected CRC32 is:

```text
0xBAEB8265
```

Stored little-endian, the resulting four bytes are:

```text
65 82 EB BA
```

---

# Expected byte differences

The combined patch intentionally changes exactly two bytes in PROGRAM #1.

Patch B:

```text
GBL offset 0x00024645

D0 -> E0
```

Patch A:

```text
GBL offset 0x0002471D

DC -> E0
```

These two changes produce a new GBL CRC32, so the four stored CRC bytes also
change.

The complete expected original-to-patched GBL difference is therefore:

```text
Offset       Original   Patched
-----------  --------   -------
0x00024645     D0         E0
0x0002471D     DC         E0
0x0010E1CC     58         65
0x0010E1CD     AB         82
0x0010E1CE     7B         EB
0x0010E1CF     DC         BA
```

Exactly:

```text
6 bytes
```

in the complete GBL file are expected to differ.

Two are intentional PROGRAM modifications.

Four contain the updated CRC32.

Any other difference causes validation to fail.

---

# Patched PROGRAM verification

Original PROGRAM #1 SHA-256:

```text
4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c
```

Expected combined patched PROGRAM #1 SHA-256:

```text
06742a2632a3d45cf697b8be85045914d004f30644dad17b3d0d20012c87c61b
```

The patcher verifies this value after applying both byte modifications.

This establishes that the resulting PROGRAM data matches the exact combined
program image produced during development and validation.

---

# Final GBL verification

Expected patched GBL size:

```text
1,106,384 bytes
```

Expected patched GBL CRC32:

```text
0xBAEB8265
```

Expected patched GBL SHA-256:

```text
7adbb31d6b7faa8b9290d7b3436af45d42af9c3602a7195cafab774ded84ac61
```

The output is considered valid only when the rebuilt GBL matches:

- the expected structure,
- the expected PROGRAM layout,
- the expected two program modifications,
- the expected PROGRAM #1 SHA-256,
- the expected CRC32,
- the exact six GBL byte differences,
- the expected final GBL SHA-256.

The file written to disk is read back and checked again.

---

# Fail-closed validation

The patcher is intentionally restricted to the known firmware image.

Before a patched file can be written, validation includes:

```text
Original file size
Original GBL SHA-256
GBL tag structure
Original GBL CRC32
PROGRAM block count
PROGRAM flash addresses
PROGRAM sizes
Original PROGRAM #1 SHA-256

Patch B original instruction
Patch B original byte

Patch A original instruction
Patch A original byte

Patched PROGRAM #1 SHA-256
Unmodified PROGRAM #2
Expected rebuilt GBL structure
Expected patched CRC32
Exact original-to-patched byte differences
Expected patched GBL SHA-256
```

If an expected value does not match, processing is aborted.

The patcher does not attempt to adapt either patch to an unknown firmware
build.

---

# Analyzer

The `--analyze` mode exposes technical information used by this project
without modifying the firmware.

The supported firmware is automatically read from:

```text
target/SHTRV-01_build_2.2.4.gbl
```

Run:

```bash
python3 patch_firmware_v.1.0.py --analyze
```

It reports information including:

```text
Firmware identity
GBL container information
GBL tag map
CRC32 ranges and values
PROGRAM layout
PROGRAM SHA-256 values

Patch B address mapping
Patch B original and patched instruction
Patch B hexadecimal context

Patch A address mapping
Patch A original and patched instruction
Patch A hexadecimal context

Expected combined patch effects
Expected patched hashes
```

Analysis mode is read-only.

It is specifically intended to make the technical basis of the implemented
patches visible and reproducible.

It is not intended to be a general-purpose GBL or binary analyzer.

---

# Runtime validation

Binary validation establishes what was changed.

Runtime validation is performed separately to determine whether the expected
behavior is actually observed on physical hardware.

Several forms of runtime evidence are used:

```text
Debug logs
Packet captures
Device status/statistics
Longer-term battery-logger reports
```

---

## Patch B-only runtime validation

Patch B was first tested independently on a physical Shelly TRV running
firmware 2.2.4.

The device contained the periodic mDNS restart bypass but retained the original
beacon-recovery logic.

A packet capture monitoring UDP port 5353 for the device showed:

```text
0 periodic mDNS packets observed
```

during the monitored capture window.

This is consistent with Patch B bypassing the targeted periodic restart call.

It does not establish that mDNS is globally disabled.

Event-driven mDNS callers remain intact.

---

## Beacon recovery with Patch B only

The same Patch B-only device continued to produce:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip 20)
```

approximately once per minute.

Importantly, this behavior was observed even with RSSI around:

```text
-58 to -59 dBm
```

where the normal desired beacon-skip selection was:

```text
20
```

This provides runtime evidence that poor RSSI is not required for the observed
recovery behavior under the tested conditions.

It also demonstrates that suppressing the targeted periodic mDNS restart does
not by itself suppress the beacon-recovery sequence.

---

## Combined Patch A+B runtime validation

The final combined firmware was generated with both modifications and installed
on a separate physical Shelly TRV.

The device was upgraded from:

```text
20220202-080736/v2.1.3@d255ad74
```

to:

```text
20240619-130912/v2.2.4@ee290818
```

using the local OTA server.

The patch intentionally retains the original 2.2.4 version string.

The device successfully rebooted and resumed normal operation.

Observed operation included:

- Wi-Fi connectivity,
- cloud connectivity,
- temperature measurement,
- thermostat processing,
- normal RSSI-dependent beacon-skip selection.

---

## Combined Patch B result

A packet capture was performed after installing the combined firmware.

During the monitored capture window, the previously identified periodic mDNS
activity was not observed.

This provides runtime evidence that Patch B remains effective when combined
with Patch A.

Again, this result applies to the targeted periodic restart path.

It does not mean that all mDNS functionality has been disabled.

---

## Combined Patch A result

The combined patched device has been observed for multiple hours.

During the evaluated multi-hour runtime log, the device continued normal
minute-based operation.

The previously recurring sequence:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip N)
```

was not observed.

In particular, the additional recurring transition into:

```text
powersave state 1
```

was absent from the monitored log.

Normal operation using:

```text
powersave state 3 (skip 20)
```

continued under the observed signal conditions.

This is consistent with the intended Patch A control-flow effect.

The result provides multi-hour physical runtime evidence that the targeted
recovery path is being bypassed under the tested conditions.

It does not establish that the event can never occur under every possible
runtime condition.

---

# Runtime statistics

Firmware 2.2.4 exposes additional beacon-related statistics that are useful
during investigation.

Observed fields include values such as:

```text
desired_beacon_skip
real_beacon_skip
beacon_err_counter
```

Reverse engineering established substantially more context for these fields
than was available during the earlier phase of the project.

The desired beacon-skip value represents the normal RSSI-dependent target
selection.

The calculated real-beacon-skip value is derived from beacon receive counter
behavior and is not equivalent to the desired configured skip value.

Therefore a state such as:

```text
desired_beacon_skip: 20
real_beacon_skip:     3
```

is not inherently contradictory.

The device can continue using:

```text
powersave state 3 (skip 20)
```

while the separately calculated beacon statistic has another value.

The recovery logic must therefore not be interpreted as simply checking
whether the configured WLAN skip value is 1 or 2.

---

# Longer-term monitoring

Short runtime tests are complemented by the project's `battery_logger`.

The logger periodically collects device information for longer-term comparison
and report generation.

Depending on firmware support, collected information includes:

```text
firmware version
battery percentage
battery voltage
uptime
Wi-Fi RSSI
beacon statistics
desired beacon skip
calculated real beacon skip
beacon error/recovery counters
```

Older firmware versions do not expose all of these statistics.

Unavailable fields are therefore recorded as unavailable rather than inferred.

The generated reports are used to compare longer-term runtime behavior and
battery trends across different firmware and patch configurations.

These reports complement:

```text
static reverse engineering
binary validation
debug logging
packet capture
```

but do not replace any of them.

---

# Battery-consumption interpretation

The original investigation was motivated by unexpectedly high battery
consumption observed on Shelly TRV Gen1 devices.

The current analysis has identified multiple recurring or potentially
energy-relevant firmware behaviors.

These include:

- periodic mDNS restart activity,
- recurring beacon-skip recovery,
- temporary WLAN powersave state changes,
- additional conditional power-management behavior investigated in the
  research repository.

However, identifying a recurring firmware activity does not establish its
quantitative contribution to battery consumption.

The project has not directly measured the electrical current attributable to
Patch A or Patch B.

Battery percentage and battery voltage are also not direct current
measurements.

Cross-device battery comparisons are affected by variables including:

- battery cells,
- battery state,
- battery calibration,
- valve activity,
- temperature regulation,
- Wi-Fi conditions,
- device history,
- hardware variation.

The strongest current conclusion is therefore:

```text
Patch A:
The targeted recurring beacon-recovery path is bypassed and the expected
runtime suppression has been observed.

Patch B:
The targeted periodic connected-state mDNS restart is bypassed and the
expected network-level suppression has been observed.

Combined firmware:
Both modifications operate together on physical hardware under the tested
conditions.

Battery-life improvement:
Not yet established.
```

Long-term battery monitoring remains separate from verification of the binary
and runtime effects of the patches.

---

# Scope of the technical conclusion

The following properties are directly established by binary analysis and
deterministic patch validation:

- the exact supported original firmware,
- the exact original instructions,
- the exact patched instructions,
- the two PROGRAM byte modifications,
- the resulting control-flow changes,
- the unchanged branch destinations,
- the unchanged normal RSSI-dependent beacon-skip selection code,
- the unchanged event-driven mDNS restart callers,
- the exact rebuilt GBL differences,
- the resulting CRC32,
- the resulting PROGRAM SHA-256,
- the resulting GBL SHA-256.

Physical-device testing additionally establishes under the observed test
conditions:

- successful installation of the combined patched firmware,
- successful boot,
- normal basic TRV operation,
- continued normal RSSI-dependent beacon-skip selection,
- suppression of the targeted periodic mDNS traffic during the capture window,
- absence of the targeted beacon-recovery sequence during the evaluated
  multi-hour combined-patch log.

The current evidence does **not** establish:

- behavior under every possible WLAN condition,
- behavior under every possible RSSI condition,
- that mDNS is completely disabled,
- that the two targeted mechanisms can never interact indirectly,
- indefinite long-term firmware stability,
- the quantitative energy cost of either original mechanism,
- that either mechanism was the sole cause of historical battery drain,
- that either mechanism was the primary cause of historical battery drain,
- a quantified improvement in battery life.

These distinctions are intentional.

---

# Reproducibility summary

For the supported firmware:

```text
Device:
Shelly TRV (SHTRV-01)

Firmware:
20240619-130912/v2.2.4@ee290818


Original GBL size:
1,106,384 bytes

Original GBL SHA-256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f

Original GBL CRC32:
0xDC7BAB58


Original PROGRAM #1 SHA-256:
4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c


Patch B — periodic mDNS restart bypass

Instruction:
PROGRAM 0x0001E0F0

02 D0
->
02 E0

Modified PROGRAM byte:
0x0001E0F1
D0 -> E0

GBL patch location:
0x00024645
D0 -> E0


Patch A — beacon-skip recovery bypass

Instruction:
PROGRAM 0x0001E1C8

31 DC
->
31 E0

Modified PROGRAM byte:
0x0001E1C9
DC -> E0

GBL patch location:
0x0002471D
DC -> E0


Combined patched PROGRAM #1 SHA-256:
06742a2632a3d45cf697b8be85045914d004f30644dad17b3d0d20012c87c61b


Combined patched GBL CRC32:
0xBAEB8265

Combined patched GBL SHA-256:
7adbb31d6b7faa8b9290d7b3436af45d42af9c3602a7195cafab774ded84ac61


Expected complete GBL differences:

0x00024645  D0 -> E0
0x0002471D  DC -> E0
0x0010E1CC  58 -> 65
0x0010E1CD  AB -> 82
0x0010E1CE  7B -> EB
0x0010E1CF  DC -> BA


Total changed GBL bytes:
6
```

These values define the exact combined firmware transformation currently
implemented by this project.