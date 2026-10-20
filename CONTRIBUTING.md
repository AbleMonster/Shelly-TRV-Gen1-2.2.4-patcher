# Contributing to Shelly TRV Gen1 2.2.4 Patcher

Thank you for your interest in contributing to this project.

This repository provides tools and documentation for reproducibly applying validated modifications to the supported Shelly TRV Gen1 2.2.4 firmware.

The repository does **not** distribute original or patched Shelly firmware. Users must provide their own supported firmware image.

---

## What You Can Contribute

Useful contributions include:

- Bug fixes for the firmware patcher
- Improvements to firmware validation
- Improvements to patch verification
- OTA server fixes or improvements
- Automated tests
- Error handling improvements
- Documentation corrections
- User guide improvements
- Platform compatibility fixes
- Reproducibility improvements
- Review of patch generation or verification logic

New reverse-engineering findings, battery-drain research, hardware A/B test results, and investigation of additional firmware behavior should generally be submitted to the corresponding research repository instead.

---

## Supported Firmware

Firmware modifications in this repository are designed for a specific Shelly TRV Gen1 firmware build.

Unless explicitly documented otherwise, the supported firmware is:

```text
Device:   Shelly TRV Gen1
Firmware: 2.2.4
Build:    20240619-130912/v2.2.4@ee290818
```

The patcher must not assume that offsets, instructions, data structures, or other binary properties are valid for another firmware version.

Changes that affect firmware identification or compatibility must document:

- The exact supported firmware version
- The build identifier
- The expected input hash
- Any changes to compatibility checks
- How unsupported input was tested

---

## Firmware Input Validation

Input validation is a safety-critical part of the patching process.

The patcher should fail safely when the supplied firmware does not match the expected source image or structure.

Contributions must not weaken firmware validation merely to make additional firmware images pass.

If validation behavior is changed, explain:

1. Why the existing validation is insufficient
2. What additional inputs will be accepted or rejected
3. How false-positive acceptance is prevented
4. How the new behavior was tested

A patch must never be applied to an unknown firmware image based only on a matching filename or reported version string.

---

## Patcher Changes

Changes to patching logic should be deterministic and reproducible.

Where applicable, document:

- Original behavior
- Modified behavior
- Patch location
- Original bytes or instructions
- Replacement bytes or instructions
- Expected input hash
- Expected output hash
- Integrity or checksum changes
- Any firmware layout changes

Avoid broad or unrelated modifications when a smaller change is sufficient.

Patch generation should produce identical output when given identical input, patcher version, and configuration.

---

## Verification and Testing

Patcher changes should be tested at the appropriate level.

Useful verification includes:

- Unit tests
- Integration tests
- Input hash validation
- Negative tests using unsupported or modified firmware
- Patch-location verification
- Original-byte verification before replacement
- Output hash verification
- Deterministic rebuild comparison
- Static binary verification
- Independent disassembly
- GBL/container integrity verification
- Controlled hardware testing where appropriate

A successful script execution alone is not sufficient verification for a change that modifies firmware patching logic.

When possible, tests should also verify that malformed or unexpected input is rejected rather than silently producing an output image.

---

## Firmware and Copyrighted Material

This repository is intended to contain original tools, documentation, verification logic, tests, and independently created patching methods.

Please do **not** submit:

- Original Shelly firmware binaries
- Complete extracted proprietary firmware images
- Modified or patched complete Shelly firmware binaries
- GBL files containing proprietary Shelly firmware
- Large raw disassembly dumps containing unnecessary proprietary code
- Proprietary SDK material that cannot legally be redistributed
- Files obtained from unauthorized sources

Users should obtain the supported firmware through legitimate means and apply the patch locally.

Small instruction sequences, byte sequences, addresses, hashes, and technical excerpts may be included where necessary to document and reproduce the patching process.

Contributors are responsible for ensuring that submitted material can legally be redistributed.

---

## OTA Server Contributions

Changes to `ota_server.py` should preserve predictable and minimal behavior.

Please document changes affecting:

- Listening address or port
- Firmware file selection
- HTTP behavior
- Error handling
- Logging
- Network exposure
- Platform-specific behavior

Do not introduce unnecessary network services or remote functionality.

Security-sensitive changes should follow `SECURITY.md`.

---

## Documentation

Documentation should clearly distinguish between:

- What the patcher does
- Which firmware it supports
- How the generated image is verified
- How the user installs the generated image
- Known limitations or risks

Do not describe compatibility with firmware versions or devices that have not been explicitly validated.

Commands and examples should be reproducible where practical.

---

## Issues

Before opening an issue:

- Search existing issues
- Identify the affected patcher version or commit
- Include your operating system and Python version
- Include reproduction steps
- Include relevant console output
- Include firmware hashes where relevant
- Remove sensitive information
- Do not attach proprietary firmware

Please keep one issue focused on one technical problem whenever practical.

Research questions concerning the underlying TRV firmware should generally be handled in the research repository rather than as patcher bugs.

---

## Pull Requests

Pull requests should be focused and reviewable.

A pull request should:

- Explain what is being changed
- Explain why the change is necessary
- Reference relevant issues or research where appropriate
- Include verification or test information
- Avoid unrelated modifications
- Update documentation when behavior changes
- Preserve firmware validation and safety checks

Changes affecting patch generation should include enough information for the result to be independently reproduced and reviewed.

Do not combine unrelated patcher changes, documentation rewrites, and research work into a single pull request unless they are directly dependent on each other.

---

## Logs and Sensitive Information

Before submitting logs or console output, remove:

- Passwords
- Authentication tokens
- API keys
- Wi-Fi credentials
- Device identifiers where unnecessary
- MAC addresses where unnecessary
- Local network information where unnecessary
- Other personal or sensitive information

Prefer focused excerpts over large unfiltered logs.

---

## Security

Do not publicly disclose vulnerabilities that could create a meaningful risk to users or devices.

This includes issues that could cause the patcher to:

- Accept an unsupported firmware image
- Patch unexpected binary locations
- Bypass integrity or source-image validation
- Produce malformed firmware without detecting the failure
- Expose firmware or sensitive files through the OTA server

Please follow the reporting process described in `SECURITY.md`.

---

## Code of Conduct

Participation in this project is subject to `CODE_OF_CONDUCT.md`.

Please keep technical discussions constructive and focused on reproducible behavior.

---

## Final Principle

The patcher should prefer refusing an unknown or invalid input over producing a firmware image whose correctness cannot be established.

Changes should preserve the project's goals of safety, reproducibility, and independent verification.