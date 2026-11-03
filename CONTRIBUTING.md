# Contributing to Shelly TRV Gen1 2.2.4 Patcher

Thank you for your interest in contributing to this project.

This repository provides tools and documentation for deterministically reconstructing the qualified experimental B2.2 firmware from the exact supported Shelly TRV Gen1 Stock 2.2.4 firmware image.

The repository does **not** distribute original or reconstructed Shelly firmware.

Users must provide their own supported Stock firmware image locally.

---

## Current Project Scope

The current reconstruction tool is:

```text
patch_firmware_v2.0.py
```

The current firmware candidate is:

```text
B2.2
```

B2.2 is an observer-free integrated experimental firmware containing exactly nine selected qualified correction components.

The current project goal is:

```text
exact supported Stock 2.2.4
        |
        v
exact qualified B2.2
```

The patcher must reproduce the qualified B2.2 application and GBL exactly.

A functionally similar but byte-different firmware is a different firmware candidate and must not be silently treated as B2.2.

---

## What You Can Contribute

Useful contributions include:

- bug fixes for the firmware patcher,
- improvements to Stock firmware validation,
- improvements to expected-preimage validation,
- improvements to output-integrity verification,
- OTA server fixes or improvements,
- automated tests,
- negative and fail-closed tests,
- error-handling improvements,
- documentation corrections,
- user-guide improvements,
- platform compatibility fixes,
- reproducibility improvements,
- review of reconstruction or verification logic,
- improvements that preserve exact B2.2 output identity.

New reverse-engineering findings, battery-drain research, hardware A/B test results, and investigation of additional firmware behavior should generally be submitted to the corresponding research repository instead.

Security-sensitive firmware findings must follow the process described in `SECURITY.md`.

---

## Supported Firmware

Firmware reconstruction in this repository is designed for one exact Shelly TRV Gen1 firmware build.

Unless explicitly documented otherwise, the supported firmware is:

```text
Device:
Shelly TRV Gen1 / SHTRV-01

Firmware:
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

The patcher must not assume that offsets, instructions, structures, preimages, or other binary properties are valid for another firmware version.

Changes affecting firmware identification or compatibility must document:

- exact supported firmware version,
- exact build identifier,
- expected input SHA256,
- any changes to structural validation,
- any changes to preimage validation,
- how unsupported input was tested,
- how false-positive acceptance is prevented.

Support for an additional Stock firmware image must be explicitly qualified.

---

## Qualified B2.2 Output

The current qualified application identity is:

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

The current qualified GBL identity is:

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

A change that intentionally alters either final identity creates a new firmware candidate.

Such a change must not be merged as a normal maintenance change to B2.2 without separate qualification.

---

## Firmware Input Validation

Input validation is a safety-critical part of the reconstruction process.

The patcher should fail closed when the supplied firmware does not match the expected Stock image or expected structure.

Contributions must not weaken validation merely to make additional firmware images pass.

If validation behavior is changed, explain:

1. why the existing validation is insufficient,
2. what additional inputs will be accepted or rejected,
3. how false-positive acceptance is prevented,
4. how malformed input is handled,
5. how the new behavior was tested.

A reconstruction must never be applied to an unknown firmware image based only on:

- matching filename,
- reported version string,
- approximate file size,
- similar instruction sequence,
- general GBL structure.

The exact supported identity is required.

---

## Expected-Preimage Validation

The v2.0 reconstruction uses checked Stock preimages.

A contribution must preserve the principle:

```text
expected Stock preimage
        |
        v
compare with actual input
        |
        +-- mismatch --> abort
        |
        v
