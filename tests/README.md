# B2.2 Firmware – Testing and Validation

This directory documents the validation, deterministic reconstruction, OTA-server testing, hardware qualification, and battery/stability monitoring performed for the **Shelly TRV Gen1 (SHTRV-01) B2.2 Beta** firmware project.

**Last updated:** November 9, 2026
**Patcher:** v2.0
**Firmware:** B2.2 Beta
**Base firmware:** Shelly TRV Gen1 Stock 2.2.4

> **Current assessment**
>
> B2.2 has passed its documented reconstruction and component qualification tests and has operated on physical TRV hardware for more than six days.
>
> No severe battery depletion comparable to the documented historical Stock episodes has been observed in the regular B2.2 fleet during that period.
>
> **Known reliability issue:** Several devices have experienced unexpected automatic reboots. Their cause remains unconfirmed. Long-term firmware stability and battery lifetime are not yet established.

## 1. Validation Scope

The project separates five types of evidence:

| Test area | What it establishes |
|---|---|
| Stock firmware validation | The exact supported input firmware |
| Deterministic reconstruction | Byte-identical B2.2 application and GBL |
| OTA-server validation | Correct firmware identity and server behavior |
| Physical runtime testing | Real-device installation, boot and operation |
| Battery and stability monitoring | Measured behavior over time |

These are independent evidence levels.

A successful reconstruction does not prove a successful OTA installation. Successful OTA installation does not prove long-term stability, and a stable voltage trend does not prove that the historical battery-drain root cause has been identified.

## 2. Supported Firmware

The v2.0 patcher accepts only the following original firmware:

| Property | Value |
|---|---|
| Device | Shelly TRV Gen1 / SHTRV-01 |
| Firmware | Stock 2.2.4 |
| Build | `20240619-130912/v2.2.4@ee290818` |
| Filename | `SHTRV-01_build_2.2.4.gbl` |
| Size | 1,106,384 bytes |

**Stock SHA-256:**

```text
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

Unsupported, modified, truncated or corrupted firmware must be rejected.

The public repository does not contain proprietary Shelly firmware images.

## 3. Qualified B2.2 Artifacts

The deterministic reconstruction produces two files.

### Application binary

| Property | Value |
|---|---|
| Filename | `SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin` |
| Size | 1,069,320 bytes |
| CRC32 | `42657D97` |

**SHA-256:**

```text
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9
```

### OTA GBL

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

The `EXPERIMENTAL` filenames remain unchanged to preserve the qualified artifact identities and compatibility with the existing reconstruction and OTA workflow.

The release classification is **Beta**.

B2.2 deliberately retains the original Shelly firmware version string. Consequently, the `/status` endpoint alone cannot distinguish B2.2 from Stock 2.2.4.

## 4. Deterministic Reconstruction

The primary acceptance criterion is exact binary reproduction.

The generated application and GBL must be **byte-identical** to their qualified B2.2 reference artifacts.

### Reconstruction method

The patcher:

1. Validates the original Stock firmware.
2. Verifies expected source bytes before modification.
3. Applies approximately 1,404 authorized transformation runs.
4. Reconstructs the application and GBL integrity information.
5. Validates the resulting binary identities.
6. Writes the files and verifies them again after writing.

The approximately 1,404 transformation runs describe the binary reconstruction process. They do not represent 1,404 separate firmware fixes.

B2.2 contains exactly nine selected correction components.

### Verified result

| Artifact | Comparison result |
|---|---|
| Application BIN | Byte-identical |
| OTA GBL | Byte-identical |
| Unexplained application differences | None reported |
| Unexplained container differences | None reported |

The final artifacts matched the qualified reference hashes exactly.

### Standalone test

The patcher was also executed in an isolated environment containing only:

```text
patch_firmware_v2.0.py
target/SHTRV-01_build_2.2.4.gbl
```

No completed B2.2 reference image, research tree, Ghidra installation or REA environment was required.

The generated files matched the qualified B2.2 artifacts.

This demonstrates that normal patcher execution does not rely on copying an existing patched firmware image.

## 5. Automated Patcher Tests

The v2.0 acceptance suite completed successfully:

```text
Ran 18 tests

