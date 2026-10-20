# Security Policy

## Supported Versions

Security-related fixes are provided for the current version of the Shelly TRV Gen1 2.2.4 Patcher.

Older commits, development snapshots, experimental branches, or locally modified versions may not receive security fixes.

The patcher currently targets:

```text
Device:   Shelly TRV Gen1
Firmware: 2.2.4
Build:    20240619-130912/v2.2.4@ee290818
```

Support for additional firmware versions must be explicitly documented and validated.

---

## Reporting a Security Issue

Please do **not** open a public GitHub issue for a vulnerability that could create a meaningful risk to users, devices, firmware integrity, or sensitive information.

Examples include:

- Bypassing source-firmware validation
- Causing the patcher to accept an unsupported firmware image
- Applying patches at incorrect or unexpected binary locations
- Bypassing original-byte or integrity checks
- Producing malformed firmware without detecting the failure
- Path traversal or unintended file access
- Arbitrary file overwrite
- Command or code execution vulnerabilities
- Exposure of firmware files through the OTA server
- Unintended network exposure by the OTA server
- Disclosure of credentials, tokens, keys, or other sensitive information

For these issues, please use GitHub's private security reporting functionality where available.

If private security reporting is not available, contact the repository maintainer privately before publishing technical details.

Please include enough information to reproduce and evaluate the issue.

Useful information includes:

- Affected component
- Affected version or commit
- Operating system
- Python version
- Reproduction steps
- Expected behavior
- Observed behavior
- Security impact
- Relevant logs or error messages
- Suggested mitigation, if known

Do **not** include proprietary Shelly firmware binaries unless a private and legally appropriate method of sharing them has been explicitly agreed upon.

---

## Firmware Validation Issues

Firmware validation is considered a security- and safety-relevant component of this project.

The patcher is intended to operate only on explicitly supported firmware images.

A report should be treated as security-sensitive if the patcher can be made to:

- Accept an unsupported firmware image as supported
- Continue after a required validation check fails
- Apply a patch when expected original bytes do not match
- Apply patch data at an unintended offset or address
- Generate an output image after detecting inconsistent firmware structure
- Incorrectly report a malformed output image as valid

The preferred behavior for unknown, modified, malformed, or unsupported firmware is to **fail safely and produce no patched firmware image**.

---

## OTA Server Security

The included OTA server is intended as a minimal tool for controlled local firmware installation.

Security reports are particularly relevant if the OTA server:

- Exposes files other than the intended firmware image
- Allows unintended directory traversal or arbitrary file access
- Becomes accessible beyond the intended network interface unexpectedly
- Allows unintended file modification or upload
- Executes user-controlled input
- Leaks sensitive local information
- Serves a firmware image other than the explicitly selected image

Users should run the OTA server only for the time required to perform the firmware update and only on trusted networks.

The OTA server is not intended to be exposed directly to the public Internet.

---

## Firmware and Copyrighted Material

Please do not include the following in public security reports:

- Original Shelly firmware binaries
- Complete extracted proprietary firmware images
- Complete patched Shelly firmware images
- Proprietary GBL firmware images
- Credentials or authentication material
- Wi-Fi credentials
- Private keys
- API tokens
- Other sensitive information

Hashes, addresses, small byte sequences, instruction sequences, and focused technical excerpts may be used where necessary to identify and reproduce an issue.

---

## Coordinated Disclosure

Please allow reasonable time to investigate and, where necessary, prepare a fix before publicly disclosing security-sensitive technical details.

Once the issue has been addressed, coordinated public documentation of the problem and fix is encouraged where it can be done without unnecessarily exposing users to risk.

---

## Scope

This security policy covers the software and tooling maintained in this repository, including:

- Firmware patching scripts
- Firmware validation logic
- Patch verification logic
- OTA server
- Tests
- Repository automation directly affecting generated firmware

Issues in the original Shelly firmware, Shelly cloud services, Silicon Labs firmware, third-party software, or the Shelly TRV hardware itself are outside the direct security-maintenance scope of this repository.

Such findings may still be relevant to the associated research project or should be reported to the appropriate vendor.

---

## Safety Principle

The patcher should fail closed.

If the identity, structure, integrity, or expected contents of the input firmware cannot be established, the patcher should refuse to modify it rather than attempt a best-effort patch.