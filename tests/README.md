# Tests

This directory documents validation and runtime testing performed for the
Shelly TRV Gen1 2.2.4 Firmware Patcher.

The project intentionally does not include proprietary Shelly firmware test
fixtures.

All firmware-dependent tests are performed locally using an original firmware
image supplied separately by the user.

## Test scope

Testing is divided into two areas:

1. patcher and firmware-image validation
2. runtime testing on physical Shelly TRV hardware

The first verifies that the patcher produces exactly the expected binary
transformation.

The second verifies that the resulting firmware can be installed and operates
on the target device.

These are separate test objectives.

Successful binary validation does not by itself prove long-term runtime
stability or improved battery life.

## Reference firmware

The tests described here use the specifically supported firmware:

```text
Device:   Shelly TRV (SHTRV-01)
Version:  2.2.4
Build:    20240619-130912/v2.2.4@ee290818
```

Original GBL SHA-256:

```text
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

Original GBL size:

```text
1,106,384 bytes
```

No copy of this firmware is stored in this repository.

## Expected patched result

The expected patched GBL has:

```text
Size:
1,106,384 bytes

CRC32:
0x432F734F

SHA-256:
ac7d85c8e9239bebd3b134c4b93fc838859c613e59f7690650097da984ea7222
```

Expected patched PROGRAM #1 SHA-256:

```text
d69fc6157e50b3d72b4c800c0008e7f1d7e7e4d9799cee2b0f4b2269b68fc7d4
```

These values are used as deterministic reference values during validation.

## Expected binary difference

The intended firmware modification consists of one program byte:

```text
PROGRAM #1 offset:
0x0001E1C9

Original:
DC

Patched:
E0
```

Within the complete GBL file, this byte is located at:

```text
0x0002471D
```

The GBL CRC32 must also change as a consequence.

The complete expected GBL difference is:

```text
Offset      Original   Patched
----------  --------   -------
0x0002471D     DC         E0
0x0010E1CC     58         4F
0x0010E1CD     AB         73
0x0010E1CE     7B         2F
0x0010E1CF     DC         43
```

Exactly five bytes are expected to differ between the original and patched
GBL.

Any additional difference is considered a validation failure.

## CLI tests

The following command-line modes have been tested.

### Help

```text
python patch_firmware.py --help
```

Expected behavior:

- command-line help is displayed
- no firmware is modified
- no output firmware is created

### Version

```text
python patch_firmware.py --version
```

Expected behavior:

- patcher version is displayed
- no firmware file is required
- no output firmware is created

### Original firmware verification

```text
python patch_firmware.py ORIGINAL.gbl --verify
```

Expected behavior:

- supported original firmware is accepted
- file size is verified
- original SHA-256 is verified
- GBL structure is verified
- original CRC32 is verified
- PROGRAM layout is verified
- patch location is verified
- no patched firmware is written

### Firmware analysis

```text
python patch_firmware.py ORIGINAL.gbl --analyze
```

Expected behavior:

- analysis completes successfully for the supported original firmware
- firmware identity is displayed
- GBL structure is displayed
- PROGRAM layout is displayed
- CRC information is displayed
- patch address mapping is displayed
- patch instruction and byte are displayed
- hexadecimal context around the patch is displayed
- expected patched hashes are displayed
- no firmware is modified
- no output firmware is written

The analyzer is specific to the firmware and patch investigated by this
project. It is not tested or intended as a general-purpose firmware or GBL
analyzer.

### Dry run

```text
python patch_firmware.py ORIGINAL.gbl --dry-run
```

Expected behavior:

- complete original validation succeeds
- patch is applied in memory
- patched PROGRAM validation succeeds
- rebuilt GBL validation succeeds
- expected CRC32 is produced
- expected patched SHA-256 is produced
- no output firmware is written

### Dry run with byte differences

```text
python patch_firmware.py ORIGINAL.gbl --dry-run --diff
```

Expected behavior:

- dry-run validation succeeds
- PROGRAM byte difference is reported
- complete GBL byte differences are reported
- exactly the expected five GBL byte differences are present
- no output firmware is written

### Output-file creation

Example:

```text
python patch_firmware.py ORIGINAL.gbl --output PATCHED.gbl
```

Expected behavior:

- all validation stages complete before writing
- patched GBL is written to the requested path
- written file is read back
- written file SHA-256 is verified
- output matches the expected patched GBL

### Existing-output protection

The patcher was executed a second time using an output path that already
contained the previously generated patched GBL.

Expected behavior:

- execution is aborted
- existing output file is not overwritten

This behavior was confirmed.

### Conflicting command-line options

Mutually exclusive modes were tested together, for example:

```text
python patch_firmware.py ORIGINAL.gbl --verify --analyze
```

Expected behavior:

- command-line parsing rejects the conflicting options
- patching does not start
- no output firmware is written

This behavior was confirmed.

## Fail-closed input test

A copy of the supported original GBL was deliberately modified by changing a
byte before passing it to the patcher.

The resulting file no longer matched the expected original SHA-256.

Expected behavior:

- modified input is rejected
- patching does not proceed
- no patched output is created

This behavior was confirmed.

This test demonstrates that the patcher does not accept a file merely because
its filename, size or general GBL structure resembles the supported firmware.

The complete original firmware identity must match the expected reference.

## Reproducibility test

The patching process was used to generate the patched GBL from the known
original firmware.

The resulting values matched the expected references:

```text
Patched PROGRAM #1 SHA-256:
d69fc6157e50b3d72b4c800c0008e7f1d7e7e4d9799cee2b0f4b2269b68fc7d4

