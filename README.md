# Shelly TRV Gen1 2.2.4 Firmware Patcher

Local patching and OTA installation tools for the Shelly TRV (SHTRV-01)
firmware 2.2.4 beacon-skip recovery modification.

> **Experimental software**
>
> This project is currently under development and should be considered
> experimental.
>
> The firmware modification has been successfully installed and tested on
> physical Shelly TRV devices. Long-term stability and battery-consumption
> testing is still in progress.

## Purpose

This project creates a patched Shelly TRV 2.2.4 firmware image from an
original firmware file supplied locally by the user.

The patch targets the recurring firmware behavior:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip N)
```

The patch bypasses the additional recovery path while preserving the normal
RSSI-dependent beacon-skip mechanism.

The modification was derived from reverse-engineering and runtime analysis of
the specifically supported Shelly TRV firmware build.

This project is intentionally limited to that known firmware image. It is not
intended to be a general-purpose Shelly firmware patcher or GBL manipulation
tool.

## Firmware distribution

**This repository does not contain or distribute Shelly firmware.**

Users must obtain the original firmware independently.

The patcher operates locally and:

1. validates the supplied firmware,
2. verifies the expected GBL structure,
3. extracts the relevant program block,
4. verifies the original patch location,
5. applies the one-byte modification,
6. validates the patched program data,
7. rebuilds the GBL container,
8. recalculates its CRC32,
9. validates the final firmware image,
10. writes the patched GBL locally.

The patched firmware is not uploaded anywhere by the patching tool.

The included OTA server can subsequently make the locally generated patched
firmware available to a Shelly TRV on the user's local network.

## Supported firmware

Currently only the specifically analyzed Shelly TRV firmware is supported:

```text
Device:   Shelly TRV (SHTRV-01)
Version:  2.2.4
Build:    20240619-130912/v2.2.4@ee290818
```

Original GBL SHA-256:

```text
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

The patcher will refuse to modify firmware that does not match the expected
firmware image.

## Requirements

- Python 3
- the original supported Shelly TRV 2.2.4 GBL firmware file
- a computer on the same local network as the Shelly TRV for OTA installation
- no third-party Python packages are required

Both `patch_firmware.py` and `ota_server.py` use only the Python standard
library.

## Quick start

The complete workflow is:

1. Obtain the original supported Shelly TRV 2.2.4 GBL firmware.
2. Verify the original firmware with `patch_firmware.py`.
3. Create the patched GBL.
4. Start `ota_server.py` with the patched GBL.
5. Use the OTA URL printed by the server for the target Shelly TRV.
6. Keep the OTA server running until the firmware transfer has completed.
7. Wait for the TRV to reboot.
8. Verify the installed firmware version and normal device operation.

### 1. Verify the original firmware

```text
python patch_firmware.py ORIGINAL.gbl --verify
```

The firmware must pass all validation checks before it can be patched.

### 2. Create the patched firmware

```text
python patch_firmware.py ORIGINAL.gbl
```

The default output file is:

```text
SHTRV-01_2.2.4_patch.gbl
```

### 3. Start the OTA server

```text
python ota_server.py SHTRV-01_2.2.4_patch.gbl
```

The OTA server validates the patched firmware before serving it.

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
http://192.168.178.159/SHTRV-01_2.2.4_patch.gbl
```

The actual IP address and port are detected automatically and may differ.

### 4. Start the OTA update

The server prints an OTA URL in the following form:

```text
http://<SHELLY-TRV-IP>/ota?url=http://192.168.178.159/SHTRV-01_2.2.4_patch.gbl
```

Replace:

```text
<SHELLY-TRV-IP>
```

with the IP address of the Shelly TRV that should receive the firmware.

For example, if the TRV has the local IP address:

```text
192.168.178.88
```

the resulting URL would be:

```text
http://192.168.178.88/ota?url=http://192.168.178.159/SHTRV-01_2.2.4_patch.gbl
```

Open the resulting OTA URL while `ota_server.py` is still running.

If port 8000 was selected instead of port 80, the server-generated firmware
URL will contain `:8000`.

Do not close the OTA server while the firmware is being transferred.

### 5. Verify the device after OTA

A completed HTTP transfer means that the OTA server successfully served the
firmware data requested by the device.

It does **not** by itself prove that the firmware was successfully installed
or that the device successfully rebooted.

After the update, wait for the Shelly TRV to become reachable again.

Verify that it reports:

```text
20240619-130912/v2.2.4@ee290818
```

Also verify normal operation of:

- Wi-Fi connectivity
- cloud connectivity, if used
- temperature measurement
- thermostat control
- valve movement
- device calibration

The firmware modification should be evaluated separately over a longer period
for stability and battery behavior.

## Patcher usage

### Basic usage

```text
python patch_firmware.py ORIGINAL.gbl
```

If all validation steps succeed, the patched firmware is written next to the
original file.

The default output filename is:

```text
SHTRV-01_2.2.4_patch.gbl
```

An existing output file will not be overwritten.

### Verify the original firmware

```text
python patch_firmware.py ORIGINAL.gbl --verify
```

This validates the supplied firmware without patching or writing a new
firmware file.

The verification includes the expected file identity, GBL structure, CRC32,
program layout and patch location.

### Analyze the supported firmware

```text
python patch_firmware.py ORIGINAL.gbl --analyze
```

Analysis mode is read-only.

It displays technical information relevant to the reverse-engineering and
patching work performed for this specific firmware, including:

- firmware identity
- GBL container information
- GBL tag layout
- CRC32 information
- program block layout
- flash and file offsets
- program SHA-256 values
- patch address mapping
- original and patched instruction bytes
- hexadecimal context around the patch location
- expected patch effects
- expected patched hashes and CRC32

The analyzer is intentionally tied to the firmware and patch investigated by
this project.

It is **not** intended to be a general BIN, firmware or GBL analyzer.

### Dry run

```text
python patch_firmware.py ORIGINAL.gbl --dry-run
```

Dry-run mode performs the complete validation and patching process in memory
but does not write a patched firmware file.

This can be used to confirm that the original firmware can be patched
successfully before creating an output file.

### Show byte differences

```text
python patch_firmware.py ORIGINAL.gbl --dry-run --diff
```

The `--diff` option displays the byte-level differences produced by the patch.

For the supported firmware, the expected result is:

```text
Program data:
0x0001E1C9  DC -> E0

