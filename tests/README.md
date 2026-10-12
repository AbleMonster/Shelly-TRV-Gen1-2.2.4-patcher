# Tests

This directory documents validation, OTA-transfer testing, physical-device
runtime testing and longer-term monitoring performed for the Shelly TRV Gen1
2.2.4 Firmware Patcher.

The current patcher applies two firmware modifications:

- **Patch A:** beacon-skip recovery bypass
- **Patch B:** periodic mDNS restart bypass

The project intentionally does not include proprietary Shelly firmware test
fixtures.

All firmware-dependent tests are performed locally using an original firmware
image supplied separately by the user.

---

## Test scope

Testing is divided into four areas:

1. patcher and firmware-image validation,
2. OTA-server and transfer validation,
3. runtime testing on physical Shelly TRV hardware,
4. longer-term battery and runtime monitoring.

These are separate test objectives.

Binary validation verifies that the patcher produces exactly the expected
firmware transformation.

OTA-server testing verifies that the generated patched firmware can be
independently validated and transferred over the local network.

Physical-device testing verifies that the resulting firmware can be installed,
booted and operated on the target hardware and that the intended runtime paths
are affected under the tested conditions.

Longer-term monitoring uses periodically collected device data to observe
runtime behavior and battery trends over extended periods.

Successful binary validation, firmware transfer or suppression of the targeted
runtime paths does not by itself prove improved battery life.

---

## Reference firmware

The tests described here use the specifically supported firmware:

```text
Device:   Shelly TRV (SHTRV-01)
Version:  2.2.4
Build:    20240619-130912/v2.2.4@ee290818
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

No copy of this firmware is stored in this repository.

---

## Expected combined patched result

The current patcher applies both Patch A and Patch B.

The expected patched GBL has:

```text
Size:
1,106,384 bytes

CRC32:
0xBAEB8265

SHA-256:
7adbb31d6b7faa8b9290d7b3436af45d42af9c3602a7195cafab774ded84ac61
```

Expected patched main PROGRAM SHA-256:

```text
06742a2632a3d45cf697b8be85045914d004f30644dad17b3d0d20012c87c61b
```

These values are deterministic reference values used during validation.

---

## Expected binary differences

The intended firmware transformation consists of two modified bytes in the
main PROGRAM data.

### Patch B — periodic mDNS restart bypass

Instruction offset:

```text
PROGRAM offset:
0x0001E0F0
```

Original instruction:

```text
02 D0
```

Patched instruction:

```text
02 E0
```

Modified byte:

```text
PROGRAM offset:
0x0001E0F1

Original:
D0

Patched:
E0
```

Within the complete GBL file, this byte is located at:

```text
0x00024645
```

### Patch A — beacon-skip recovery bypass

Instruction offset:

```text
PROGRAM offset:
0x0001E1C8
```

Original instruction:

```text
31 DC
```

Patched instruction:

```text
31 E0
```

Modified byte:

```text
PROGRAM offset:
0x0001E1C9

Original:
DC

Patched:
E0
```

Within the complete GBL file, this byte is located at:

```text
0x0002471D
```

### Complete expected GBL difference

Rebuilding the GBL also changes its four-byte CRC32 value.

The complete expected difference is:

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

Exactly six bytes are expected to differ between the supported original GBL
and the final combined patched GBL.

Any additional difference is considered a validation failure.

---

## Target-directory workflow

The current patcher uses a fixed local `target` directory.

The original firmware is supplied locally as:

```text
target/SHTRV-01_build_2.2.4.gbl
```

The generated combined patched firmware is written as:

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

No firmware path is supplied to the patcher on the command line.

The `target` directory itself is retained in the repository using `.gitkeep`,
while firmware files inside it are excluded from version control.

A typical local target directory after patching therefore contains:

```text
target/
├── .gitkeep
├── SHTRV-01_build_2.2.4.gbl
└── SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

Only `.gitkeep` is intended to be tracked by Git.

---

## CLI tests

The command-line interface was exercised during development using the
supported firmware image.

Current patcher version:

```text
1.0-beta
```

Current patcher revision:

```text
2
```

### Help

```bash
python3 patch_firmware_v.1.0.py --help
```

Expected behavior:

- command-line help is displayed,
- no firmware is modified,
- no output firmware is created.

