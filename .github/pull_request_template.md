# Pull Request

## Summary

Describe what this pull request changes.

Keep the summary focused on the concrete repository change.

## Type of Change

- [ ] Patcher logic
- [ ] B2.2 reconstruction
- [ ] Bug fix
- [ ] OTA server
- [ ] Firmware validation
- [ ] Tests
- [ ] Documentation
- [ ] Repository maintenance
- [ ] Other

## Motivation

Why is this change necessary?

Reference relevant issues, test results, qualification evidence, or findings from the research repository where applicable.

For firmware-related changes, distinguish between:

- demonstrated firmware defect,
- reconstruction or tooling change,
- diagnostic finding,
- runtime observation,
- battery-life hypothesis.

Do not describe a firmware change as a proven battery-drain fix unless supported by long-term physical evidence.

## Technical Details

Describe the implementation changes.

For patcher or firmware-related changes, include relevant information such as:

- supported device,
- supported firmware version/build,
- expected input firmware identity,
- modified reconstruction or patching logic,
- original behavior,
- modified behavior,
- relevant addresses, instructions, replacement bytes, or authorized byte ranges where appropriate,
- changes to validation or safety checks,
- output identity expectations,
- fail-closed behavior.

Keep implementation changes focused on reproducible and verifiable firmware reconstruction.

For the current B2.2 workflow, the supported stock firmware is:

```text
Device:
Shelly TRV Gen1 / SHTRV-01

Build:
20240619-130912/v2.2.4@ee290818

Stock GBL SHA256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

The current patcher is:

```text
patch_firmware_v2.0.py
```

Its purpose is to reconstruct the exact qualified B2.2 artifacts from the supported Stock 2.2.4 input.

## Expected B2.2 Output

If the pull request affects the current B2.2 reconstruction path, verify the expected final identities.

### Application

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

### GBL

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

If a firmware-related change intentionally produces different identities, explain why and provide the complete qualification basis before submission.

## Verification

Describe how the change was verified.

Relevant verification methods include:

- patcher unit tests,
- integration tests,
- standalone reconstruction tests,
- input validation tests,
- negative tests using modified or unsupported input,
- truncated-input rejection,
- corrupted-CRC rejection,
- expected-preimage rejection,
- output-integrity failure detection,
- application SHA256 verification,
- GBL SHA256 verification,
- byte-for-byte reference comparison,
- static binary verification,
- independent disassembly,
- deterministic rebuild comparison,
- GBL structure / CRC verification,
- OTA-server startup validation,
- OTA transfer test,
- physical-device runtime test,
- documentation review.

For current `patch_firmware_v2.0.py` changes, include the result of the relevant automated test suite and state whether the final application and GBL remain byte-identical to the qualified B2.2 references.

## Qualification Boundary

For firmware-related changes, state clearly which level of evidence applies:

- [ ] Static analysis only
- [ ] Reconstruction verified
- [ ] Byte-identical to qualified reference
- [ ] Automated regression tests passed
- [ ] OTA transfer tested
- [ ] Physical-device boot tested
- [ ] Physical runtime tested
- [ ] Long-term battery validation performed

Do not collapse these levels into a single claim.

In particular:

```text
exact reconstruction
!=
OTA success
!=
physical runtime success
!=
long-term battery improvement
!=
historical battery-drain root cause proven
```

## Firmware / Copyright Check

I confirm that this pull request does **not** include:

- [ ] Original Shelly firmware binaries
- [ ] Complete patched Shelly firmware binaries
- [ ] Proprietary GBL firmware images
- [ ] Unnecessary large proprietary disassembly dumps
- [ ] Credentials, tokens, keys, Wi-Fi credentials, or other secrets
- [ ] Private network identifiers or unrelated device data

If any item above cannot be confirmed, explain why before submitting the pull request.

Public repository changes should contain only the minimum technical material required to reproduce or document the patching workflow.

## Compatibility

If the change affects firmware reconstruction or patching, specify:

**Device:** Shelly TRV Gen1 / SHTRV-01
**Supported firmware version/build:**
**Expected input GBL SHA256:**

Does this change alter compatibility with previously supported input firmware?

- [ ] No
- [ ] Yes — explained below
- [ ] Not applicable

The current B2.2 v2.0 patcher intentionally supports only the exact qualified Stock 2.2.4 input.

Unexpected firmware variants must fail closed rather than being patched heuristically.

## Side Effects / Risks

Describe known or possible side effects.

For patcher or firmware-related changes, explicitly state whether the change affects:

- input firmware validation,
- expected preimage validation,
- authorized patch ranges,
- patch locations or replacement bytes,
- generated application layout,
- generated GBL structure,
- stored END CRC32 handling,
- output identity verification,
- deterministic reconstruction,
- OTA behavior,
- stock behavior outside the intended correction set.

If the pull request changes the final B2.2 application or GBL identity, this must be treated as a new firmware candidate requiring separate qualification.

## OTA Server Changes

If `ota_server.py` is modified, verify where applicable:

- expected B2.2 filename,
- expected file size,
- expected SHA256,
- expected END CRC32,
- TCP port behavior,
- HTTP/1.1 behavior,
- Range support,
- restrictive served path,
- startup validation.

Current expected GBL:

```text
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Current expected OTA-server identity:

```text
ShellyTRVOTA/2.0
```

Current supported local OTA port:

```text
TCP 80
```

## Security-Sensitive Changes

Security findings must remain separate from the public battery-drain research unless they are already suitable for public disclosure.

Do not include:

- unpublished exploit details,
- private proof-of-concept material,
- responsible-disclosure evidence,
- attack payloads,
- credentials or secrets.

Follow `SECURITY.md` for security-sensitive findings.

## Checklist

- [ ] The change is focused and contains no unrelated modifications.
- [ ] Relevant automated tests pass.
- [ ] Unsupported or unexpected firmware input is rejected safely.
- [ ] Expected preimages are validated where applicable.
- [ ] Final output identities are verified where applicable.
- [ ] Deterministic reconstruction remains intact where applicable.
- [ ] Relevant documentation has been updated.
- [ ] Firmware versions, builds, and hashes are identified where relevant.
- [ ] No proprietary firmware binary has been added.
- [ ] No generated patched firmware binary has been added.
- [ ] Sensitive information has been removed.
- [ ] Qualification claims match the actual evidence level.
- [ ] No battery-drain root-cause claim is made without supporting evidence.
- [ ] I have reviewed `CONTRIBUTING.md`.
- [ ] I have followed `SECURITY.md` for security-sensitive findings.

## Additional Notes

Add anything else reviewers should know.

For changes affecting B2.2, state explicitly whether the change:

```text
preserves the exact qualified B2.2 output
```

or:

```text
creates a new firmware candidate requiring new qualification
```

This distinction must remain explicit.