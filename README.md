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

The patcher will refuse to modify firmware that does not match the expected
firmware image.

## Safety

The patcher is designed to fail closed.

If any validation step fails, no patched firmware image will be produced.

Checks include:

- firmware SHA-256
- firmware size
- GBL structure
- GBL CRC32
- program block address and size
- original patch bytes
- patched program integrity
- final GBL integrity

## Project status

The firmware modification has successfully booted on a test device.

Initial continuous runtime testing has shown normal beacon-skip operation
without recurrence of the targeted recovery loop.

Long-term stability and battery-consumption testing are still in progress.

This does **not yet prove an improvement in battery life**.

## Research

The reverse-engineering work, firmware comparison, ARM/Thumb analysis,
runtime testing and technical reasoning behind this patch are documented
separately in the research repository:

**Shelly-TRV-Gen1-2.2.4-beacon-skip-fix**

A direct link will be added when this repository is published.

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