### Version

```bash
python3 patch_firmware_v.1.0.py --version
```

Expected output:

```text
patch_firmware_v.1.0.py 1.0-beta revision 2
```

Expected behavior:

- patcher version and revision are displayed,
- no firmware file argument is required,
- no output firmware is created.

### Original firmware verification

With the original firmware present at:

```text
target/SHTRV-01_build_2.2.4.gbl
```

run:

```bash
python3 patch_firmware_v.1.0.py --verify
```

Expected behavior:

- supported original firmware is accepted,
- file size is verified,
- original SHA-256 is verified,
- GBL structure is verified,
- original CRC32 is verified,
- PROGRAM layout is verified,
- original PROGRAM SHA-256 is verified,
- both original patch locations are verified,
- both original instruction sequences are verified,
- no patched firmware is written.

### Firmware analysis

```bash
python3 patch_firmware_v.1.0.py --analyze
```

Expected behavior:

- analysis completes successfully for the supported original firmware,
- firmware identity is displayed,
- GBL structure is displayed,
- PROGRAM layout is displayed,
- CRC information is displayed,
- both patch address mappings are displayed,
- original and patched instructions are displayed,
- hexadecimal context around both patch locations is displayed,
- expected patched hashes are displayed,
- no firmware is modified,
- no output firmware is written.

The analyzer is specific to the firmware and patches investigated by this
project.

It is not tested or intended as a general-purpose firmware or GBL analyzer.

### Dry run

```bash
python3 patch_firmware_v.1.0.py --dry-run
```

Expected behavior:

- complete original validation succeeds,
- both patches are applied in memory,
- patched PROGRAM validation succeeds,
- rebuilt GBL validation succeeds,
- expected CRC32 is produced,
- expected patched SHA-256 is produced,
- no output firmware is written.

### Dry run with byte differences

```bash
python3 patch_firmware_v.1.0.py --dry-run --diff
```

Expected behavior:

- dry-run validation succeeds,
- both PROGRAM byte differences are reported,
- complete GBL byte differences are reported,
- exactly the expected six GBL byte differences are present,
- no output firmware is written.

Expected PROGRAM differences:

```text
0x0001E0F1  D0 -> E0
0x0001E1C9  DC -> E0
```

Expected complete GBL differences:

```text
0x00024645  D0 -> E0
0x0002471D  DC -> E0
0x0010E1CC  58 -> 65
0x0010E1CD  AB -> 82
0x0010E1CE  7B -> EB
0x0010E1CF  DC -> BA
```

### Output-file creation

Run:

```bash
python3 patch_firmware_v.1.0.py
```

Expected behavior:

- input is read automatically from the `target` directory,
- all validation stages complete before writing,
- both patches are applied,
- patched GBL is written to:

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

- written file is read back,
- written file SHA-256 is verified,
- output matches the expected combined patched GBL.

This workflow has been executed successfully with the supported original
firmware.

### Existing-output protection

The patcher refuses to overwrite an existing output firmware file.

Expected behavior:

- execution is aborted,
- existing output file is not overwritten.

This behavior is retained as a safety mechanism.

### Conflicting command-line options

Mutually exclusive modes can be tested together, for example:

```bash
python3 patch_firmware_v.1.0.py --verify --analyze
```

Expected behavior:

- command-line parsing rejects the conflicting options,
- patching does not start,
- no output firmware is written.

---

## Fail-closed input test

A copy of the supported original GBL was deliberately modified before being
passed to the patcher.

The resulting file no longer matched the expected original SHA-256.

Expected behavior:

- modified input is rejected,
- patching does not proceed,
- no patched output is created.

This behavior was confirmed during development.

This demonstrates that the patcher does not accept a file merely because its
filename, size or general GBL structure resembles the supported firmware.

The complete original firmware identity must match the expected reference.

---

## Reproducibility test

The current patching process was used to generate the combined patched GBL
from the known original firmware.

The resulting values matched the expected references:

```text
Patched main PROGRAM SHA-256:
06742a2632a3d45cf697b8be85045914d004f30644dad17b3d0d20012c87c61b

Patched GBL CRC32:
0xBAEB8265

Patched GBL SHA-256:
7adbb31d6b7faa8b9290d7b3436af45d42af9c3602a7195cafab774ded84ac61
```

