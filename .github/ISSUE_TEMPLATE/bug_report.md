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

- [ ] Firmware patcher (`patch_firmware_v1.0.py`)
- [ ] OTA server (`ota_server.py`)
- [ ] Firmware validation
- [ ] Patched firmware output
- [ ] Installation / OTA procedure
- [ ] Documentation
- [ ] Other

## Environment

**Operating system:**

**Python version:**

**Patcher version / release:**

**Relevant commit:**

## Input Firmware

If the issue involves firmware patching, please provide:

**Device:** Shelly TRV Gen1  
**Firmware version:**  
**Build:**  
**Input firmware SHA256:**  

The patcher is intended for the supported Shelly TRV Gen1 firmware only.

Do **not** upload or attach proprietary Shelly firmware files.

If not applicable, write `N/A`.

## Patch Output

If a patched firmware image was successfully created:

**Output firmware SHA256:**  
**Output filename:**  

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

Please remove credentials, tokens, Wi-Fi credentials, device identifiers, MAC addresses, local IP addresses, and other sensitive information before posting.

Do **not** attach proprietary firmware files.

## Reproducibility

Does the problem occur:

- [ ] Every time
- [ ] Intermittently
- [ ] Only once so far
- [ ] Unknown

## Additional Context

Add any other information that may help reproduce or understand the problem.