# Tests

This directory documents validation and runtime testing performed for the
Shelly TRV Gen1 2.2.4 Firmware Patcher.

The project intentionally does not include proprietary Shelly firmware test
fixtures.

All firmware-dependent tests are performed locally using an original firmware
image supplied separately by the user.

## Test scope

Testing is divided into three areas:

1. patcher and firmware-image validation,
2. OTA-server and transfer validation,
3. runtime testing on physical Shelly TRV hardware.

These are separate test objectives.

Binary validation verifies that the patcher produces exactly the expected
firmware transformation.

OTA-server testing verifies that the generated patched firmware can be
validated and transferred over the local network.

Physical-device testing verifies that the resulting firmware can be installed
and operated on the target hardware.

Successful validation or transfer does not by itself prove long-term runtime
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

The command-line interface was exercised during development using the
supported firmware image.

### Help

```text
python patch_firmware.py --help
```

Expected behavior:

- command-line help is displayed,
- no firmware is modified,
- no output firmware is created.

### Version

```text
python patch_firmware.py --version
```

Expected behavior:

- patcher version is displayed,
- no firmware file is required,
- no output firmware is created.

### Original firmware verification

```text
python patch_firmware.py ORIGINAL.gbl --verify
```

Expected behavior:

- supported original firmware is accepted,
- file size is verified,
- original SHA-256 is verified,
- GBL structure is verified,
- original CRC32 is verified,
- PROGRAM layout is verified,
- patch location is verified,
- no patched firmware is written.

### Firmware analysis

```text
python patch_firmware.py ORIGINAL.gbl --analyze
```

Expected behavior:

- analysis completes successfully for the supported original firmware,
- firmware identity is displayed,
- GBL structure is displayed,
- PROGRAM layout is displayed,
- CRC information is displayed,
- patch address mapping is displayed,
- patch instruction and byte are displayed,
- hexadecimal context around the patch is displayed,
- expected patched hashes are displayed,
- no firmware is modified,
- no output firmware is written.

The analyzer is specific to the firmware and patch investigated by this
project. It is not tested or intended as a general-purpose firmware or GBL
analyzer.

### Dry run

```text
python patch_firmware.py ORIGINAL.gbl --dry-run
```

Expected behavior:

- complete original validation succeeds,
- patch is applied in memory,
- patched PROGRAM validation succeeds,
- rebuilt GBL validation succeeds,
- expected CRC32 is produced,
- expected patched SHA-256 is produced,
- no output firmware is written.

### Dry run with byte differences

```text
python patch_firmware.py ORIGINAL.gbl --dry-run --diff
```

Expected behavior:

- dry-run validation succeeds,
- PROGRAM byte difference is reported,
- complete GBL byte differences are reported,
- exactly the expected five GBL byte differences are present,
- no output firmware is written.

### Output-file creation

Example:

```text
python patch_firmware.py ORIGINAL.gbl --output PATCHED.gbl
```

Expected behavior:

- all validation stages complete before writing,
- patched GBL is written to the requested path,
- written file is read back,
- written file SHA-256 is verified,
- output matches the expected patched GBL.

### Existing-output protection

The patcher was executed a second time using an output path that already
contained the previously generated patched GBL.

Expected behavior:

- execution is aborted,
- existing output file is not overwritten.

This behavior was confirmed.

### Conflicting command-line options

Mutually exclusive modes were tested together, for example:

```text
python patch_firmware.py ORIGINAL.gbl --verify --analyze
```

Expected behavior:

- command-line parsing rejects the conflicting options,
- patching does not start,
- no output firmware is written.

This behavior was confirmed.

## Fail-closed input test

A copy of the supported original GBL was deliberately modified by changing a
byte before passing it to the patcher.

The resulting file no longer matched the expected original SHA-256.

Expected behavior:

- modified input is rejected,
- patching does not proceed,
- no patched output is created.

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

## OTA-server tests

The local OTA server was tested using the patched GBL generated by
`patch_firmware.py`.

The tested server is:

```text
ota_server.py
```

### Patched-firmware validation