The resulting complete GBL differed from the original at exactly the six
expected byte positions.

---

## OTA-server tests

The local OTA server was tested using the combined patched GBL generated by:

```text
patch_firmware_v.1.0.py
```

The tested server is:

```text
ota_server.py
```

Current OTA-server version:

```text
1.0
```

Current OTA-server revision:

```text
1
```

### Automatic target-file selection

The current OTA server automatically loads:

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

No firmware filename or path has to be supplied on the command line.

The tested start command was:

```bash
sudo python3 ota_server.py
```

### Patched-firmware validation

Before starting the HTTP server, `ota_server.py` independently validates the
generated firmware.

The combined patched image was accepted with:

```text
Size:
1,106,384 bytes

CRC32:
0xBAEB8265

SHA-256:
7adbb31d6b7faa8b9290d7b3436af45d42af9c3602a7195cafab774ded84ac61
```

The HTTP server starts only after validation succeeds.

### Automatic network selection

During the documented test, the server automatically selected the local IPv4
address and successfully bound to TCP port 80.

The server also implements fallback to TCP port 8000 when port 80 is not
available.

The documented test used TCP port 80.

### HTTP 200 full-transfer test

A complete firmware request was made against the local OTA server.

The server returned:

```text
HTTP/1.1 200 OK
Content-Length: 1106384
```

The complete:

```text
1,106,384 bytes
```

were transferred successfully.

The tested server identified itself as:

```text
ShellyTRVOTA/1.0
```

This confirmed:

- the server was reachable,
- the expected firmware path was served,
- complete HTTP transfer operated,
- the expected file length was served,
- transfer progress reporting operated.

This transfer test alone does not establish successful firmware installation
on a TRV.

### HTTP Range support

The OTA server implements HTTP byte-range handling.

Supported request forms include:

```text
Range: bytes=0-
Range: bytes=<start>-<end>
Range: bytes=<start>-
Range: bytes=-<length>
```

A test request for:

```text
Range: bytes=0-1023
```

returned:

```text
HTTP/1.1 206 Partial Content
Content-Range: bytes 0-1023/1106384
Content-Length: 1024
```

Exactly 1,024 bytes were transferred.

This confirmed that Range handling operates correctly for the tested request.

### Transfer-status limitation

The OTA server reports the state of the HTTP transfer.

A completed transfer does not by itself establish that:

- the firmware was accepted by the TRV,
- the firmware was successfully written to flash,
- the TRV rebooted successfully,
- the firmware operated correctly after reboot.

Those properties are verified separately by physical-device testing.

---

## Physical-device testing

Physical-device testing is deliberately separated by patch configuration.

This is important because Patch A and Patch B target different recurring
firmware paths.

The current test set includes:

```text
Stock 2.2.4:     unmodified runtime reference
Patch B only:    physical runtime test
Patch A only:    earlier physical runtime tests
Patch A + B:     current combined physical runtime test
Older firmware:  historical/reference configurations
```

The tests below document the configurations relevant to validation of the
current combined patch.

---

## Patch B-only runtime test

A physical Shelly TRV running firmware 2.2.4 was tested with only:

```text
Patch B — periodic mDNS restart bypass
```

Patch A was not present on this test device.

### mDNS packet-capture result

A packet capture was performed for UDP port 5353 traffic from the test device.

During the monitored capture window, no periodic mDNS packets from the device
were observed.

This contrasts with the recurring periodic mDNS activity previously observed
on unmodified firmware.

The result provides runtime evidence that Patch B suppresses the targeted
periodic connected-state mDNS restart path under the tested conditions.

It does **not** establish that mDNS is globally disabled.

Other event-driven mDNS paths remain outside the patched call site and may
still operate when triggered.

### Beacon-recovery behavior with Patch B only

