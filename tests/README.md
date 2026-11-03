# Tests

This directory documents validation, deterministic reconstruction testing, OTA-related testing, physical-device runtime testing, and longer-term monitoring performed for the Shelly TRV Gen1 2.2.4 B2.2 firmware project.

The current firmware reconstruction tool is:

```text
patch_firmware_v2.0.py
```

The current integrated firmware candidate is:

```text
B2.2
```

B2.2 is an observer-free experimental build containing the selected set of nine qualified corrections.

The project intentionally does not include proprietary Shelly firmware binaries as test fixtures.

Firmware-dependent tests are performed locally using an original firmware image supplied separately by the user.

---

## Test scope

Testing is divided into five distinct areas:

1. Stock firmware input validation,
2. deterministic B2.2 reconstruction validation,
3. OTA-server validation,
4. physical-device runtime validation,
5. longer-term battery and stability monitoring.

These test objectives must remain separate.

For example:

```text
exact reconstruction
!=
successful OTA installation
!=
successful hardware runtime
!=
long-term stability
!=
battery-life improvement
!=
historical battery-drain root cause proven
```

A result at one evidence level must not automatically be promoted to another.

---

# Supported Stock firmware

The current v2.0 patcher supports exactly:

```text
Device:
Shelly TRV Gen1 / SHTRV-01

Firmware:
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

The patcher is intentionally restricted to this exact firmware identity.

A file is not accepted merely because:

- its filename matches,
- it reports version 2.2.4,
- its size appears plausible,
- its general GBL structure resembles the supported image.

Unexpected input must fail closed.

No copy of the Stock firmware is stored in the public repository.

---

# Current B2.2 correction set

B2.2 contains exactly nine selected correction components:

```text
1. A1R including A1 lifecycle correction
2. C-C Beacon-Recovery evidence correction
3. B2 bounded serialization with saved-PRIMASK semantics
4. minimal MQTT PUBLISH guard
5. official Silicon Labs WF200 3.18.0
6. Calibration Restore Guard
7. P01 ownership-aware Battery-PA3 release
8. P02 bounded synchronous I2C timeout retirement
9. P03 WLAN-GPIO notification interrupt-mask correction
```

There is no implicit tenth correction.

B2.2 does not include:

```text
periodic mDNS bypass
MIN80
D3 observer
PM52/cmd66 observer
additional diagnostic counters
additional debug logging
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

Historical tests involving those components remain useful research evidence but do not describe the current B2.2 firmware.

---

# Expected B2.2 artifacts

## Application

The expected reconstructed application is:

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

The expected reconstructed GBL is:

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

These values define the current qualified B2.2 artifacts.

Any firmware with a different final application or GBL identity is a different candidate.

---

# Native firmware identity

B2.2 deliberately retains the original Shelly firmware identity:

```text
20240619-130912/v2.2.4@ee290818
```

Therefore:

```text
/status
```

cannot uniquely prove whether a device is running Stock 2.2.4 or B2.2.

B2.2 is identified during construction and distribution by its exact artifact identity.

---

# Target-directory workflow

The current patcher uses the repository-local:

```text
target/
```

directory.

Supported Stock input:

```text
target/SHTRV-01_build_2.2.4.gbl
```

Expected generated application:

```text
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin
```

Expected generated GBL:

```text
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

A typical local target directory may therefore contain:

```text
target/
├── .gitkeep
├── SHTRV-01_build_2.2.4.gbl
├── SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin
└── SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Firmware artifacts are excluded from version control.

Only repository-control files such as:

```text
target/.gitkeep
```

are intended to be tracked.

---

# Deterministic reconstruction test

The principal v2.0 acceptance criterion is not functional similarity.

The generated output must be byte-identical to the qualified B2.2 reference.

The accepted reconstruction produced:

```text
Application SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9

GBL SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c
```

Direct byte comparison against the qualified reference artifacts returned:

```text
BIN cmp exit = 0
GBL cmp exit = 0
```

This establishes:

```text
generated application
==
qualified B2.2 application
```

and:

```text
generated GBL
==
qualified B2.2 GBL
```

byte-for-byte.

---