Before starting the HTTP server, `ota_server.py` validates the supplied
firmware.

During testing, the expected patched image was accepted with:

```text
Size:
1,106,384 bytes

CRC32:
0x432F734F

SHA-256:
ac7d85c8e9239bebd3b134c4b93fc838859c613e59f7690650097da984ea7222
```

The HTTP server was started only after validation succeeded.

### Automatic network selection

During the documented OTA test, the server automatically selected a local
IPv4 address and an available HTTP port.

The tested configuration successfully used TCP port 80.

The server also implements fallback to TCP port 8000 when port 80 is not
available.

The port-8000 fallback is implemented behavior; the documented physical-device
OTA test used port 80.

### Browser transfer test

Before the physical-device OTA test, the generated firmware URL was opened in
a browser.

The patched GBL was successfully transferred from the local OTA server.

This confirmed:

- the server was reachable,
- the expected firmware path was served,
- normal HTTP transfer operated,
- transfer progress reporting operated.

This browser test did not itself test Shelly OTA installation.

### HTTP Range support

The OTA server implements HTTP byte-range handling.

Supported request forms include:

```text
Range: bytes=0-
Range: bytes=<start>-<end>
Range: bytes=<start>-
Range: bytes=-<length>
```

During a successful physical-device OTA transfer, the Shelly TRV requested
firmware using a Range request beginning at byte zero.

The server handled the request and transferred the firmware to the device.

### Transfer-status limitation

The OTA server reports the state of the HTTP transfer.

A completed transfer does not by itself establish that:

- the firmware was accepted by the TRV,
- the firmware was successfully written to flash,
- the TRV rebooted successfully,
- the firmware operated correctly after reboot.

Those properties are verified separately by physical-device testing.

## Physical-device testing

The patched firmware has been installed and operated on multiple physical
Shelly TRV (SHTRV-01) devices.

The tests described below are independent runtime observations of the same
firmware modification.

## Test device #1

The first physical-device test was used to establish that the rebuilt patched
GBL could be accepted and booted by a Shelly TRV.

Observed after installation:

- patched firmware 2.2.4 booted successfully,
- Wi-Fi connectivity remained operational,
- cloud connectivity remained operational,
- normal RSSI-dependent beacon-skip behavior was observed,
- the targeted recurring recovery sequence was not observed during the
  monitored test period.