The same Patch B-only device continued to produce the recurring sequence:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip 20)
```

approximately once per minute during the observed period.

This occurred while the device had a relatively strong Wi-Fi signal of
approximately:

```text
-58 to -59 dBm
```

and normal RSSI-dependent beacon-skip selection was:

```text
skip 20
```

The recurring beacon-recovery behavior therefore remained present even though
the targeted periodic mDNS activity was no longer observed during the packet
capture.

Under the tested conditions, periodic mDNS restart activity was therefore not
required for the observed beacon-recovery sequence to continue.

This result should not be interpreted as proof that the two mechanisms can
never interact under other conditions.

---

## Combined Patch A+B physical-device test

A separate physical Shelly TRV was used to test the current combined firmware:

```text
Patch A — beacon-skip recovery bypass
Patch B — periodic mDNS restart bypass
```

This device provides the primary physical runtime validation of the firmware
currently generated by the patcher.

### Pre-update state

Before the update, the device was running original firmware:

```text
Device:   Shelly TRV (SHTRV-01)
Version:  2.1.3
Build:    20220202-080736/v2.1.3@d255ad74
```

The device was upgraded directly from original firmware 2.1.3 to the generated
combined patched 2.2.4 firmware.

### OTA procedure

The combined patched firmware was generated using:

```bash
python3 patch_firmware_v.1.0.py
```

The generated firmware was automatically written to:

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

The OTA server was started using:

```bash
sudo python3 ota_server.py
```

The server:

- automatically selected the generated target firmware,
- validated its size,
- validated its SHA-256,
- validated its CRC32,
- started the local HTTP server,
- received the firmware request,
- transferred the firmware to the TRV.

The TRV accepted the OTA request and reported an update from:

```text
20220202-080736/v2.1.3@d255ad74
```

to:

```text
20240619-130912/v2.2.4@ee290818
```

The device subsequently rebooted and became reachable again.

### Post-update firmware

After the OTA update, the device reported:

```text
Device:   Shelly TRV (SHTRV-01)
Version:  2.2.4
Build:    20240619-130912/v2.2.4@ee290818
```

The patch intentionally preserves the original firmware version string.

The version string alone therefore cannot distinguish stock 2.2.4 from the
patched 2.2.4 image.

The strict patcher validation, deterministic output identity, independent
OTA-server validation, successful OTA transition and subsequent runtime
testing are evaluated together when validating the patched installation.

---

## Combined Patch B runtime validation

A packet capture was performed on the combined Patch A+B device after
installation.

During the monitored capture window, the previously identified periodic mDNS
activity was not observed.

This provides runtime evidence that Patch B remains effective when combined
with Patch A under the tested conditions.

The result is consistent with the earlier independent Patch B-only test.

It does not establish that all mDNS functionality is disabled.

The patch bypasses the targeted recurring connected-state restart call, while
other event-driven mDNS paths remain outside the modified call site.

---

## Combined Patch A runtime validation

Patch A is intended to bypass the recurring path associated with:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip N)
```

The combined Patch A+B firmware has now been observed for multiple hours on
the physical test device.

During the evaluated runtime log, the device continued normal minute-based
operation with:

- Wi-Fi connected,
- cloud connected,
- normal temperature measurement,
- normal thermostat processing,
- normal RSSI-dependent beacon-skip selection,
- beacon skip 20 under the observed signal conditions.

The evaluated log showed stable RSSI values around the normal strong-signal
range while the device continued using:

```text
Enter powersave state 3 (skip 20)
```

behavior.

The previously recurring:

```text
Beacon skip error! Attempt recovery
```

sequence was not observed in the evaluated multi-hour runtime log.

No corresponding recurring transition into:

```text
Enter powersave state 1
```

was observed.

This is significant because the unpatched recovery behavior had previously
been observed approximately once per minute on affected stock 2.2.4 devices
and remained present on the Patch B-only test device.

The result therefore provides physical runtime evidence that Patch A
successfully suppresses the targeted beacon-skip recovery path in the
combined Patch A+B firmware under the tested conditions.

Current status:

```text
Patch A binary validation:        confirmed
Patch A physical installation:   confirmed
Patch A multi-hour runtime test: confirmed
Targeted recovery observed:      no
Long-term stability:             still under evaluation
Battery-life improvement:        not established
```

Absence during the current observation period must not be interpreted as proof
that the event can never occur under every possible operating condition.

---

## Runtime comparison

The current runtime experiments provide the following separation:

```text
Configuration          Periodic mDNS       Beacon recovery
---------------------  ------------------  -----------------------------
Stock 2.2.4            observed            observed

Patch B only           not observed in     observed repeatedly
                       capture window

Patch A + B             not observed in     not observed during
                       capture window       multi-hour runtime log
```