GBL file:
0x0002471D  DC -> E0
```

The rebuilt GBL also contains four changed CRC32 bytes.

Therefore the final patched GBL differs from the original at exactly five byte
positions:

```text
0x0002471D  DC -> E0
0x0010E1CC  58 -> 4F
0x0010E1CD  AB -> 73
0x0010E1CE  7B -> 2F
0x0010E1CF  DC -> 43
```

### Select an output file

```text
python patch_firmware.py ORIGINAL.gbl --output PATCHED.gbl
```

The output path can be specified explicitly.

The patcher will refuse to overwrite an existing file.

### Show version

```text
python patch_firmware.py --version
```

### Show command-line help

```text
python patch_firmware.py --help
```

## OTA server

The included `ota_server.py` provides a small local HTTP server specifically
for transferring the patched firmware to a Shelly TRV.

It does not patch firmware and it does not automatically initiate an OTA
update on a device.

Before the server starts, it validates that the supplied file is exactly the
expected patched firmware.

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

A valid Range request is answered with HTTP `206 Partial Content`.

A request without a Range header is answered with HTTP `200 OK`.

Invalid or unsupported ranges are rejected.

The successful physical-device OTA tests included a Shelly TRV requesting the
firmware from this local server.

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

## Patch

The modification changes one byte in the main program data.

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

The actual modified byte is:

```text
PROGRAM offset : 0x0001E1C9
Original       : DC
Patched        : E0
```

Within the original GBL file this byte is located at:

```text
GBL file offset: 0x0002471D
```

The modification forces execution to branch to the existing continuation path,
bypassing the additional recovery block associated with the observed
beacon-skip recovery behavior.

Detailed reverse-engineering information is maintained in the separate
research repository and in `docs/technical-details.md`.

## Reproducibility

The supported original firmware has the following SHA-256:

```text
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

The original main program block has the SHA-256:

```text
4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c
```

After applying the one-byte modification, the expected main program SHA-256 is:

```text
d69fc6157e50b3d72b4c800c0008e7f1d7e7e4d9799cee2b0f4b2269b68fc7d4
```

The rebuilt GBL has the expected CRC32:

```text
0x432F734F
```

The expected SHA-256 of the final patched GBL is:

```text
ac7d85c8e9239bebd3b134c4b93fc838859c613e59f7690650097da984ea7222
```

These values allow the patching process to be reproduced and independently
verified.

## Safety

The patcher is designed to fail closed.

If any validation step fails, no new patched firmware image should be produced.

Checks include:

- original firmware SHA-256
- original firmware size
- expected GBL structure
- original GBL CRC32
- program block addresses and sizes
- original program SHA-256
- original patch instruction and patch byte
- patched program SHA-256
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

## Project status

The firmware modification has successfully booted and operated on multiple
physical Shelly TRV devices.

Testing performed so far includes:

- generation of the patched 2.2.4 GBL from the known original firmware
- successful installation of the patched firmware on physical hardware
- successful boot of patched firmware 2.2.4
- successful OTA transfer using the included local OTA server
- an upgrade test from original firmware 2.1.3 to patched firmware 2.2.4
- normal Wi-Fi operation after installation
- normal cloud operation after installation
- successful thermostat calibration
- successful thermostat valve movement
- normal RSSI-dependent beacon-skip selection
- operation without recurrence of the targeted recovery sequence during the
  observed test periods

The targeted sequence is:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip N)
```

Long-term stability and battery-consumption testing are still in progress.

These tests do **not yet prove an improvement in battery life**.

## Research

The reverse-engineering work, firmware comparison, ARM/Thumb analysis,
runtime testing and technical reasoning behind this patch are documented
separately in the research repository:

**Shelly-TRV-Gen1-2.2.4-beacon-skip-fix**

https://github.com/AbleMonster/Shelly-TRV-Gen1-2.2.4-beacon-skip-fix

The research repository contains the investigation and supporting technical
evidence.

This repository contains the local patching and OTA-serving implementation.

## Testing

Testing performed during development includes:

- validation of the known original firmware
- rejection of a deliberately modified input file
- read-only verification mode
- read-only analysis mode
- complete in-memory dry run
- byte-difference verification
- output-file creation
- existing-output protection
- command-line option conflict handling
- verification of the expected patched CRC32
- verification of the expected patched SHA-256
- installation and boot testing on physical Shelly TRV hardware
- local HTTP firmware serving
- HTTP Range request handling
- firmware-transfer progress reporting
- OTA installation on a second physical Shelly TRV
- post-update Wi-Fi and cloud verification
- post-update thermostat calibration and valve-operation verification

Additional test information is documented in:

```text
tests/README.md
```

No proprietary firmware test images are stored in this repository.

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

## License

The original source code and documentation in this repository are licensed
under the MIT License. See [LICENSE](LICENSE).

This license applies only to the original code and documentation contained in
this repository.

It does **not** grant any rights to Shelly firmware, trademarks, product names,
or other third-party intellectual property.

No original or modified Shelly firmware images are distributed as part of
this project.