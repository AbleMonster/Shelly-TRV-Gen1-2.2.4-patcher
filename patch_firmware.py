from __future__ import annotations

import hashlib
import struct
import sys
import zlib
from pathlib import Path


# =============================================================================
# Shelly TRV 2.2.4 Beacon-Skip Firmware Patcher
#
# Supported firmware:
#   Device : Shelly TRV (SHTRV-01)
#   Version: 2.2.4
#   Build  : 20240619-130912/v2.2.4@ee290818
#
# Patch:
#   Program offset 0x0001E1C9
#   DC -> E0
#
# Original ARM/Thumb instruction:
#   31 DC    bgt 0x0001E22E
#
# Patched ARM/Thumb instruction:
#   31 E0    b   0x0001E22E
#
# The script:
#   1. validates the exact supported original GBL,
#   2. validates the GBL structure and CRC32,
#   3. validates the main PROGRAM block,
#   4. applies the one-byte patch in memory,
#   5. validates the patched PROGRAM block,
#   6. rebuilds the GBL in memory,
#   7. recalculates the GBL CRC32,
#   8. validates the complete patched GBL,
#   9. writes the final GBL only after all checks pass.
#
# No firmware is downloaded or uploaded by this tool.
# =============================================================================


# -----------------------------------------------------------------------------
# Supported original firmware
# -----------------------------------------------------------------------------

SUPPORTED_DEVICE = "Shelly TRV (SHTRV-01)"
SUPPORTED_VERSION = "2.2.4"
SUPPORTED_BUILD = "20240619-130912/v2.2.4@ee290818"

EXPECTED_ORIGINAL_GBL_SIZE = 1_106_384

EXPECTED_ORIGINAL_GBL_SHA256 = (
    "5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f"
)

EXPECTED_ORIGINAL_GBL_CRC32 = 0xDC7BAB58


# -----------------------------------------------------------------------------
# Expected patched GBL
# -----------------------------------------------------------------------------

EXPECTED_PATCHED_GBL_SIZE = 1_106_384

EXPECTED_PATCHED_GBL_SHA256 = (
    "ac7d85c8e9239bebd3b134c4b93fc838859c613e59f7690650097da984ea7222"
)

EXPECTED_PATCHED_GBL_CRC32 = 0x432F734F

OUTPUT_FILENAME = "SHTRV-01_2.2.4_patch.gbl"


# -----------------------------------------------------------------------------
# GBL format
# -----------------------------------------------------------------------------

GBL_HEADER_TAG = 0x03A617EB
GBL_APPLICATION_INFO_TAG = 0xF40A0AF4
GBL_BOOTLOADER_TAG = 0xF50909F5
GBL_PROGRAM_TAG = 0xFD0303FD
GBL_END_TAG = 0xFC0404FC

EXPECTED_GBL_VERSION = 0x03000000
EXPECTED_GBL_TYPE = 0x00000000

EXPECTED_TAGS = [
    (GBL_HEADER_TAG, 8),
    (GBL_APPLICATION_INFO_TAG, 28),
    (GBL_BOOTLOADER_TAG, 25_868),
    (GBL_PROGRAM_TAG, 1_049_552),
    (GBL_PROGRAM_TAG, 30_876),
    (GBL_END_TAG, 4),
]


# -----------------------------------------------------------------------------
# Main PROGRAM block
# -----------------------------------------------------------------------------

EXPECTED_MAIN_FLASH_ADDRESS = 0x00000000
EXPECTED_MAIN_PROGRAM_SIZE = 1_049_548

EXPECTED_ORIGINAL_PROGRAM_SHA256 = (
    "4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c"
)

EXPECTED_PATCHED_PROGRAM_SHA256 = (
    "d69fc6157e50b3d72b4c800c0008e7f1d7e7e4d9799cee2b0f4b2269b68fc7d4"
)


# -----------------------------------------------------------------------------
# Secondary PROGRAM block
# -----------------------------------------------------------------------------

EXPECTED_SECONDARY_FLASH_ADDRESS = 0x00130A98
EXPECTED_SECONDARY_PROGRAM_SIZE = 30_872


# -----------------------------------------------------------------------------
# Patch
# -----------------------------------------------------------------------------

PATCH_INSTRUCTION_OFFSET = 0x0001E1C8
PATCH_BYTE_OFFSET = 0x0001E1C9

