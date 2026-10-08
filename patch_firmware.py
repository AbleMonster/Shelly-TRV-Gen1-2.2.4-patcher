from __future__ import annotations

import hashlib
import struct
import sys
import zlib
from pathlib import Path


# =============================================================================
# Shelly TRV 2.2.4 Beacon-Skip Firmware Patcher
#
# Current implementation:
#   1. Validate input file
#   2. Validate exact supported firmware by size and SHA-256
#   3. Parse and validate the GBL container
#   4. Validate GBL header/version/type
#   5. Validate expected GBL tag structure
#   6. Validate GBL CRC32
#   7. Locate the main PROGRAM tag
#   8. Validate its flash address
#   9. Extract and validate the program data
#  10. Validate the expected ARM/Thumb instruction at the patch location
#
# IMPORTANT:
# No firmware modification is performed yet.
# =============================================================================


# -----------------------------------------------------------------------------
# Supported firmware
# -----------------------------------------------------------------------------

SUPPORTED_DEVICE = "Shelly TRV (SHTRV-01)"
SUPPORTED_VERSION = "2.2.4"
SUPPORTED_BUILD = "20240619-130912/v2.2.4@ee290818"

EXPECTED_SIZE = 1_106_384

EXPECTED_SHA256 = (
    "5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f"
)


# -----------------------------------------------------------------------------
# GBL format constants
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
# Main firmware PROGRAM block
# -----------------------------------------------------------------------------

EXPECTED_PROGRAM_FLASH_ADDRESS = 0x00000000

EXPECTED_PROGRAM_SIZE = 1_049_548

EXPECTED_PROGRAM_SHA256 = (
    "4dc770fe535008ef150f3a144354169199e1a0e235173abcc3f7387b95ee9b5c"
)


# -----------------------------------------------------------------------------
# Beacon-skip patch location
#
# Original ARM/Thumb instruction:
#
#   0x0001E1C8: 31 DC    bgt 0x0001E22E
#
# Future patched instruction:
#
#   0x0001E1C8: 31 E0    b   0x0001E22E
#
# Only the second byte changes:
#
#   Program offset 0x0001E1C9
#   DC -> E0
#
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
    """
    Abort safely.

    No output firmware is created by the current implementation.
    """

    print()
    print("=" * 60)
    print("ERROR")
    print("=" * 60)
    print()
    print(message)
    print()
    print("No patched firmware was created.")
    print()

    raise SystemExit(1)


def sha256_bytes(data: bytes) -> str:
    """
    Calculate SHA-256 of bytes held in memory.
    """

    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """
    Calculate SHA-256 of a file.
    """

    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# -----------------------------------------------------------------------------
# GBL parser / validator
# -----------------------------------------------------------------------------

