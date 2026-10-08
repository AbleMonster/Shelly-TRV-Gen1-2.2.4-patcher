# Technical Details

This document describes the technical implementation of the firmware patcher.

Detailed reverse-engineering research is maintained in the separate research repository.

## Supported firmware

Device:

`Shelly TRV (SHTRV-01)`

Firmware:

`20240619-130912/v2.2.4@ee290818`

Original firmware SHA-256:

`5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f`

## Patch

Relevant program offset:

`0x0001E1C8`

Original instruction:

```asm
31 DC    bgt 0x0001E22E
```

### Patched instruction:
```asm
31 E0    b 0x0001E22E
```

The actual byte modification occurs at program offset:
0x0001E1C9
Modification:
DC -> E0

## GBL handling

The patcher does not construct a firmware image from scratch.
It parses the original GBL container, identifies the program block mapped to
flash address 0x00000000, validates and modifies that program data, reinserts
it into a copy of the original container, and recalculates the GBL CRC32.
All unrelated firmware data must remain unchanged.


