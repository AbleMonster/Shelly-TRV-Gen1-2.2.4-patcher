# Shelly TRV Gen1 2.2.4 Patcher — User Guide

This guide explains how to create and install the patched firmware for a **Shelly TRV Gen1 running firmware 2.2.4**.

No firmware file is included in this repository.

The patcher modifies an original Shelly TRV 2.2.4 firmware file locally on your computer. The patched firmware can then be transferred to the TRV using the included OTA server.

You do not need to understand the technical details of the patch to follow this guide.

---

## Important

This patcher is designed for one specific firmware:

**Device:** Shelly TRV Gen1  
**Firmware:** 2.2.4  
**Build:** `20240619-130912/v2.2.4@ee290818`

Do **not** use firmware from another Shelly device or another firmware version.

Do **not** rename another firmware version to make it look like 2.2.4.

The patcher performs several checks before modifying the firmware and will refuse a file that does not match the expected original firmware.

Firmware updates always carry some risk. Make sure the TRV has sufficient battery charge and do not interrupt power or network connectivity while the update is being installed.

---

# 1. What you need

Before starting, you need:

- a Shelly TRV Gen1
- the original Shelly TRV firmware 2.2.4
- a Windows, macOS, or Linux computer
- Python 3 installed
- the computer and TRV connected to the same local network
- this repository downloaded to your computer

The repository should look approximately like this:

```text
Shelly_TRV_2.2.4_Patcher/
├── docs/
├── target/
│   └── .gitkeep
├── tests/
├── ota_server.py
├── patch_firmware_v.1.0.py
├── README.md
└── USER_GUIDE.md
```

The `target` directory is where the original and patched firmware files are stored locally.

Firmware files inside `target` are intentionally excluded from Git.

---

# 2. Download the repository

On the GitHub repository page, select:

**Code → Download ZIP**

Extract the ZIP file to a convenient location on your computer.

Alternatively, users familiar with Git can clone the repository normally.

---

# 3. Check that Python is installed

## Windows

Open **PowerShell** and enter:

```powershell
python --version
```

If that does not work, try:

```powershell
py --version
```

You should see a Python 3 version.

Example:

```text
Python 3.13.3
```

## macOS / Linux

Open **Terminal** and enter:

```bash
python3 --version
```

You should see a Python 3 version.

If Python is not installed, install a current Python 3 release before continuing.

---

# 4. Prepare the original firmware

Obtain the original Shelly TRV Gen1 firmware version **2.2.4**.

The firmware file used by the patcher must be named exactly:

```text
SHTRV-01_build_2.2.4.gbl
```

Copy this file into the repository's:

```text
target
```

directory.

After copying the file, the directory should look like this:

```text
target/
├── .gitkeep
└── SHTRV-01_build_2.2.4.gbl
```

Do not modify the original firmware file.

The patcher will verify that the file is the exact firmware image it expects.

---

# 5. Open a terminal in the repository directory

The commands in the following sections must be executed from the main repository directory.

This is the directory containing:

```text
patch_firmware_v.1.0.py
ota_server.py
README.md
```

## Windows

Open the repository folder in File Explorer.

Right-click inside the folder and choose:

**Open in Terminal**

Depending on your Windows configuration, this may open PowerShell or Windows Terminal.

## macOS

Open **Terminal**.

Type:

```bash
cd 
```

including the space after `cd`.

Then drag the repository folder from Finder into the Terminal window and press **Enter**.

## Linux

Open a terminal in the repository directory using your file manager or use `cd` to change to the directory.

---

# 6. Create the patched firmware

## Windows

Run:

```powershell
python patch_firmware_v.1.0.py
```

If your system uses the Python launcher instead:

```powershell
py patch_firmware_v.1.0.py
```

## macOS / Linux

Run:

```bash
python3 patch_firmware_v.1.0.py
```

The patcher automatically looks for:

```text
target/SHTRV-01_build_2.2.4.gbl
```

You do not need to specify the firmware file manually.

---

# 7. What the patcher does

Before changing anything, the patcher verifies the original firmware.

Among other checks, it verifies:

- firmware file size
- SHA-256
- CRC32
- GBL structure
- application image
- expected original instruction bytes

If any important check fails, the patcher stops instead of creating an unsupported firmware image.

When all checks succeed, two modifications are applied:

- Beacon Skip recovery bypass
- periodic mDNS restart bypass

The patcher then validates the resulting firmware again.

A successful run ends with the patched firmware being written to:

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

Your `target` directory should now contain:

```text
target/
├── .gitkeep
├── SHTRV-01_build_2.2.4.gbl
└── SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

Keep both firmware files local.

Do not upload them to GitHub.

---

# 8. Start the OTA server

The included OTA server transfers the patched firmware from your computer to the TRV.

Leave the terminal open after creating the firmware.

## Windows

Run:

```powershell
python ota_server.py
```

or, if required:

```powershell
py ota_server.py
```

## macOS / Linux

The OTA server normally needs permission to use HTTP port 80.

Run:

```bash
sudo python3 ota_server.py
```

Enter your computer password if requested.

The password may not be displayed while you type it. This is normal.

---

# 9. Check the OTA server

Before serving anything, the OTA server independently validates:

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

For the supported patched firmware, the expected values are:

```text
Size:    1,106,384 bytes
SHA-256: 7adbb31d6b7faa8b9290d7b3436af45d42af9c3602a7195cafab774ded84ac61
CRC32:   0xBAEB8265
```

If validation succeeds, the server displays information including its local IP address and the firmware URL.

For example:

```text
http://192.168.1.100/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

Your IP address will probably be different.

**Use the URL displayed by your own OTA server.**

Keep this terminal window open while updating the TRV.

---

# 10. Find the IP address of your TRV

You now need the local IP address of the Shelly TRV.

You can normally find it in:

- your router's list of connected devices
- the Shelly app
- Home Assistant, if the TRV is integrated there

An example TRV address could be:

```text
192.168.1.50
```

Your address will be different.

You can test access by opening the TRV address in a browser:

```text
http://192.168.1.50
```

Replace `192.168.1.50` with the actual IP address of your TRV.

---

# 11. Install the patched firmware

There are two simple ways to start the OTA update.

## Option A — Web browser

This is usually the easiest method.

The Shelly OTA command uses this format:

```text
http://TRV-IP/ota?url=http://COMPUTER-IP/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

You need to replace:

```text
TRV-IP
```

with the IP address of your Shelly TRV, and:

```text
COMPUTER-IP
```

with the IP address displayed by the OTA server.

### Example

Suppose:

```text
TRV IP:      192.168.1.50
Computer IP: 192.168.1.100
```

You would open:

```text
http://192.168.1.50/ota?url=http://192.168.1.100/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

Paste the complete address into your browser's address bar and press **Enter**.

If the update is accepted, the TRV should return a response similar to:

```json
{
  "status": "updating",
  "has_update": true
}
```

The exact response may contain additional information.

---

# 12. Alternative — start the update with curl

If you prefer to use the terminal, the same update can be started with `curl`.

Example:

```bash
curl "http://192.168.1.50/ota?url=http://192.168.1.100/SHTRV-01_2.2.4_beacon_mdns_patch.gbl"
```

Again:

- `192.168.1.50` is only an example TRV IP
- `192.168.1.100` is only an example computer IP

Use your actual addresses.

A successful request should return a response indicating that the TRV is updating.

---

# 13. Watch the OTA server

After the TRV accepts the update request, look at the terminal running:

```text
ota_server.py
```

The TRV should connect to the server and request the firmware.

The server displays information about the transfer.

A complete HTTP transfer confirms that the firmware file was transferred to the TRV.

It does **not**, by itself, prove that the firmware was successfully installed.

The TRV still has to validate, install, and boot the firmware.

---

# 14. Wait for the TRV to reboot

Do not interrupt the TRV during the update.

Do not:

- remove the batteries
- restart the TRV manually
- disconnect the computer from the network
- stop the OTA server during the transfer

Give the TRV time to finish the update and reboot.

The device may temporarily disappear from the network.

---

# 15. Verify the firmware version

After the TRV is back online, open:

```text
http://TRV-IP/status
```

For example:

```text
http://192.168.1.50/status
```

Look for the firmware information.

The device should report firmware 2.2.4, for example:

```text
20240619-130912/v2.2.4@ee290818
```

## Why does it still say 2.2.4?

This is expected.

The patch does **not** change the firmware version string.

The patched firmware is still based on Shelly TRV firmware 2.2.4.

Therefore, `/status` alone cannot distinguish the patched firmware from the original stock 2.2.4 firmware.

Successful patcher validation, OTA transfer, reboot, and runtime behavior together provide the relevant validation.

---

# 16. What has been changed?

The patch contains two narrowly targeted modifications.

### Beacon Skip recovery bypass

Firmware 2.2.4 contains a recurring Beacon Skip recovery path observed during testing.

The patch bypasses this recovery action while leaving the normal Beacon Skip calculation and power-save configuration in place.

### Periodic mDNS restart bypass

Firmware 2.2.4 also contains a periodic connected-state path that restarts the mDNS responder.

The patch bypasses this periodic restart call.

