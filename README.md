# Shelly TRV Gen1 2.2.4 Firmware Patcher

Local reconstruction and OTA tools for the Shelly TRV Gen1 (`SHTRV-01`) firmware 2.2.4.

> **Experimental software**
>
> This project reconstructs the experimental B2.2 firmware candidate from one exact supported Shelly TRV Gen1 Stock 2.2.4 firmware image.
>
> B2.2 has been deterministically reconstructed, independently verified byte-for-byte, installed on physical Shelly TRV hardware, and is currently undergoing longer-term runtime and battery observation.
>
> The historical Shelly TRV battery-drain root cause has **not** been conclusively proven, and long-term battery-life improvement with B2.2 has **not** yet been established.

---

## Purpose

This repository provides two tools:

```text
patch_firmware_v2.0.py
ota_server.py
```

`patch_firmware_v2.0.py` reconstructs the exact qualified B2.2 firmware from the supported Stock 2.2.4 input.

`ota_server.py` validates the generated B2.2 GBL and serves it locally to a Shelly TRV over HTTP for an explicitly initiated OTA update.

The project is intentionally restricted to one specific firmware build.

It is not intended to be:

- a general Shelly firmware patcher,
- a general GBL editor,
- a firmware downloader,
- a generic OTA server,
- a device-management service.

---

# Current firmware: B2.2

B2.2 is the current observer-free integrated experimental build.

It contains exactly nine selected qualified correction components:

1. **A1R including the A1 lifecycle correction**
2. **C-C Beacon-Recovery evidence correction**
3. **B2 bounded serialization with saved-PRIMASK semantics**
4. **minimal MQTT PUBLISH guard**
5. **official Silicon Labs WF200 3.18.0**
6. **Calibration Restore Guard**
7. **P01 ownership-aware Battery-PA3 release**
8. **P02 bounded synchronous I2C timeout retirement**
9. **P03 WLAN-GPIO notification interrupt-mask correction**

There is no implicit tenth correction.

B2.2 represents:

```text
All Known Qualified Fixes
```

within the selected qualification scope.

It does **not** mean:

```text
all suspicious code paths ever identified
```

and it does not mean that every possible source of battery drain has been corrected.

---

## Not included in B2.2

The following research, diagnostic, deferred, or historical modifications are not part of B2.2:

- periodic mDNS bypass,
- MIN80,
- D3 observer,
- PM52/cmd66 observer,
- additional diagnostic counters,
- additional debug logging,
- FastPS experiments,
- P04,
- P05/P06/P07/P08/P10/P11/P12/P13,
- `valve_min_percent` correction,
- raw-ADC publication correction,
- raw TXDMA candidates,
- EM3 experiments.

In particular, the historical periodic mDNS modification from the old v1.0 patcher is **not** included in B2.2.

---

# Firmware distribution

**This repository does not contain or distribute Shelly firmware.**

Users must obtain the supported original firmware independently.

The patcher operates entirely on a local firmware file.

It does not:

- download Shelly firmware,
- upload firmware to an external service,
- contain the complete Stock firmware,
- contain the complete B2.2 firmware,
- copy a finished B2.2 reference artifact at runtime.

The generated firmware remains local to the user's computer.

---

# Supported Stock firmware

Only the specifically qualified Shelly TRV Gen1 firmware is supported.

```text
Device:
Shelly TRV Gen1 / SHTRV-01

Version:
2.2.4

Build:
20240619-130912/v2.2.4@ee290818
```

Expected Stock GBL:

```text
Filename:
SHTRV-01_build_2.2.4.gbl

Size:
1,106,384 bytes

SHA256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

The patcher refuses to reconstruct B2.2 if the input firmware does not match the supported identity.

A file reporting version `2.2.4` is not sufficient.

The exact binary identity must match.

---

# Expected B2.2 output

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

These identities define the current qualified B2.2 artifacts.

A different application or GBL hash represents a different firmware candidate.

---

# Native Shelly firmware identity

B2.2 deliberately retains the original Shelly firmware identity:

```text
20240619-130912/v2.2.4@ee290818
```

Therefore the normal Shelly firmware version reported by `/status` does not distinguish Stock 2.2.4 from B2.2.

B2.2 is identified during reconstruction and distribution by its exact artifact hashes.

---

# Requirements

- Python 3
- the exact supported Stock Shelly TRV 2.2.4 GBL
- a computer capable of running the Python scripts
- for OTA installation: network connectivity between the computer and the Shelly TRV
- for the supported OTA workflow: TCP port 80

No third-party Python packages are required for the patcher or OTA server.

Both tools use the Python standard library.

---

# Repository layout

Typical repository layout:

```text
Shelly_TRV_2.2.4_Patcher/
├── patch_firmware_v2.0.py
├── ota_server.py
├── README.md
├── USER_GUIDE.md
├── SECURITY.md
├── docs/
│   ├── technical-details.md
│   └── ota_server.md
├── target/
│   └── .gitkeep
└── tests/
    └── README.md