The Patch B-only result is particularly useful because beacon recovery
continued even after the targeted periodic mDNS activity was suppressed.

This demonstrates that the periodic mDNS restart is not required for the
observed recurring beacon-recovery behavior under the tested conditions.

"Not observed" always refers to the documented observation window.

It must not be interpreted as proof that the corresponding behavior can never
occur under other operating conditions.

---

## Automated battery and runtime monitoring

Longer-term behavior is monitored using the project's `battery_logger`.

The logger periodically queries the participating Shelly TRVs and records
device-state information for later comparison and report generation.

Depending on firmware support, the collected data includes information such
as:

- firmware version,
- battery percentage,
- battery voltage,
- device uptime,
- Wi-Fi RSSI,
- available beacon statistics,
- desired beacon-skip value,
- calculated real beacon-skip value,
- beacon-recovery/error counters where available.

Not every firmware version exposes the same runtime statistics.

Fields that are unavailable on a particular firmware are therefore treated as
unavailable rather than inferred.

### Report generation

The collected measurements are used to generate periodic reports.

These reports provide a reproducible record of longer-term observations and
allow firmware and patch configurations to be compared over time without
relying only on isolated manual status readings.

The reports are used to examine:

- battery percentage trends,
- battery-voltage trends,
- uptime continuity and reboot events,
- RSSI behavior,
- available beacon statistics,
- recovery-counter behavior,
- differences between firmware and patch configurations.

The battery logger therefore complements the short-term debug-log and packet
capture tests.

The different methods answer different questions:

```text
Binary validation:
Confirms exactly which firmware bytes were changed.

Debug logging:
Observes firmware control-flow behavior at runtime.

Packet capture:
Observes network activity such as periodic mDNS traffic.

battery_logger:
Collects longer-term device status and produces comparison reports.
```

No single method is treated as sufficient evidence for every aspect of the
investigation.

### Current monitoring configurations

The longer-term monitoring set includes devices with different firmware and
patch configurations.

Relevant configurations include:

```text
Firmware 2.1.0 reference
Stock firmware 2.2.4 reference
Patch B-only firmware 2.2.4
Combined Patch A+B firmware 2.2.4
```

Historical measurements from additional firmware and patch configurations are
retained where relevant to the investigation.

### Interpretation limitations

The logger data is observational evidence.

Battery percentage and battery voltage are not direct electrical current or
energy measurements.

Direct battery comparisons between different physical TRVs must therefore be
treated cautiously.

Potential confounding factors include:

- different battery cells,
- battery state and history,
- battery-voltage characteristics,
- device-specific battery calibration,
- valve movement,
- thermostat activity,
- temperature conditions,
- Wi-Fi signal conditions,
- network behavior,
- device uptime,
- individual hardware differences.

For this reason, battery-logger reports are primarily used to identify trends,
runtime events and potentially meaningful differences that can be investigated
further.

They do not by themselves prove that either firmware patch reduces electrical
energy consumption.

---

## Battery-testing status

Battery behavior remains a separate research question.

The current patch removes or bypasses two recurring firmware paths identified
through static analysis and runtime testing.

Patch A targets the recurring beacon-skip recovery path.

Patch B targets the recurring connected-state mDNS restart path.

Both targeted runtime behaviors have now shown the expected suppression under
the tested patch configurations.

However, the quantitative energy contribution of either mechanism has not
been established.

The current evidence therefore supports:

```text
Patch A control-flow effect:       supported by runtime observation
Patch B network effect:            supported by packet capture
Combined firmware operation:       confirmed on physical hardware
Long-term battery behavior:        under observation
Battery-life improvement:          not established
```

No battery-life improvement should be claimed from the current results.

---

## Current physical-test summary

At the current stage, the project has demonstrated:

```text
Original firmware validation:       confirmed
Combined patched GBL generation:    confirmed
Deterministic binary output:        confirmed
Patched PROGRAM SHA-256:             confirmed
Patched GBL CRC32:                   confirmed
Patched GBL SHA-256:                 confirmed
Expected six-byte GBL difference:   confirmed

Automatic target workflow:          confirmed

OTA-server firmware validation:     confirmed
HTTP 200 full transfer:             confirmed
HTTP 206 Range transfer:            confirmed
Physical OTA installation:          confirmed
Patched firmware boot:              confirmed

Patch B-only physical test:         confirmed
Patch B periodic mDNS suppression:  observed in capture
Beacon recovery with Patch B only:  observed repeatedly

Combined Patch A+B installation:    confirmed
Combined Patch B behavior:          observed in capture
Combined Patch A behavior:          confirmed in multi-hour runtime log
Beacon recovery with Patch A+B:     not observed in multi-hour runtime log

Automated battery logging:          active
Periodic report generation:         active

Long-term stability:                still under evaluation
Battery-life improvement:           not established
```