def validate_gbl(path: Path) -> tuple[bytes, list[dict]]:
    """
    Parse and validate the complete GBL container.
    """

    print()
    print("=" * 60)
    print("GBL container validation")
    print("=" * 60)
    print()

    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(
            "Could not read firmware file.\n\n"
            f"{exc}"
        )

    tags: list[dict] = []

    offset = 0
    tag_number = 0

    # -------------------------------------------------------------------------
    # Parse all GBL tags
    # -------------------------------------------------------------------------

    while offset < len(data):
        tag_number += 1

        if offset + 8 > len(data):
            fail(
                "Truncated GBL tag header.\n\n"
                f"Tag number : {tag_number}\n"
                f"Offset     : 0x{offset:08X}"
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
                f"Tag number    : {tag_number}\n"
                f"Tag ID        : 0x{tag_id:08X}\n"
                f"Tag offset    : 0x{offset:08X}\n"
                f"Payload length: {length:,}\n"
                f"Payload end   : 0x{payload_end:08X}\n"
                f"File size     : 0x{len(data):08X}"
            )

        tags.append(
            {
                "number": tag_number,
                "offset": offset,
                "tag_id": tag_id,
                "length": length,
                "payload_start": payload_start,
                "payload_end": payload_end,
            }
        )

        offset = payload_end

    # -------------------------------------------------------------------------
    # Parser must end exactly at EOF
    # -------------------------------------------------------------------------

    if offset != len(data):
        fail(
            "GBL parser did not terminate exactly at the end of the file.\n\n"
            f"Parser offset: 0x{offset:08X}\n"
            f"File size    : 0x{len(data):08X}"
        )

    print(f"Tags found   : {len(tags)}")
    print()

    # -------------------------------------------------------------------------
    # Validate number of tags
    # -------------------------------------------------------------------------

    if len(tags) != len(EXPECTED_TAGS):
        fail(
            "Unexpected number of GBL tags.\n\n"
            f"Expected: {len(EXPECTED_TAGS)}\n"
            f"Found   : {len(tags)}"
        )

    # -------------------------------------------------------------------------
    # Validate tag IDs and lengths
    # -------------------------------------------------------------------------

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
                f"Unexpected GBL tag #{index}.\n\n"
                f"Expected ID: 0x{expected_id:08X}\n"
                f"Found ID   : 0x{tag['tag_id']:08X}"
            )

        if tag["length"] != expected_length:
            fail(
                f"Unexpected length for GBL tag #{index}.\n\n"
                f"Expected: {expected_length:,}\n"
                f"Found   : {tag['length']:,}"
            )

    # -------------------------------------------------------------------------
    # Validate GBL header
    # -------------------------------------------------------------------------

    print()
    print("-" * 60)
    print("GBL header")
    print("-" * 60)
    print()

    header = tags[0]

    if header["tag_id"] != GBL_HEADER_TAG:
        fail(
            "The first GBL tag is not the expected GBL header."
        )

    if header["length"] != 8:
        fail(
            "Unexpected GBL header payload length.\n\n"
            f"Expected: 8\n"
            f"Found   : {header['length']}"
        )

    header_payload = data[
        header["payload_start"]:
        header["payload_end"]
    ]

    if len(header_payload) != 8:
        fail(
            "GBL header payload could not be read completely."
        )

    version, gbl_type = struct.unpack(
        "<II",
        header_payload,
    )

    print(f"GBL version  : 0x{version:08X}")
    print(f"GBL type     : 0x{gbl_type:08X}")

    if version != EXPECTED_GBL_VERSION:
        fail(
            "Unexpected GBL version.\n\n"
            f"Expected: 0x{EXPECTED_GBL_VERSION:08X}\n"
            f"Found   : 0x{version:08X}"
        )

    if gbl_type != EXPECTED_GBL_TYPE:
        fail(
            "Unexpected GBL type or flags.\n\n"
            f"Expected: 0x{EXPECTED_GBL_TYPE:08X}\n"
            f"Found   : 0x{gbl_type:08X}\n\n"
            "The supplied firmware may use a different GBL "
            "configuration and will not be processed."
        )

    # -------------------------------------------------------------------------
    # Validate end tag and CRC32
    # -------------------------------------------------------------------------

    print()
    print("-" * 60)
    print("GBL end tag / CRC32")
    print("-" * 60)
    print()

    end_tag = tags[-1]

    if end_tag["tag_id"] != GBL_END_TAG:
        fail(
            "The final GBL tag is not the expected end tag."
        )

    if end_tag["length"] != 4:
        fail(
            "Unexpected GBL end-tag payload length.\n\n"
            f"Expected: 4\n"
            f"Found   : {end_tag['length']}"
        )

    stored_crc = struct.unpack_from(
        "<I",
        data,
        end_tag["payload_start"],
    )[0]

    calculated_crc = zlib.crc32(
        data[:-4]
    ) & 0xFFFFFFFF

    print(f"Stored CRC32 : 0x{stored_crc:08X}")
    print(f"Calc. CRC32  : 0x{calculated_crc:08X}")

    if stored_crc != calculated_crc:
        fail(
            "GBL CRC32 validation failed.\n\n"
            f"Stored     : 0x{stored_crc:08X}\n"
            f"Calculated : 0x{calculated_crc:08X}"
        )

    print()
    print("GBL structure : OK")
    print("GBL header    : OK")
    print("GBL CRC32     : OK")

    return data, tags


# -----------------------------------------------------------------------------
# Main PROGRAM block validation
# -----------------------------------------------------------------------------