apply authorized transformation
```

Reconstruction data must not be blindly applied to an offset whose expected Stock contents are no longer present.

Changes that alter preimage handling must explain:

- what preimage is expected,
- how it is validated,
- what failure behavior is used,
- how mismatches are tested.

---

## Patcher Changes

Changes to reconstruction logic must be deterministic and reproducible.

Where applicable, document:

- original behavior,
- modified behavior,
- affected reconstruction region,
- expected Stock preimage,
- transformed bytes or logic,
- expected input hash,
- expected application hash,
- expected GBL hash,
- checksum or integrity changes,
- firmware layout changes,
- interaction with existing B2.2 corrections.

Avoid broad or unrelated modifications when a smaller change is sufficient.

For changes intended only to maintain the current B2.2 workflow:

```text
same input
+
same patcher behavior
=
same qualified B2.2 output
```

must remain true.

---

## Changes That Create a New Firmware Candidate

Any change that intentionally modifies the final:

```text
Application SHA256
```

or:

```text
GBL SHA256
```

must be treated as a new firmware candidate.

Examples include:

- adding another correction,
- changing existing correction semantics,
- replacing embedded radio firmware,
- changing integrated helper code,
- changing firmware layout,
- modifying the selected correction set.

Such changes require separate qualification.

They must not be described merely as a documentation or maintenance update.

---

## Verification and Testing

Patcher changes should be tested at the appropriate level.

Useful verification includes:

- unit tests,
- integration tests,
- exact input hash validation,
- negative tests using unsupported or modified firmware,
- truncated-input tests,
- corrupted-integrity tests,
- B2.2-as-input rejection,
- expected-preimage rejection,
- output-integrity failure tests,
- application SHA256 verification,
- GBL SHA256 verification,
- deterministic rebuild comparison,
- byte-for-byte reference comparison,
- static binary verification,
- independent disassembly,
- GBL/container integrity verification,
- standalone reconstruction testing,
- controlled hardware testing where appropriate.

A successful script execution alone is not sufficient verification for a change that affects firmware reconstruction.

Malformed or unexpected input should be tested specifically for safe rejection.

---

## Current Automated Regression Suite

The current v2.0 patcher regression suite contains:

```text
18 tests
```

The accepted current result is:

```text
OK
```

Some negative tests intentionally cause validation errors.

An expected failure message during a negative test does not represent a suite failure if the complete test suite passes.

Contributions affecting `patch_firmware_v2.0.py` should run the relevant regression tests before submission.

---

## Reproducibility

The final v2.0 patcher has been verified to reconstruct the qualified B2.2 artifacts byte-for-byte.

The distributed patcher must remain standalone.

Normal reconstruction must not require:

- reference B2.2 firmware files,
- research directories,
- qualification build trees,
- Ghidra,
- REA,
- Codex,
- external reverse-engineering tooling.

The runtime dependency should remain limited to the exact supported Stock firmware and the repository tooling required for reconstruction.

---

## Firmware and Copyrighted Material

This repository is intended to contain original tools, documentation, verification logic, tests, and independently created reconstruction methods.

Please do **not** submit:

- original Shelly firmware binaries,
- complete extracted proprietary firmware images,
- modified or reconstructed complete Shelly firmware binaries,
- GBL files containing proprietary Shelly firmware,
- proprietary radio firmware blobs,
- large raw disassembly dumps containing unnecessary proprietary code,
- proprietary SDK material that cannot legally be redistributed,
- files obtained from unauthorized sources.

Users should obtain the supported Stock firmware through legitimate means and perform reconstruction locally.

Small instruction sequences, byte sequences, addresses, hashes, and focused technical excerpts may be included where necessary to document and reproduce the reconstruction process.

Contributors are responsible for ensuring that submitted material can legally be redistributed.

---

## OTA Server Contributions

Changes to `ota_server.py` should preserve predictable and minimal behavior.

The current server is designed specifically for:

```text
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Current server identity:

```text
ShellyTRVOTA/2.0
```

Current supported OTA port:

```text
TCP 80
```

Please document changes affecting:

- listening address,
- TCP port,
- local IP detection,
- firmware file selection,
- firmware validation,
- HTTP behavior,
- Range handling,
- error handling,
- logging,
- network exposure,
- platform-specific behavior.

Do not introduce unnecessary network services, upload functionality, general filesystem access, or remote management behavior.

Security-sensitive changes must follow `SECURITY.md`.

---

## Documentation

Documentation should clearly distinguish between:

- what the patcher reconstructs,
- which Stock firmware it supports,
- which corrections are part of B2.2,
- how generated output is verified,
- how the OTA server operates,
- how the user installs the generated firmware,
- what has been physically tested,
- what remains under observation,
- known limitations and risks.

Do not describe compatibility with firmware versions or devices that have not been explicitly validated.