# Standalone reconstruction test

The patcher was also tested independently from the research and qualification environment.

The isolated test directory contained only:

```text
patch_firmware_v2.0.py

target/
└── SHTRV-01_build_2.2.4.gbl
```

No qualified B2.2 reference output was present.

No research tree was present.

No build tree was present.

No Ghidra or REA dependency was required at runtime.

The standalone patcher successfully reconstructed the expected B2.2 artifacts.

The generated identities again matched:

```text
Application:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9

GBL:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c
```

This confirms that the distributed patcher does not depend on the reference firmware output as a runtime shortcut.

---

# Patcher dependency check

Static inspection of the final `patch_firmware_v2.0.py` confirmed that it does not read the qualified B2.2 reference output during normal reconstruction.

The final standalone workflow requires only:

```text
patch_firmware_v2.0.py
+
exact supported Stock 2.2.4 GBL
```

The qualification environment used to derive the reconstruction is not required for normal end-user execution.

---

# Automated v2.0 acceptance tests

During qualification, the reconstructed v2.0 patcher was exercised with an automated test suite.

Current result:

```text
Ran 18 tests

OK
```

The suite includes positive reconstruction tests and fail-closed negative cases.

One negative test deliberately causes output-integrity rejection and may print an error such as:

```text
ERROR: output GBL SHA256 mismatch
```

That message is expected within the negative test.

The significant suite result is:

```text
18 tests completed
OK
```

---

# Fail-closed negative tests

The v2.0 qualification specifically covers rejection cases including:

```text
1. Stock GBL with a modified byte
2. truncated GBL
3. corrupt CRC / integrity
4. B2.2 supplied as input instead of Stock
5. modified expected preimage data
6. forced output-integrity failure
```

The required behavior is:

```text
unexpected input
        |
        v
validation failure
        |
        v
abort
```

The patcher must not:

- guess the firmware version,
- relocate corrections heuristically,
- partially apply the correction set,
- silently accept a near-match,
- emit an artifact and label it B2.2 despite identity failure.

---

# Preimage validation

The B2.2 reconstruction uses checked Stock preimages.

Conceptually:

```text
expected Stock bytes
        |
        v
compare against actual input
        |
        +-- mismatch --> reject
        |
        v
apply authorized transformation
```

The qualified reconstruction contains approximately:

```text
1,404 authorized Stock -> B2.2 transformation runs
```

This number describes binary reconstruction geometry.

It does **not** represent:

```text
1,404 bugs
```

or:

```text
1,404 independent fixes
```

B2.2 still contains exactly nine selected correction components.

---

# Output-integrity tests

The final application is accepted only if it matches:

```text
Size:
1,069,320 bytes

SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9

CRC32:
42657D97
```

The final GBL is accepted only if it matches:

```text
Size:
1,126,156 bytes

SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

END CRC32:
52A97051
```

The file written to disk is read back and verified again.

Successful in-memory reconstruction alone is not considered sufficient.

---

# Qualification coverage

The underlying B2.2 build qualification included substantially broader component and integration testing than the public patcher regression suite.

Recorded qualification includes:

```text
A1R:
151 / 151

C-C:
512 + 10000

B2:
2060 + 102
plus mixed/preemption cases

MQTT:
258

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

motor / B2 / P01:
10 + 30

sleep / PA8:
48

battery / OTA / boot:
10002 + 2 + 4 + 3

interfaces / flows:
10 interactions
13 flow groups
```

The B2.2 qualification process additionally established:

```text
multiple clean application constructions identical
multiple GBL constructions byte-identical
zero unexplained application differences
zero unexplained container differences
observer absence verified
```

These are qualification results for the selected integrated B2.2 build.

They must not be interpreted as proof of long-term battery performance.

---

# Historical v1.0 tests

Earlier versions of this repository documented a two-patch firmware:

```text
Beacon-Recovery bypass
+
periodic mDNS restart bypass
```

That historical workflow produced:

```text
SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

and expected only two application-byte changes plus the updated GBL checksum.

Those test results belong to the historical v1.0 patcher.

They are **not** the acceptance criteria for:

```text
patch_firmware_v2.0.py
```

or:

```text
B2.2
```

In particular, the historical statement:

```text
exactly six bytes differ in the complete GBL
```

must not be applied to B2.2.

---

# Historical mDNS tests

The project previously tested a specific periodic connected-state mDNS restart bypass.

Historical packet capture established that the targeted periodic mDNS activity could be suppressed.

Historical testing also showed that Beacon Recovery could continue despite suppression of the periodic mDNS restart.

This helped separate the two mechanisms.

However:

```text
periodic mDNS bypass
```

is not included in B2.2.

Those results remain historical research evidence only.

---

# OTA server

The current local OTA server is:

```text
ota_server.py
```

Current version:

```text
2.0
```

Current revision:

```text
1
```

Server identity:

```text
ShellyTRVOTA/2.0
```

The OTA server automatically expects:

```text
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

It independently validates that artifact before opening the HTTP server.

---

# OTA-server firmware validation

Current expected GBL:

```text
Filename:
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl

Size:
1,126,156 bytes

SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

END CRC32:
0x52A97051
```

The OTA server checks:

- file existence,
- file type,
- exact size,
- exact SHA-256,
- stored END CRC32,
- independently calculated END CRC32,
- expected END CRC32.

The HTTP server starts only after validation succeeds.

---

# OTA-server TCP-port behavior

The current server intentionally supports:

```text
TCP port 80
```

for the Shelly TRV Gen1 OTA workflow.

It does not automatically fall back to port 8000.

Earlier project testing showed that a server on port 8000 could be reachable by another HTTP client while the expected TRV firmware retrieval did not occur as required.

TCP port 80 produced the expected TRV OTA retrieval behavior.

For this reason the current server fails if TCP port 80 cannot be used.

---

# Current OTA-server startup test

The current B2.2-specific OTA server was tested for local startup and firmware validation.

Confirmed:

```text
Python syntax:       PASS

Version:
2.0 revision 1

B2.2 file size:
1,126,156 bytes

B2.2 SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

GBL END CRC32:
0x52A97051

Firmware validation:
PASSED

Selected HTTP port:
80

Server startup:
PASSED
```

The server successfully reached its waiting state.

---

# Current OTA-server network-test boundary

During the current v2.0 documentation update, the server was being accessed remotely through a VPN environment.

A new end-to-end LAN HTTP transfer test was therefore not performed during that session.

Accordingly, the current v2.0 test record does **not** claim a newly executed:

```text
HTTP 200 full-file network transfer
```

or:

```text
HTTP 206 Range network transfer
```

for the updated B2.2-specific server revision during that session.

The HTTP/1.1 and Range implementations remain present in the server code.

Historical OTA-server versions had separately demonstrated HTTP 200 and 206 transfer behavior, but those results must not be presented as newly executed v2.0 tests.

---

# Physical B2.2 installation

B2.2 has been installed and operated on physical Shelly TRV Gen1 hardware.

The first B2.2 hardware canary successfully completed:

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

This confirms real hardware execution of the qualified B2.2 artifact.

---

# Initial B2.2 canary

After approximately 29 hours, the initial B2.2 canary showed:

```text
reboot_counter:       1
reconnect_counter:    1
beacon_err_counter:   0
desired_beacon_skip:  20
real_beacon_skip:     21
battery:              99 %
voltage:              approximately 4.027 V
```

No unexpected additional reboot or reconnect was observed during that period.

This represents positive short-term runtime evidence.

It does not establish long-term battery behavior.

---

# B2.2 fleet rollout

After the initial canary test, the physical test fleet was moved to B2.2 on:

```text
2026-11-02
approximately 18:55 local time
```

The current test fleet contains seven physical TRV devices running B2.2.

This means there is currently:

```text
no parallel Stock 2.2.4 control device
```

in the active fleet.

Historical Stock and previous experimental snapshots remain available as reference data.

This limitation must be considered when interpreting later long-term results.

---

# Post-rollout baseline

Immediately after the B2.2 fleet rollout, the devices established new baseline measurements.

The important test purpose of this baseline is to provide a clean start point for:

- uptime,
- reboot count,
- reconnect count,
- battery voltage,
- displayed battery percentage,
- beacon statistics,
- subsequent long-term trend comparison.