def validate_main_program(
    gbl_data: bytes,
    tags: list[dict],
) -> bytes:
    """
    Locate, extract and validate the main firmware PROGRAM block.

    The PROGRAM tag payload consists of:

        4 bytes  - flash address
        remaining bytes - program data

    For the supported firmware the main block must target flash address
    0x00000000.
    """

    print()
    print("=" * 60)
    print("Main firmware PROGRAM block")
    print("=" * 60)
    print()

    program_tags = [
        tag
        for tag in tags
        if tag["tag_id"] == GBL_PROGRAM_TAG
    ]

    print(f"PROGRAM tags : {len(program_tags)}")

    if len(program_tags) != 2:
        fail(
            "Unexpected number of PROGRAM tags.\n\n"
            f"Expected: 2\n"
            f"Found   : {len(program_tags)}"
        )

    main_program_tag = None

    # -------------------------------------------------------------------------
    # Inspect PROGRAM tags and locate flash address 0x00000000
    # -------------------------------------------------------------------------

    for index, tag in enumerate(
        program_tags,
        start=1,
    ):
        if tag["length"] < 4:
            fail(
                f"PROGRAM tag #{index} is too short to contain "
                "a flash address."
            )

        flash_address = struct.unpack_from(
            "<I",
            gbl_data,
            tag["payload_start"],
        )[0]

        program_size = tag["length"] - 4

        print(
            f"PROGRAM #{index}   : "
            f"flash 0x{flash_address:08X}, "
            f"data {program_size:,} bytes"
        )

        if flash_address == EXPECTED_PROGRAM_FLASH_ADDRESS:
            if main_program_tag is not None:
                fail(
                    "More than one PROGRAM tag targets "
                    "flash address 0x00000000."
                )

            main_program_tag = tag

    if main_program_tag is None:
        fail(
            "Could not locate the main PROGRAM tag targeting "
            "flash address 0x00000000."
        )

    # -------------------------------------------------------------------------
    # Read and validate flash address again
    # -------------------------------------------------------------------------

    flash_address = struct.unpack_from(
        "<I",
        gbl_data,
        main_program_tag["payload_start"],
    )[0]

    if flash_address != EXPECTED_PROGRAM_FLASH_ADDRESS:
        fail(
            "Unexpected main PROGRAM flash address.\n\n"
            f"Expected: 0x{EXPECTED_PROGRAM_FLASH_ADDRESS:08X}\n"
            f"Found   : 0x{flash_address:08X}"
        )

    # -------------------------------------------------------------------------
    # Extract actual program data
    #
    # PROGRAM payload:
    #
    #   +0x00  flash address (4 bytes)
    #   +0x04  firmware program data
    #
    # -------------------------------------------------------------------------

    program_data_start = (
        main_program_tag["payload_start"] + 4
    )

    program_data_end = (
        main_program_tag["payload_end"]
    )

    program_data = gbl_data[
        program_data_start:
        program_data_end
    ]

    print()
    print(f"Flash address: 0x{flash_address:08X}")
    print(f"Program size : {len(program_data):,} bytes")

    # -------------------------------------------------------------------------
    # Validate program size
    # -------------------------------------------------------------------------

    if len(program_data) != EXPECTED_PROGRAM_SIZE:
        fail(
            "Unexpected main program size.\n\n"
            f"Expected: {EXPECTED_PROGRAM_SIZE:,} bytes\n"
            f"Found   : {len(program_data):,} bytes"
        )

    print("Program size : OK")

    # -------------------------------------------------------------------------
    # Validate program SHA-256
    # -------------------------------------------------------------------------

    print("Program SHA  : calculating...")

    program_sha256 = sha256_bytes(
        program_data
    )

    print(f"Program SHA  : {program_sha256}")

    if program_sha256.lower() != EXPECTED_PROGRAM_SHA256.lower():
        fail(
            "Main program SHA-256 validation failed.\n\n"
            f"Expected:\n"
            f"{EXPECTED_PROGRAM_SHA256}\n\n"
            f"Found:\n"
            f"{program_sha256}"
        )

    print("Program SHA  : OK")

    # -------------------------------------------------------------------------
    # Validate patch offsets are inside the program
    # -------------------------------------------------------------------------

    if (
        PATCH_INSTRUCTION_OFFSET + len(EXPECTED_ORIGINAL_INSTRUCTION)
        > len(program_data)
    ):
        fail(
            "Patch instruction offset is outside the main program data."
        )

    if PATCH_BYTE_OFFSET >= len(program_data):
        fail(
            "Patch byte offset is outside the main program data."
        )

    # -------------------------------------------------------------------------
    # Read original instruction
    # -------------------------------------------------------------------------

    original_instruction = program_data[
        PATCH_INSTRUCTION_OFFSET:
        PATCH_INSTRUCTION_OFFSET + len(EXPECTED_ORIGINAL_INSTRUCTION)
    ]

    original_patch_byte = program_data[
        PATCH_BYTE_OFFSET
    ]

    print()
    print("-" * 60)
    print("Patch location verification")
    print("-" * 60)
    print()

    print(
        f"Instruction offset : "
        f"0x{PATCH_INSTRUCTION_OFFSET:08X}"
    )

    print(
        f"Expected instruction: "
        f"{EXPECTED_ORIGINAL_INSTRUCTION.hex(' ').upper()}"
    )

    print(
        f"Found instruction   : "
        f"{original_instruction.hex(' ').upper()}"
    )

    # -------------------------------------------------------------------------
    # Validate complete original instruction
    # -------------------------------------------------------------------------

    if original_instruction != EXPECTED_ORIGINAL_INSTRUCTION:
        fail(
            "Unexpected instruction at the patch location.\n\n"
            f"Offset  : 0x{PATCH_INSTRUCTION_OFFSET:08X}\n"
            f"Expected: "
            f"{EXPECTED_ORIGINAL_INSTRUCTION.hex(' ').upper()}\n"
            f"Found   : "
            f"{original_instruction.hex(' ').upper()}\n\n"
            "The firmware will not be modified."
        )

    # -------------------------------------------------------------------------
    # Validate exact byte to be modified
    # -------------------------------------------------------------------------

    print()
    print(
        f"Patch byte offset   : "
        f"0x{PATCH_BYTE_OFFSET:08X}"
    )

    print(
        f"Expected byte       : "
        f"0x{EXPECTED_ORIGINAL_BYTE:02X}"
    )

    print(
        f"Found byte          : "
        f"0x{original_patch_byte:02X}"
    )

    if original_patch_byte != EXPECTED_ORIGINAL_BYTE:
        fail(
            "Unexpected byte at the patch location.\n\n"
            f"Offset  : 0x{PATCH_BYTE_OFFSET:08X}\n"
            f"Expected: 0x{EXPECTED_ORIGINAL_BYTE:02X}\n"
            f"Found   : 0x{original_patch_byte:02X}\n\n"
            "The firmware will not be modified."
        )

    # -------------------------------------------------------------------------
    # Show future patch
    # -------------------------------------------------------------------------

    print()
    print(
        f"Original instruction: "
        f"{EXPECTED_ORIGINAL_INSTRUCTION.hex(' ').upper()}"
    )

    print(
        f"Future instruction  : "
        f"{EXPECTED_PATCHED_INSTRUCTION.hex(' ').upper()}"
    )

    print(
        f"Future byte change  : "
        f"0x{EXPECTED_ORIGINAL_BYTE:02X} -> "
        f"0x{EXPECTED_PATCHED_BYTE:02X}"
    )

    print()
    print("Main PROGRAM block : OK")
    print("Program SHA-256    : OK")
    print("Patch instruction  : OK")
    print("Patch byte         : OK")

    return program_data


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> None:
    print()
    print("Shelly TRV 2.2.4 Beacon-Skip Firmware Patcher")
    print("=" * 60)
    print()

    # -------------------------------------------------------------------------
    # Command-line argument
    # -------------------------------------------------------------------------

    if len(sys.argv) != 2:
        print("Usage:")
        print()
        print(
            f'  python {Path(sys.argv[0]).name} '
            '"<path-to-original-firmware.gbl>"'
        )
        print()
        print("Example:")
        print()
        print(
            f'  python {Path(sys.argv[0]).name} '
            '"C:\\path\\to\\SHTRV-01_build.gbl"'
        )
        print()

        raise SystemExit(2)

    firmware_path = Path(
        sys.argv[1]
    ).expanduser().resolve()

    print(f"Input file  : {firmware_path}")

    # -------------------------------------------------------------------------
    # Check input file
    # -------------------------------------------------------------------------

    if not firmware_path.exists():
        fail(
            "Input firmware does not exist.\n\n"
            f"Path:\n{firmware_path}"
        )

    if not firmware_path.is_file():
        fail(
            "Input path is not a file.\n\n"
            f"Path:\n{firmware_path}"
        )

    # -------------------------------------------------------------------------
    # File size
    # -------------------------------------------------------------------------

    try:
        file_size = firmware_path.stat().st_size
    except OSError as exc:
        fail(
            "Could not determine firmware file size.\n\n"
            f"{exc}"
        )

    print(f"File size   : {file_size:,} bytes")

    if file_size != EXPECTED_SIZE:
        fail(
            "Unsupported firmware size.\n\n"
            f"Expected: {EXPECTED_SIZE:,} bytes\n"
            f"Found   : {file_size:,} bytes\n\n"
            "This patcher only supports the specifically analyzed "
            "Shelly TRV firmware 2.2.4 image."
        )

    # -------------------------------------------------------------------------
    # Complete firmware SHA-256
    # -------------------------------------------------------------------------

    print("SHA-256     : calculating...")

    try:
        actual_sha256 = sha256_file(
            firmware_path
        )
    except OSError as exc:
        fail(
            "Could not calculate firmware SHA-256.\n\n"
            f"{exc}"
        )

    print(f"SHA-256     : {actual_sha256}")

    if actual_sha256.lower() != EXPECTED_SHA256.lower():
        fail(
            "Firmware SHA-256 does not match the supported "
            "Shelly TRV 2.2.4 firmware image.\n\n"
            f"Expected:\n"
            f"{EXPECTED_SHA256}\n\n"
            f"Found:\n"
            f"{actual_sha256}\n\n"
            "The firmware will not be modified."
        )

    # -------------------------------------------------------------------------
    # Firmware identity successful
    # -------------------------------------------------------------------------

    print()
    print("Firmware identity verification successful.")
    print()
    print(f"Device       : {SUPPORTED_DEVICE}")
    print(f"Firmware     : {SUPPORTED_VERSION}")
    print(f"Build        : {SUPPORTED_BUILD}")
    print("File size    : OK")
    print("SHA-256      : OK")

    # -------------------------------------------------------------------------
    # Validate GBL
    # -------------------------------------------------------------------------

    gbl_data, tags = validate_gbl(
        firmware_path
    )

    # -------------------------------------------------------------------------
    # Validate main PROGRAM block and patch location
    # -------------------------------------------------------------------------

    program_data = validate_main_program(
        gbl_data,
        tags,
    )

    # Keep this available for the next implementation stage.
    _ = program_data

    # -------------------------------------------------------------------------
    # Final result
    # -------------------------------------------------------------------------

    print()
    print("=" * 60)
    print("VALIDATION SUCCESSFUL")
    print("=" * 60)
    print()

    print(f"Device       : {SUPPORTED_DEVICE}")
    print(f"Firmware     : {SUPPORTED_VERSION}")
    print(f"Build        : {SUPPORTED_BUILD}")

    print()
    print("Input file       : OK")
    print("File size        : OK")
    print("Firmware SHA-256 : OK")
    print("GBL structure    : OK")
    print("GBL header       : OK")
    print("GBL CRC32        : OK")
    print("Main PROGRAM     : OK")
    print("Program size     : OK")
    print("Program SHA-256  : OK")
    print("Patch instruction: OK")
    print("Patch byte       : OK")

    print()
    print("The firmware is ready for the patching stage.")
    print()
    print(
        f"Verified future modification:"
    )
    print(
        f"  Program offset 0x{PATCH_BYTE_OFFSET:08X}: "
        f"{EXPECTED_ORIGINAL_BYTE:02X} -> "
        f"{EXPECTED_PATCHED_BYTE:02X}"
    )

    print()
    print("No modifications have been made yet.")
    print("No output firmware has been created.")
    print()


if __name__ == "__main__":
    main()