OK
```

The suite covers successful reconstruction and intentional failure cases.

### Fail-closed tests

The documented negative cases include:

| Test | Expected behavior |
|---|---|
| Modified Stock GBL | Reject |
| Truncated input | Reject |
| Invalid input integrity | Reject |
| B2.2 supplied instead of Stock | Reject |
| Modified expected preimage | Reject |
| Forced output-integrity mismatch | Reject |

The patcher must not silently accept a near-match, partially apply corrections, or produce an output labeled as qualified B2.2 after a validation failure.

Some negative tests deliberately generate error messages. These are expected when the final test-suite result is successful.

## 6. B2.2 Component Qualification

B2.2 contains exactly nine selected correction components:

| Component | Qualification area |
|---|---|
| A1R | Power-management lifecycle and A1 regression correction |
| C-C | Beacon-Recovery evidence validation |
| B2 | Bounded sleep-inhibit counter synchronization |
| MQTT guard | Selected MQTT PUBLISH malformed-input condition |
| WF200 3.18.0 | Updated official Silicon Labs radio firmware integration |
| Calibration Restore Guard | Restore scheduling and state handling |
| P01 | Battery PA3 resource release |
| P02 | Synchronous I2C timeout retirement |
| P03 | WLAN-GPIO interrupt-mask correction |

The original qualification records include the following test counts:

| Qualification group | Recorded tests |
|---|---|
| A1R | 151 / 151 |
| C-C | 512 + 10,000 |
| B2 | 2,060 + 102, plus mixed/preemption cases |
| MQTT | 258 |
| Calibration Restore Guard | 68 native + 66,535 scalar + 104 queue + 30 countdown, plus negative cases |
| P01 | 128 + 6 |
| P02 | 90 + 480 |
| P03 | 128 native |
| Motor / B2 / P01 interactions | 10 + 30 |
| Sleep / PA8 | 48 |
| Battery / OTA / boot | 10,002 + 2 + 4 + 3 |
| Interfaces / flows | 10 interactions + 13 flow groups |

These are recorded qualification results for the selected build and its supporting tests.

They are **not** a count of distinct firmware defects and do not establish long-term battery performance.

### Excluded modifications

B2.2 does not include the historical periodic mDNS bypass, MIN80, D3 or PM52 observers, FastPS experiments, additional debug instrumentation, EM3 experiments or deferred P04+ candidates.

Historical experiments involving those modifications must not be presented as tests of the current B2.2 build.

## 7. OTA-Server Validation

The current OTA server is:

```text
ota_server.py
```

**Version:** 2.0, revision 1
**HTTP identity:** `ShellyTRVOTA/2.0`
**Required port:** TCP 80

The server expects:

```text
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Before serving firmware, it validates:

- File existence and type
- Exact file size
- SHA-256 identity
- Stored END CRC32
- Independently calculated END CRC32
- Expected END CRC32 value

If validation fails, the server does not start.

### Confirmed tests

| Test | Result |
|---|---|
| Python syntax validation | Passed |
| B2.2 firmware identity validation | Passed |
| GBL END CRC32 verification | Passed |
| TCP port 80 selection | Confirmed |
| Server startup | Passed |

### Network-test limitation

The current B2.2-specific OTA-server revision was validated and started during a remote/VPN maintenance session.

A new complete LAN-side HTTP `200 OK` and `206 Partial Content` transfer test of that exact revision was not performed during that session.

The HTTP/1.1 and Range implementations are present in the source. Historical OTA-server versions separately demonstrated full-file and Range transfers.

Those historical results must not be represented as newly executed v2.0 network tests.

Physical B2.2 OTA installation has nevertheless been demonstrated on real hardware.

## 8. Physical Hardware Validation

B2.2 was installed and executed on physical Shelly TRV Gen1 hardware.

The initial hardware canary successfully demonstrated:

```text
OTA installation
    ↓
Application boot
    ↓
FMAC 3.7.0 initialization
    ↓
WF200 3.18.0 initialization
    ↓
Wi-Fi association
    ↓
DHCP
    ↓
Calibration
    ↓
Connected power-save operation
    ↓
Cloud connectivity
```