EXPECTED_ORIGINAL_INSTRUCTION = bytes.fromhex("31 DC")
EXPECTED_PATCHED_INSTRUCTION = bytes.fromhex("31 E0")

EXPECTED_ORIGINAL_BYTE = 0xDC
EXPECTED_PATCHED_BYTE = 0xE0


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------

def fail(message: str) -> None:
    print()
    print("=" * 68)
    print("ERROR")
    print("=" * 68)
    print()
    print(message)
    print()
    print("No new patched firmware file was written.")
    print()

    raise SystemExit(1)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def format_bytes(data: bytes) -> str:
    return data.hex(" ").upper()


# -----------------------------------------------------------------------------
# Generic GBL parser
# -----------------------------------------------------------------------------

def parse_gbl(data: bytes) -> list[dict]:
    tags: list[dict] = []

    offset = 0
    number = 0

    while offset < len(data):
        number += 1

        if offset + 8 > len(data):
            fail(
                "Truncated GBL tag header.\n\n"
                f"Tag number: {number}\n"
                f"Offset    : 0x{offset:08X}"
            )

        tag_id, length = struct.unpack_from(
            "<II",
            data,
            offset,
        )

        payload_start = offset + 8
        payload_end = payload_start + length

        if payload_end > len(data):
            fail(
                "GBL tag extends beyond the end of the file.\n\n"
                f"Tag number : {number}\n"
                f"Tag ID     : 0x{tag_id:08X}\n"
                f"Tag offset : 0x{offset:08X}\n"
                f"Length     : {length:,}"
            )

        tags.append(
            {
                "number": number,
                "offset": offset,
                "tag_id": tag_id,
                "length": length,
                "payload_start": payload_start,
                "payload_end": payload_end,
            }
        )

        offset = payload_end

    if offset != len(data):
        fail(
            "GBL parser did not terminate exactly at the end of the file."
        )

    return tags


# -----------------------------------------------------------------------------
# GBL structure validation
# -----------------------------------------------------------------------------

def validate_gbl_structure(
    data: bytes,
    *,
    label: str,
) -> list[dict]:

    print()
    print("=" * 68)
    print(f"{label} - GBL container validation")
    print("=" * 68)
    print()

    tags = parse_gbl(data)

    print(f"Tags found   : {len(tags)}")
    print()

    if len(tags) != len(EXPECTED_TAGS):
        fail(
            f"{label}: unexpected number of GBL tags.\n\n"
            f"Expected: {len(EXPECTED_TAGS)}\n"
            f"Found   : {len(tags)}"
        )

    for index, (tag, expected) in enumerate(
        zip(tags, EXPECTED_TAGS),
        start=1,
    ):
        expected_id, expected_length = expected

        print(
            f"Tag {index:<2}       : "
            f"0x{tag['tag_id']:08X}  "
            f"length {tag['length']:,}  "
            f"offset 0x{tag['offset']:08X}"
        )

        if tag["tag_id"] != expected_id:
            fail(
                f"{label}: unexpected tag #{index}.\n\n"
                f"Expected ID: 0x{expected_id:08X}\n"
                f"Found ID   : 0x{tag['tag_id']:08X}"
            )

        if tag["length"] != expected_length:
            fail(
                f"{label}: unexpected length for tag #{index}.\n\n"
                f"Expected: {expected_length:,}\n"
                f"Found   : {tag['length']:,}"
            )

    # Header

    header = tags[0]

    if header["tag_id"] != GBL_HEADER_TAG:
        fail(
            f"{label}: first tag is not the expected GBL header."
        )

    if header["length"] != 8:
        fail(
            f"{label}: unexpected GBL header length."
        )

    version, gbl_type = struct.unpack_from(
        "<II",
        data,
        header["payload_start"],
    )

    print()
    print(f"GBL version  : 0x{version:08X}")
    print(f"GBL type     : 0x{gbl_type:08X}")

    if version != EXPECTED_GBL_VERSION:
        fail(
            f"{label}: unexpected GBL version.\n\n"
            f"Expected: 0x{EXPECTED_GBL_VERSION:08X}\n"
            f"Found   : 0x{version:08X}"
        )

    if gbl_type != EXPECTED_GBL_TYPE:
        fail(
            f"{label}: unexpected GBL type/flags.\n\n"
            f"Expected: 0x{EXPECTED_GBL_TYPE:08X}\n"
            f"Found   : 0x{gbl_type:08X}"
        )

    # End tag / CRC

    end_tag = tags[-1]

    if end_tag["tag_id"] != GBL_END_TAG:
        fail(
            f"{label}: final tag is not the expected end tag."
        )

    if end_tag["length"] != 4:
        fail(
            f"{label}: end tag does not contain a 4-byte CRC32."
        )

    stored_crc = struct.unpack_from(
        "<I",
        data,
        end_tag["payload_start"],
    )[0]

    calculated_crc = zlib.crc32(
        data[:-4]
    ) & 0xFFFFFFFF

    print()
    print(f"Stored CRC32 : 0x{stored_crc:08X}")
    print(f"Calc. CRC32  : 0x{calculated_crc:08X}")

    if stored_crc != calculated_crc:
        fail(
            f"{label}: CRC32 validation failed.\n\n"
            f"Stored     : 0x{stored_crc:08X}\n"
            f"Calculated : 0x{calculated_crc:08X}"
        )

    print()
    print("GBL structure : OK")
    print("GBL header    : OK")
    print("GBL CRC32     : OK")

    return tags


