#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
import zlib
from pathlib import Path


# =============================================================================
# Tool identity
# =============================================================================

PATCHER_VERSION = "1.0-beta"
PATCHER_REVISION = "2"

SUPPORTED_DEVICE = "Shelly TRV Gen1"
SUPPORTED_VERSION = "2.2.4"
SUPPORTED_BUILD = "20240619-130912/v2.2.4@ee290818"


# =============================================================================
# Known firmware identity
# =============================================================================

EXPECTED_ORIGINAL_GBL_SIZE = 1_106_384

EXPECTED_ORIGINAL_GBL_SHA256 = (
    "5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f"
)

EXPECTED_ORIGINAL_GBL_CRC32 = 0xDC7BAB58

EXPECTED_PATCHED_GBL_SHA256 = (
    "7adbb31d6b7faa8b9290d7b3436af45d42af9c3602a7195cafab774ded84ac61"
)

EXPECTED_PATCHED_GBL_CRC32 = 0xBAEB8265

DEFAULT_OUTPUT_FILENAME = "SHTRV-01_2.2.4_beacon_mdns_patch.gbl"
TARGET_DIRECTORY_NAME = "target"
DEFAULT_INPUT_FILENAME = "SHTRV-01_build_2.2.4.gbl"

# =============================================================================
# Known PROGRAM identity
# =============================================================================

EXPECTED_MAIN_PROGRAM_SIZE = 1_049_548

EXPECTED_ORIGINAL_PROGRAM_SHA256 = (
    "4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c"
)

EXPECTED_PATCHED_PROGRAM_SHA256 = (
    "06742a2632a3d45cf697b8be85045914d004f30644dad17b3d0d20012c87c61b"
)


# =============================================================================
# Patch definitions
# =============================================================================

PATCHES = [
    {
        "name": "Patch B - periodic mDNS restart",
        "instruction_offset": 0x0001E0F0,
        "byte_offset": 0x0001E0F1,
        "original_instruction": bytes.fromhex("02 D0"),
        "patched_instruction": bytes.fromhex("02 E0"),
        "original_byte": 0xD0,
        "patched_byte": 0xE0,
    },
    {
        "name": "Patch A - beacon-skip recovery",
        "instruction_offset": 0x0001E1C8,
        "byte_offset": 0x0001E1C9,
        "original_instruction": bytes.fromhex("31 DC"),
        "patched_instruction": bytes.fromhex("31 E0"),
        "original_byte": 0xDC,
        "patched_byte": 0xE0,
    },
]


# =============================================================================
# GBL tag IDs
# =============================================================================

GBL_HEADER_TAG = 0x03A617EB
GBL_PROGRAM_TAG = 0xFD0303FD
GBL_END_TAG = 0xFC0404FC

EXPECTED_TAGS = [
    GBL_HEADER_TAG,
    0xF40A0AF4,
    0xF50909F5,
    GBL_PROGRAM_TAG,
    GBL_PROGRAM_TAG,
    GBL_END_TAG,
]


# =============================================================================
# General helpers
# =============================================================================

def fail(message: str) -> None:
    print()
    print("ERROR")
    print("=" * 79)
    print(message)
    print()
    raise SystemExit(1)


def separator(char: str = "=") -> str:
    return char * 79


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def format_bytes(data: bytes) -> str:
    return " ".join(f"{value:02X}" for value in data)


