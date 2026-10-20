# Pull Request

## Summary

Describe what this pull request changes.

## Type of Change

- [ ] Patcher logic
- [ ] Bug fix
- [ ] OTA server
- [ ] Firmware validation
- [ ] Tests
- [ ] Documentation
- [ ] Repository maintenance
- [ ] Other

## Motivation

Why is this change necessary?

Reference relevant issues, test results, or findings from the research repository where applicable.

## Technical Details

Describe the implementation changes.

For patcher or firmware-related changes, include relevant information such as:

- Supported firmware version/build
- Expected input firmware SHA256
- Modified patching logic
- Original behavior
- Modified behavior
- Relevant addresses, instructions, or replacement bytes where appropriate
- Changes to validation or safety checks

Keep the implementation focused on reproducible patch generation.

## Verification

Describe how the change was verified.

Examples:

- Patcher unit/integration tests
- Input validation tests
- Negative tests with unsupported or modified input firmware
- Output hash verification
- Static binary verification
- Independent disassembly
- Deterministic rebuild comparison
- OTA procedure test
- Documentation review

For patcher changes, include the relevant input and output hashes where applicable.

## Firmware / Copyright Check

I confirm that this pull request does **not** include:

- [ ] Original Shelly firmware binaries
- [ ] Complete patched Shelly firmware binaries
- [ ] Proprietary GBL firmware images
- [ ] Unnecessary large proprietary disassembly dumps
- [ ] Credentials, tokens, keys, Wi-Fi credentials, or other secrets

If any item above cannot be confirmed, explain why before submitting the pull request.

## Compatibility

If the change affects firmware patching, specify:

**Device:** Shelly TRV Gen1  
**Supported firmware version/build:**  
**Expected input SHA256:**  

Does this change alter compatibility with previously supported input firmware?

- [ ] No
- [ ] Yes — explained below
- [ ] Not applicable

## Side Effects / Risks

Describe known or possible side effects.

For patcher changes, explicitly state whether the change affects:

- Input firmware validation
- Patch locations or replacement bytes
- Generated firmware layout
- Checksums / integrity handling
- OTA behavior
- Existing stock behavior outside the intended patch

## Checklist

- [ ] The change is focused and does not contain unrelated modifications.
- [ ] Relevant tests pass.
- [ ] Unsupported or unexpected firmware input is rejected safely.
- [ ] Relevant documentation has been updated.
- [ ] Firmware versions/builds and hashes are identified where relevant.
- [ ] No proprietary firmware binary has been added.
- [ ] Sensitive information has been removed.
- [ ] I have reviewed `CONTRIBUTING.md`.
- [ ] I have followed `SECURITY.md` for any security-sensitive findings.

## Additional Notes

Add anything else reviewers should know.