# -----------------------------------------------------------------------------
# PROGRAM block helpers
# -----------------------------------------------------------------------------

def get_program_blocks(
    data: bytes,
    tags: list[dict],
) -> list[dict]:

    blocks: list[dict] = []

    for tag in tags:
        if tag["tag_id"] != GBL_PROGRAM_TAG:
            continue

        if tag["length"] < 4:
            fail(
                "PROGRAM tag is too short to contain a flash address."
            )

        flash_address = struct.unpack_from(
            "<I",
            data,
            tag["payload_start"],
        )[0]

        data_start = tag["payload_start"] + 4
        data_end = tag["payload_end"]

        program_data = data[
            data_start:
            data_end
        ]

        blocks.append(
            {
                "tag": tag,
                "flash_address": flash_address,
                "data_start": data_start,
                "data_end": data_end,
                "program_data": program_data,
            }
        )

    return blocks


def find_program_block(
    blocks: list[dict],
    flash_address: int,
) -> dict:

    matches = [
        block
        for block in blocks
        if block["flash_address"] == flash_address
    ]

    if len(matches) != 1:
        fail(
            "Could not uniquely identify PROGRAM block.\n\n"
            f"Flash address: 0x{flash_address:08X}\n"
            f"Matches      : {len(matches)}"
        )

    return matches[0]


# -----------------------------------------------------------------------------
# Validate original PROGRAM blocks
# -----------------------------------------------------------------------------

