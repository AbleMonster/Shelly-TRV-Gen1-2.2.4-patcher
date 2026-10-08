# Technical Details

This document describes the technical implementation of the firmware patch
used by this project and the validation performed by `patch_firmware.py`.

Detailed reverse-engineering research, firmware comparisons, runtime logs and
the investigation that led to this modification are maintained in the separate
research repository.

This document intentionally describes only the firmware build and patch
supported by this project. It is not intended as general documentation for the
GBL format or other Shelly firmware versions.

## Supported firmware

Device:

```text
Shelly TRV (SHTRV-01)
```

Firmware:

```text
Version: 2.2.4
Build:   20240619-130912/v2.2.4@ee290818
```

Original GBL size:

```text
1,106,384 bytes
```

Original GBL SHA-256:

```text
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

Only this specifically analyzed firmware image is accepted by the patcher.

## Observed behavior

The modification targets the recurring runtime sequence:

```text
Beacon skip error! Attempt recovery
Enter powersave state 1
Enter powersave state 3 (skip N)
```

Testing and firmware comparison showed that the normal RSSI-dependent
beacon-skip mechanism and the additional recovery behavior are separate parts
of the firmware logic.

The patch is intended to bypass the additional recovery path while leaving the
normal beacon-skip selection mechanism intact.

## Beacon-skip selection

Analysis of the supported firmware showed the following RSSI-dependent desired
beacon-skip values:

```text
RSSI >= -69 dBm        -> beacon skip 20
RSSI -79 .. -70 dBm    -> beacon skip 15
RSSI < -79 dBm         -> beacon skip 10
```

Equivalent threshold behavior was also observed in the analyzed older firmware
code used during the investigation.

The one-byte patch described below does not modify these RSSI thresholds.

## Recovery-path condition

The relevant code in firmware 2.2.4 contains the following sequence:

```asm
0001E1B6  21 4B        ldr      r3,[...]
0001E1B8  93 F9 00 30  ldrsb.w  r3,[r3,#0]
0001E1BC  00 2B        cmp      r3,#0
0001E1BE  36 D0        beq      0x0001E22E

0001E1C0  1E 4B        ldr      r3,[...]
0001E1C2  93 F9 00 30  ldrsb.w  r3,[r3,#0]
0001E1C6  02 2B        cmp      r3,#2
0001E1C8  31 DC        bgt      0x0001E22E
```

The additional recovery block follows this conditional branch.

From the control flow:

```text
value == 0   -> branch to continuation
value 1..2   -> enter recovery block
value > 2    -> branch to continuation
```

The exact semantic meaning of the underlying firmware variable has not been
proven conclusively.

For that reason, this project does not assign an unverified descriptive name
to that variable.

What is relevant to the patch is the verified control flow: the conditional
branch at `0x0001E1C8` determines whether execution can enter the additional
recovery block or continue at `0x0001E22E`.

## Patch

Relevant instruction offset in PROGRAM #1:

```text
0x0001E1C8
```

Original instruction:

```asm
31 DC    bgt 0x0001E22E
```

Patched instruction:

```asm
31 E0    b 0x0001E22E
```

The original conditional branch is therefore replaced with an unconditional
branch to the same existing destination.

This causes execution to continue at `0x0001E22E` instead of entering the
additional recovery block.

### Actual byte modification

The instruction is two bytes long:

```text
Original: 31 DC
Patched : 31 E0
```

Only the second byte changes.

PROGRAM #1 offset:

```text
0x0001E1C9
```

Modification:

```text
DC -> E0
```

No other program byte is intentionally modified.

## Patch context

The original bytes around the patch location are:

```text
0x0001E1B8:
93 F9 00 30 00 2B 36 D0 1E 4B 93 F9 00 30 02 2B

0x0001E1C8:
31 DC 07 F1 14 03 18 46 54 F0 BC FB F8 62 EC F7

0x0001E1D8:
27 F8
```

The modified byte is the `DC` at:

```text
0x0001E1C9
```

After patching, the beginning of the second row becomes:

```text
31 E0 07 F1 ...
```

## GBL container

The supported original firmware is stored in a GBL container.

For this specific image, the parsed container contains six tags:

```text
#1  HEADER
    ID             : 0x03A617EB
    Tag offset     : 0x00000000
    Payload length : 8 bytes

#2  APPLICATION_INFO
    ID             : 0xF40A0AF4
    Tag offset     : 0x00000010
    Payload length : 28 bytes

#3  BOOTLOADER
    ID             : 0xF50909F5
    Tag offset     : 0x00000034
    Payload length : 25,868 bytes

#4  PROGRAM
    ID             : 0xFD0303FD
    Tag offset     : 0x00006548
    Payload length : 1,049,552 bytes

#5  PROGRAM
    ID             : 0xFD0303FD
    Tag offset     : 0x00106920
    Payload length : 30,876 bytes

#6  END
    ID             : 0xFC0404FC
    Tag offset     : 0x0010E1C4
    Payload length : 4 bytes
```

The patcher validates this expected structure before modifying the firmware.

## PROGRAM blocks

The supported GBL contains two PROGRAM tags.

Each PROGRAM payload contains a four-byte flash address followed by the program
data.

### PROGRAM #1

Flash start:

```text
0x00000000
```

Flash end:

```text
0x001003CB
```

Program data size:

```text
1,049,548 bytes
```

GBL program-data range:

```text
0x00006554 - 0x0010691F
```

Original PROGRAM #1 SHA-256:

```text
4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c
```

This is the program block containing the patch location.

### PROGRAM #2

Flash start:

```text
0x00130A98
```

Flash end:

```text
0x0013832F
```

Program data size:

```text
30,872 bytes
```

GBL program-data range:

```text
0x0010692C - 0x0010E1C3
```

PROGRAM #2 SHA-256:

```text
662bd549f050ab81a120d3daa07646652c38880b9d2bfa988ff6bee7f731e33e
```

PROGRAM #2 is not modified by this patch.

The patcher verifies that it remains unchanged when rebuilding the GBL.

## Address mapping

The patch location can be represented in three relevant address spaces.

PROGRAM #1 byte offset:

```text
0x0001E1C9
```

Because PROGRAM #1 is mapped to flash address `0x00000000`, the corresponding
flash address is:

```text
0x0001E1C9
```

PROGRAM #1 data begins at GBL file offset:

```text
0x00006554
```

Therefore:

```text
0x00006554 + 0x0001E1C9 = 0x0002471D
```

The complete mapping is:

```text
PROGRAM offset : 0x0001E1C9
Flash address  : 0x0001E1C9
GBL file offset: 0x0002471D
```

The byte at GBL file offset `0x0002471D` is therefore changed from:

```text
DC -> E0
```

## GBL handling

The patcher does not construct a firmware image from scratch.

It:

1. reads the original GBL,
2. validates the complete original file identity,
3. parses the expected GBL tag structure,
4. validates the original GBL CRC32,
5. identifies the expected PROGRAM blocks,
6. validates PROGRAM #1 and the patch location,
7. modifies one byte in PROGRAM #1 in memory,
8. validates the resulting PROGRAM #1,
9. reinserts the modified program data into a copy of the original GBL,
10. recalculates the GBL CRC32,
11. validates the rebuilt GBL,
12. verifies the exact expected byte differences,
13. verifies the final GBL SHA-256,
14. writes the result only after validation succeeds.

Unrelated firmware data is expected to remain unchanged.

## CRC32

The original GBL contains the stored CRC32:

```text
0xDC7BAB58
```

For this firmware, CRC32 is calculated over the GBL data from:

```text
0x00000000
```

through:

```text
0x0010E1CB
```

inclusive.

The four stored CRC bytes occupy:

```text
0x0010E1CC - 0x0010E1CF
```

The CRC32 calculated over the original file matches the stored value:

```text
Calculated: 0xDC7BAB58
Stored    : 0xDC7BAB58
```

After the one-byte program modification, the expected CRC32 is:

```text
0x432F734F
```

The rebuilt GBL stores this new CRC value.

## Expected byte differences

Only one firmware-content byte changes.

Original GBL program byte:

```text
0x0002471D  DC
```

Patched:

```text
0x0002471D  E0
```

Changing this byte changes the GBL CRC32, so the four stored CRC bytes also
change.

The complete expected original-to-patched GBL difference is therefore:

```text
Offset      Original   Patched
----------  --------   -------
0x0002471D     DC         E0
0x0010E1CC     58         4F
0x0010E1CD     AB         73
0x0010E1CE     7B         2F
0x0010E1CF     DC         43
```

Exactly five bytes in the complete GBL file are expected to differ.

One is the intentional program modification.

The remaining four bytes contain the updated CRC32.

Any other difference causes validation to fail.

## Patched PROGRAM verification

Original PROGRAM #1 SHA-256:

```text
4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c
```

Expected patched PROGRAM #1 SHA-256:

```text
d69fc6157e50b3d72b4c800c0008e7f1d7e7e4d9799cee2b0f4b2269b68fc7d4
```

The patcher verifies this value after applying the byte modification.

This provides an additional check that the resulting program data is exactly
the program image produced during development and testing.

## Final GBL verification

Expected patched GBL size:

```text
1,106,384 bytes
```

Expected patched GBL CRC32:

```text
0x432F734F
```

Expected patched GBL SHA-256:

```text
ac7d85c8e9239bebd3b134c4b93fc838859c613e59f7690650097da984ea7222
```

The output is considered valid only when the rebuilt GBL matches the expected
structure, CRC32, byte differences and SHA-256.

The file written to disk is read back and checked again.

## Fail-closed validation

The patcher is intentionally restricted to the known firmware image.

Before a patched file can be written, validation includes:

```text
Original file size
Original GBL SHA-256
GBL tag structure
Original GBL CRC32
PROGRAM block count
PROGRAM flash addresses
PROGRAM sizes
Original PROGRAM #1 SHA-256
Original patch instruction
Original patch byte
Patched PROGRAM #1 SHA-256
Unmodified PROGRAM #2
Expected rebuilt GBL structure
Expected patched CRC32
Exact original-to-patched byte differences
Expected patched GBL SHA-256
```

If an expected value does not match, processing is aborted.

This behavior is intentional. The patcher does not attempt to adapt the patch
to unknown firmware builds.

## Analyzer

The `--analyze` mode exposes the technical information used by this project
without modifying the firmware.

Example:

```text
python patch_firmware.py ORIGINAL.gbl --analyze
```

It reports information including:

```text
Firmware identity
GBL container information
GBL tag map
CRC32 ranges and values
PROGRAM layout
PROGRAM SHA-256 values
Patch address mapping
Original and patched instruction
Hex context around the patch
Expected patch effects
Expected patched hashes
```

Analysis mode is read-only.

It is specifically intended to make the technical basis of this patch visible
and reproducible.

It is not intended to be a general-purpose GBL or binary analyzer.

## Patch behavior

The original instruction:

```asm
bgt 0x0001E22E
```

branches to the existing continuation only when its condition is satisfied.

The patched instruction:

```asm
b 0x0001E22E
```

always branches to that same continuation.

The modification therefore prevents execution from falling through from this
branch into the additional recovery block.

The destination code itself is not modified.

The normal RSSI-dependent beacon-skip selection code is also not modified by
this patch.

## Scope of the conclusion

The binary modification and resulting control-flow change are directly
verifiable.

Runtime testing of the patched firmware has shown operation without recurrence
of the targeted recovery sequence during the observed test period.

However, this patch does not by itself establish the exact semantic meaning of
every internal firmware variable involved in the recovery logic.

It also does not by itself prove that the observed recovery behavior was the
cause of increased battery consumption.

Long-term battery-consumption testing remains separate from verification of the
binary patch itself.

## Reproducibility summary

For the supported firmware:

```text
Original GBL SHA-256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f

Original PROGRAM #1 SHA-256:
4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c

Patch:
PROGRAM 0x0001E1C9
DC -> E0

GBL patch location:
0x0002471D
DC -> E0

Patched PROGRAM #1 SHA-256:
d69fc6157e50b3d72b4c800c0008e7f1d7e7e4d9799cee2b0f4b2269b68fc7d4

Original GBL CRC32:
0xDC7BAB58

Patched GBL CRC32:
0x432F734F

Patched GBL SHA-256:
ac7d85c8e9239bebd3b134c4b93fc838859c613e59f7690650097da984ea7222

Total changed GBL bytes:
5
```

These values define the exact firmware transformation currently implemented by
this project.