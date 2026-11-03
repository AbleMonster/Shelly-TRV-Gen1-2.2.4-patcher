# Shelly TRV Gen1 2.2.4 Patcher — User Guide

This guide explains how to reconstruct and install the experimental **B2.2 firmware** for a **Shelly TRV Gen1 (`SHTRV-01`) running Stock firmware 2.2.4**.

No Shelly firmware file is included in this repository.

The patcher uses an original Stock 2.2.4 firmware file supplied locally by the user and reconstructs the exact qualified B2.2 firmware.

The generated firmware can then be transferred to the TRV using the included OTA server.

You do not need to understand the reverse-engineering details to follow this guide.

---

# Important

This patcher is designed for exactly one firmware:

```text
Device:
Shelly TRV Gen1 / SHTRV-01

Firmware:
2.2.4

Build:
20240619-130912/v2.2.4@ee290818
```

Supported Stock GBL:

```text
Filename:
SHTRV-01_build_2.2.4.gbl

Size:
1,106,384 bytes

SHA256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

Do **not**:

- use firmware from another Shelly device,
- use another TRV firmware version,
- rename another firmware file to make it look like 2.2.4,
- bypass input validation,
- modify the generated firmware before OTA installation.

The patcher is intentionally fail-closed and refuses unsupported input.

Firmware updates always carry some risk.

Make sure the TRV has sufficient battery charge and do not intentionally interrupt power while an update is being installed.

---

# Experimental status

B2.2 is experimental firmware.

It has been:

```text
deterministically reconstructed
verified byte-for-byte
installed on physical Shelly TRV hardware
successfully booted
operated on a physical test fleet
```

Long-term testing is still in progress.

At this stage:

```text
Long-term battery-life improvement:
NOT ESTABLISHED

Historical battery-drain root cause:
NOT CONCLUSIVELY PROVEN
```

Do not treat B2.2 as an official Shelly production firmware release.

---

# 1. What you need

Before starting, you need:

- a Shelly TRV Gen1,
- the exact supported Stock 2.2.4 firmware,
- a Windows, macOS, or Linux computer,
- Python 3,
- this repository,
- for OTA installation: the computer and TRV on a network where they can reach each other.

No additional Python packages are required.

The patcher and OTA server use only the Python standard library.

---

# 2. Repository layout

The repository should look approximately like this:

```text
Shelly_TRV_2.2.4_Patcher/
├── docs/
├── target/
│   └── .gitkeep
├── tests/
├── ota_server.py
├── patch_firmware_v2.0.py
├── README.md
├── SECURITY.md
└── USER_GUIDE.md
```

The `target/` directory is used for local firmware input and output.

Firmware files inside `target/` must remain local and must not be committed to Git.

---

# 3. Download the repository

On GitHub, select:

```text
Code → Download ZIP
```

Extract the ZIP to a convenient location.

Users familiar with Git can clone the repository instead.

---

# 4. Check Python

## Windows

Open PowerShell or Windows Terminal:

```powershell
python --version
```

If that does not work:

```powershell
py --version
```

You should see a Python 3 version.

---

## macOS / Linux

Open Terminal:

```bash
python3 --version
```

You should see a Python 3 version.

If Python is not installed, install a current Python 3 release before continuing.

---

# 5. Prepare the Stock firmware

Obtain the original Shelly TRV Gen1 Stock firmware 2.2.4 independently.

The firmware file must be named exactly:

```text
SHTRV-01_build_2.2.4.gbl
```

Copy it into:

```text
target/
```

The resulting directory should contain:

```text
target/
├── .gitkeep
└── SHTRV-01_build_2.2.4.gbl
```

Do not modify the Stock firmware file.

The patcher verifies its exact identity before reconstructing B2.2.

---

# 6. Open a terminal in the repository directory

The following commands must be run from the main repository directory.

This is the directory containing:

```text
patch_firmware_v2.0.py
ota_server.py
README.md
```

## Windows

Open the repository directory in File Explorer.

Right-click inside the directory and choose:

```text
Open in Terminal
```

depending on your Windows configuration.

---

## macOS

Open Terminal.

Type:

```bash
cd 
```

including the space after `cd`.

Drag the repository directory from Finder into Terminal and press **Enter**.

---

## Linux

Open a terminal in the repository directory using your file manager or use `cd`.

---

# 7. Create B2.2

## Windows

Run:

```powershell
python patch_firmware_v2.0.py
```

If your system uses the Python launcher:

```powershell
py patch_firmware_v2.0.py
```

---

## macOS / Linux

Run:

```bash
python3 patch_firmware_v2.0.py
```

The patcher automatically looks for:

```text
target/SHTRV-01_build_2.2.4.gbl
```

No firmware path has to be supplied manually.

---

# 8. What the patcher does

The patcher first verifies the exact Stock firmware.

It then performs the qualified Stock-to-B2.2 reconstruction.

The process includes:

```text
Stock firmware validation
        |
        v