def validate_original_programs(
    data: bytes,
    tags: list[dict],
) -> tuple[bytes, bytes, dict]:

    print()
    print("=" * 68)
    print("Original PROGRAM block validation")
    print("=" * 68)
    print()

    blocks = get_program_blocks(
        data,
        tags,
    )

    print(f"PROGRAM tags : {len(blocks)}")

    if len(blocks) != 2:
        fail(
            "Unexpected number of PROGRAM blocks.\n\n"
            f"Expected: 2\n"
            f"Found   : {len(blocks)}"
        )

    for index, block in enumerate(
        blocks,
        start=1,
    ):
        print(
            f"PROGRAM #{index}   : "
            f"flash 0x{block['flash_address']:08X}, "
            f"data {len(block['program_data']):,} bytes"
        )

    main_block = find_program_block(
        blocks,
        EXPECTED_MAIN_FLASH_ADDRESS,
    )

    secondary_block = find_program_block(
        blocks,
        EXPECTED_SECONDARY_FLASH_ADDRESS,
    )

    original_program = main_block[
        "program_data"
    ]

    secondary_program = secondary_block[
        "program_data"
    ]

    # Main block

    print()
    print("-" * 68)
    print("Main PROGRAM")
    print("-" * 68)
    print()

    print(
        f"Flash address : "
        f"0x{main_block['flash_address']:08X}"
    )

    print(
        f"Program size  : "
        f"{len(original_program):,} bytes"
    )

    if len(original_program) != EXPECTED_MAIN_PROGRAM_SIZE:
        fail(
            "Unexpected main PROGRAM size.\n\n"
            f"Expected: {EXPECTED_MAIN_PROGRAM_SIZE:,}\n"
            f"Found   : {len(original_program):,}"
        )

    original_program_sha = sha256_bytes(
        original_program
    )

    print(
        f"Program SHA   : "
        f"{original_program_sha}"
    )

    if original_program_sha != EXPECTED_ORIGINAL_PROGRAM_SHA256:
        fail(
            "Original main PROGRAM SHA-256 mismatch.\n\n"
            f"Expected:\n{EXPECTED_ORIGINAL_PROGRAM_SHA256}\n\n"
            f"Found:\n{original_program_sha}"
        )

    # Patch location

    original_instruction = original_program[
        PATCH_INSTRUCTION_OFFSET:
        PATCH_INSTRUCTION_OFFSET + 2
    ]

    original_byte = original_program[
        PATCH_BYTE_OFFSET
    ]

    print()
    print(
        f"Instruction   : "
        f"{format_bytes(original_instruction)}"
    )

    print(
        f"Patch byte    : "
        f"0x{original_byte:02X} "
        f"at 0x{PATCH_BYTE_OFFSET:08X}"
    )

    if original_instruction != EXPECTED_ORIGINAL_INSTRUCTION:
        fail(
            "Unexpected original instruction at patch location.\n\n"
            f"Expected: {format_bytes(EXPECTED_ORIGINAL_INSTRUCTION)}\n"
            f"Found   : {format_bytes(original_instruction)}"
        )

    if original_byte != EXPECTED_ORIGINAL_BYTE:
        fail(
            "Unexpected original patch byte."
        )

    # Secondary block

    print()
    print("-" * 68)
    print("Secondary PROGRAM")
    print("-" * 68)
    print()

    print(
        f"Flash address : "
        f"0x{secondary_block['flash_address']:08X}"
    )

    print(
        f"Program size  : "
        f"{len(secondary_program):,} bytes"
    )

    if len(secondary_program) != EXPECTED_SECONDARY_PROGRAM_SIZE:
        fail(
            "Unexpected secondary PROGRAM size.\n\n"
            f"Expected: {EXPECTED_SECONDARY_PROGRAM_SIZE:,}\n"
            f"Found   : {len(secondary_program):,}"
        )

    print()
    print("Main PROGRAM      : OK")
    print("Main PROGRAM SHA  : OK")
    print("Patch location    : OK")
    print("Secondary PROGRAM : OK")

    return (
        original_program,
        secondary_program,
        main_block,
    )


# -----------------------------------------------------------------------------
# Patch main PROGRAM
# -----------------------------------------------------------------------------

def create_patched_program(
    original_program: bytes,
) -> bytes:

    print()
    print("=" * 68)
    print("Creating patched PROGRAM in memory")
    print("=" * 68)
    print()

    if original_program[PATCH_BYTE_OFFSET] != EXPECTED_ORIGINAL_BYTE:
        fail(
            "Pre-patch safety check failed."
        )

    if (
        original_program[
            PATCH_INSTRUCTION_OFFSET:
            PATCH_INSTRUCTION_OFFSET + 2
        ]
        != EXPECTED_ORIGINAL_INSTRUCTION
    ):
        fail(
            "Pre-patch instruction check failed."
        )

    patched = bytearray(
        original_program
    )

    patched[
        PATCH_BYTE_OFFSET
    ] = EXPECTED_PATCHED_BYTE

    patched_program = bytes(
        patched
    )

    # Size

    if len(patched_program) != len(original_program):
        fail(
            "Patched PROGRAM size changed unexpectedly."
        )

    # Differences

    differences = [
        index
        for index, (old, new) in enumerate(
            zip(
                original_program,
                patched_program,
            )
        )
        if old != new
    ]

    print(
        f"Changed bytes       : "
        f"{len(differences)}"
    )

    if differences != [PATCH_BYTE_OFFSET]:
        fail(
            "Unexpected PROGRAM differences.\n\n"
            f"Expected only: 0x{PATCH_BYTE_OFFSET:08X}\n"
            f"Found         : "
            + ", ".join(
                f"0x{x:08X}"
                for x in differences
            )
        )

    print(
        f"Changed offset      : "
        f"0x{differences[0]:08X}"
    )

    old_byte = original_program[
        PATCH_BYTE_OFFSET
    ]

    new_byte = patched_program[
        PATCH_BYTE_OFFSET
    ]

    print(
        f"Byte change         : "
        f"{old_byte:02X} -> {new_byte:02X}"
    )

    if (
        old_byte != EXPECTED_ORIGINAL_BYTE
        or new_byte != EXPECTED_PATCHED_BYTE
    ):
        fail(
            "Unexpected byte transition."
        )

    # Instruction

    patched_instruction = patched_program[
        PATCH_INSTRUCTION_OFFSET:
        PATCH_INSTRUCTION_OFFSET + 2
    ]

    print(
        f"Patched instruction : "
        f"{format_bytes(patched_instruction)}"
    )

    if patched_instruction != EXPECTED_PATCHED_INSTRUCTION:
        fail(
            "Patched instruction validation failed."
        )

    # Hash

    patched_sha = sha256_bytes(
        patched_program
    )

    print(
        f"Patched SHA-256     : "
        f"{patched_sha}"
    )

    if patched_sha != EXPECTED_PATCHED_PROGRAM_SHA256:
        fail(
            "Patched PROGRAM SHA-256 mismatch.\n\n"
            f"Expected:\n{EXPECTED_PATCHED_PROGRAM_SHA256}\n\n"
            f"Found:\n{patched_sha}"
        )

    # Original still unchanged

    if original_program[PATCH_BYTE_OFFSET] != EXPECTED_ORIGINAL_BYTE:
        fail(
            "Original PROGRAM was unexpectedly modified."
        )

    print()
    print("PROGRAM patch       : OK")
    print("Changed byte count  : OK")
    print("Changed offset      : OK")
    print("Patched instruction : OK")
    print("Patched SHA-256     : OK")

    return patched_program