The targeted sequence is:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip N)
```

The first device subsequently remained under observation for a longer runtime
period without recurrence of the targeted recovery behavior during the
observed period.

This test provided the first physical-device evidence that the modified
control flow could operate on the target hardware.

## Test device #2 — OTA workflow test

A second physical Shelly TRV was used to test the complete local workflow,
including OTA delivery using `ota_server.py`.

### Pre-update state

Before the update, the device was running original firmware:

```text
Device:   Shelly TRV (SHTRV-01)
Version:  2.1.3
Build:    20220202-080736/v2.1.3@d255ad74
```

Before flashing:

- the device was connected to Wi-Fi,
- cloud connectivity was operational,
- the thermostat was calibrated,
- valve movement was functional.

This established a known functional baseline before the OTA update.

### OTA procedure

The patched firmware generated by `patch_firmware.py` was supplied to:

```text
ota_server.py
```

The server:

- validated the patched firmware,
- selected the local network address,
- selected TCP port 80,
- started the HTTP/1.1 server,
- received a firmware request from the TRV,
- handled the firmware transfer,
- displayed transfer progress.

The device accepted the firmware and rebooted.

### Post-update firmware

After the OTA update, the device reported:

```text
Device:   Shelly TRV (SHTRV-01)
Version:  2.2.4
Build:    20240619-130912/v2.2.4@ee290818
```

This confirmed that the device was no longer running the original 2.1.3
firmware and had booted the 2.2.4 image delivered during the OTA test.

### Post-update connectivity

After reboot:

- Wi-Fi connectivity was operational,
- the device retained its network configuration,
- cloud connectivity became operational,
- the device was reachable through its local interface.

The initial cloud connection process included reconnect/rekey activity before
normal cloud operation was established.

This startup behavior was observed but has not been attributed to the firmware
patch.

### Calibration and valve operation

An initial calibration attempt during startup failed.

A subsequent calibration completed successfully.

After successful calibration, thermostat regulation commanded valve movement
and the physical valve actuator moved.

This verified that the patched firmware did not prevent:

- calibration,
- thermostat control,
- valve-close operation,
- stepper-motor movement.

The temporary initial calibration failure was observed during the OTA reboot
sequence but has not been attributed to the one-byte patch.

### Beacon-skip behavior

After Wi-Fi connection, the device initially entered:

```text
Enter powersave state 3 (skip 1)
```

The normal signal-strength logic then selected:

```text
Enter powersave state 3 (skip 20)
```

for the observed strong Wi-Fi signal.

This is consistent with the normal RSSI-dependent beacon-skip behavior that
the patch is intended to preserve.

During the monitored post-update period, the log did not contain:

```text
Beacon skip error! Attempt recovery
```

and did not contain:

```text
Enter powersave state 1
```

The targeted recovery path therefore was not observed during that test period.

### Runtime statistics

Runtime statistics obtained from the second test device showed:

```text
desired_beacon_skip: 20
beacon_err_counter:  0
```

A separate field reported:

```text
real_beacon_skip: 3
```

The exact semantics of this field have not been established.

It is therefore not treated as proof that the low-level WLAN firmware was
configured with a beacon-skip value of 3.

In particular, runtime logging simultaneously showed the normal firmware
operation:

```text
Enter powersave state 3 (skip 20)
```

The project therefore keeps the observed statistics and the verified runtime
log behavior separate rather than assigning an unverified interpretation to
`real_beacon_skip`.

### Result of test device #2

The second physical-device test confirmed, under the tested conditions:

- original 2.1.3 firmware could be upgraded to the patched 2.2.4 image,
- the local OTA server successfully delivered the firmware,
- the patched firmware booted,
- Wi-Fi remained functional,
- cloud connectivity operated,
- calibration completed successfully,
- thermostat control operated,
- valve movement operated,
- normal RSSI-dependent beacon-skip selection remained active,
- the targeted recovery sequence was not observed during the monitored
  post-update period.

## Current physical-test summary

At the current stage, the project has demonstrated:

```text
Patched GBL generation:          confirmed
Deterministic binary output:     confirmed
Patched GBL CRC32:               confirmed
Patched GBL SHA-256:             confirmed
Physical firmware installation:  confirmed
Patched firmware boot:           confirmed
Local OTA delivery:              confirmed
HTTP Range OTA request:          observed
Wi-Fi after patch:               confirmed
Cloud after patch:               confirmed
Thermostat calibration:          confirmed
Valve movement:                  confirmed
Normal beacon-skip selection:    observed
Targeted recovery recurrence:    not observed during monitored test periods
Long-term stability:             still under evaluation
Battery-life improvement:        not established
```

## Runtime-test limitations

Runtime testing is still ongoing.

The current tests do not establish:

- long-term stability over all operating conditions,
- behavior on every Shelly TRV hardware revision,
- behavior with every Wi-Fi access point or network configuration,
- behavior under all possible RSSI conditions,
- behavior under every possible WLAN failure condition,
- long-term battery-consumption improvement,
- a quantified battery-life improvement.

In particular, absence of the targeted recovery sequence does not by itself
prove that battery consumption has improved.

Battery behavior must be evaluated separately over a sufficiently long test
period.

## Future tests

Further testing may include:

- longer continuous runtime,
- additional Shelly TRV devices,
- controlled reboot testing,
- additional thermostat open/close cycles,
- additional Wi-Fi conditions,
- weaker RSSI conditions,
- comparison between patched and unpatched firmware,
- longer-term battery-voltage and battery-consumption observations.

Results should only be documented as confirmed when they have actually been
tested.

## Test fixtures

No Shelly firmware images are stored in this repository.

This includes:

- original GBL firmware,
- patched GBL firmware,
- extracted proprietary program binaries,
- bootloader binaries,
- proprietary firmware fragments intended as reusable fixtures.

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