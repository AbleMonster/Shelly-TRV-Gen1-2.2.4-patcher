# Security Policy

## Supported Versions

Security-related fixes are provided for the current version of the Shelly TRV Gen1 2.2.4 Patcher and OTA tooling.

The current reconstruction tool is:

```text
patch_firmware_v2.0.py
```

The current experimental firmware target is:

```text
B2.2
```

Older commits, historical patcher versions, development snapshots, experimental branches, archived tooling, or locally modified versions may not receive security fixes.

The patcher currently supports exactly:

```text
Device:
Shelly TRV Gen1 / SHTRV-01

Firmware:
2.2.4

Build:
20240619-130912/v2.2.4@ee290818

Supported Stock GBL SHA256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

Support for any additional firmware version or binary identity must be explicitly documented, independently validated, and qualified before use.

---

## Reporting a Security Issue

Please do **not** open a public GitHub issue for a vulnerability that could create a meaningful risk to users, devices, firmware integrity, local files, or sensitive information.

Examples include:

- bypassing supported Stock-firmware validation,
- causing the patcher to accept an unsupported firmware image,
- bypassing expected-preimage validation,
- applying reconstruction data at unintended offsets or addresses,
- bypassing output-integrity validation,
- producing malformed firmware without detecting the failure,
- incorrectly identifying a non-B2.2 artifact as qualified B2.2,
- path traversal or unintended file access,
- arbitrary file overwrite,
- command or code execution vulnerabilities,
- exposure of local firmware files through the OTA server,
- unintended network exposure by the OTA server,
- serving files other than the expected B2.2 GBL,
- disclosure of credentials, tokens, keys, or other sensitive information.

For these issues, use GitHub's private security reporting functionality where available.

If private security reporting is unavailable, contact the repository maintainer privately before publishing technical details.

Please include enough information to reproduce and evaluate the issue.

Useful information includes:

- affected component,
- affected version or commit,
- operating system,
- Python version,
- reproduction steps,
- expected behavior,
- observed behavior,
- security impact,
- relevant logs or error messages,
- relevant hashes,
- suggested mitigation, if known.

Do **not** include proprietary Shelly firmware binaries unless a private and legally appropriate method of sharing them has been explicitly agreed upon.

---

## Patcher and Reconstruction Security

Firmware reconstruction and validation are security- and safety-relevant parts of this project.

`patch_firmware_v2.0.py` is intended to reconstruct the qualified B2.2 artifacts only from the exact supported Stock 2.2.4 input.

The reconstruction process is intentionally deterministic and fail-closed.

A report should be treated as security-sensitive if the patcher can be made to:

- accept an unsupported firmware image as supported,
- continue after a required validation check fails,
- continue when an expected Stock preimage does not match,
- apply reconstruction data at an unintended location,
- partially apply the B2.2 transformation and still report success,
- generate output after detecting inconsistent firmware structure,
- accept a corrupted or truncated input,
- accept B2.2 itself as valid Stock input,
- bypass final application-integrity validation,
- bypass final GBL-integrity validation,
- incorrectly report a modified output as the qualified B2.2 artifact.

The preferred behavior for any unknown, modified, malformed, inconsistent, or unsupported firmware is:

```text
validation failure
        |
        v
abort
        |
        v
no artifact accepted as B2.2
```

The patcher must not attempt heuristic or best-effort adaptation to unknown firmware builds.

---

## Qualified B2.2 Output Identity

The current qualified B2.2 application is:

```text
Filename:
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin

SHA256:
7ee593265c76abd8cd628a81133d4b1310c1ae24c9ebe2ca3f2c2948acfc64f9
```

The current qualified B2.2 GBL is:

```text
Filename:
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl

SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

END CRC32:
52A97051
```

A generated artifact with a different final identity must not be silently treated as B2.2.

A change that intentionally alters the final B2.2 application or GBL identity creates a new firmware candidate requiring separate qualification.

---

## OTA Server Security

The included OTA server is intended as a minimal local tool for controlled firmware installation.

The current server is:

```text
ota_server.py
```

with the identity:

```text
ShellyTRVOTA/2.0
```

The current supported OTA workflow uses:

```text
TCP port 80
```

The OTA server is intended to serve only:

```text
/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Security reports are particularly relevant if the OTA server:

- exposes files other than the intended firmware image,
- permits directory traversal or arbitrary file access,
- serves an unvalidated firmware image,
- serves a file whose B2.2 identity does not match the expected reference,
- becomes reachable on unintended interfaces unexpectedly,
- exposes local filesystem information,
- allows unintended file modification or upload,
- executes user-controlled input,
- leaks sensitive local information,
- bypasses firmware validation,
- silently uses an unintended network port or target file.

The OTA server is not a general-purpose HTTP file server.

It should be run only for the time required to perform the firmware update and only on a trusted network.