Commands, filenames, hashes, and examples should match the current v2.0/B2.2 workflow.

Historical results must remain identified as historical.

---

## Evidence and Claims

Contributions must preserve the distinction between evidence levels.

In particular:

```text
firmware defect
!=
battery-drain root cause
```

and:

```text
qualified correction
!=
battery-life improvement
```

and:

```text
exact reconstruction
!=
successful physical runtime
```

and:

```text
successful physical runtime
!=
long-term stability
```

Do not claim that B2.2:

- conclusively proves the historical battery-drain root cause,
- guarantees restored battery lifetime,
- has proven long-term battery improvement,

unless new evidence actually supports those claims.

---

## Research Contributions

The patcher repository should remain focused on reproducible reconstruction and OTA tooling.

New work involving:

- reverse engineering,
- root-cause investigation,
- battery-drain mechanisms,
- additional firmware defects,
- experimental diagnostic builds,
- new observers,
- new correction candidates,

should generally be developed and qualified in the research repository first.

Only qualified and deliberately selected results should move into this repository.

---

## Security Research

Security-sensitive findings must remain separate from ordinary patcher maintenance.

Do not include unpublished:

- exploit payloads,
- attack scripts,
- responsible-disclosure evidence,
- sensitive proof-of-concept material,
- vendor correspondence,

in public pull requests or issues.

The minimal MQTT PUBLISH guard included in B2.2 does not make this repository the public home of the separate MQTT security investigation.

Follow `SECURITY.md`.

---

## Issues

Before opening an issue:

- search existing issues,
- identify the affected patcher version or commit,
- include your operating system,
- include your Python version,
- include reproduction steps,
- include relevant console output,
- include firmware hashes where relevant,
- remove sensitive information,
- do not attach proprietary firmware.

Please keep one issue focused on one technical problem whenever practical.

Research questions concerning underlying TRV firmware behavior should generally be handled in the research repository rather than as patcher bugs.

---

## Pull Requests

Pull requests should be focused and reviewable.

A pull request should:

- explain what is being changed,
- explain why the change is necessary,
- reference relevant issues or qualification evidence where appropriate,
- include verification or test information,
- avoid unrelated modifications,
- update documentation when behavior changes,
- preserve fail-closed validation,
- preserve expected-preimage checks,
- preserve deterministic reconstruction where applicable,
- identify whether the exact B2.2 output is preserved.

For firmware-related changes, explicitly state either:

```text
Exact qualified B2.2 output preserved
```

or:

```text
New firmware candidate created
```

Do not combine unrelated patcher changes, documentation rewrites, and new research work into one pull request unless they are directly dependent on each other.

---

## Logs and Sensitive Information

Before submitting logs or console output, remove:

- passwords,
- authentication tokens,
- API keys,
- Wi-Fi credentials,
- device identifiers where unnecessary,
- MAC addresses where unnecessary,
- local IP addresses where unnecessary,
- public IP addresses where unnecessary,
- private filesystem paths where unnecessary,
- other personal or sensitive information.

Prefer focused excerpts over large unfiltered logs.

---

## Security

Do not publicly disclose vulnerabilities that could create a meaningful risk to users, devices, firmware integrity, or sensitive information.

This includes issues that could cause the patcher or OTA server to:

- accept unsupported firmware,
- bypass expected-preimage validation,
- apply transformation data at unintended locations,
- bypass integrity checks,
- report malformed output as qualified B2.2,
- expose firmware or local files,
- create arbitrary files,
- execute unintended user-controlled input.

Follow the reporting process in:

```text
SECURITY.md
```

---

## Code of Conduct

Participation in this project is subject to:

```text
CODE_OF_CONDUCT.md
```

Keep technical discussions constructive, evidence-based, and focused on reproducible behavior.

---

## Final Principle

The patcher should prefer refusing an unknown, malformed, inconsistent, or unsupported input over producing a firmware image whose correctness cannot be established.

The current project principle is:

```text
unknown input
!=
supported Stock firmware
```

and:

```text
similar output
!=
qualified B2.2
```

Changes should preserve:

```text
safety
+
determinism
+
reproducibility
+
fail-closed validation
+
independent verification
```

unless a deliberately new firmware candidate is being developed and separately qualified.