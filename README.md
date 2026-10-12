# Shelly TRV Gen1 2.2.4 Firmware Patcher

Local patching and OTA installation tools for the Shelly TRV (SHTRV-01)
firmware 2.2.4.

> **Experimental software**
>
> This project is currently under development and should be considered
> experimental.
>
> The combined firmware modification has been successfully generated,
> validated, installed and booted on a physical Shelly TRV.
>
> Runtime validation and long-term battery-consumption testing are still
> in progress.

## Purpose

This project creates a patched Shelly TRV 2.2.4 firmware image from an
original firmware file supplied locally by the user.

The current patch contains two modifications derived from reverse-engineering
and runtime analysis of the specifically supported firmware build:

1. **Beacon-skip recovery bypass**
2. **Periodic mDNS restart bypass**

The beacon-skip patch targets the recurring firmware behavior:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip N)
```

The patch bypasses the additional recovery path while preserving the normal
RSSI-dependent beacon-skip mechanism.

The second patch bypasses a recurring connected-state mDNS restart path that
was observed during runtime analysis.

The normal mDNS responder and event-driven mDNS initialization paths are not
intentionally disabled by this modification.

This project is intentionally limited to one known firmware image. It is not
intended to be a general-purpose Shelly firmware patcher or GBL manipulation
tool.

---

## Firmware distribution

**This repository does not contain or distribute Shelly firmware.**

Users must obtain the original firmware independently.

The patcher operates entirely on a local firmware file and:

1. validates the original firmware,
2. verifies the expected GBL structure,
3. extracts the relevant program block,
4. verifies both original patch locations,
5. applies the two byte modifications,
6. validates the patched program data,
7. rebuilds the GBL container,
8. recalculates its CRC32,
9. validates the final firmware image,
10. writes the patched GBL locally.

The patched firmware is not uploaded anywhere by the patching tool.

The included OTA server can subsequently make the locally generated patched
firmware available to a Shelly TRV on the user's local network.

---

## Supported firmware

Currently only the specifically analyzed Shelly TRV firmware is supported:

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

Original main PROGRAM SHA-256:

```text
4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c
```

The patcher will refuse to modify firmware that does not match the expected
firmware image.

---

## Requirements

- Python 3
- the original supported Shelly TRV 2.2.4 GBL firmware file
- a computer on the same local network as the Shelly TRV for OTA installation
- no third-party Python packages are required

Both `patch_firmware_v.1.0.py` and `ota_server.py` use only the Python standard
library.

---

## Repository layout

The patcher uses a fixed local `target` directory for firmware input and
output:

```text
Shelly_TRV_2.2.4_Patcher/
├── patch_firmware_v.1.0.py
├── ota_server.py
├── README.md
├── target/
│   └── .gitkeep
└── tests/
    └── README.md
```

The `target` directory is part of the repository, but firmware files inside
that directory must not be committed.

The user supplies the original firmware locally as:

```text
target/SHTRV-01_build_2.2.4.gbl
```

After successful patching, the generated firmware is written automatically as:

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

Both the original and patched GBL files remain local.

---

## Quick start

### 1. Obtain the original firmware

Obtain the supported Shelly TRV 2.2.4 GBL firmware independently.

The file must match:

```text
Version:
20240619-130912/v2.2.4@ee290818

Size:
1,106,384 bytes

SHA-256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

### 2. Place the original firmware in `target`

The original firmware must be named:

```text
SHTRV-01_build_2.2.4.gbl
```

and placed at:

```text
target/SHTRV-01_build_2.2.4.gbl
```

The patcher deliberately uses this fixed location and filename.

No firmware path has to be supplied on the command line.

### 3. Verify the original firmware

Run:

```bash
python3 patch_firmware_v.1.0.py --verify
```

The firmware must pass all validation checks before it can be patched.

### 4. Create the patched firmware

Run:

```bash
python3 patch_firmware_v.1.0.py
```

If all validation and patching steps succeed, the output is written
automatically to:

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

The patcher validates the written file after creation.

### 5. Start the OTA server

On systems where binding to TCP port 80 requires elevated privileges:

```bash
sudo python3 ota_server.py
```

The OTA server automatically uses:

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

No firmware path has to be supplied.

Before starting the HTTP server, the firmware is independently validated
against the expected patched size, SHA-256 and CRC32.

If validation succeeds, the server automatically:

- detects a local IPv4 address,
- checks whether TCP port 80 is available,
- falls back to TCP port 8000 if necessary,
- starts a local HTTP/1.1 server,
- enables HTTP Range request support,
- displays firmware-transfer progress,
- prints the local firmware URL,
- prints an OTA URL template.

Example firmware URL:

```text
http://192.168.178.232/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

The actual IP address and port are detected automatically and may differ.

### 6. Start the OTA update

The OTA endpoint of the target TRV can be called with the firmware URL served
by `ota_server.py`.

General form:

```text
http://<SHELLY-TRV-IP>/ota?url=http://<COMPUTER-IP>/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

Example using `curl`:

```bash
curl "http://192.168.178.226/ota?url=http://192.168.178.232/SHTRV-01_2.2.4_beacon_mdns_patch.gbl"
```

Use the actual IP addresses printed or configured in your local network.

If the OTA server selected port 8000 instead of port 80, include `:8000` in
the firmware URL.

Keep `ota_server.py` running until the firmware transfer has completed.

### 7. Verify the device after OTA

A completed HTTP transfer means that the OTA server successfully served the
firmware data requested by the device.

It does **not** by itself prove that the firmware was successfully installed
or that the device successfully rebooted.

After the update, wait for the Shelly TRV to become reachable again.

Verify that it reports:

```text
20240619-130912/v2.2.4@ee290818
```

The patch intentionally does not change the original firmware version string.

Also verify normal operation of:

- Wi-Fi connectivity
- cloud connectivity, if used
- temperature measurement
- thermostat control
- valve movement
- device calibration

Runtime behavior and battery consumption must be evaluated separately.

---

## Patcher usage

The current patcher version is:

```text
1.0-beta
```

The current patcher revision is:

```text
2
```

### Basic usage

```bash
python3 patch_firmware_v.1.0.py
```

The patcher automatically reads:

```text
target/SHTRV-01_build_2.2.4.gbl
```

and writes:

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

An existing output file will not be overwritten.

### Verify the original firmware

```bash
python3 patch_firmware_v.1.0.py --verify
```

This validates the original firmware without patching or writing a new
firmware file.

Verification includes:

- expected file size
- original firmware SHA-256
- GBL structure
- original CRC32
- PROGRAM layout
- original PROGRAM SHA-256
- both original patch instructions
- both original patch bytes

### Analyze the supported firmware

```bash
python3 patch_firmware_v.1.0.py --analyze
```

Analysis mode is read-only.

It displays technical information relevant to the reverse-engineering and
patching work performed for this specific firmware, including:

- firmware identity
- GBL container information
- GBL tag layout
- CRC32 information
- PROGRAM block layout
- flash and file offsets
- PROGRAM SHA-256 values
- patch address mappings
- original and patched instruction bytes
- hexadecimal context around the patch locations
- expected patch effects
- expected patched hashes and CRC32

The analyzer is intentionally tied to the firmware and patches investigated
by this project.

It is **not** intended to be a general BIN, firmware or GBL analyzer.

### Dry run

```bash
python3 patch_firmware_v.1.0.py --dry-run
```

Dry-run mode performs the complete validation and patching process in memory
but does not write a patched firmware file.

This can be used to confirm that the original firmware can be patched
successfully before creating an output file.

### Show byte differences

```bash
python3 patch_firmware_v.1.0.py --dry-run --diff
```

The `--diff` option displays the byte-level differences produced by both
patches.

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

The first two changes are the intended program modifications.

The final four bytes contain the rebuilt GBL CRC32.

Exactly six bytes are therefore expected to differ between the original and
final patched GBL.

Any additional difference is treated as a validation failure.

### Show version

```bash
python3 patch_firmware_v.1.0.py --version
```

Expected current version information:

```text
patch_firmware_v.1.0.py 1.0-beta revision 2
```

### Show command-line help

```bash
python3 patch_firmware_v.1.0.py --help
```

---

## OTA server

The included `ota_server.py` provides a small local HTTP server specifically
for transferring the generated patched firmware to a Shelly TRV.

It does not patch firmware and it does not automatically initiate an OTA
update on a device.

The current OTA-server version is:

```text
1.0
```

Before the server starts, it automatically loads:

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

and validates that the file is exactly the expected combined patched
firmware.

Validation includes:

- expected file size
- expected patched SHA-256
- stored GBL CRC32
- calculated GBL CRC32
- expected patched GBL CRC32