# -----------------------------------------------------------------------------
# Rebuild GBL in memory
# -----------------------------------------------------------------------------

def rebuild_gbl(
    original_gbl: bytes,
    main_block: dict,
    patched_program: bytes,
) -> bytes:

    print()
    print("=" * 68)
    print("Rebuilding patched GBL in memory")
    print("=" * 68)
    print()

    if len(patched_program) != EXPECTED_MAIN_PROGRAM_SIZE:
        fail(
            "Refusing to rebuild GBL: patched PROGRAM has wrong size."
        )

    rebuilt = bytearray(
        original_gbl
    )

    program_start = main_block[
        "data_start"
    ]

    program_end = main_block[
        "data_end"
    ]

    if (
        program_end - program_start
        != len(patched_program)
    ):
        fail(
            "PROGRAM replacement range has unexpected size."
        )

    # Replace only main PROGRAM data

    rebuilt[
        program_start:
        program_end
    ] = patched_program

    # Recalculate CRC32.
    #
    # The final four bytes contain the stored CRC.
    # CRC is calculated over everything before those four bytes.

    new_crc = zlib.crc32(
        rebuilt[:-4]
    ) & 0xFFFFFFFF

    print(
        f"New CRC32           : "
        f"0x{new_crc:08X}"
    )

    if new_crc != EXPECTED_PATCHED_GBL_CRC32:
        fail(
            "Generated CRC32 does not match expected patched CRC32.\n\n"
            f"Expected: 0x{EXPECTED_PATCHED_GBL_CRC32:08X}\n"
            f"Found   : 0x{new_crc:08X}"
        )

    rebuilt[-4:] = struct.pack(
        "<I",
        new_crc,
    )

    patched_gbl = bytes(
        rebuilt
    )

    if len(patched_gbl) != len(original_gbl):
        fail(
            "Rebuilt GBL size differs from original."
        )

    print(
        f"Rebuilt GBL size    : "
        f"{len(patched_gbl):,} bytes"
    )

    print("GBL rebuild         : OK")

    return patched_gbl


# -----------------------------------------------------------------------------
# Final patched GBL validation
# -----------------------------------------------------------------------------