Other mDNS initialization and event-driven paths remain present.

For the reverse-engineering details, exact offsets, hashes, and runtime observations, see:

```text
docs/technical-details.md
```

---

# 17. Current test status

The combined patched firmware has been installed on a physical Shelly TRV Gen1.

Runtime testing has confirmed that, under the tested conditions:

- the periodic mDNS restart is no longer observed
- the targeted recurring Beacon Skip recovery sequence is no longer observed during multi-hour testing
- the TRV continues to operate on firmware 2.2.4

Long-term testing is still ongoing.

In particular:

**An improvement in battery life has not yet been established.**

The purpose of the project is to investigate the battery-drain behavior scientifically. Suppressing the identified recurring firmware mechanisms does not automatically prove that they are the only causes of battery drain.

---

# 18. Troubleshooting

## `Original firmware not found`

Make sure the original firmware is located at:

```text
target/SHTRV-01_build_2.2.4.gbl
```

Check the filename carefully.

---

## Firmware validation fails

Do not try to bypass the validation.

The patcher is intentionally designed to stop when the input firmware does not match the supported original firmware.

Possible causes include:

- wrong firmware version
- firmware for another Shelly device
- modified firmware
- damaged download
- incorrectly renamed firmware file

Use the exact original Shelly TRV Gen1 2.2.4 firmware expected by the patcher.

---

## `python` command not found

Python 3 is either not installed or is not available through your system's command path.

On Windows, also try:

```powershell
py --version
```

On macOS/Linux, try:

```bash
python3 --version
```

---

## OTA server cannot start

Another application may already be using the required network port, or your operating system may require additional permission.

On macOS/Linux, make sure you started it with:

```bash
sudo python3 ota_server.py
```

Also check whether your firewall is blocking incoming connections to Python.

---

## The TRV does not download the firmware

Check that:

1. the TRV and computer are on the same local network
2. the OTA server is still running
3. the computer IP address in the OTA URL is correct
4. the TRV IP address is correct
5. your firewall allows the connection
6. the firmware URL shown by the OTA server is reachable on your local network

Do not use `localhost` or `127.0.0.1` in the OTA URL.

Those addresses would refer to the TRV itself when requested by the TRV, not to your computer.

---

## The browser shows `status: updating`

That is expected.

It means the TRV accepted the OTA request.

Now watch the OTA server terminal and allow the device to complete the transfer, installation, and reboot.

---

## The OTA server says the transfer completed successfully

This confirms the HTTP transfer.

It does not by itself confirm installation.

Wait for the TRV to reboot and check:

```text
http://TRV-IP/status
```

---

## `/status` still reports firmware 2.2.4

That is correct.

The patch intentionally retains the original 2.2.4 firmware identification.

---

# 19. Keep the firmware files private

The repository intentionally does not contain original or patched Shelly firmware images.

The following files should remain local:

```text
target/SHTRV-01_build_2.2.4.gbl
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

The repository's `.gitignore` is configured to prevent firmware files in `target` from being committed.

Do not remove this protection when contributing to the project.

---

# 20. Quick reference

Once everything is prepared, the complete process is:

### 1. Put the original firmware here

```text
target/SHTRV-01_build_2.2.4.gbl
```

### 2. Run the patcher

Windows:

```powershell
python patch_firmware_v.1.0.py
```

macOS/Linux:

```bash
python3 patch_firmware_v.1.0.py
```

### 3. Confirm that this file was created

```text
target/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

### 4. Start the OTA server

Windows:

```powershell
python ota_server.py
```

macOS/Linux:

```bash
sudo python3 ota_server.py
```

### 5. Note the firmware URL displayed by the server

Example:

```text
http://192.168.1.100/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

### 6. Start the OTA update

Open this pattern in a browser:

```text
http://TRV-IP/ota?url=http://COMPUTER-IP/SHTRV-01_2.2.4_beacon_mdns_patch.gbl
```

or use:

```bash
curl "http://TRV-IP/ota?url=http://COMPUTER-IP/SHTRV-01_2.2.4_beacon_mdns_patch.gbl"
```

### 7. Wait for transfer, installation, and reboot

Do not interrupt the device.

### 8. Check the TRV

Open:

```text
http://TRV-IP/status
```

The firmware should report:

```text
20240619-130912/v2.2.4@ee290818
```

The version remaining at 2.2.4 is expected.

---

## Further information

For an overview of the project, see:

```text
README.md
```

For technical details about the firmware modifications and reverse engineering, see:

```text
docs/technical-details.md
```

For OTA server details, see:

```text
docs/ota_server.md
```

For test procedures and current validation status, see:

```text
tests/README.md
```