---

## Runtime-test limitations

Runtime testing is still ongoing.

The current tests do not establish:

- indefinite long-term stability,
- behavior on every Shelly TRV hardware revision,
- behavior with every Wi-Fi access point or network configuration,
- behavior under all possible RSSI conditions,
- behavior under every possible WLAN failure condition,
- complete absence of event-driven mDNS activity,
- complete independence of the two patched mechanisms under every condition,
- quantitative energy savings from either patch,
- long-term battery-consumption improvement,
- a quantified battery-life improvement.

In particular, suppression of the targeted recurring firmware paths does not
by itself prove that battery consumption has improved.

Battery behavior must be evaluated separately over a sufficiently long
observation period.

---

## Evidence hierarchy

The project deliberately distinguishes between different levels of evidence.

### Static reverse-engineering evidence

Used to determine:

- firmware control flow,
- patch locations,
- instruction behavior,
- callers and conditions,
- expected binary effects.

### Deterministic binary validation

Used to establish:

- exact original firmware identity,
- exact modified bytes,
- expected patched PROGRAM identity,
- expected GBL identity,
- absence of unintended binary differences.

### Runtime debug-log evidence

Used to observe:

- beacon-skip selection,
- recovery messages,
- powersave-state transitions,
- thermostat behavior,
- temperature processing,
- valve activity,
- connectivity state.

### Packet-capture evidence

Used to observe:

- actual network traffic,
- periodic mDNS activity,
- suppression of the targeted recurring mDNS behavior.

### Battery-logger evidence

Used to observe longer-term:

- battery percentage,
- battery voltage,
- uptime,
- RSSI,
- available beacon statistics,
- recovery counters,
- trends between firmware configurations.

These evidence types are complementary.

A result established by one method is not automatically treated as proof of a
different property.

For example:

```text
No recurring recovery log
does not automatically mean
improved battery life.

No periodic mDNS packets
does not automatically mean
mDNS is completely disabled.

Successful HTTP transfer
does not automatically mean
successful firmware installation.

Different battery percentages
between two devices
do not automatically establish
different firmware energy consumption.
```

---

## Future tests

Further testing includes or may include:

- longer continuous runtime of the combined Patch A+B firmware,
- overnight and multi-day debug-log observation,
- additional packet captures,
- additional Shelly TRV devices,
- controlled reboot testing,
- thermostat open/close cycles,
- additional valve movement,
- additional Wi-Fi conditions,
- weaker RSSI conditions,
- comparison between patched and unpatched firmware,
- continued automated battery logging,
- additional battery-logger reports,
- longer-term battery-voltage observations,
- longer-term battery-percentage observations.

Results should only be documented as confirmed when they have actually been
tested.

---

## Test fixtures

No Shelly firmware images are stored in this repository.

This includes:

- original GBL firmware,
- patched GBL firmware,
- extracted proprietary program binaries,
- bootloader binaries,
- proprietary firmware fragments intended as reusable fixtures.

Local firmware files used by the patcher are stored in:

```text
target/
```

but remain excluded from version control.

The repository retains only:

```text
target/.gitkeep
```

so that the required directory exists after cloning the repository.

The corresponding `.gitignore` configuration prevents firmware files inside
`target` from being committed.

No proprietary firmware is required to be committed for documentation or test
reporting.

---

## Automated tests

The `tests` directory currently documents validation performed during
development and physical runtime testing.

A standalone automated test suite using redistributable firmware fixtures has
not yet been added.

Because the patcher validates a proprietary firmware image, care must be taken
not to commit Shelly firmware data merely for use as automated test fixtures.

Future automated tests should use synthetic or independently created test data
where possible.

The `battery_logger` is an automated monitoring and report-generation tool,
but it is not a replacement for a deterministic software unit-test suite.