```

The `target/` directory is used for local firmware input and generated output.

Firmware files inside `target/` must not be committed.

---

# Quick start

## 1. Obtain the supported Stock firmware

Obtain the Shelly TRV Gen1 Stock 2.2.4 GBL independently.

It must match:

```text
Build:
20240619-130912/v2.2.4@ee290818

Size:
1,106,384 bytes

SHA256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

---

## 2. Place the Stock firmware in `target/`

The input file must be named:

```text
SHTRV-01_build_2.2.4.gbl
```

and placed at:

```text
target/SHTRV-01_build_2.2.4.gbl
```

---

## 3. Run the B2.2 patcher

Run:

```bash
python3 patch_firmware_v2.0.py
```

The patcher validates the Stock firmware and reconstructs the qualified B2.2 artifacts.

Expected outputs:

```text
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

The reconstruction is accepted only if the final application and GBL match the expected qualified identities.

---

## 4. Verify the generated hashes

Expected application:

```text
SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9
```

Expected GBL:

```text
SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c
```

The patcher performs its own output-integrity verification and verifies the written files again after creation.

---

## 5. Start the OTA server

On macOS or Linux, TCP port 80 normally requires elevated privileges:

```bash
sudo python3 ota_server.py
```

The OTA server automatically loads:

```text
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

and independently validates it before opening the HTTP server.

Expected firmware identity:

```text
Size:
1,126,156 bytes

SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

END CRC32:
0x52A97051
```

The current OTA server uses:

```text
TCP port 80
```

only.

There is no automatic port-8000 fallback.

---

## 6. Start the OTA update

The OTA server prints the firmware URL after startup.

General firmware URL:

```text
http://<COMPUTER-IP>/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

General Shelly OTA request:

```text
http://<SHELLY-TRV-IP>/ota?url=http://<COMPUTER-IP>/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Example with `curl`:

```bash
curl "http://<SHELLY-TRV-IP>/ota?url=http://<COMPUTER-IP>/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl"
```

Replace both placeholders with the actual local addresses.

Keep `ota_server.py` running until the firmware transfer has completed.

Do not intentionally interrupt power during firmware installation.

---

## 7. Verify the device after OTA

A completed HTTP transfer does not by itself prove successful installation.

After the OTA operation, wait for the TRV to reboot and become reachable again.

Expected native firmware identity:

```text
Device:
SHTRV-01

Version:
2.2.4

Build:
20240619-130912/v2.2.4@ee290818
```

Also verify normal device operation:

- Wi-Fi connectivity,
- cloud connectivity if enabled,
- temperature measurement,
- thermostat operation,
- calibration state,
- valve movement.

Because B2.2 retains the original version string, `/status` alone cannot prove that B2.2 is installed.

---

# Patcher v2.0

`patch_firmware_v2.0.py` is a deterministic reconstruction tool.

Its purpose is:

```text
exact supported Stock 2.2.4
        |
        v
exact qualified B2.2
```

It does not attempt to produce a merely functionally equivalent image.

The final generated application and GBL must be byte-identical to the qualified B2.2 references.

---

## Reconstruction method

The supported Stock-to-B2.2 transformation is encoded as approximately:

```text
1,404 authorized transformation runs
```

with checked Stock preimages.

Conceptually:

```text
read expected Stock region
        |
        v
verify expected preimage
        |
        +-- mismatch --> abort
        |
        v
apply qualified transformation
```

The unchanged data originates from the verified Stock image.

The patcher then reconstructs the required application and GBL integrity data.