It is not intended to be exposed directly to the public Internet.

---

## OTA Server Limitations

The OTA server intentionally provides:

```text
no authentication
no TLS
```

This is acceptable only within the intended temporary trusted-LAN workflow.

Users should:

- stop the server when it is no longer required,
- avoid exposing TCP port 80 to the public Internet,
- verify the local IP address selected by the server,
- be particularly careful when VPNs or multiple network interfaces are active,
- confirm that only the intended B2.2 firmware is present and validated.

A successful HTTP transfer does not prove successful firmware installation.

Device-level verification is a separate step.

---

## Firmware and Copyrighted Material

Do not include the following in public security reports:

- original Shelly firmware binaries,
- complete extracted proprietary firmware images,
- complete patched Shelly firmware images,
- proprietary GBL firmware images,
- proprietary radio-firmware images,
- large proprietary binary or disassembly dumps,
- credentials,
- authentication material,
- Wi-Fi credentials,
- private keys,
- API tokens,
- other secrets or sensitive information.

Where technically necessary, reports may include limited identifying material such as:

- hashes,
- addresses,
- offsets,
- small byte sequences,
- instruction sequences,
- short focused technical excerpts.

Use only the minimum material necessary to reproduce or explain the issue.

---

## Security Findings in Shelly Firmware

This repository's security-maintenance scope covers the patcher and related tooling maintained here.

A vulnerability discovered in:

- original Shelly firmware,
- Shelly cloud services,
- Shelly mobile applications,
- Silicon Labs firmware,
- third-party components,
- Shelly hardware,

is not automatically a vulnerability in this repository.

Such findings should normally be reported responsibly to the relevant vendor.

Do not publish vendor vulnerabilities through this repository merely because they were discovered during the battery-drain investigation.

---

## MQTT Security Research

A separate security investigation exists for the Shelly TRV MQTT input path.

That work is intentionally kept separate from the public Battery Drain patcher project.

The B2.2 firmware includes a minimal qualified MQTT PUBLISH guard, but detailed security-research material, proof-of-concept data, disclosure evidence, and reproduction material must remain in the appropriate security-research and responsible-disclosure workflow.

This repository must not be used to publish unpublished:

- exploit payloads,
- attack scripts,
- responsible-disclosure correspondence,
- sensitive proof-of-concept material.

The current research does **not** establish:

```text
remote code execution
```

or:

```text
arbitrary write
```

and public documentation must not claim either result without new supporting evidence.

---

## Coordinated Disclosure

Please allow reasonable time to investigate, reproduce, assess, and where necessary prepare a fix before publicly disclosing security-sensitive technical details.

Where a finding affects third-party software or firmware, responsible disclosure should be coordinated with the relevant vendor.

Once an issue has been addressed, coordinated public documentation of the problem and mitigation is encouraged where it can be done without unnecessarily increasing risk to users or devices.

---

## Scope

This security policy directly covers software and tooling maintained in this repository, including:

- `patch_firmware_v2.0.py`,
- Stock firmware validation,
- expected-preimage validation,
- B2.2 reconstruction logic,
- output-integrity validation,
- GBL reconstruction and integrity handling,
- output-file handling,
- `ota_server.py`,
- OTA firmware validation,
- OTA HTTP serving behavior,
- tests,
- repository automation directly affecting generated firmware.

It does not directly cover vulnerabilities in:

- original Shelly firmware,
- Shelly cloud services,
- Silicon Labs firmware,
- third-party software,
- the Shelly TRV hardware itself.

Those findings may still be relevant to the associated research project or responsible-disclosure process.

---

## Historical Tooling

Historical patcher versions such as:

```text
patch_firmware_v.1.0.py
```

and historical experimental firmware such as:

```text
SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

are not the current supported reconstruction workflow.

A security problem affecting only historical or archived tooling may still be worth reporting, but maintenance priority is given to the current v2.0/B2.2 workflow.

Historical output identities must not be used to validate current B2.2 artifacts.

---

## Sensitive Information

Before submitting any report, remove information that is not required for reproduction.

Examples include:

- local IP addresses,
- public IP addresses,
- MAC addresses,
- BSSIDs,
- Wi-Fi SSIDs where sensitive,
- usernames,
- filesystem paths containing personal names,
- access tokens,
- passwords,
- private keys,
- cloud identifiers,
- unrelated device identifiers.

Use placeholders where the exact value is not technically important.

---

## Safety Principle

The core safety principle of the patcher is:

```text
fail closed
```

If the identity, structure, integrity, expected preimage, reconstruction result, or final artifact identity cannot be established, the patcher should refuse to continue rather than attempt a best-effort reconstruction.

In particular:

```text
unknown input
!=
supported input
```

and:

```text
similar output
!=
qualified B2.2
```

Only the exact validated reconstruction is accepted as B2.2.