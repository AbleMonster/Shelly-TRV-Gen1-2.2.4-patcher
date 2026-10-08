# Shelly TRV Gen1 2.2.4 Firmware Patcher

Local patching tool for the Shelly TRV (SHTRV-01) firmware 2.2.4 beacon-skip recovery modification.

> **Experimental software**
>
> This project is currently under development and should be considered experimental.
> Long-term stability and battery-consumption testing of the firmware modification
> is still in progress.

## Purpose

This tool creates a patched Shelly TRV 2.2.4 firmware image from an original
firmware file supplied locally by the user.

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

The patched firmware is not uploaded anywhere by this tool.

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
- no third-party Python packages are required

The patcher uses only the Python standard library.

## Usage

Basic usage:

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

This validates the supplied firmware without patching or writing a new firmware
file.

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

Detailed reverse-engineering information is maintained in the separate research
repository and in `docs/technical-details.md`.

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

No automatic flashing is performed.

## Project status

The firmware modification has successfully booted on a test Shelly TRV.

Runtime testing has shown normal beacon-skip operation without recurrence of
the targeted recovery loop during the observed test period.

Normal Wi-Fi and cloud operation have also been observed with the patched
firmware.

Long-term stability and battery-consumption testing are still in progress.

This does **not yet prove an improvement in battery life**.

## Research

The reverse-engineering work, firmware comparison, ARM/Thumb analysis,
runtime testing and technical reasoning behind this patch are documented
separately in the research repository:

**Shelly-TRV-Gen1-2.2.4-beacon-skip-fix**

https://github.com/AbleMonster/Shelly-TRV-Gen1-2.2.4-beacon-skip-fix

The research repository contains the investigation and supporting technical
evidence.

This repository contains the local patching implementation.

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
- installation and boot testing on a physical Shelly TRV

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

Use of this tool and any firmware generated with it is at the user's own risk.

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