The approximately 1,404 transformation runs must not be interpreted as 1,404 independent firmware fixes.

B2.2 contains exactly nine selected correction components.

---

# Fail-closed validation

The v2.0 patcher is deliberately fail-closed.

Qualification includes rejection of cases such as:

- modified Stock GBL,
- truncated GBL,
- corrupt input integrity,
- B2.2 supplied as input instead of Stock,
- altered expected preimage data,
- forced output-integrity failure.

Unexpected firmware is not patched heuristically.

The patcher does not search for similar instruction patterns in unknown firmware builds.

---

# Deterministic reconstruction verification

The final v2.0 patcher has reproduced the qualified B2.2 reference artifacts byte-for-byte.

Application:

```text
Generated SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9

Reference SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9

Byte comparison:
IDENTICAL
```

GBL:

```text
Generated SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

Reference SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

Byte comparison:
IDENTICAL
```

---

# Standalone patcher verification

The final patcher was also tested in an isolated directory containing only:

```text
patch_firmware_v2.0.py

target/
└── SHTRV-01_build_2.2.4.gbl
```

No B2.2 reference artifact was present.

No research tree or qualification build tree was present.

The generated artifacts still matched the qualified B2.2 identities exactly.

This confirms that the distributed patcher does not depend on the final reference image as a runtime shortcut.

---

# Automated patcher tests

The current v2.0 regression suite completed:

```text
18 tests

OK
```

The suite includes positive reconstruction and negative fail-closed cases.

Some negative tests intentionally cause validation error messages.

An expected rejection during a negative test does not represent a suite failure if the final result is:

```text
OK
```

---

# B2.2 technical summary

## A1R

A1R preserves the qualified host power-management lifecycle corrections while fixing a regression introduced by the earlier experimental A1 implementation.

The original A1 regression involved temporary power-state overrides being incorrectly retained as persistent selected policy in specific native paths.

A1R qualification included:

```text
151 / 151 Thumb tests PASS
```

---

## C-C Beacon-Recovery evidence correction

C-C corrects problems in the evidence used by the Stock Beacon-Recovery decision.

The investigation identified issues involving:

- signed interpretation of the calculated control value,
- measurement-window validity,
- stale recovery evidence.

C-C does **not** globally disable Beacon Recovery.

Recovery remains possible with fresh, valid and qualifying evidence.

This differs fundamentally from the historical v1.0 unconditional Recovery bypass.

---

## B2 bounded serialization

B2 is a shared host sleep-inhibit/reference counter.

Unsynchronized read-modify-write operations could lose or create contributions under preemption.

B2.2 adds bounded serialization using saved-PRIMASK semantics around the relevant operations.

This prevents the selected lost-update races while preserving the previous interrupt state.

---

## Minimal MQTT PUBLISH guard

B2.2 contains a minimal guard for a qualified malformed-input failure in the MQTT PUBLISH path.

Security-sensitive reproduction details are intentionally maintained separately from this public battery-drain repository.

The public project does not claim:

```text
remote code execution
```

or:

```text
arbitrary write
```

because neither has been demonstrated.

---

## WF200 3.18.0

Stock Shelly TRV 2.2.4 uses:

```text
Shelly FMAC 3.7.0
WF200 3.16.1
```

B2.2 integrates the official Silicon Labs:

```text
WF200 3.18.0
```

The integrated combination:

```text
FMAC 3.7.0
+
WF200 3.18.0
```

has successfully operated on physical TRV hardware, including:

- initialization,
- WLAN scan,
- association,
- DHCP,
- cloud connectivity,
- connected power save.

WF200 3.18.0 alone has not been proven to fix the historical battery drain.

---

## Calibration Restore Guard

A qualified calibration defect allowed a successful queued restore to immediately schedule itself again.

B2.2 includes a guard against the selected self-requeue condition.

---

## P01 Battery-PA3 release

A battery ADC timeout path could return without correctly releasing PA3.

B2.2 adds an ownership-aware cleanup path.

The electrical energy contribution of the original resource-lifecycle defect has not been directly measured.

---

## P02 synchronous I2C timeout retirement

An I2C/display timeout path could return with incomplete transaction state and interrupt-related resources still active.

B2.2 adds bounded retirement of the selected timeout condition.

---

## P03 WLAN-GPIO interrupt mask