The initial approximately 29-hour canary observation reported:

| Metric | Value |
|---|---:|
| Reboot counter | 1 |
| Reconnect counter | 1 |
| Beacon error counter | 0 |
| Desired Beacon Skip | 20 |
| Real Beacon Skip | 21 |
| Battery voltage | Approximately 4.027 V |

No additional unexpected reboot or reconnect was observed during that initial canary period.

This established successful short-term operation but did not establish long-term reliability.

## 9. Six-Day Fleet Evaluation

**Evaluation date:** November 9, 2026
**B2.2 deployment:** November 2, 2026, approximately 18:55 local time
**Elapsed test time:** Approximately 6.46 days

### Device population

The regular B2.2 monitoring fleet consists of six devices:

```text
TRV .11
TRV .61
TRV .71
TRV .77
TRV .88
TRV .97
```

TRV .234 is excluded from the regular B2.2 battery and stability evaluation. It runs Stock firmware and is used for separate MQTT security testing.

TRV .61 was recharged during the observation period. Its battery measurements before and after charging must not be treated as one continuous discharge curve.

### Battery results

No severe battery depletion comparable to the historical Stock episodes was observed during the first 6+ days of the regular B2.2 fleet test.

Four devices without a reported charging event in the compared snapshot sequence showed the following voltage changes:

| Device | November 3 | November 9 | Change |
|---|---:|---:|---:|
| TRV .71 | 3.507 V | 3.487 V | −20 mV |
| TRV .77 | 3.801 V | 3.782 V | −19 mV |
| TRV .88 | 4.051 V | 4.029 V | −22 mV |
| TRV .97 | 3.737 V | 3.721 V | −16 mV |

These measurements span approximately 5.4 days of available voltage snapshots, not the full 6.46-day deployment interval.

The observed voltage development is encouraging. It is not a direct measurement of current consumption, accumulated energy or remaining battery capacity.

### Historical Stock comparison

Historical Shelly Cloud data from January–February 2026 includes repeated original-firmware discharge episodes reaching an indicated 0% after approximately 5.8–6.5 days.

The historical data contains reported battery percentages, whereas the current B2.2 analysis also uses voltage measurements.

The exact firmware build for every historical observation was not independently established.

There is no simultaneous matched Stock control group under equivalent conditions.

Therefore, the comparison supports an encouraging observation, but not a controlled quantitative estimate of B2.2 battery-life improvement.

## 10. Unexpected Reboots

Unexpected automatic restarts are a documented B2.2 reliability issue.

Multiple devices experienced restarts without manual intervention during fleet monitoring.

### Reboot counters

| Device | November 3 | November 9 | Recorded change |
|---|---:|---:|---:|
| TRV .11 | 2 | 6 | +4 |
| TRV .61 | 2 | 3 | +1 |
| TRV .71 | 1 | 65 | +64 |
| TRV .77 | 1 | 6 | +5 |
| TRV .88 | 1 | 2 | +1 |
| TRV .97 | 1 | 1 | 0 |

**TRV .71 requires particular caution:** Its reboot counter increased from 1 to 65, but uptime evidence establishes only that at least one restart occurred. The counter change is not yet proof of 64 distinct reset events.

The observed reboot events do not establish whether the underlying cause was a Watchdog timeout, software reset, CPU exception, power-related reset or a counting anomaly.

### Planned investigation

The next investigation should examine:

- EFM32 reset-cause handling (`RMU_RSTCAUSE`)
- Watchdog initialization and feeding
- Firmware sleep and wake transitions
- Reboot-counter storage and update behavior
- Potential interactions with the selected B2.2 corrections

A specific reset cause must not be claimed without direct evidence.

### Beta interpretation

Despite the observed reboots, devices were reachable and operational after their observed restarts.

This supports continued voluntary beta evaluation, but it does not prove uninterrupted heating regulation during every restart.

The issue remains open and must be disclosed in the public release documentation.

## 11. Beacon-Recovery Monitoring

The available B2.2 snapshots showed no persistent Beacon-Recovery loop comparable to the previously documented problematic behavior.

At the November 9 snapshot, the six regular devices reported a current Beacon-Recovery error counter of zero.

