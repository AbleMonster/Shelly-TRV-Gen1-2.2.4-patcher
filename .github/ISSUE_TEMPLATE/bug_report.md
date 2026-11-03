---
name: Bug report
about: Report a reproducible problem with the patcher, OTA server, documentation, or patching workflow
title: "[BUG] "
labels: bug
assignees: ''
---

# Bug Report

## Summary

Provide a concise description of the problem.

## Affected Component

Select or describe the affected component:

- [ ] Firmware patcher (`patch_firmware_v2.0.py`)
- [ ] OTA server (`ota_server.py`)
- [ ] Firmware validation
- [ ] B2.2 reconstruction
- [ ] Patched firmware output
- [ ] Installation / OTA procedure
- [ ] Documentation
- [ ] Other

## Environment

**Operating system:**

**Python version:**

**Patcher version / release:**

**OTA server version / revision:**

**Relevant commit:**

## Input Firmware

If the issue involves firmware patching, please provide:

**Device:** Shelly TRV Gen1 / SHTRV-01
**Firmware version:**
**Build:**
**Input GBL filename:**
**Input GBL SHA256:**

The current patcher is intended only for the supported Shelly TRV Gen1 Stock 2.2.4 firmware:

```text
Build:
20240619-130912/v2.2.4@ee290818

Expected Stock GBL SHA256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

Do **not** upload or attach proprietary Shelly firmware files.

If not applicable, write `N/A`.

## Patch Output

If B2.2 output was successfully created, please provide the relevant identities.

**Application filename:**
**Application SHA256:**

**GBL filename:**
**GBL SHA256:**

For the current qualified B2.2 reconstruction, the expected output identities are:

```text
Application:
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin

SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9
```

```text
GBL:
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl

SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c
```

Do **not** upload or attach patched firmware images containing proprietary Shelly firmware.

If no output was created, write `N/A`.

## Steps to Reproduce

1.
2.
3.

## Expected Behavior

Describe what you expected to happen.

## Observed Behavior

Describe what actually happened.

## Console Output / Evidence

Include relevant console output, error messages, screenshots, hashes, or other evidence.

For patcher failures, include the complete validation or rejection message when possible.

For OTA-server issues, include the startup and firmware-validation output when relevant.

Please remove credentials, tokens, Wi-Fi credentials, device identifiers, MAC addresses, local IP addresses, and other sensitive information before posting.

Do **not** attach proprietary firmware files or patched firmware images.

## Reproducibility

Does the problem occur:

- [ ] Every time
- [ ] Intermittently
- [ ] Only once so far
- [ ] Unknown

## Safety / Recovery State

If the issue occurred during an OTA or physical-device test, please describe the resulting device state:

- [ ] Device remained reachable
- [ ] Device rebooted normally
- [ ] Device required a manual reboot
- [ ] Device became temporarily unreachable
- [ ] Device recovery was required
- [ ] Not applicable
- [ ] Unknown

Do not include instructions for bypassing firmware validation or other safety checks.

## Additional Context

Add any other information that may help reproduce or understand the problem.

Please distinguish where possible between:

- patcher construction or validation failure,
- OTA-server or transfer failure,
- device installation failure,
- runtime firmware behavior,
- battery-runtime observations.

A successful B2.2 reconstruction or OTA transfer does **not** by itself establish long-term battery-life improvement or prove the historical Shelly TRV battery-drain root cause.