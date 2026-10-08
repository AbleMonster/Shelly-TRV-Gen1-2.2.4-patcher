from __future__ import annotations

import argparse
import hashlib
import struct
import sys
import zlib
from pathlib import Path


# =============================================================================
# Shelly TRV Gen1 2.2.4 Beacon-Skip Firmware Patcher
# =============================================================================

PATCHER_VERSION = "0.1.0"

SUPPORTED_DEVICE = "Shelly TRV (SHTRV-01)"
SUPPORTED_VERSION = "2.2.4"
SUPPORTED_BUILD = "20240619-130912/v2.2.4@ee290818"


# -----------------------------------------------------------------------------
# Original GBL
# -----------------------------------------------------------------------------

EXPECTED_ORIGINAL_GBL_SIZE = 1_106_384

EXPECTED_ORIGINAL_GBL_SHA256 = (
    "5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f"
)

EXPECTED_ORIGINAL_GBL_CRC32 = 0xDC7BAB58


# -----------------------------------------------------------------------------
# Patched GBL
# -----------------------------------------------------------------------------

EXPECTED_PATCHED_GBL_SIZE = 1_106_384

EXPECTED_PATCHED_GBL_SHA256 = (
    "ac7d85c8e9239bebd3b134c4b93fc838859c613e59f7690650097da984ea7222"
)

EXPECTED_PATCHED_GBL_CRC32 = 0x432F734F

DEFAULT_OUTPUT_FILENAME = "SHTRV-01_2.2.4_patch.gbl"


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
# Main PROGRAM
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
# Secondary PROGRAM
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


# =============================================================================
# Utility
# =============================================================================

def separator(char: str = "=", length: int = 68) -> str:
    return char * length


def fail(message: str) -> None:
    print()
    print(separator())
    print("ERROR")
    print(separator())
    print()
    print(message)
    print()
    print("No new patched firmware file was written.")
    print()

    raise SystemExit(1)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def format_bytes(data: bytes) -> str:
    return data.hex(" ").upper()


def tag_name(tag_id: int) -> str:
    names = {
        GBL_HEADER_TAG: "HEADER",
        GBL_APPLICATION_INFO_TAG: "APPLICATION_INFO",
        GBL_BOOTLOADER_TAG: "BOOTLOADER",
        GBL_PROGRAM_TAG: "PROGRAM",
        GBL_END_TAG: "END",
    }

    return names.get(
        tag_id,
        "UNKNOWN",
    )


# =============================================================================
# CLI
# =============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patch_firmware.py",
        description=(
            "Patch the supported Shelly TRV Gen1 2.2.4 firmware "
            "to bypass the identified beacon-skip recovery branch."
        ),
        epilog=(
            "The tool only supports the exact firmware image identified "
            "by its expected size, SHA-256, GBL structure, CRC32, "
            "PROGRAM hash and patch bytes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "firmware",
        nargs="?",
        metavar="ORIGINAL.gbl",
        help="path to the original supported Shelly TRV 2.2.4 GBL",
    )

    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help=(
            "output path for the patched GBL "
            "(default: next to the input firmware)"
        ),
    )

    mode_group = parser.add_mutually_exclusive_group()

    mode_group.add_argument(
        "--verify",
        action="store_true",
        help=(
            "verify the original firmware and exit without patching"
        ),
    )

    mode_group.add_argument(
        "--analyze",
        action="store_true",
        help=(
            "analyze the original GBL and patch location without "
            "modifying or writing firmware"
        ),
    )

    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "perform the complete patch and validation process in "
            "memory without writing an output file"
        ),
    )

    parser.add_argument(
        "--diff",
        action="store_true",
        help=(
            "show detailed byte differences produced by the patch"
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {PATCHER_VERSION}",
    )

    return parser


# =============================================================================
# GBL parsing
# =============================================================================

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
            "GBL parser did not terminate exactly at end of file."
        )

    return tags


# =============================================================================
# GBL validation
# =============================================================================