However, this does not establish that no Beacon-Recovery error occurred throughout the test period.

Counters may reset during device restarts or relevant state reinitialization. Debug logs contain only bounded recent history.

The C-C correction also intentionally preserves Beacon Recovery when its evidence is fresh, valid and meets the recovery conditions.

## 12. Measurement Limitations

The project uses observational device telemetry rather than laboratory current-consumption measurements.

Relevant limitations include:

- Battery percentage is voltage-derived and is not a coulomb counter.
- Battery voltage is influenced by temperature, load and cell characteristics.
- Recharging invalidates continuous discharge comparisons.
- Reboots can reset counters and diagnostic history.
- Device activity, valve movement and WLAN conditions vary.
- Historical Stock data does not provide a simultaneous matched control.
- Short Debug logs cannot establish behavior across an entire multi-day interval.

Accordingly, observed low voltage loss cannot be converted directly into a guaranteed battery lifetime.

A longer observation period is required to evaluate whether the historical rapid-drain condition remains absent.

## 13. Current Test Status

| Area | Status |
|---|---|
| Supported Stock input identification | Confirmed |
| Exact B2.2 reconstruction | Confirmed |
| Application byte comparison | Passed |
| GBL byte comparison | Passed |
| Standalone reconstruction | Passed |
| Automated patcher regression suite | 18 tests passed |
| Fail-closed negative testing | Passed |
| Selected component qualification | Recorded and completed |
| OTA-server firmware validation | Passed |
| OTA-server startup | Passed |
| New v2.0 LAN HTTP 200/206 retest | Not completed in documented session |
| Physical OTA installation | Confirmed |
| Physical application boot | Confirmed |
| WF200 3.18.0 initialization | Confirmed |
| Wi-Fi / DHCP / cloud operation | Confirmed |
| Six-day battery observation | Completed initial milestone |
| Historical Stock-like severe drain | Not observed during initial B2.2 evaluation |
| Unexpected automatic reboots | Observed; unresolved |
| Long-term firmware stability | Not established |
| Quantified battery-life improvement | Not established |
| Complete historical drain root cause | Not conclusively proven |

## 14. Continuing Test Policy

The existing B2.2 fleet should remain on the same firmware and WLAN configuration where possible to preserve the value of the ongoing dataset.

Continuing observations should include:

- Battery voltage and reported percentage
- Device uptime
- Reboot and reconnect counters
- Beacon-Recovery statistics
- Calibration state
- Thermostat and valve behavior
- Available Debug logs
- Any future reset-cause information

Further firmware corrections should be developed and qualified separately rather than silently introduced into the current B2.2 fleet.

A modified firmware image represents a new candidate with a different binary identity.

## 15. Historical Research and Security Boundaries

Earlier experiments involving Beacon-Recovery bypasses, periodic mDNS suppression, MIN80, observer firmware, B2.1 and other experimental builds remain historical research evidence.

They are not acceptance tests for the current B2.2 firmware unless explicitly performed against that build.

The minimal MQTT PUBLISH guard included in B2.2 originates from a separate security investigation.

Sensitive reproduction details, exploit material and unpublished responsible-disclosure evidence do not belong in this public test documentation.

No remote code execution or arbitrary-write capability has been demonstrated.

## 16. Firmware Distribution

No original, modified or extracted proprietary Shelly firmware images should be committed to this repository.

Local firmware artifacts belong under:

```text
target/
```

The repository may contain source code, reconstruction metadata, hashes, validation logic and documentation.

Firmware images must remain excluded from version control.

## Conclusion

**B2.2 Beta is a deterministically reconstructable firmware build containing nine selected qualified corrections.**

Its application and GBL have been reproduced byte-for-byte from the exact supported Stock 2.2.4 firmware.

The initial six-day hardware evaluation shows encouraging battery behavior: the previously documented severe, rapid battery depletion has not recurred in the regular B2.2 fleet.

At the same time, unexpected automatic restarts remain a documented and unresolved reliability issue.

**The results support continued beta testing. They do not establish fully stable operation, a guaranteed battery-life improvement or a conclusively proven historical battery-drain root cause.**