Patched GBL CRC32:
0x432F734F

Patched GBL SHA-256:
ac7d85c8e9239bebd3b134c4b93fc838859c613e59f7690650097da984ea7222
```

The resulting complete GBL differed from the original at exactly the five
expected byte positions.

## Physical-device test

The generated patched GBL has been installed on a physical Shelly TRV
(SHTRV-01).

The device successfully accepted the firmware and booted the patched 2.2.4
image.

Observed after installation:

- device booted successfully
- firmware operated as version 2.2.4
- Wi-Fi connectivity remained operational
- cloud connectivity remained operational
- normal beacon-skip operation was observed
- the targeted recurring recovery sequence was not observed during the
  monitored test period

The targeted sequence is:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip N)
```

These observations provide runtime evidence that the modified firmware can
operate on the target hardware and that the patched control-flow path behaves
as intended during the observed period.

## Runtime-test limitations

Runtime testing is still ongoing.

The current tests do not establish:

- long-term stability over all operating conditions
- behavior on every Shelly TRV hardware revision
- behavior with every Wi-Fi access point or network configuration
- long-term battery-consumption improvement
- a quantified battery-life improvement

In particular, absence of the targeted recovery sequence does not by itself
prove that battery consumption has improved.

Battery behavior must be evaluated separately over a sufficiently long test
period.

## Future tests

Further testing may include:

- longer continuous runtime
- additional Shelly TRV devices
- controlled reboot testing
- thermostat valve open/close operation
- additional Wi-Fi conditions
- comparison between patched and unpatched firmware
- longer-term battery-voltage and battery-consumption observations

Results should only be documented as confirmed when they have actually been
tested.

## Test fixtures

No Shelly firmware images are stored in this repository.

This includes:

- original GBL firmware
- patched GBL firmware
- extracted proprietary program binaries
- bootloader binaries
- proprietary firmware fragments intended as reusable fixtures

Local firmware files used during development must remain outside the
repository.

The repository `.gitignore` is intended to help prevent accidental inclusion
of firmware artifacts.

## Automated tests

The `tests` directory currently documents the validation performed during
development.

A standalone automated test suite using redistributable test fixtures has not
yet been added.

Because the patcher validates a proprietary firmware image, care must be taken
not to commit Shelly firmware data merely for use as automated test fixtures.

Future automated tests should use synthetic or independently created test data
where possible.