If validation fails, the firmware is not served.

### HTTP behavior

The server uses HTTP/1.1 and supports byte-range requests.

Supported request forms include:

```text
Range: bytes=0-
Range: bytes=<start>-<end>
Range: bytes=<start>-
Range: bytes=-<length>
```

A valid Range request is answered with:

```text
206 Partial Content
```

A request without a Range header is answered with:

```text
200 OK
```

Invalid or unsupported ranges are rejected.

The server has been tested with both complete HTTP transfers and HTTP Range
requests.

### Transfer progress

During a firmware request, the server displays transfer information including:

- requesting client
- requested byte range
- HTTP response status
- transferred bytes
- transfer progress
- transfer rate
- completion or interruption status

The transfer status describes the HTTP transfer only.

The OTA server deliberately does not claim that a completed transfer means the
firmware has been installed successfully.

Device status must be checked separately after the OTA operation.

More detailed OTA-server documentation is maintained in:

```text
docs/ota-server.md
```

---

## Firmware modifications

The combined firmware contains two independent program modifications.

### Patch A — beacon-skip recovery bypass

Original instruction:

```text
PROGRAM offset 0x0001E1C8

31 DC    bgt 0x0001E22E
```

Patched instruction:

```text
PROGRAM offset 0x0001E1C8

31 E0    b 0x0001E22E
```

Modified byte:

```text
PROGRAM offset : 0x0001E1C9
Original       : DC
Patched        : E0
```

Within the complete GBL file:

```text
GBL file offset: 0x0002471D
```

The modification forces execution to branch to the existing continuation path,
bypassing the additional recovery block associated with the observed
beacon-skip recovery behavior.

The normal RSSI-dependent beacon-skip selection remains in place.

### Patch B — periodic mDNS restart bypass

Original instruction:

```text
PROGRAM offset 0x0001E0F0

02 D0    beq 0x0001E0F8
```

Patched instruction:

```text
PROGRAM offset 0x0001E0F0

02 E0    b 0x0001E0F8
```

Modified byte:

```text
PROGRAM offset : 0x0001E0F1
Original       : D0
Patched        : E0
```

Within the complete GBL file:

```text
GBL file offset: 0x00024645
```

This modification bypasses the recurring connected-state call to the existing
mDNS restart routine.

The normal mDNS responder implementation and other event-driven callers are
not intentionally removed.

Detailed reverse-engineering information is maintained in the separate
research repository.

---

## Reproducibility

The supported original firmware has the following SHA-256:

```text
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

The original main PROGRAM block has the SHA-256:

```text
4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c
```

After applying both modifications, the expected main PROGRAM SHA-256 is:

```text
06742a2632a3d45cf697b8be85045914d004f30644dad17b3d0d20012c87c61b
```

The rebuilt combined-patch GBL has the expected CRC32:

```text
0xBAEB8265
```

The expected SHA-256 of the final combined patched GBL is:

```text
7adbb31d6b7faa8b9290d7b3436af45d42af9c3602a7195cafab774ded84ac61
```

The expected output size remains:

```text
1,106,384 bytes
```

These values allow the patching process to be reproduced and independently
verified.

---

## Safety

The patcher is designed to fail closed.

If any validation step fails, no new patched firmware image should be
produced.

Checks include:

- original firmware SHA-256
- original firmware size
- expected GBL structure
- original GBL CRC32
- PROGRAM block addresses and sizes
- original PROGRAM SHA-256
- both original patch instructions
- both original patch bytes
- patched PROGRAM SHA-256
- rebuilt GBL structure
- rebuilt GBL CRC32
- expected byte differences
- final patched GBL SHA-256
- written-file verification

The patcher also refuses to overwrite an existing output file.

`ota_server.py` independently validates the patched firmware before making it
available over HTTP.

Neither tool automatically initiates flashing on a Shelly TRV.

Firmware modification and OTA installation always involve risk. Do not
disconnect power or intentionally interrupt the device while an update is in
progress.

---

## Project status

The combined patch has successfully passed the deterministic binary-generation
and validation stages.

The current combined-patch testing has demonstrated:

```text
Original firmware validation:        confirmed
Combined patch generation:           confirmed
Deterministic patched output:        confirmed
Patched PROGRAM SHA-256:              confirmed
Patched GBL CRC32:                    confirmed
Patched GBL SHA-256:                  confirmed
OTA-server firmware validation:       confirmed
HTTP 200 transfer:                    confirmed
HTTP 206 Range transfer:              confirmed
Physical firmware installation:      confirmed
Patched firmware boot:                confirmed
Periodic mDNS suppression:            observed in runtime capture
Beacon-recovery suppression:          longer runtime validation in progress
Long-term stability:                  still under evaluation
Battery-life improvement:             not established
```

The combined patched firmware has been installed on a physical Shelly TRV that
previously ran firmware 2.1.3.

After installation, the device successfully booted firmware 2.2.4.

A packet capture performed with the combined patch did not observe the
previously identified periodic mDNS activity during the monitored test window.

This provides runtime evidence that Patch B is active in the combined firmware
under the tested conditions.

Longer runtime observation of the beacon-skip recovery behavior is still in
progress.

### Separate Patch B runtime test

Patch B was also tested independently on another physical Shelly TRV.

During the monitored packet-capture window, the recurring periodic mDNS
activity was not observed.

The device nevertheless continued to produce the recurring sequence:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip 20)
```