The baseline is not itself evidence of battery improvement.

---

# Automated battery and runtime monitoring

Longer-term B2.2 behavior is monitored using the project's battery logger.

Depending on firmware support, the logger records fields including:

```text
firmware version
battery percentage
battery voltage
uptime
Wi-Fi RSSI
reboot information
reconnect information
desired beacon skip
calculated real beacon skip
beacon error / recovery counters
```

Unavailable fields are recorded as unavailable rather than inferred.

---

# Battery percentage interpretation

The displayed Shelly battery percentage is not a coulomb counter.

Static analysis established that it is derived from measured/cached battery voltage.

This has also been observed at runtime: displayed percentage values can rise without charging.

Therefore:

```text
battery percentage
```

must not be treated as a direct accumulated-energy measurement.

For short-term trend comparison, measured voltage is generally more useful than percentage alone.

Neither percentage nor voltage is a direct current measurement.

---

# Monitoring interpretation

Battery logger data is observational.

Direct comparison between different physical TRVs is affected by factors including:

- battery-cell variation,
- state of charge,
- battery history,
- battery voltage response,
- valve activity,
- thermostat activity,
- room temperature,
- Wi-Fi conditions,
- individual hardware variation,
- prior device history.

For this reason, long-term results must be interpreted as trend evidence rather than laboratory-grade energy measurements.

---

# Evidence hierarchy

The project deliberately separates evidence types.

## Static reverse engineering

Used to establish:

- firmware control flow,
- state relationships,
- defect candidates,
- instruction behavior,
- ownership and lifecycle behavior.

## Component qualification

Used to establish:

- correction semantics,
- edge-case handling,
- negative-case behavior,
- interaction behavior.

## Deterministic reconstruction

Used to establish:

- exact Stock input identity,
- expected preimages,
- exact B2.2 output identity,
- absence of unexplained reconstruction differences.

## Physical runtime testing

Used to establish:

- boot behavior,
- WLAN operation,
- WF200 initialization,
- cloud operation,
- thermostat operation,
- calibration behavior,
- runtime stability under tested conditions.

## Battery monitoring

Used to observe:

- longer-term voltage trends,
- displayed battery percentage,
- uptime continuity,
- reboot events,
- reconnect events,
- beacon statistics,
- device-to-device trends.

Each method answers a different question.

---

# Examples of invalid inference

The following reasoning is explicitly rejected:

```text
B2.2 hash is correct
therefore
battery drain is fixed
```

Incorrect.

---

```text
OTA transfer completed
therefore
firmware installed successfully
```

Incorrect without device-level verification.

---

```text
device booted successfully
therefore
long-term stability is proven
```

Incorrect.

---

```text
beacon_err_counter remains zero
therefore
battery lifetime is restored
```

Incorrect.

---

```text
battery percentage increased
therefore
battery was charged
```

Incorrect.

---

```text
seven B2.2 devices remain stable
therefore
the historical root cause has been proven
```

Incorrect.

---

# Current test summary

Current evidence supports:

```text
Exact Stock input identity:
CONFIRMED

v2.0 deterministic reconstruction:
CONFIRMED

Generated application byte-identical to qualified B2.2:
CONFIRMED

Generated GBL byte-identical to qualified B2.2:
CONFIRMED

Standalone patcher execution:
CONFIRMED

Fail-closed negative tests:
CONFIRMED

Automated v2.0 acceptance suite:
18 tests PASS

B2.2 application hash:
CONFIRMED

B2.2 GBL hash:
CONFIRMED

B2.2 END CRC32:
CONFIRMED

OTA-server B2.2 validation:
CONFIRMED

OTA-server v2.0 startup:
CONFIRMED

Current v2.0 LAN HTTP 200 re-test:
NOT PERFORMED DURING REMOTE SESSION

Current v2.0 LAN HTTP 206 re-test:
NOT PERFORMED DURING REMOTE SESSION

B2.2 physical installation:
CONFIRMED

B2.2 physical boot:
CONFIRMED

WF200 3.18.0 physical initialization:
CONFIRMED

WLAN association:
CONFIRMED

DHCP:
CONFIRMED

Cloud connectivity:
CONFIRMED

Connected power save:
CONFIRMED

Initial ~29 h canary:
STABLE UNDER OBSERVED CONDITIONS

B2.2 fleet rollout:
ACTIVE

Long-term stability:
UNDER OBSERVATION

Long-term battery behavior:
UNDER OBSERVATION

Quantified battery-life improvement:
NOT ESTABLISHED

Historical battery-drain root cause:
NOT CONCLUSIVELY PROVEN
```