def read_file(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        fail(f"Firmware file not found:\n{path}")
    except OSError as exc:
        fail(
            f"Could not read firmware file:\n"
            f"{path}\n\n"
            f"{exc}"
        )


# =============================================================================
# Command line
# =============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patch_firmware_v.1.0.py",
        description=(
            "Patch the supported Shelly TRV Gen1 2.2.4 firmware "
            "to apply the beacon-skip recovery and periodic mDNS restart bypasses."
        ),
        epilog=(
            "The tool only supports the exact firmware image identified "
            "by its expected size, SHA-256, GBL structure, CRC32, "
            "PROGRAM hash and both patch locations."
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
        help="verify the original firmware and exit without patching",
    )

    mode_group.add_argument(
        "--analyze",
        action="store_true",
        help=(
            "analyze the original GBL and patch locations without "
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
        help="show detailed byte differences produced by both patches",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {PATCHER_VERSION} revision {PATCHER_REVISION}",
    )

    return parser


# =============================================================================
# GBL parsing
# =============================================================================

def tag_name(tag_id: int) -> str:
    names = {
        0x03A617EB: "HEADER",
        0xF60808F6: "APP_INFO",
        0xF40A0AF4: "BOOTLOADER",
        0xF50909F5: "METADATA",
        0xFD0303FD: "PROGRAM",
        0xFC0404FC: "END",
    }

    return names.get(
        tag_id,
        "UNKNOWN",
    )


def parse_gbl(data: bytes) -> list[dict]:
    tags: list[dict] = []

    offset = 0
    number = 0

    while offset < len(data):
        if offset + 8 > len(data):
            fail(
                f"Truncated GBL tag header at file offset "
                f"0x{offset:08X}."
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
                f"GBL tag at 0x{offset:08X} exceeds file size."
            )

        number += 1

        tags.append(
            {
                "number": number,
                "tag_id": tag_id,
                "length": length,
                "offset": offset,
                "payload_start": payload_start,
                "payload_end": payload_end,
            }
        )

        offset = payload_end

        if tag_id == GBL_END_TAG:
            break

    if not tags:
        fail(
            "No GBL tags found."
        )

    if offset != len(data):
        fail(
            "Unexpected trailing data after final GBL tag.\n\n"
            f"Parsed size : {offset}\n"
            f"File size   : {len(data)}"
        )

    actual_tags = [
        tag["tag_id"]
        for tag in tags
    ]

    if actual_tags != EXPECTED_TAGS:
        fail(
            "Unexpected GBL tag structure.\n\n"
            f"Expected: "
            f"{[f'0x{x:08X}' for x in EXPECTED_TAGS]}\n"
            f"Found   : "
            f"{[f'0x{x:08X}' for x in actual_tags]}"
        )

    if tags[0]["tag_id"] != GBL_HEADER_TAG:
        fail(
            "Unexpected first GBL tag.\n\n"
            f"Expected: 0x{GBL_HEADER_TAG:08X}\n"
            f"Found   : 0x{tags[0]['tag_id']:08X}"
        )

    if tags[-1]["tag_id"] != GBL_END_TAG:
        fail(
            "GBL END tag not found."
        )

    if tags[-1]["length"] != 4:
        fail(
            "Unexpected GBL END tag length.\n\n"
            f"Expected: 4\n"
            f"Found   : {tags[-1]['length']}"
        )

    return tags


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

        blocks.append(
            {
                "tag": tag,
                "flash_address": flash_address,
                "data_start": data_start,
                "data_end": data_end,
                "program_data": data[data_start:data_end],
            }
        )

    return blocks


def locate_supported_programs(
    data: bytes,
    tags: list[dict],
) -> tuple[dict, dict]:
    blocks = get_program_blocks(
        data,
        tags,
    )

    if len(blocks) != 2:
        fail(
            "Unexpected number of PROGRAM blocks.\n\n"
            "This patcher expects exactly two PROGRAM tags.\n"
            f"Found: {len(blocks)}"
        )

    main_block = None
    secondary_block = None

    for block in blocks:
        if len(block["program_data"]) == EXPECTED_MAIN_PROGRAM_SIZE:
            if main_block is not None:
                fail(
                    "More than one PROGRAM block matches the expected "
                    "main PROGRAM size."
                )

            main_block = block
        else:
            if secondary_block is not None:
                fail(
                    "Unexpected PROGRAM layout: more than one secondary "
                    "PROGRAM block found."
                )

            secondary_block = block

    if main_block is None:
        fail(
            "Expected main PROGRAM block not found.\n\n"
            f"Expected PROGRAM size: "
            f"{EXPECTED_MAIN_PROGRAM_SIZE}"
        )

    if secondary_block is None:
        fail(
            "Secondary PROGRAM block not found."
        )

    return (
        main_block,
        secondary_block,
    )


# =============================================================================
# Original firmware validation
# =============================================================================

def validate_original_firmware(
    input_path: Path,
    original_gbl: bytes,
    *,
    verbose: bool = True,
) -> tuple[list[dict], dict, dict]:

    if len(original_gbl) != EXPECTED_ORIGINAL_GBL_SIZE:
        fail(
            "Unsupported firmware size.\n\n"
            f"Expected: {EXPECTED_ORIGINAL_GBL_SIZE} bytes\n"
            f"Found   : {len(original_gbl)} bytes"
        )

    original_sha = sha256_bytes(
        original_gbl
    )

    if original_sha != EXPECTED_ORIGINAL_GBL_SHA256:
        fail(
            "Unsupported firmware SHA-256.\n\n"
            "This tool only patches the exact supported Shelly TRV "
            "Gen1 2.2.4 image.\n\n"
            f"Expected:\n"
            f"{EXPECTED_ORIGINAL_GBL_SHA256}\n\n"
            f"Found:\n"
            f"{original_sha}"
        )

    tags = parse_gbl(
        original_gbl
    )

    end_tag = tags[-1]

    stored_crc = struct.unpack_from(
        "<I",
        original_gbl,
        end_tag["payload_start"],
    )[0]

    calculated_crc = (
        zlib.crc32(
            original_gbl[:-4]
        )
        & 0xFFFFFFFF
    )

    if stored_crc != calculated_crc:
        fail(
            "Original GBL CRC32 is invalid.\n\n"
            f"Stored     : 0x{stored_crc:08X}\n"
            f"Calculated : 0x{calculated_crc:08X}"
        )

    if stored_crc != EXPECTED_ORIGINAL_GBL_CRC32:
        fail(
            "Unexpected original GBL CRC32.\n\n"
            f"Expected: 0x{EXPECTED_ORIGINAL_GBL_CRC32:08X}\n"
            f"Found   : 0x{stored_crc:08X}"
        )

    main_block, secondary_block = locate_supported_programs(
        original_gbl,
        tags,
    )

    original_program = main_block[
        "program_data"
    ]

    program_sha = sha256_bytes(
        original_program
    )

    if program_sha != EXPECTED_ORIGINAL_PROGRAM_SHA256:
        fail(
            "Unexpected main PROGRAM SHA-256.\n\n"
            f"Expected:\n"
            f"{EXPECTED_ORIGINAL_PROGRAM_SHA256}\n\n"
            f"Found:\n"
            f"{program_sha}"
        )

    for patch in PATCHES:
        instruction_offset = patch[
            "instruction_offset"
        ]

        byte_offset = patch[
            "byte_offset"
        ]

        original_instruction = original_program[
            instruction_offset:
            instruction_offset + 2
        ]

        original_byte = original_program[
            byte_offset
        ]

        if original_instruction != patch["original_instruction"]:
            fail(
                f"{patch['name']}: unexpected original instruction "
                f"at PROGRAM 0x{instruction_offset:08X}.\n\n"
                f"Expected: "
                f"{format_bytes(patch['original_instruction'])}\n"
                f"Found   : "
                f"{format_bytes(original_instruction)}"
            )

        if original_byte != patch["original_byte"]:
            fail(
                f"{patch['name']}: unexpected original byte "
                f"at PROGRAM 0x{byte_offset:08X}.\n\n"
                f"Expected: "
                f"0x{patch['original_byte']:02X}\n"
                f"Found   : "
                f"0x{original_byte:02X}"
            )

    if verbose:
        print()
        print(separator())
        print("ORIGINAL FIRMWARE VERIFICATION")
        print(separator())

        print()
        print(
            f"File                : "
            f"{input_path}"
        )

        print(
            f"Size                : "
            f"{len(original_gbl):,} bytes"
        )

        print(
            f"GBL SHA-256         : "
            f"{original_sha}"
        )

        print(
            f"GBL CRC32           : "
            f"0x{stored_crc:08X}"
        )

        print()

        print(
            f"Main PROGRAM SHA    : "
            f"{program_sha}"
        )

        for patch in PATCHES:
            instruction_offset = patch[
                "instruction_offset"
            ]

            byte_offset = patch[
                "byte_offset"
            ]

            instruction = original_program[
                instruction_offset:
                instruction_offset + 2
            ]

            print()
            print(
                patch["name"]
            )

            print(
                f"  Instruction       : "
                f"{format_bytes(instruction)}"
            )

            print(
                f"  Patch byte        : "
                f"0x{original_program[byte_offset]:02X} "
                f"at 0x{byte_offset:08X}"
            )

        print()
        print(
            "Firmware validation : OK"
        )

    return (
        tags,
        main_block,
        secondary_block,
    )


# =============================================================================
# Read-only analysis
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

    calculated_crc = (
        zlib.crc32(
            original_gbl[:-4]
        )
        & 0xFFFFFFFF
    )

    version, gbl_type = struct.unpack_from(
        "<II",
        original_gbl,
        tags[0]["payload_start"],
    )

    main_flash_end = (
        main_block["flash_address"]
        + len(main_program)
        - 1
    )

    secondary_flash_end = (
        secondary_block["flash_address"]
        + len(secondary_program)
        - 1
    )

    total_program = (
        len(main_program)
        + len(secondary_program)
    )

    print()
    print(separator())
    print("FIRMWARE ANALYSIS")
    print(separator())

    print()
    print("Mode                : READ-ONLY")
    print("Writes performed    : NO")
    print("Firmware modified   : NO")

    print()
    print("Identity")
    print(separator("-"))

    print(
        f"Device              : "
        f"{SUPPORTED_DEVICE}"
    )

    print(
        f"Firmware            : "
        f"{SUPPORTED_VERSION}"
    )

    print(
        f"Build               : "
        f"{SUPPORTED_BUILD}"
    )

    print(
        f"Path                : "
        f"{input_path}"
    )

    print(
        f"Size                : "
        f"{len(original_gbl):,} bytes"
    )

    print(
        f"SHA-256             : "
        f"{sha256_bytes(original_gbl)}"
    )

    print(
        "Supported           : YES"
    )

    print()
    print("GBL container")
    print(separator("-"))

    print(
        f"Version             : "
        f"0x{version:08X}"
    )

    print(
        f"Type / flags        : "
        f"0x{gbl_type:08X}"
    )

    print(
        f"Tags                : "
        f"{len(tags)}"
    )

    print(
        f"Stored CRC32        : "
        f"0x{stored_crc:08X}"
    )

    print(
        f"Calculated CRC32    : "
        f"0x{calculated_crc:08X}"
    )

    print(
        "CRC valid           : YES"
    )

    print(
        f"CRC covered range   : "
        f"0x00000000 - "
        f"0x{len(original_gbl) - 5:08X}"
    )

    print(
        f"Stored CRC range    : "
        f"0x{len(original_gbl) - 4:08X} - "
        f"0x{len(original_gbl) - 1:08X}"
    )

    print()
    print("GBL tag map")
    print(separator("-"))

    for tag in tags:
        print(
            f"#{tag['number']:<2} "
            f"{tag_name(tag['tag_id']):<18} "
            f"ID 0x{tag['tag_id']:08X}"
        )

        print(
            f"    Tag range        : "
            f"0x{tag['offset']:08X} - "
            f"0x{tag['payload_end'] - 1:08X}"
        )

        print(
            f"    Payload range    : "
            f"0x{tag['payload_start']:08X} - "
            f"0x{tag['payload_end'] - 1:08X}"
        )

        print(
            f"    Payload length   : "
            f"{tag['length']:,} bytes"
        )

    print()
    print("PROGRAM layout")
    print(separator("-"))

    print("PROGRAM #1")

    print(
        f"  Flash start       : "
        f"0x{main_block['flash_address']:08X}"
    )

    print(
        f"  Flash end         : "
        f"0x{main_flash_end:08X}"
    )

    print(
        f"  GBL data range    : "
        f"0x{main_block['data_start']:08X} - "
        f"0x{main_block['data_end'] - 1:08X}"
    )

    print(
        f"  Size              : "
        f"{len(main_program):,} bytes"
    )

    print(
        f"  File share        : "
        f"{len(main_program) / len(original_gbl) * 100:.2f}%"
    )

    print(
        f"  SHA-256           : "
        f"{sha256_bytes(main_program)}"
    )

    print()
    print("PROGRAM #2")

    print(
        f"  Flash start       : "
        f"0x{secondary_block['flash_address']:08X}"
    )

    print(
        f"  Flash end         : "
        f"0x{secondary_flash_end:08X}"
    )

    print(
        f"  GBL data range    : "
        f"0x{secondary_block['data_start']:08X} - "
        f"0x{secondary_block['data_end'] - 1:08X}"
    )

    print(
        f"  Size              : "
        f"{len(secondary_program):,} bytes"
    )

    print(
        f"  File share        : "
        f"{len(secondary_program) / len(original_gbl) * 100:.2f}%"
    )

    print(
        f"  SHA-256           : "
        f"{sha256_bytes(secondary_program)}"
    )

    print()
    print(
        f"PROGRAM data total  : "
        f"{total_program:,} bytes "
        f"({total_program / len(original_gbl) * 100:.2f}% of GBL)"
    )

    print()
    print("Patch address mapping")
    print(separator("-"))

    for patch in PATCHES:
        instruction_offset = patch[
            "instruction_offset"
        ]

        byte_offset = patch[
            "byte_offset"
        ]

        absolute_patch_offset = (
            main_block["data_start"]
            + byte_offset
        )

        flash_patch_address = (
            main_block["flash_address"]
            + byte_offset
        )

        instruction = main_program[
            instruction_offset:
            instruction_offset + 2
        ]

        context_start = max(
            0,
            instruction_offset - 16,
        )

        context_end = min(
            len(main_program),
            instruction_offset + 2 + 16,
        )

        print()
        print(
            patch["name"]
        )

        print(
            f"  Instruction offset: "
            f"0x{instruction_offset:08X} (PROGRAM #1)"
        )

        print(
            f"  Patch byte offset : "
            f"0x{byte_offset:08X} (PROGRAM #1)"
        )

        print(
            f"  Flash address     : "
            f"0x{flash_patch_address:08X}"
        )

        print(
            f"  GBL file offset   : "
            f"0x{absolute_patch_offset:08X}"
        )

        print(
            f"  Original          : "
            f"{format_bytes(instruction)}"
        )

        print(
            f"  Patched           : "
            f"{format_bytes(patch['patched_instruction'])}"
        )

        print(
            f"  Byte change       : "
            f"{patch['original_byte']:02X} -> "
            f"{patch['patched_byte']:02X}"
        )

        print(
            "  Patch applicable  : YES"
        )

        print(
            f"  Hex context       : "
            f"PROGRAM 0x{context_start:08X} - "
            f"0x{context_end - 1:08X}"
        )

        for row_start in range(
            context_start,
            context_end,
            16,
        ):
            row_end = min(
                row_start + 16,
                context_end,
            )

            fields = []

            for offset in range(
                row_start,
                row_end,
            ):
                value = main_program[
                    offset
                ]

                if offset == byte_offset:
                    fields.append(
                        f"[{value:02X}]"
                    )
                else:
                    fields.append(
                        f" {value:02X} "
                    )

            print(
                f"    0x{row_start:08X}: "
                + " ".join(fields)
            )

    print()
    print("Expected patch effects")
    print(separator("-"))

    print(
        "PROGRAM data bytes  : 2 changed"
    )

    print(
        "GBL content bytes   : 2 changed"
    )

    print(
        "Stored CRC bytes    : 4 changed"
    )

    print(
        "Total GBL bytes     : 6 changed"
    )

    for patch in PATCHES:
        absolute_patch_offset = (
            main_block["data_start"]
            + patch["byte_offset"]
        )

        print(
            patch["name"]
        )

        print(
            f"  PROGRAM byte      : "
            f"0x{patch['byte_offset']:08X} "
            f"{patch['original_byte']:02X} -> "
            f"{patch['patched_byte']:02X}"
        )

        print(
            f"  GBL patch byte    : "
            f"0x{absolute_patch_offset:08X} "
            f"{patch['original_byte']:02X} -> "
            f"{patch['patched_byte']:02X}"
        )

    print(
        f"CRC32               : "
        f"0x{EXPECTED_ORIGINAL_GBL_CRC32:08X} -> "
        f"0x{EXPECTED_PATCHED_GBL_CRC32:08X}"
    )

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

    for patch in PATCHES:
        byte_offset = patch[
            "byte_offset"
        ]

        instruction_offset = patch[
            "instruction_offset"
        ]

        if (
            original_program[
                byte_offset
            ]
            != patch["original_byte"]
        ):
            fail(
                f"{patch['name']}: "
                "pre-patch byte safety check failed."
            )

        if (
            original_program[
                instruction_offset:
                instruction_offset + 2
            ]
            != patch["original_instruction"]
        ):
            fail(
                f"{patch['name']}: "
                "pre-patch instruction safety check failed."
            )

    patched = bytearray(
        original_program
    )

    for patch in PATCHES:
        patched[
            patch["byte_offset"]
        ] = patch["patched_byte"]

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

    expected_differences = sorted(
        patch["byte_offset"]
        for patch in PATCHES
    )

    if differences != expected_differences:
        fail(
            "Unexpected PROGRAM differences.\n\n"
            f"Expected: "
            f"{[f'0x{x:08X}' for x in expected_differences]}\n"
            f"Found   : "
            f"{[f'0x{x:08X}' for x in differences]}"
        )

    for patch in PATCHES:
        instruction_offset = patch[
            "instruction_offset"
        ]

        patched_instruction = patched_program[
            instruction_offset:
            instruction_offset + 2
        ]

        if patched_instruction != patch["patched_instruction"]:
            fail(
                f"{patch['name']}: "
                "patched instruction validation failed."
            )

    patched_sha = sha256_bytes(
        patched_program
    )

    if patched_sha != EXPECTED_PATCHED_PROGRAM_SHA256:
        fail(
            "Patched PROGRAM SHA-256 mismatch.\n\n"
            f"Expected:\n"
            f"{EXPECTED_PATCHED_PROGRAM_SHA256}\n\n"
            f"Found:\n"
            f"{patched_sha}"
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
            "PROGRAM replacement size mismatch."
        )

    rebuilt[
        start:end
    ] = patched_program

    crc = (
        zlib.crc32(
            rebuilt[:-4]
        )
        & 0xFFFFFFFF
    )

    rebuilt[-4:] = struct.pack(
        "<I",
        crc,
    )

    return bytes(
        rebuilt
    )


# =============================================================================
# Validate patched GBL
# =============================================================================

def validate_patched_gbl(
    original_gbl: bytes,
    patched_gbl: bytes,
) -> tuple[list[int], dict]:

    if len(patched_gbl) != EXPECTED_ORIGINAL_GBL_SIZE:
        fail(
            "Patched GBL size mismatch.\n\n"
            f"Expected: "
            f"{EXPECTED_ORIGINAL_GBL_SIZE}\n"
            f"Found   : "
            f"{len(patched_gbl)}"
        )

    tags = parse_gbl(
        patched_gbl
    )

    end_tag = tags[-1]

    stored_crc = struct.unpack_from(
        "<I",
        patched_gbl,
        end_tag["payload_start"],
    )[0]

    calculated_crc = (
        zlib.crc32(
            patched_gbl[:-4]
        )
        & 0xFFFFFFFF
    )

    if stored_crc != calculated_crc:
        fail(
            "Patched GBL CRC32 is invalid.\n\n"
            f"Stored     : "
            f"0x{stored_crc:08X}\n"
            f"Calculated : "
            f"0x{calculated_crc:08X}"
        )

    if stored_crc != EXPECTED_PATCHED_GBL_CRC32:
        fail(
            "Patched GBL CRC32 does not match expected result.\n\n"
            f"Expected: "
            f"0x{EXPECTED_PATCHED_GBL_CRC32:08X}\n"
            f"Found   : "
            f"0x{stored_crc:08X}"
        )

    patched_main, _ = locate_supported_programs(
        patched_gbl,
        tags,
    )

    patched_main_program = patched_main[
        "program_data"
    ]

    patched_program_sha = sha256_bytes(
        patched_main_program
    )

    if patched_program_sha != EXPECTED_PATCHED_PROGRAM_SHA256:
        fail(
            "Final PROGRAM SHA-256 mismatch.\n\n"
            f"Expected:\n"
            f"{EXPECTED_PATCHED_PROGRAM_SHA256}\n\n"
            f"Found:\n"
            f"{patched_program_sha}"
        )

    for patch in PATCHES:
        instruction_offset = patch[
            "instruction_offset"
        ]

        final_instruction = patched_main_program[
            instruction_offset:
            instruction_offset + 2
        ]

        if final_instruction != patch["patched_instruction"]:
            fail(
                f"{patch['name']}: final GBL does not contain "
                "the expected patched instruction."
            )

    patched_gbl_sha = sha256_bytes(
        patched_gbl
    )

    if patched_gbl_sha != EXPECTED_PATCHED_GBL_SHA256:
        fail(
            "Patched GBL SHA-256 mismatch.\n\n"
            f"Expected:\n"
            f"{EXPECTED_PATCHED_GBL_SHA256}\n\n"
            f"Found:\n"
            f"{patched_gbl_sha}"
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

    expected_gbl_patch_offsets = sorted(
        patched_main["data_start"]
        + patch["byte_offset"]
        for patch in PATCHES
    )

    expected_differences = (
        expected_gbl_patch_offsets
        + [
            len(patched_gbl) - 4,
            len(patched_gbl) - 3,
            len(patched_gbl) - 2,
            len(patched_gbl) - 1,
        ]
    )

    if differences != expected_differences:
        fail(
            "Unexpected final GBL byte differences.\n\n"
            f"Expected: "
            f"{[f'0x{x:08X}' for x in expected_differences]}\n"
            f"Found   : "
            f"{[f'0x{x:08X}' for x in differences]}"
        )

    return (
        differences,
        patched_main,
    )


# =============================================================================
# Difference report
# =============================================================================

def show_diff(
    original_gbl: bytes,
    patched_gbl: bytes,
    differences: list[int],
) -> None:

    print()
    print(separator())
    print("BYTE DIFFERENCES")
    print(separator())

    print()

    for offset in differences:
        old = original_gbl[
            offset
        ]

        new = patched_gbl[
            offset
        ]

        print(
            f"0x{offset:08X} : "
            f"{old:02X} -> {new:02X}"
        )

    print()

    print(
        f"Total changed bytes : "
        f"{len(differences)}"
    )


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    parser = create_argument_parser()

    args = parser.parse_args()

    script_directory = Path(__file__).resolve().parent

    target_directory = (
        script_directory
        / TARGET_DIRECTORY_NAME
    )

    input_path = (
        target_directory
        / DEFAULT_INPUT_FILENAME
    ).resolve()

    original_gbl = read_file(
        input_path
    )

    print()
    print(separator())

    print(
        "Shelly TRV Gen1 2.2.4 "
        "Beacon-Skip + mDNS Firmware Patcher"
    )

    print(separator())

    print()

    print(
        f"Patcher version     : "
        f"{PATCHER_VERSION}"
    )

    print(
        f"Supported device    : "
        f"{SUPPORTED_DEVICE}"
    )

    print(
        f"Supported firmware  : "
        f"{SUPPORTED_BUILD}"
    )

    tags, main_block, secondary_block = validate_original_firmware(
        input_path,
        original_gbl,
        verbose=not args.analyze,
    )

    if args.verify:
        print()
        print(
            "Verification complete."
        )
        print(
            "No firmware was modified or written."
        )
        return

    if args.analyze:
        show_analysis(
            input_path,
            original_gbl,
            tags,
            main_block,
            secondary_block,
        )
        return

    original_program = main_block[
        "program_data"
    ]

    patched_program = create_patched_program(
        original_program
    )

    patched_gbl = rebuild_gbl(
        original_gbl,
        main_block,
        patched_program,
    )

    differences, patched_main = validate_patched_gbl(
        original_gbl,
        patched_gbl,
    )

    print()
    print(separator())
    print("PATCH RESULT")
    print(separator())

    print()

    for patch in PATCHES:
        print(
            patch["name"]
        )

        print(
            f"  Patch             : "
            f"0x{patch['byte_offset']:08X} "
            f"{patch['original_byte']:02X} -> "
            f"{patch['patched_byte']:02X}"
        )

        print(
            f"  Instruction       : "
            f"{format_bytes(patch['original_instruction'])} -> "
            f"{format_bytes(patch['patched_instruction'])}"
        )

        print()

    print(
        f"PROGRAM SHA-256     : "
        f"{sha256_bytes(patched_main['program_data'])}"
    )

    print(
        f"GBL CRC32           : "
        f"0x{EXPECTED_PATCHED_GBL_CRC32:08X}"
    )

    print(
        f"GBL SHA-256         : "
        f"{sha256_bytes(patched_gbl)}"
    )

    print(
        "Patch locations     : VERIFIED"
    )

    print(
        "Final validation    : OK"
    )

    if args.diff:
        show_diff(
            original_gbl,
            patched_gbl,
            differences,
        )

    if args.dry_run:
        print()
        print(separator())
        print("DRY RUN")
        print(separator())

        print()

        print(
            "Patch performed     : IN MEMORY ONLY"
        )

        print(
            "Output written      : NO"
        )

        print(
            "Final validation    : OK"
        )

        print()

        return

    if args.output:
        output_path = Path(
            args.output
        ).expanduser().resolve()
    else:
        output_path = input_path.with_name(
            DEFAULT_OUTPUT_FILENAME
        )

    if output_path == input_path:
        fail(
            "Refusing to overwrite the original firmware.\n\n"
            "Choose a different output path."
        )

    try:
        output_path.write_bytes(
            patched_gbl
        )
    except OSError as exc:
        fail(
            f"Could not write patched firmware:\n"
            f"{output_path}\n\n"
            f"{exc}"
        )

    written_data = read_file(
        output_path
    )

    if written_data != patched_gbl:
        fail(
            "Output file verification failed after writing."
        )

    print()
    print(separator())
    print("OUTPUT")
    print(separator())

    print()

    print(
        f"Written             : "
        f"{output_path}"
    )

    print(
        f"Size                : "
        f"{len(written_data):,} bytes"
    )

    print(
        f"SHA-256             : "
        f"{sha256_bytes(written_data)}"
    )

    print(
        "Write verification  : OK"
    )

    print()


if __name__ == "__main__":
    main()