def validate_gbl_structure(
    data: bytes,
    *,
    label: str,
    verbose: bool = True,
) -> list[dict]:

    tags = parse_gbl(data)

    if verbose:
        print()
        print(separator())
        print(f"{label} - GBL container validation")
        print(separator())
        print()
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

        if verbose:
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

    header = tags[0]

    version, gbl_type = struct.unpack_from(
        "<II",
        data,
        header["payload_start"],
    )

    if verbose:
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

    if verbose:
        print()
        print(f"Stored CRC32 : 0x{stored_crc:08X}")
        print(f"Calc. CRC32  : 0x{calculated_crc:08X}")

    if stored_crc != calculated_crc:
        fail(
            f"{label}: CRC32 validation failed.\n\n"
            f"Stored     : 0x{stored_crc:08X}\n"
            f"Calculated : 0x{calculated_crc:08X}"
        )

    if verbose:
        print()
        print("GBL structure : OK")
        print("GBL header    : OK")
        print("GBL CRC32     : OK")

    return tags


# =============================================================================
# PROGRAM block helpers
# =============================================================================

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


# =============================================================================
# Original firmware validation
# =============================================================================

def validate_original_firmware(
    input_path: Path,
    *,
    verbose: bool = True,
) -> tuple[bytes, list[dict], dict, dict]:

    if not input_path.exists():
        fail(
            "Input firmware does not exist.\n\n"
            f"{input_path}"
        )

    if not input_path.is_file():
        fail(
            "Input path is not a file."
        )

    try:
        original_gbl = input_path.read_bytes()
    except OSError as exc:
        fail(
            "Could not read input firmware.\n\n"
            f"{exc}"
        )

    if verbose:
        print()
        print("Firmware identity")
        print(separator("-"))
        print()
        print(f"Input file          : {input_path}")
        print(f"File size           : {len(original_gbl):,} bytes")

    if len(original_gbl) != EXPECTED_ORIGINAL_GBL_SIZE:
        fail(
            "Unsupported firmware size.\n\n"
            f"Expected: {EXPECTED_ORIGINAL_GBL_SIZE:,}\n"
            f"Found   : {len(original_gbl):,}"
        )

    original_sha = sha256_bytes(
        original_gbl
    )

    if verbose:
        print(f"SHA-256             : {original_sha}")

    if original_sha != EXPECTED_ORIGINAL_GBL_SHA256:
        fail(
            "Input firmware SHA-256 does not match the supported "
            "Shelly TRV 2.2.4 image.\n\n"
            f"Expected:\n{EXPECTED_ORIGINAL_GBL_SHA256}\n\n"
            f"Found:\n{original_sha}"
        )

    tags = validate_gbl_structure(
        original_gbl,
        label="Original GBL",
        verbose=verbose,
    )

    stored_crc = struct.unpack_from(
        "<I",
        original_gbl,
        len(original_gbl) - 4,
    )[0]

    if stored_crc != EXPECTED_ORIGINAL_GBL_CRC32:
        fail(
            "Original GBL CRC32 does not match the known supported image."
        )

    blocks = get_program_blocks(
        original_gbl,
        tags,
    )

    if len(blocks) != 2:
        fail(
            "Unexpected number of PROGRAM blocks.\n\n"
            f"Expected: 2\n"
            f"Found   : {len(blocks)}"
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

    if len(original_program) != EXPECTED_MAIN_PROGRAM_SIZE:
        fail(
            "Unexpected main PROGRAM size."
        )

    if len(secondary_program) != EXPECTED_SECONDARY_PROGRAM_SIZE:
        fail(
            "Unexpected secondary PROGRAM size."
        )

    program_sha = sha256_bytes(
        original_program
    )

    if program_sha != EXPECTED_ORIGINAL_PROGRAM_SHA256:
        fail(
            "Original main PROGRAM SHA-256 mismatch.\n\n"
            f"Expected:\n{EXPECTED_ORIGINAL_PROGRAM_SHA256}\n\n"
            f"Found:\n{program_sha}"
        )

    original_instruction = original_program[
        PATCH_INSTRUCTION_OFFSET:
        PATCH_INSTRUCTION_OFFSET + 2
    ]

    original_byte = original_program[
        PATCH_BYTE_OFFSET
    ]

    if original_instruction != EXPECTED_ORIGINAL_INSTRUCTION:
        fail(
            "Unexpected original instruction at patch location."
        )

    if original_byte != EXPECTED_ORIGINAL_BYTE:
        fail(
            "Unexpected original byte at patch location."
        )

    if verbose:
        print()
        print(separator())
        print("PROGRAM validation")
        print(separator())
        print()

        print(
            f"PROGRAM #1          : "
            f"flash 0x{main_block['flash_address']:08X}, "
            f"{len(original_program):,} bytes"
        )

        print(
            f"PROGRAM #2          : "
            f"flash 0x{secondary_block['flash_address']:08X}, "
            f"{len(secondary_program):,} bytes"
        )

        print()
        print(f"Main PROGRAM SHA    : {program_sha}")
        print(
            f"Instruction         : "
            f"{format_bytes(original_instruction)}"
        )
        print(
            f"Patch byte          : "
            f"0x{original_byte:02X} "
            f"at 0x{PATCH_BYTE_OFFSET:08X}"
        )

        print()
        print("Firmware validation : OK")

    return (
        original_gbl,
        tags,
        main_block,
        secondary_block,
    )


# =============================================================================
# Analysis mode
# =============================================================================

def show_analysis(
    input_path: Path,
    original_gbl: bytes,
    tags: list[dict],
    main_block: dict,
    secondary_block: dict,
) -> None:

    main_program = main_block[
        "program_data"
    ]

    secondary_program = secondary_block[
        "program_data"
    ]

    end_tag = tags[-1]

    stored_crc = struct.unpack_from(
        "<I",
        original_gbl,
        end_tag["payload_start"],
    )[0]

    calculated_crc = zlib.crc32(
        original_gbl[:-4]
    ) & 0xFFFFFFFF

    version, gbl_type = struct.unpack_from(
        "<II",
        original_gbl,
        tags[0]["payload_start"],
    )

    absolute_patch_offset = (
        main_block["data_start"]
        + PATCH_BYTE_OFFSET
    )

    instruction = main_program[
        PATCH_INSTRUCTION_OFFSET:
        PATCH_INSTRUCTION_OFFSET + 2
    ]

    print()
    print(separator())
    print("FIRMWARE ANALYSIS")
    print(separator())

    print()
    print("File")
    print(separator("-"))
    print(f"Path                : {input_path}")
    print(f"Size                : {len(original_gbl):,} bytes")
    print(f"SHA-256             : {sha256_bytes(original_gbl)}")
    print("Supported           : YES")

    print()
    print("GBL")
    print(separator("-"))
    print(f"Version             : 0x{version:08X}")
    print(f"Type                : 0x{gbl_type:08X}")
    print(f"Tags                : {len(tags)}")
    print(f"Stored CRC32        : 0x{stored_crc:08X}")
    print(f"Calculated CRC32    : 0x{calculated_crc:08X}")
    print("CRC valid           : YES")

    print()
    print("Tag map")
    print(separator("-"))

    for tag in tags:
        print(
            f"#{tag['number']:<2} "
            f"{tag_name(tag['tag_id']):<18} "
            f"ID 0x{tag['tag_id']:08X}  "
            f"offset 0x{tag['offset']:08X}  "
            f"length {tag['length']:,}"
        )

    print()
    print("PROGRAM #1")
    print(separator("-"))
    print(
        f"Flash address       : "
        f"0x{main_block['flash_address']:08X}"
    )
    print(
        f"GBL data offset     : "
        f"0x{main_block['data_start']:08X}"
    )
    print(
        f"Size                : "
        f"{len(main_program):,} bytes"
    )
    print(
        f"SHA-256             : "
        f"{sha256_bytes(main_program)}"
    )

    print()
    print("PROGRAM #2")
    print(separator("-"))
    print(
        f"Flash address       : "
        f"0x{secondary_block['flash_address']:08X}"
    )
    print(
        f"GBL data offset     : "
        f"0x{secondary_block['data_start']:08X}"
    )
    print(
        f"Size                : "
        f"{len(secondary_program):,} bytes"
    )
    print(
        f"SHA-256             : "
        f"{sha256_bytes(secondary_program)}"
    )

    print()
    print("Patch target")
    print(separator("-"))
    print(
        f"Program offset      : "
        f"0x{PATCH_BYTE_OFFSET:08X}"
    )
    print(
        f"GBL offset          : "
        f"0x{absolute_patch_offset:08X}"
    )
    print(
        f"Instruction offset  : "
        f"0x{PATCH_INSTRUCTION_OFFSET:08X}"
    )
    print(
        f"Current instruction : "
        f"{format_bytes(instruction)}"
    )
    print(
        f"Patched instruction : "
        f"{format_bytes(EXPECTED_PATCHED_INSTRUCTION)}"
    )
    print(
        f"Byte change         : "
        f"{EXPECTED_ORIGINAL_BYTE:02X} -> "
        f"{EXPECTED_PATCHED_BYTE:02X}"
    )
    print("Patch applicable    : YES")

    print()
    print("Expected patched result")
    print(separator("-"))
    print(
        f"PROGRAM SHA-256     : "
        f"{EXPECTED_PATCHED_PROGRAM_SHA256}"
    )
    print(
        f"GBL CRC32           : "
        f"0x{EXPECTED_PATCHED_GBL_CRC32:08X}"
    )
    print(
        f"GBL SHA-256         : "
        f"{EXPECTED_PATCHED_GBL_SHA256}"
    )

    print()


# =============================================================================
# Patch PROGRAM
# =============================================================================

def create_patched_program(
    original_program: bytes,
) -> bytes:

    if original_program[
        PATCH_BYTE_OFFSET
    ] != EXPECTED_ORIGINAL_BYTE:
        fail(
            "Pre-patch byte safety check failed."
        )

    if (
        original_program[
            PATCH_INSTRUCTION_OFFSET:
            PATCH_INSTRUCTION_OFFSET + 2
        ]
        != EXPECTED_ORIGINAL_INSTRUCTION
    ):
        fail(
            "Pre-patch instruction safety check failed."
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

    if len(patched_program) != len(original_program):
        fail(
            "Patched PROGRAM size changed unexpectedly."
        )

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

    if differences != [PATCH_BYTE_OFFSET]:
        fail(
            "Unexpected PROGRAM differences."
        )

    patched_instruction = patched_program[
        PATCH_INSTRUCTION_OFFSET:
        PATCH_INSTRUCTION_OFFSET + 2
    ]

    if patched_instruction != EXPECTED_PATCHED_INSTRUCTION:
        fail(
            "Patched instruction validation failed."
        )

    patched_sha = sha256_bytes(
        patched_program
    )

    if patched_sha != EXPECTED_PATCHED_PROGRAM_SHA256:
        fail(
            "Patched PROGRAM SHA-256 mismatch.\n\n"
            f"Expected:\n{EXPECTED_PATCHED_PROGRAM_SHA256}\n\n"
            f"Found:\n{patched_sha}"
        )

    return patched_program


# =============================================================================
# Rebuild GBL
# =============================================================================

def rebuild_gbl(
    original_gbl: bytes,
    main_block: dict,
    patched_program: bytes,
) -> bytes:

    rebuilt = bytearray(
        original_gbl
    )

    start = main_block[
        "data_start"
    ]

    end = main_block[
        "data_end"
    ]

    if end - start != len(patched_program):
        fail(
            "PROGRAM replacement range has unexpected size."
        )

    rebuilt[
        start:
        end
    ] = patched_program

    new_crc = zlib.crc32(
        rebuilt[:-4]
    ) & 0xFFFFFFFF

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

    return bytes(
        rebuilt
    )


# =============================================================================
# Final patched GBL validation
# =============================================================================

def validate_patched_gbl(
    original_gbl: bytes,
    patched_gbl: bytes,
    original_secondary_program: bytes,
) -> tuple[str, list[int]]:

    if len(patched_gbl) != EXPECTED_PATCHED_GBL_SIZE:
        fail(
            "Final patched GBL has unexpected size."
        )

    patched_tags = validate_gbl_structure(
        patched_gbl,
        label="Patched GBL",
        verbose=False,
    )

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

    if (
        sha256_bytes(patched_main_program)
        != EXPECTED_PATCHED_PROGRAM_SHA256
    ):
        fail(
            "Final GBL main PROGRAM SHA-256 mismatch."
        )

    final_instruction = patched_main_program[
        PATCH_INSTRUCTION_OFFSET:
        PATCH_INSTRUCTION_OFFSET + 2
    ]

    if final_instruction != EXPECTED_PATCHED_INSTRUCTION:
        fail(
            "Final GBL does not contain expected patched instruction."
        )

    if patched_secondary_program != original_secondary_program:
        fail(
            "Secondary PROGRAM block was modified unexpectedly."
        )

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

    expected_gbl_patch_offset = (
        patched_main["data_start"]
        + PATCH_BYTE_OFFSET
    )

    expected_differences = [
        expected_gbl_patch_offset,
        len(patched_gbl) - 4,
        len(patched_gbl) - 3,
        len(patched_gbl) - 2,
        len(patched_gbl) - 1,
    ]

    if differences != expected_differences:
        fail(
            "Final GBL contains changes at unexpected offsets."
        )

    stored_crc = struct.unpack_from(
        "<I",
        patched_gbl,
        len(patched_gbl) - 4,
    )[0]

    calculated_crc = zlib.crc32(
        patched_gbl[:-4]
    ) & 0xFFFFFFFF

    if stored_crc != EXPECTED_PATCHED_GBL_CRC32:
        fail(
            "Final stored CRC32 does not match expected value."
        )

    if calculated_crc != EXPECTED_PATCHED_GBL_CRC32:
        fail(
            "Final calculated CRC32 does not match expected value."
        )

    final_sha = sha256_bytes(
        patched_gbl
    )

    if final_sha != EXPECTED_PATCHED_GBL_SHA256:
        fail(
            "Final patched GBL SHA-256 mismatch.\n\n"
            f"Expected:\n{EXPECTED_PATCHED_GBL_SHA256}\n\n"
            f"Found:\n{final_sha}"
        )

    return final_sha, differences


# =============================================================================
# Diff output
# =============================================================================

def show_diff(
    original_gbl: bytes,
    patched_gbl: bytes,
    main_block: dict,
) -> None:

    original_program = main_block[
        "program_data"
    ]

    patched_program = patched_gbl[
        main_block["data_start"]:
        main_block["data_end"]
    ]

    program_differences = [
        index
        for index, (old, new) in enumerate(
            zip(
                original_program,
                patched_program,
            )
        )
        if old != new
    ]

    gbl_differences = [
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
    print(separator())
    print("FIRMWARE DIFFERENCES")
    print(separator())

    print()
    print("PROGRAM changes")
    print(separator("-"))

    for offset in program_differences:
        print(
            f"0x{offset:08X}: "
            f"{original_program[offset]:02X} -> "
            f"{patched_program[offset]:02X}"
        )

    print()
    print("GBL changes")
    print(separator("-"))

    for offset in gbl_differences:
        print(
            f"0x{offset:08X}: "
            f"{original_gbl[offset]:02X} -> "
            f"{patched_gbl[offset]:02X}"
        )

    print()
    print(
        f"Changed PROGRAM bytes : "
        f"{len(program_differences)}"
    )

    print(
        f"Changed GBL bytes     : "
        f"{len(gbl_differences)}"
    )


# =============================================================================
# Output
# =============================================================================

def write_output(
    output_path: Path,
    patched_gbl: bytes,
    expected_sha256: str,
) -> None:

    if output_path.exists():
        fail(
            "Output file already exists.\n\n"
            f"{output_path}\n\n"
            "Delete, rename or choose another output file."
        )

    try:
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_bytes(
            patched_gbl
        )

    except OSError as exc:
        fail(
            "Could not write output file.\n\n"
            f"{exc}"
        )

    try:
        written_data = output_path.read_bytes()

    except OSError as exc:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass

        fail(
            "Could not re-read output file.\n\n"
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
            "Data read back from disk differs from "
            "validated in-memory firmware."
        )

    if written_sha != expected_sha256:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass

        fail(
            "Output SHA-256 verification failed after writing."
        )

    print()
    print(separator())
    print("OUTPUT")
    print(separator())
    print()
    print(f"File                : {output_path}")
    print(f"Size                : {len(written_data):,} bytes")
    print(f"SHA-256             : {written_sha}")
    print()
    print("Disk write          : OK")
    print("Read-back           : OK")
    print("Read-back SHA-256   : OK")


# =============================================================================
# Modes
# =============================================================================

def run_verify(input_path: Path) -> None:
    validate_original_firmware(
        input_path,
        verbose=True,
    )

    print()
    print(separator())
    print("VERIFICATION SUCCESSFUL")
    print(separator())
    print()
    print("The firmware is the exact supported original image.")
    print("No firmware was modified or written.")
    print()


def run_analyze(input_path: Path) -> None:
    (
        original_gbl,
        tags,
        main_block,
        secondary_block,
    ) = validate_original_firmware(
        input_path,
        verbose=False,
    )

    show_analysis(
        input_path,
        original_gbl,
        tags,
        main_block,
        secondary_block,
    )

    print("Analysis completed.")
    print("No firmware was modified or written.")
    print()


def run_patch(
    input_path: Path,
    output_path: Path | None,
    *,
    dry_run: bool,
    show_differences: bool,
) -> None:

    print()
    print("Shelly TRV Gen1 2.2.4 Beacon-Skip Firmware Patcher")
    print(separator())
    print()
    print(f"Patcher version     : {PATCHER_VERSION}")

    (
        original_gbl,
        tags,
        main_block,
        secondary_block,
    ) = validate_original_firmware(
        input_path,
        verbose=True,
    )

    _ = tags

    original_program = main_block[
        "program_data"
    ]

    original_secondary_program = secondary_block[
        "program_data"
    ]

    print()
    print(separator())
    print("Creating patched PROGRAM in memory")
    print(separator())
    print()

    patched_program = create_patched_program(
        original_program
    )

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

    print(
        f"Patched PROGRAM SHA  : "
        f"{sha256_bytes(patched_program)}"
    )

    print()
    print("PROGRAM patch        : OK")

    print()
    print(separator())
    print("Rebuilding GBL in memory")
    print(separator())
    print()

    patched_gbl = rebuild_gbl(
        original_gbl,
        main_block,
        patched_program,
    )

    print(
        f"New CRC32            : "
        f"0x{EXPECTED_PATCHED_GBL_CRC32:08X}"
    )

    print(
        f"Rebuilt size         : "
        f"{len(patched_gbl):,} bytes"
    )

    print()
    print("GBL rebuild          : OK")

    final_sha, differences = validate_patched_gbl(
        original_gbl,
        patched_gbl,
        original_secondary_program,
    )

    if show_differences:
        show_diff(
            original_gbl,
            patched_gbl,
            main_block,
        )

    print()
    print(separator())
    print("FINAL VALIDATION")
    print(separator())
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
    print(
        f"Changed GBL bytes   : "
        f"{len(differences)}"
    )

    print()
    print(
        f"Final SHA-256:"
    )
    print(
        f"  {final_sha}"
    )

    if dry_run:
        print()
        print(separator())
        print("DRY RUN SUCCESSFUL")
        print(separator())
        print()
        print("The complete patch process was performed in memory.")
        print("All final validation checks passed.")
        print("No output file was written.")
        print()

        return

    if output_path is None:
        output_path = (
            input_path.parent
            / DEFAULT_OUTPUT_FILENAME
        )
    else:
        output_path = output_path.expanduser().resolve()

    write_output(
        output_path,
        patched_gbl,
        final_sha,
    )

    print()
    print(separator())
    print("PATCHING COMPLETED SUCCESSFULLY")
    print(separator())
    print()
    print(f"Device               : {SUPPORTED_DEVICE}")
    print(f"Firmware             : {SUPPORTED_VERSION}")
    print(f"Build                : {SUPPORTED_BUILD}")
    print()
    print(f"Patched firmware     : {output_path}")
    print()
    print("The tool does not flash the device automatically.")
    print()


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    parser = create_argument_parser()

    args = parser.parse_args()

    if args.firmware is None:
        parser.error(
            "ORIGINAL.gbl is required unless --help or --version is used"
        )

    input_path = Path(
        args.firmware
    ).expanduser().resolve()

    output_path = (
        Path(args.output)
        if args.output is not None
        else None
    )

    # --output makes no sense for non-writing modes.

    if args.output is not None and (
        args.verify
        or args.analyze
        or args.dry_run
    ):
        parser.error(
            "--output cannot be used with "
            "--verify, --analyze or --dry-run"
        )

    # --diff requires the patch to actually be built in memory.
    # Therefore it is useful in normal and dry-run mode, but not
    # in verify/analyze mode.

    if args.diff and (
        args.verify
        or args.analyze
    ):
        parser.error(
            "--diff cannot be used with --verify or --analyze"
        )

    if args.verify:
        run_verify(
            input_path
        )

        return

    if args.analyze:
        run_analyze(
            input_path
        )

        return

    run_patch(
        input_path,
        output_path,
        dry_run=args.dry_run,
        show_differences=args.diff,
    )


if __name__ == "__main__":
    main()