def validate_patched_gbl(
    original_gbl: bytes,
    patched_gbl: bytes,
    original_secondary_program: bytes,
) -> str:

    print()
    print("=" * 68)
    print("Final patched GBL validation")
    print("=" * 68)
    print()

    # Size

    if len(patched_gbl) != EXPECTED_PATCHED_GBL_SIZE:
        fail(
            "Final patched GBL has unexpected size.\n\n"
            f"Expected: {EXPECTED_PATCHED_GBL_SIZE:,}\n"
            f"Found   : {len(patched_gbl):,}"
        )

    print(
        f"File size           : "
        f"{len(patched_gbl):,} bytes"
    )

    # Parse entire rebuilt GBL and validate CRC

    patched_tags = validate_gbl_structure(
        patched_gbl,
        label="Patched GBL",
    )

    # PROGRAM blocks

    patched_blocks = get_program_blocks(
        patched_gbl,
        patched_tags,
    )

    if len(patched_blocks) != 2:
        fail(
            "Final GBL does not contain exactly two PROGRAM blocks."
        )

    patched_main = find_program_block(
        patched_blocks,
        EXPECTED_MAIN_FLASH_ADDRESS,
    )

    patched_secondary = find_program_block(
        patched_blocks,
        EXPECTED_SECONDARY_FLASH_ADDRESS,
    )

    patched_main_program = patched_main[
        "program_data"
    ]

    patched_secondary_program = patched_secondary[
        "program_data"
    ]

    # Main PROGRAM hash

    final_program_sha = sha256_bytes(
        patched_main_program
    )

    print()
    print(
        f"Main PROGRAM SHA    : "
        f"{final_program_sha}"
    )

    if final_program_sha != EXPECTED_PATCHED_PROGRAM_SHA256:
        fail(
            "Final GBL main PROGRAM SHA-256 mismatch."
        )

    # Patch instruction

    final_instruction = patched_main_program[
        PATCH_INSTRUCTION_OFFSET:
        PATCH_INSTRUCTION_OFFSET + 2
    ]

    print(
        f"Final instruction   : "
        f"{format_bytes(final_instruction)}"
    )

    if final_instruction != EXPECTED_PATCHED_INSTRUCTION:
        fail(
            "Final GBL does not contain the expected patched instruction."
        )

    # Secondary PROGRAM must be identical

    if patched_secondary_program != original_secondary_program:
        fail(
            "Secondary PROGRAM block was modified unexpectedly."
        )

    print(
        "Secondary PROGRAM   : unchanged"
    )

    # -------------------------------------------------------------------------
    # Compare complete original and patched GBL
    # -------------------------------------------------------------------------

    differences = [
        index
        for index, (old, new) in enumerate(
            zip(
                original_gbl,
                patched_gbl,
            )
        )
        if old != new
    ]

    print()
    print(
        f"GBL changed bytes   : "
        f"{len(differences)}"
    )

    if len(differences) != 5:
        fail(
            "Unexpected number of changed bytes in final GBL.\n\n"
            f"Expected: 5\n"
            f"Found   : {len(differences)}"
        )

    # Expected absolute GBL offset of firmware patch

    expected_gbl_patch_offset = (
        patched_main["data_start"]
        + PATCH_BYTE_OFFSET
    )

    # Final four bytes are the CRC32.

    expected_difference_offsets = [
        expected_gbl_patch_offset,
        len(patched_gbl) - 4,
        len(patched_gbl) - 3,
        len(patched_gbl) - 2,
        len(patched_gbl) - 1,
    ]

    if differences != expected_difference_offsets:
        fail(
            "Final GBL contains changes at unexpected offsets.\n\n"
            "Expected:\n"
            + "\n".join(
                f"  0x{x:08X}"
                for x in expected_difference_offsets
            )
            + "\n\nFound:\n"
            + "\n".join(
                f"  0x{x:08X}"
                for x in differences
            )
        )

    print()
    print("Changed offsets:")

    for offset in differences:
        print(
            f"  0x{offset:08X}: "
            f"{original_gbl[offset]:02X} -> "
            f"{patched_gbl[offset]:02X}"
        )

    # Verify actual patch byte at absolute GBL offset

    if (
        original_gbl[expected_gbl_patch_offset]
        != EXPECTED_ORIGINAL_BYTE
    ):
        fail(
            "Original GBL patch byte is unexpected."
        )

    if (
        patched_gbl[expected_gbl_patch_offset]
        != EXPECTED_PATCHED_BYTE
    ):
        fail(
            "Final GBL patch byte is unexpected."
        )

    # Verify final stored CRC

    stored_crc = struct.unpack_from(
        "<I",
        patched_gbl,
        len(patched_gbl) - 4,
    )[0]

    calculated_crc = zlib.crc32(
        patched_gbl[:-4]
    ) & 0xFFFFFFFF

    print()
    print(
        f"Final stored CRC32  : "
        f"0x{stored_crc:08X}"
    )

    print(
        f"Final calc. CRC32   : "
        f"0x{calculated_crc:08X}"
    )

    if stored_crc != EXPECTED_PATCHED_GBL_CRC32:
        fail(
            "Final stored CRC32 does not match expected value."
        )

    if calculated_crc != EXPECTED_PATCHED_GBL_CRC32:
        fail(
            "Final calculated CRC32 does not match expected value."
        )

    # Final SHA-256

    final_sha = sha256_bytes(
        patched_gbl
    )

    print()
    print(
        f"Final GBL SHA-256   : "
        f"{final_sha}"
    )

    if final_sha != EXPECTED_PATCHED_GBL_SHA256:
        fail(
            "Final patched GBL SHA-256 mismatch.\n\n"
            f"Expected:\n{EXPECTED_PATCHED_GBL_SHA256}\n\n"
            f"Found:\n{final_sha}"
        )

    print()
    print("Final file size     : OK")
    print("Final GBL structure : OK")
    print("Final GBL CRC32     : OK")
    print("Main PROGRAM        : OK")
    print("Secondary PROGRAM   : unchanged")
    print("Changed byte count  : OK")
    print("Changed offsets     : OK")
    print("Final GBL SHA-256   : OK")

    return final_sha