---

# Current long-term test policy

During the current B2.2 fleet observation period, firmware and WLAN configuration should remain stable unless a concrete test requirement justifies a change.

The objective is to avoid introducing unnecessary variables into the long-term dataset.

Routine activities are therefore limited primarily to:

```text
status snapshots
battery-logger collection
runtime observation
report generation
```

rather than further experimental firmware changes.

---

# No active Stock control

The current B2.2 fleet test does not include a simultaneously running Stock 2.2.4 control.

This is an important limitation.

Historical Stock measurements are available, but they are not equivalent to a concurrent matched control.

Future battery conclusions must account for this distinction.

---

# Test fixtures and copyright

No proprietary Shelly firmware images should be committed to this repository.

This includes:

- original Shelly GBL files,
- generated patched GBL files,
- extracted proprietary application binaries,
- bootloader images,
- radio firmware blobs extracted from proprietary packages,
- large reusable proprietary binary fragments.

Local working artifacts remain under:

```text
target/
```

and are excluded from version control.

The repository should contain only the code, metadata, documentation, hashes, and reconstruction information required for the project workflow.

---

# Security-sensitive testing

B2.2 contains a minimal MQTT PUBLISH guard.

The detailed MQTT security investigation is maintained separately from the public Battery Drain project.

Public test documentation must not include unpublished:

- exploit payloads,
- attack scripts,
- responsible-disclosure evidence,
- sensitive reproduction details.

Current public conclusions must not claim:

```text
remote code execution
```

or:

```text
arbitrary write
```

because neither has been demonstrated.

---

# Historical evidence

Historical experiments remain valid evidence for the configuration actually tested at that time.

They must not be retrospectively renamed as B2.2 tests.

Examples include:

```text
historical Patch B-only mDNS tests
historical Beacon-Recovery bypass tests
MIN80 experiments
D3 observer tests
B2.1
B2.1_OBS
earlier A1-based builds
```

These results remain part of the research history.

They are not part of the current v2.0 patcher acceptance criteria.

---

# Current battery-testing conclusion

The project has identified and qualified multiple concrete firmware defects and integrated selected corrections into B2.2.

The current physical evidence establishes that B2.2 operates on real Shelly TRV Gen1 hardware under the tested conditions.

However:

```text
battery-life improvement:
not yet established
```

and:

```text
historical battery-drain root cause:
not conclusively proven
```

Long-term B2.2 observation remains necessary.

---

# Future tests

Current or future testing may include:

- continued multi-day and multi-week B2.2 fleet observation,
- reboot and reconnect tracking,
- continued battery-voltage monitoring,
- controlled valve-operation observation,
- weaker and stronger Wi-Fi conditions where scientifically useful,
- investigation of any first observed B2.2 failure,
- additional deterministic patcher regression testing,
- OTA-server network retesting when directly present on the target LAN,
- comparison against preserved historical Stock datasets.

A new firmware correction should not be introduced into the active B2.2 fleet merely to expand the test matrix.

Any new correction would create a new firmware candidate requiring its own qualification and identity.

---

# Current research boundary

The current strongest defensible statement is:

```text
B2.2 is an exact, deterministically reconstructable,
observer-free integrated experimental firmware containing
nine selected qualified corrections.

Its application and GBL identities are reproducible
byte-for-byte from the supported Stock 2.2.4 input.

B2.2 has successfully operated on physical Shelly TRV Gen1
hardware and is currently undergoing longer-term fleet testing.

Long-term battery-life improvement and the historical
Battery Drain root cause remain unproven.
```

This distinction is intentional and should be preserved in all test documentation.