expected preimage validation
        |
        v
authorized B2.2 reconstruction
        |
        v
application integrity validation
        |
        v
GBL reconstruction
        |
        v
GBL integrity validation
        |
        v
write output
        |
        v
read output back
        |
        v
verify again
```

If an important check fails, the process stops.

The patcher does not attempt to adapt B2.2 to an unknown firmware version.

---

# 9. Expected output

A successful reconstruction creates:

```text
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin
```

and:

```text
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Your local directory should then look similar to:

```text
target/
├── .gitkeep
├── SHTRV-01_build_2.2.4.gbl
├── SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin
└── SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Keep all three firmware files local.

Do not upload them to GitHub.

---

# 10. Expected B2.2 identities

The generated application must match:

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

The generated GBL must match:

```text
Filename:
SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl

Size:
1,126,156 bytes

SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

END CRC32:
52A97051
```

If the final identities do not match, do **not** flash the generated firmware.

---

# 11. Start the OTA server

The included OTA server transfers the generated B2.2 GBL from the computer to the TRV.

It does not automatically initiate an update.

## Windows

Run:

```powershell
python ota_server.py
```

or:

```powershell
py ota_server.py
```

TCP port 80 may require additional permission depending on your Windows configuration.

If Windows reports a permission error, run the terminal with the required administrative privileges.

If Windows Firewall asks whether Python may accept incoming connections on your local network, allow the connection only where appropriate for your trusted LAN.

---

## macOS / Linux

TCP port 80 normally requires elevated privileges.

Run:

```bash
sudo python3 ota_server.py
```

Enter your computer password if requested.

The password may not be displayed while typing. This is normal.

---

# 12. OTA server validation

Before opening the HTTP server, `ota_server.py` independently validates:

```text
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Expected values:

```text
Size:
1,126,156 bytes

SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

END CRC32:
0x52A97051
```

The server starts only if validation succeeds.

Current OTA-server version:

```text
2.0 revision 1
```

Server identity:

```text
ShellyTRVOTA/2.0
```

---

# 13. TCP port 80

The supported Shelly TRV Gen1 OTA workflow uses:

```text
TCP port 80
```

The current OTA server does **not** automatically fall back to port 8000.

If port 80 is unavailable, resolve that problem before continuing.

Do not simply substitute another port and assume the TRV will retrieve the firmware correctly.

---

# 14. Check the server URL

After successful startup, the OTA server prints its local IPv4 address and firmware URL.

Example:

```text
http://192.168.1.100/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Your IP address will probably be different.

Always use the URL displayed by your own OTA server.

If the computer has:

- multiple network interfaces,
- VPN software,
- several private IPv4 addresses,

check that the displayed address belongs to a network the TRV can actually reach.

---

# 15. Find the TRV IP address

You need the local IP address of the Shelly TRV.

It can normally be found in:

- your router's device list,
- the Shelly app,
- Home Assistant if the TRV is integrated there.

Example:

```text
192.168.1.50
```

Your actual address will be different.

---

# 16. Install B2.2

There are two simple ways to start the update.

## Option A — browser

General format:

```text
http://TRV-IP/ota?url=http://COMPUTER-IP/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Example:

```text
TRV IP:      192.168.1.50
Computer IP: 192.168.1.100
```

OTA URL:

```text
http://192.168.1.50/ota?url=http://192.168.1.100/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Open the complete URL in a browser.

If accepted, the TRV may return a response similar to:

```json
{
  "status": "updating",
  "has_update": true
}
```

---

# 17. Alternative — curl

The same OTA request can be sent from a terminal:

```bash
curl "http://TRV-IP/ota?url=http://COMPUTER-IP/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl"
```

Example:

```bash
curl "http://192.168.1.50/ota?url=http://192.168.1.100/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl"
```

Use your actual addresses.

---

# 18. Watch the OTA server

After the TRV accepts the update request, watch the terminal running:

```text
ota_server.py
```

The TRV should connect and request:

```text
/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

The server displays transfer information including:

- requesting client,
- byte range,
- transferred bytes,
- progress,
- transfer rate,
- completion or interruption.

A completed HTTP transfer means only that the requested firmware bytes were transferred.

It does **not** by itself prove that:

- the firmware was accepted,
- the firmware was successfully written to flash,
- the TRV rebooted successfully,
- B2.2 is running correctly.

---

# 19. Wait for the TRV to reboot

Do not interrupt the TRV while the update is being processed.

Do not:

- remove the batteries,
- restart the TRV manually during installation,
- stop the OTA server during transfer,
- intentionally disconnect the network during transfer.

The device may temporarily disappear from the network.

Allow it to complete the update and reboot.

---

# 20. Verify the device

After the TRV becomes reachable again, open:

```text
http://TRV-IP/status
```

The firmware should still report the native Shelly build:

```text
20240619-130912/v2.2.4@ee290818
```

This is expected.

---

## Why does it still report 2.2.4?

B2.2 intentionally retains the original Shelly firmware version string.

Therefore:

```text
/status
```

alone cannot distinguish:

```text
Stock 2.2.4
```

from:

```text
B2.2
```

The exact B2.2 identity is established during reconstruction by the artifact hashes.

---

# 21. Check normal operation

After installation, verify:

- Wi-Fi connectivity,
- cloud connectivity if enabled,
- temperature measurement,
- thermostat operation,
- valve movement,
- calibration state.

B2.2 has already demonstrated successful physical operation under tested conditions, but every experimental installation should still be checked.

---

# 22. What is B2.2?

B2.2 contains nine selected qualified corrections:

```text
1. A1R including A1 lifecycle correction
2. C-C Beacon-Recovery evidence correction
3. B2 bounded serialization
4. minimal MQTT PUBLISH guard
5. official WF200 3.18.0
6. Calibration Restore Guard
7. P01 Battery-PA3 release
8. P02 I2C timeout retirement
9. P03 WLAN-GPIO interrupt-mask correction
```

The detailed implementation is documented in:

```text
docs/technical-details.md
```

---

# 23. What B2.2 does not contain

B2.2 does not include several historical or diagnostic experiments, including:

```text
periodic mDNS bypass
MIN80
D3 observer
PM52/cmd66 observer
additional debug instrumentation
FastPS experiments
P04 and other deferred candidates
```

This is important because older versions of this repository described a periodic mDNS bypass as part of the generated firmware.

That is no longer true for B2.2.

---

# 24. Current test status

B2.2 has successfully demonstrated:

```text
deterministic reconstruction
byte-identical application output
byte-identical GBL output
physical OTA installation
physical boot
WF200 3.18.0 initialization
WLAN association
DHCP
cloud connectivity
calibration
connected power save
normal TRV runtime
```

The initial B2.2 hardware canary also operated for approximately 29 hours without an unexpected additional reboot or reconnect.

The active test fleet has subsequently been moved to B2.2 for longer-term observation.

---

# 25. Battery-life status

Do not interpret successful operation as proof of improved battery life.

Current status:

```text
Long-term battery behavior:
UNDER OBSERVATION

Battery-life improvement:
NOT ESTABLISHED

Historical battery-drain root cause:
NOT CONCLUSIVELY PROVEN
```

This distinction is intentional.

---

# 26. Troubleshooting

## `Original firmware not found`

Make sure this file exists:

```text
target/SHTRV-01_build_2.2.4.gbl
```

Check the filename exactly.

---

## Firmware validation fails

Do not bypass validation.

Check that the input is exactly:

```text
Device:
Shelly TRV Gen1 / SHTRV-01

Build:
20240619-130912/v2.2.4@ee290818

Size:
1,106,384 bytes

SHA256:
5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f
```

Possible causes include:

- wrong firmware version,
- firmware from another device,
- modified firmware,
- damaged file,
- incorrectly renamed firmware.

---

## Output hash does not match

Do not flash the result.

Expected B2.2 GBL:

```text
SHA256:
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c
```

The patcher is designed to reject unexpected output.

---

## `python` command not found

On Windows:

```powershell
python --version
```

or:

```powershell
py --version
```

On macOS/Linux:

```bash
python3 --version
```

---

## OTA server cannot use port 80

On macOS/Linux, make sure you started it with:

```bash
sudo python3 ota_server.py
```

If port 80 remains unavailable, determine which program is already using it.

The current workflow does not automatically switch to port 8000.

---

## The TRV does not download the firmware

Check that:

1. the TRV can reach the computer,
2. the OTA server is still running,
3. the computer IP in the OTA URL is correct,
4. the TRV IP is correct,
5. your firewall allows incoming TCP port 80,
6. the OTA server selected the correct LAN interface,
7. a VPN is not causing the wrong local address to be advertised.

Do not use:

```text
localhost
```

or:

```text
127.0.0.1
```

in the firmware URL.

Those addresses would refer to the requesting device itself rather than your computer.

---

## The browser reports `status: updating`

That normally means the TRV accepted the OTA request.

Now watch the OTA-server terminal.

The TRV still needs to:

```text
download
→ validate
→ install
→ reboot
```

the firmware.

---

## The OTA server reports a completed transfer

This confirms only the HTTP transfer.

Wait for the TRV to reboot and verify normal device operation.

---

## `/status` still reports 2.2.4

That is expected.

B2.2 intentionally retains:

```text
20240619-130912/v2.2.4@ee290818
```

as the native firmware identity.

---

# 27. Keep firmware files private

The repository intentionally does not contain original or generated Shelly firmware images.

Keep these files local:

```text
target/SHTRV-01_build_2.2.4.gbl
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Do not commit or upload them to the public repository.

---

# 28. Quick reference

## Step 1 — place Stock firmware

```text
target/SHTRV-01_build_2.2.4.gbl
```

---

## Step 2 — run patcher

Windows:

```powershell
python patch_firmware_v2.0.py
```

or:

```powershell
py patch_firmware_v2.0.py
```

macOS/Linux:

```bash
python3 patch_firmware_v2.0.py
```

---

## Step 3 — confirm B2.2 was created

```text
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.bin
target/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

Expected GBL SHA256:

```text
912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c
```

---

## Step 4 — start OTA server

Windows:

```powershell
python ota_server.py
```

macOS/Linux:

```bash
sudo python3 ota_server.py
```

---

## Step 5 — note the displayed firmware URL

Example:

```text
http://192.168.1.100/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

---

## Step 6 — start OTA

```text
http://TRV-IP/ota?url=http://COMPUTER-IP/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl
```

or:

```bash
curl "http://TRV-IP/ota?url=http://COMPUTER-IP/SHTRV-01_2.2.4_B2.2_EXPERIMENTAL.gbl"
```

---

## Step 7 — wait for transfer and reboot

Do not interrupt the device.

---

## Step 8 — verify normal operation

Open:

```text
http://TRV-IP/status
```

Expected native firmware identity:

```text
20240619-130912/v2.2.4@ee290818
```

Remember that this version string alone cannot distinguish B2.2 from Stock 2.2.4.

---

# Further information

Project overview:

```text
README.md
```

Technical implementation:

```text
docs/technical-details.md
```

OTA-server documentation:

```text
docs/ota_server.md
```

Testing and current qualification status:

```text
tests/README.md
```

Security-sensitive reporting:

```text
SECURITY.md
```

---

# Final warning

B2.2 is experimental firmware.

The current evidence supports:

```text
exact deterministic reconstruction
+
successful physical operation under tested conditions
```

It does not yet support:

```text
guaranteed long-term stability
+
proven battery-life restoration
+
conclusively proven historical Battery Drain root cause
```

Use the firmware only if you understand and accept the risks associated with experimental firmware modification and OTA installation.