# -----------------------------------------------------------------------------
# Safely write final output
# -----------------------------------------------------------------------------

def write_output(
    output_path: Path,
    patched_gbl: bytes,
    expected_sha256: str,
) -> None:

    print()
    print("=" * 68)
    print("Writing final patched firmware")
    print("=" * 68)
    print()

    # Do not silently overwrite an existing file.

    if output_path.exists():
        fail(
            "Output file already exists.\n\n"
            f"{output_path}\n\n"
            "Delete or rename the existing file before running "
            "the patcher again."
        )

    try:
        output_path.write_bytes(
            patched_gbl
        )
    except OSError as exc:
        fail(
            "Could not write output file.\n\n"
            f"{exc}"
        )

    # -------------------------------------------------------------------------
    # Re-read the physical file from disk.
    #
    # This verifies what was actually written, rather than only the
    # in-memory object.
    # -------------------------------------------------------------------------

    try:
        written_data = output_path.read_bytes()
    except OSError as exc:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass

        fail(
            "Could not re-read output file for final verification.\n\n"
            f"{exc}"
        )

    written_sha = sha256_bytes(
        written_data
    )

    if written_data != patched_gbl:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass

        fail(
            "Data read back from the output file differs from "
            "the validated in-memory firmware."
        )

    if written_sha != expected_sha256:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass

        fail(
            "Output file SHA-256 verification failed after writing.\n\n"
            f"Expected:\n{expected_sha256}\n\n"
            f"Found:\n{written_sha}"
        )

    print(
        f"Output file         : "
        f"{output_path}"
    )

    print(
        f"File size           : "
        f"{len(written_data):,} bytes"
    )

    print(
        f"SHA-256             : "
        f"{written_sha}"
    )

    print()
    print("Disk write          : OK")
    print("Read-back           : OK")
    print("Read-back SHA-256   : OK")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> None:

    print()
    print("Shelly TRV 2.2.4 Beacon-Skip Firmware Patcher")
    print("=" * 68)
    print()

    # -------------------------------------------------------------------------
    # Input argument
    # -------------------------------------------------------------------------

    if len(sys.argv) != 2:
        print("Usage:")
        print()
        print(
            f'  python {Path(sys.argv[0]).name} '
            '"<path-to-original-firmware.gbl>"'
        )
        print()

        raise SystemExit(2)

    input_path = Path(
        sys.argv[1]
    ).expanduser().resolve()

    print(
        f"Input file          : "
        f"{input_path}"
    )

    if not input_path.exists():
        fail(
            "Input firmware does not exist.\n\n"
            f"{input_path}"
        )

    if not input_path.is_file():
        fail(
            "Input path is not a file."
        )

    # -------------------------------------------------------------------------
    # Read original GBL
    # -------------------------------------------------------------------------

    try:
        original_gbl = input_path.read_bytes()
    except OSError as exc:
        fail(
            "Could not read input firmware.\n\n"
            f"{exc}"
        )

    # -------------------------------------------------------------------------
    # Exact original firmware identity
    # -------------------------------------------------------------------------

    print(
        f"File size           : "
        f"{len(original_gbl):,} bytes"
    )

    if len(original_gbl) != EXPECTED_ORIGINAL_GBL_SIZE:
        fail(
            "Unsupported firmware size.\n\n"
            f"Expected: {EXPECTED_ORIGINAL_GBL_SIZE:,}\n"
            f"Found   : {len(original_gbl):,}"
        )

    print(
        "SHA-256             : calculating..."
    )

    original_sha = sha256_bytes(
        original_gbl
    )

    print(
        f"SHA-256             : "
        f"{original_sha}"
    )

    if original_sha != EXPECTED_ORIGINAL_GBL_SHA256:
        fail(
            "Input firmware SHA-256 does not match the supported "
            "Shelly TRV 2.2.4 firmware.\n\n"
            f"Expected:\n{EXPECTED_ORIGINAL_GBL_SHA256}\n\n"
            f"Found:\n{original_sha}"
        )

    print()
    print("Firmware identity verification successful.")
    print()
    print(f"Device               : {SUPPORTED_DEVICE}")
    print(f"Firmware             : {SUPPORTED_VERSION}")
    print(f"Build                : {SUPPORTED_BUILD}")
    print("File size            : OK")
    print("SHA-256              : OK")

    # -------------------------------------------------------------------------
    # Original GBL structure
    # -------------------------------------------------------------------------

    original_tags = validate_gbl_structure(
        original_gbl,
        label="Original GBL",
    )

    original_stored_crc = struct.unpack_from(
        "<I",
        original_gbl,
        len(original_gbl) - 4,
    )[0]

    if original_stored_crc != EXPECTED_ORIGINAL_GBL_CRC32:
        fail(
            "Original GBL CRC32 does not match the known supported image.\n\n"
            f"Expected: 0x{EXPECTED_ORIGINAL_GBL_CRC32:08X}\n"
            f"Found   : 0x{original_stored_crc:08X}"
        )

    # -------------------------------------------------------------------------
    # Original PROGRAM blocks
    # -------------------------------------------------------------------------

    (
        original_program,
        original_secondary_program,
        main_block,
    ) = validate_original_programs(
        original_gbl,
        original_tags,
    )

    # -------------------------------------------------------------------------
    # Patch main PROGRAM in memory
    # -------------------------------------------------------------------------

    patched_program = create_patched_program(
        original_program
    )

    # -------------------------------------------------------------------------
    # Rebuild GBL in memory
    # -------------------------------------------------------------------------

    patched_gbl = rebuild_gbl(
        original_gbl,
        main_block,
        patched_program,
    )

    # -------------------------------------------------------------------------
    # Validate complete patched GBL
    # -------------------------------------------------------------------------

    final_sha = validate_patched_gbl(
        original_gbl,
        patched_gbl,
        original_secondary_program,
    )

    # -------------------------------------------------------------------------
    # Everything has passed.
    #
    # Only NOW are we allowed to create the output file.
    # -------------------------------------------------------------------------

    output_path = (
        input_path.parent
        / OUTPUT_FILENAME
    )

    write_output(
        output_path,
        patched_gbl,
        final_sha,
    )

    # -------------------------------------------------------------------------
    # Success
    # -------------------------------------------------------------------------

    print()
    print("=" * 68)
    print("PATCHING COMPLETED SUCCESSFULLY")
    print("=" * 68)
    print()

    print(f"Device               : {SUPPORTED_DEVICE}")
    print(f"Firmware             : {SUPPORTED_VERSION}")
    print(f"Build                : {SUPPORTED_BUILD}")

    print()
    print(
        f"Patch                : "
        f"0x{PATCH_BYTE_OFFSET:08X} "
        f"{EXPECTED_ORIGINAL_BYTE:02X} -> "
        f"{EXPECTED_PATCHED_BYTE:02X}"
    )

    print(
        f"Instruction          : "
        f"{format_bytes(EXPECTED_ORIGINAL_INSTRUCTION)} -> "
        f"{format_bytes(EXPECTED_PATCHED_INSTRUCTION)}"
    )

    print()
    print("Original GBL         : VERIFIED")
    print("Original CRC32       : VERIFIED")
    print("Original PROGRAM     : VERIFIED")
    print("Patch location       : VERIFIED")
    print("Patched PROGRAM      : VERIFIED")
    print("Secondary PROGRAM    : UNCHANGED")
    print("Rebuilt GBL          : VERIFIED")
    print("Final CRC32          : VERIFIED")
    print("Final SHA-256        : VERIFIED")
    print("Disk read-back       : VERIFIED")

    print()
    print(
        f"Patched firmware:"
    )
    print(
        f"  {output_path}"
    )

    print()
    print(
        f"SHA-256:"
    )
    print(
        f"  {final_sha}"
    )

    print()
    print("The tool does not flash the device automatically.")
    print()


if __name__ == "__main__":
    main()