A WLAN notification disable path used a numeric value where the called helper expected a bit mask.

B2.2 corrects the interrupt-mask semantics.

---

# OTA server

The included:

```text
ota_server.py
```

is a small project-specific local HTTP server.

Current server version:

```text
2.0 revision 1
```

HTTP server identity:

```text
ShellyTRVOTA/2.0
```

It serves only:

```text
/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

It does not provide directory listings or general filesystem access.

---

## OTA-server validation

Before serving firmware, the OTA server verifies:

- exact file size,
- exact SHA-256,
- stored END CRC32,
- independently calculated END CRC32,
- expected B2.2 END CRC32.

If validation fails, the server does not start.

---

## HTTP behavior

The server uses:

```text
HTTP/1.1
```

and implements byte-range support.

Normal requests are served with:

```text
200 OK
```

and valid Range requests with:

```text
206 Partial Content
```

The current B2.2-specific server revision has been successfully syntax-checked, validated against the exact B2.2 GBL and started on TCP port 80.

A new LAN-side HTTP 200/206 transfer test of this exact v2.0 configuration was not performed during the most recent remote/VPN maintenance session.

Historical versions of the server had separately demonstrated both full-file and Range transfers.

---

# Physical B2.2 runtime status

B2.2 has been installed on physical Shelly TRV Gen1 hardware.

The initial canary successfully completed:

```text
OTA
→ cold reboot
→ Shelly 2.2.4 boot
→ FMAC 3.7.0
→ WF200 3.18.0 initialization
→ WLAN scan / association
→ DHCP
→ calibration
→ connected power save
→ cloud connectivity
```

After approximately 29 hours, the initial canary showed:

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

---

# Current B2.2 fleet test

On 2026-11-02 at approximately 18:55 local time, the active hardware test fleet was moved to B2.2.

The current fleet contains seven physical TRV devices.

There is currently no simultaneously running Stock 2.2.4 control device in the active fleet.

Historical Stock snapshots remain available for comparison, but they are not equivalent to a concurrent matched control.

Long-term B2.2 observation is ongoing.

---

# Battery testing

The project was originally motivated by unexpectedly high battery consumption observed on Shelly TRV Gen1 devices.

Several concrete firmware defects and potentially energy-relevant mechanisms have since been identified.

However:

```text
firmware defect
!=
battery-drain root cause
```

and:

```text
successful correction
!=
quantified battery-life improvement
```

The project therefore does not currently claim that B2.2 has restored normal battery lifetime.

---

## Battery percentage

The battery percentage reported by the Stock firmware is not a coulomb counter.

Static analysis shows that the displayed percentage is derived from battery voltage.

For short-term comparison, voltage is therefore generally more useful than percentage alone.

Neither percentage nor voltage is a direct current or accumulated-energy measurement.

---

# Project status

Current status:

```text
Supported Stock firmware:
CONFIRMED

B2.2 selected correction set:
QUALIFIED

Deterministic Stock -> B2.2 reconstruction:
CONFIRMED

Generated B2.2 application byte-identical to reference:
CONFIRMED

Generated B2.2 GBL byte-identical to reference:
CONFIRMED

Standalone patcher execution:
CONFIRMED

Fail-closed negative tests:
CONFIRMED

Automated v2.0 tests:
18 PASS

OTA-server B2.2 validation:
CONFIRMED

OTA-server v2.0 startup:
CONFIRMED

Physical B2.2 installation:
CONFIRMED

Physical B2.2 boot:
CONFIRMED

WF200 3.18.0 initialization:
CONFIRMED

WLAN / DHCP / cloud:
CONFIRMED

Initial approximately 29-hour canary:
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

# Historical v1.0 patcher

The previous:

```text
patch_firmware_v.1.0.py
```

implemented a different experimental firmware consisting of:

```text
Beacon-Recovery bypass
+
periodic mDNS restart bypass
```

Its generated firmware:

```text
SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

is historical and is not B2.2.

Historical v1.0 output identities such as:

```text
SHA256:
7adbb31d6b7faa8b9290d7b3436af45d42af9c3602a7195cafab774ded84ac61
```

must not be used to validate the current B2.2 firmware.

---

# Testing

Current testing includes:

- exact Stock firmware validation,
- deterministic B2.2 reconstruction,
- preimage validation,
- corrupted-input rejection,
- truncated-input rejection,
- wrong-firmware rejection,
- output-integrity rejection,
- byte-for-byte reference comparison,
- standalone patcher reconstruction,
- automated v2.0 regression tests,
- component qualification,
- integration qualification,
- OTA-server B2.2 validation,
- OTA-server startup testing,
- physical B2.2 installation,
- physical B2.2 boot,
- WF200 3.18.0 hardware initialization,
- WLAN association,
- DHCP,
- cloud connectivity,
- connected power save,
- longer-term battery and runtime logging.

Detailed test information is maintained in:

```text
tests/README.md
```

Detailed firmware implementation information is maintained in:

```text
docs/technical-details.md
```

Detailed OTA-server information is maintained in:

```text
docs/ota_server.md
```

---

# Research repository

The reverse-engineering investigation, runtime observations, firmware analysis and qualification work are maintained separately from this end-user patcher repository.

Research repository:

```text
Shelly-TRV-Gen1-2.2.4-Battery-Drain-Investigation
```

The research repository contains the technical evidence behind the selected B2.2 correction set.

This repository contains the reproducible end-user reconstruction and OTA workflow.

Security-sensitive MQTT research is maintained separately and must not be conflated with the battery-drain investigation.

---

# Local firmware files and `target/`

The `target/` directory exists so a fresh clone already contains the directory expected by the patcher and OTA server.

Firmware files inside it must remain local.

Typical `.gitignore` behavior:

```gitignore
target/*
!target/.gitkeep
```

The repository may contain:

```text
target/.gitkeep
```

but must not contain:

```text
target/SHTRV-01_build_2.2.4.gbl
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

This applies to both original and reconstructed Shelly firmware.

---

# Safety

The patcher is designed to fail closed.

If an expected input, preimage, reconstruction or final identity does not match, the process is aborted.

The OTA server independently validates the B2.2 GBL before serving it.

Neither tool automatically initiates flashing on a Shelly TRV.

Firmware modification and OTA installation always involve risk.

Do not intentionally remove power while a firmware update is being processed.

Keep a practical recovery path available before testing experimental firmware.

---

# Security

The OTA server is intended only for temporary use on a trusted local network.

It:

- does not provide authentication,
- does not provide TLS,
- should not be exposed directly to the public Internet,
- should be stopped when no longer required.

Security-sensitive firmware findings should follow the process documented in:

```text
SECURITY.md
```

Do not publish unpublished exploit details or responsible-disclosure material through normal bug reports or pull requests.

---

# Evidence boundary

The project deliberately distinguishes between different evidence levels.

```text
static reverse engineering
        !=
qualified correction

qualified correction
        !=
exact integrated reconstruction

exact reconstruction
        !=
successful OTA

successful OTA
        !=
successful runtime

successful runtime
        !=
long-term stability

long-term stability
        !=
battery-life improvement

battery-life improvement
        !=
historical root cause proven
```

These distinctions are intentional.

---

# Current conclusion

The strongest defensible current conclusion is:

```text
B2.2 is an exact, deterministically reconstructable,
observer-free integrated experimental firmware containing
nine selected qualified corrections.

The v2.0 patcher reproduces the qualified B2.2 application
and GBL byte-for-byte from the exact supported Stock 2.2.4
firmware.

B2.2 has successfully operated on physical Shelly TRV Gen1
hardware and is currently undergoing longer-term fleet
observation.

Long-term battery-life improvement and the complete historical
battery-drain root cause remain unproven.
```

---

# Disclaimer

This is an independent research project.

It is not affiliated with, endorsed by, sponsored by, or supported by Shelly.

Shelly and related product names are used only to identify the hardware and firmware being studied.

Firmware modification and flashing can result in malfunction, loss of configuration, device failure, or an unusable device.

Use of these tools and any firmware generated with them is at the user's own risk.

This project does not grant rights to third-party firmware, trademarks or other intellectual property.

---

# License

The original source code and documentation in this repository are licensed under the MIT License.

See:

```text
LICENSE
```

The license applies only to the original code and documentation contained in this repository.

It does **not** grant rights to Shelly firmware, trademarks, product names or other third-party intellectual property.

No original or modified Shelly firmware images are distributed as part of this project.