approximately once per minute under the observed conditions.

This provides useful runtime separation between the periodic mDNS restart path
and the beacon-skip recovery path under the tested conditions.

It does not establish that the two mechanisms can never interact under other
conditions.

### Battery testing

Long-term battery-consumption testing is still in progress.

The current runtime tests do **not** prove an improvement in battery life.

The two patched behaviors represent recurring firmware activity identified
during the investigation, but their quantitative contribution to battery
consumption has not yet been established.

---

## Research

The reverse-engineering work, firmware comparison, ARM/Thumb analysis,
runtime testing and technical reasoning behind these modifications are
documented separately in the research repository:

**Shelly-TRV-Gen1-2.2.4-beacon-skip-fix**

https://github.com/AbleMonster/Shelly-TRV-Gen1-2.2.4-beacon-skip-fix

The research repository contains the investigation and supporting technical
evidence.

This repository contains the local patching and OTA-serving implementation.

---

## Testing

Testing performed during development includes:

- validation of the known original firmware
- rejection of deliberately modified input firmware
- read-only verification mode
- read-only analysis mode
- complete in-memory dry run
- verification of both program modifications
- byte-difference verification
- deterministic output-file creation
- existing-output protection
- command-line option conflict handling
- verification of the expected patched PROGRAM SHA-256
- verification of the expected patched GBL CRC32
- verification of the expected patched GBL SHA-256
- automatic `target` directory workflow
- OTA-server validation of the generated firmware
- local HTTP firmware serving
- HTTP 200 full-file transfer
- HTTP 206 Range request handling
- firmware-transfer progress reporting
- OTA installation on physical Shelly TRV hardware
- post-update boot verification
- runtime packet capture
- independent Patch B runtime testing
- combined Patch A+B runtime testing

Additional test information is documented in:

```text
tests/README.md
```

No proprietary firmware test images are stored in this repository.

---

## Local firmware files and `target`

The `target` directory is intentionally included in the repository so that a
fresh clone already contains the directory expected by the patcher and OTA
server.

Firmware files inside `target` must remain local and must not be committed.

A typical `.gitignore` configuration is:

```gitignore
target/*
!target/.gitkeep
```

The repository therefore contains:

```text
target/.gitkeep
```

but not:

```text
target/SHTRV-01_build_2.2.4.gbl
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

This applies to both original and modified Shelly firmware.

---

## Disclaimer

This is an independent research project.

It is not affiliated with, endorsed by, sponsored by, or supported by Shelly.

Shelly and related product names are used only to identify the hardware and
firmware being studied.

Firmware modification and flashing can result in malfunction, loss of
configuration, device failure, or an unusable device.

Use of these tools and any firmware generated with them is at the user's own
risk.

The OTA server is intended for use on a trusted local network. It does not
provide authentication or TLS and should not be exposed to the public
Internet.

This project does not grant any rights to third-party firmware, trademarks,
or other intellectual property.

---

## License

The original source code and documentation in this repository are licensed
under the MIT License. See [LICENSE](LICENSE).

This license applies only to the original code and documentation contained in
this repository.

It does **not** grant any rights to Shelly firmware, trademarks, product names,
or other third-party intellectual property.

No original or modified Shelly firmware images are distributed as part of
this project.