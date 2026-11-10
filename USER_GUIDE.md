\# Shelly TRV Gen1 – B2.2 Beta Installation Guide



This guide explains how to generate and install \*\*B2.2 Beta firmware\*\* on a Shelly TRV Gen1 (`SHTRV-01`) using the original Shelly 2.2.4 firmware and the included patcher.



No reverse-engineering knowledge is required.



> \*\*Beta firmware – November 2026\*\*

>

> B2.2 has shown encouraging battery results in hardware testing. However, unexpected automatic reboots have been observed on several devices, and their cause remains unknown.

>

> This is an independent community project, not an official Shelly firmware release. Use it only if you understand and accept the risks of firmware modification.



\## 1. Before You Begin



\### Requirements



You will need:



\- A Shelly TRV Gen1 (`SHTRV-01`)

\- The exact supported original Shelly 2.2.4 firmware

\- A Windows, macOS, or Linux computer

\- Python 3

\- This project's source files

\- A local network connection between the computer and the TRV



No additional Python packages are required. The patcher and OTA server use the Python standard library.



\*\*Before flashing:\*\* Ensure the TRV is sufficiently charged, has stable network connectivity, and can be accessed physically if recovery becomes necessary. Do not interrupt power during the update. Consider the consequences of interrupted heating control before testing.



\### Supported firmware



| Property | Required value |

|---|---|

| Device | Shelly TRV Gen1 / SHTRV-01 |

| Original firmware | 2.2.4 |

| Build | `20240619-130912/v2.2.4@ee290818` |

| Original GBL size | 1,106,384 bytes |



\*\*Original firmware SHA-256:\*\*



```text

5c4a0b222a313350952f6b1200a855833402f168bd286090c23bd4d018ab918f

```



The patcher accepts only this exact firmware image. Renaming another firmware file does not make it compatible.



\## 2. Download and Prepare the Patcher



\### Download the repository



On GitHub, select \*\*Code → Download ZIP\*\* and extract the archive to a folder on your computer.



Alternatively, clone the repository using Git.



\### Verify Python



\*\*Windows:\*\* Open PowerShell or Windows Terminal and run:



```powershell

py --version

```



If the Python launcher is unavailable, try:



```powershell

python --version

```



\*\*macOS / Linux:\*\* Open Terminal and run:



```bash

python3 --version

```



A Python 3 version should be displayed.



If Python is not installed, install a current Python 3 release before proceeding.



\### Prepare the original firmware



Obtain the original supported Shelly TRV Gen1 2.2.4 firmware independently.



Rename it, if necessary, to the required filename and place it in the repository's `target` directory:



```text

target/SHTRV-01\_build\_2.2.4.gbl

```



Do not modify the contents of the firmware file.



The patcher will verify the exact file identity before performing any reconstruction.



\### Open a terminal in the repository



All commands in this guide must be executed from the repository's main directory, which contains:



```text

patch\_firmware\_v2.0.py

ota\_server.py

README.md

```



\*\*Windows:\*\* Open the repository folder in File Explorer, right-click in the folder and select \*\*Open in Terminal\*\*.



\*\*macOS:\*\* Open Terminal, type `cd` followed by a space, drag the repository folder from Finder into Terminal, then press Enter.



\*\*Linux:\*\* Use your file manager's terminal option or navigate to the repository with `cd`.



\## 3. Generate B2.2 Beta



Run the patcher from the repository's main directory.



\*\*Windows:\*\*



```powershell

py patch\_firmware\_v2.0.py

```



\*\*macOS / Linux:\*\*



```bash

python3 patch\_firmware\_v2.0.py

```



The patcher will automatically:



1\. Locate and validate the original Stock firmware.

2\. Verify the expected firmware data before modification.

3\. Apply the qualified B2.2 corrections.

4\. Reconstruct the application and GBL.

5\. Verify the generated files against their expected identities.



If any critical validation fails, the process stops.



\### Expected output



After successful reconstruction, the `target` folder contains:



```text

target/

├── SHTRV-01\_build\_2.2.4.gbl

├── SHTRV-01\_2.2.4\_B2.2\_EXPERIMENTAL.bin

└── SHTRV-01\_2.2.4\_B2.2\_EXPERIMENTAL.gbl

```



The generated files retain the `EXPERIMENTAL` filenames to preserve compatibility with the verified B2.2 artifacts and existing OTA server.



\*\*The release classification is Beta.\*\*



\### Verify the output



The patcher performs automatic output verification.



For additional manual verification, the expected B2.2 GBL SHA-256 is:



```text

912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

```



Expected GBL size: \*\*1,126,156 bytes\*\*.



If the patcher reports an integrity failure, do not flash the generated firmware.



\## 4. Start the OTA Server



The included OTA server makes the generated B2.2 GBL available on your local network.



It validates the firmware before serving it and \*\*does not automatically initiate installation\*\*.



The supported Shelly TRV Gen1 OTA workflow uses \*\*TCP port 80\*\*.



\### Windows



Run:



```powershell

py ota\_server.py

```



If required, use a terminal with appropriate permissions and allow incoming connections on your trusted local network through Windows Firewall.



\### macOS / Linux



Run:



```bash

sudo python3 ota\_server.py

```



Port 80 normally requires elevated privileges on these systems.



\### Verify the server address



After successful startup, the OTA server displays a firmware URL similar to:



```text

http://192.168.1.100/SHTRV-01\_2.2.4\_B2.2\_EXPERIMENTAL.gbl

```



This is an example. Your computer's IP address will be different.



Make sure the address is reachable from the TRV.



If your computer uses VPN software or multiple network interfaces, verify that the correct local network address is being used.



Keep the OTA server running throughout the firmware transfer.



\## 5. Install B2.2 on Your TRV



\### Find the TRV's IP address



You can normally find the device's local IP address in your router, the Shelly app or Home Assistant.



For example:



```text

192.168.1.50

```



\### Start the OTA update



Replace the example addresses below with your actual addresses.



\*\*TRV:\*\*



```text

192.168.1.50

```



\*\*Computer running the OTA server:\*\*



```text

192.168.1.100

```



Open the following URL in your browser:



```text

http://192.168.1.50/ota?url=http://192.168.1.100/SHTRV-01\_2.2.4\_B2.2\_EXPERIMENTAL.gbl

```



Alternatively, use a terminal:



```bash

curl "http://192.168.1.50/ota?url=http://192.168.1.100/SHTRV-01\_2.2.4\_B2.2\_EXPERIMENTAL.gbl"

```



A response similar to the following means that the TRV accepted the update request:



```json

{

&#x20; "status": "updating",

&#x20; "has\_update": true

}

```



\*\*This response does not prove that installation has completed successfully.\*\*



\### Monitor the transfer



Watch the terminal running `ota\_server.py`.



The TRV should request:



```text

/SHTRV-01\_2.2.4\_B2.2\_EXPERIMENTAL.gbl

```



The server provides transfer information, including progress and completion status.



Do not stop the OTA server during the transfer.



\### Allow the TRV to restart



After downloading the firmware, the TRV must complete its installation process and reboot.



During this process:



\- Do not disconnect power.

\- Do not manually reset the device.

\- Do not interrupt the network transfer.

\- Do not start another firmware update.



A temporary loss of network connectivity may be normal.



\## 6. Verify the Installation



After the TRV becomes reachable again, open:



```text

http://TRV-IP/status

```



Replace `TRV-IP` with the device's actual address.



\### Firmware version



The TRV will continue to report Shelly firmware 2.2.4:



```text

20240619-130912/v2.2.4@ee290818

```



\*\*This is expected.\*\*



B2.2 deliberately retains the original Shelly version string.



Consequently, `/status` alone cannot distinguish B2.2 from Stock 2.2.4.



The generated firmware identity is established through the patcher's deterministic reconstruction and artifact hash verification. Successful OTA transfer, reboot and runtime checks provide additional installation evidence.



\### Check normal operation



Confirm that:



\- The TRV connects to Wi-Fi.

\- Cloud connectivity works, if enabled.

\- Temperature measurements are available.

\- Calibration is valid.

\- The thermostat accepts temperature changes.

\- The valve responds as expected.



Because B2.2 is beta firmware, monitor the device after installation.



Unexpected automatic reboots have occurred during testing. If you encounter repeated restarts, report the circumstances and available diagnostic information.



\## 7. Troubleshooting



\### Original firmware not found



Confirm that the file exists at:



```text

target/SHTRV-01\_build\_2.2.4.gbl

```



Check the filename and make sure you are running the patcher from the repository's main directory.



\### Firmware validation failed



The original firmware does not match the supported identity or could not be verified.



Check that you obtained the exact Shelly TRV Gen1 2.2.4 build.



\*\*Do not bypass input validation.\*\*



\### Generated firmware hash mismatch



Do not install the firmware.



The expected B2.2 GBL SHA-256 is:



```text

912983973a5467241397b9dd967ee0039440c7d77780a2a97ee494b1a507860c

```



\### Python command not found



Verify your Python installation and try the appropriate command for your operating system:



```text

Windows:       py --version

macOS / Linux: python3 --version

```



\### OTA server cannot bind to port 80



Check whether another application is already using port 80.



On macOS or Linux, ensure that you started the server with the required permissions.



\*\*The current OTA server does not automatically fall back to port 8000.\*\*



\### The TRV cannot download the firmware



Check the following:



\- The computer and TRV can communicate over the local network.

\- The OTA server is still running.

\- Both IP addresses in the OTA URL are correct.

\- Your firewall permits inbound TCP port 80.

\- The selected computer IP belongs to the correct network interface.

\- VPN software is not causing the wrong address to be used.



Do not use `localhost` or `127.0.0.1` as the computer address in the TRV's firmware URL.



\### The browser reports `status: updating`



The update request was accepted. Continue monitoring the OTA server and wait for the TRV to complete installation.



\### The server reports a completed transfer



An HTTP transfer is not proof of successful firmware installation.



Wait for the device to reboot, then verify that it is reachable and operating normally.



\### `/status` still reports version 2.2.4



This is expected because B2.2 retains the original Shelly firmware identity.



\### The TRV restarts unexpectedly after installation



Unexpected automatic reboots are a known issue under investigation.



Record the device's uptime, reboot counter, available diagnostic logs and the time of the restart.



Do not assume that every reboot is a Watchdog reset. Its cause must be established separately.



\## 8. Known Issues and Limitations



\*\*Unexpected automatic restarts:\*\* Observed during multi-device beta testing. The underlying reset cause remains unknown.



\*\*Battery lifetime:\*\* More than six days of testing showed no recurrence of the historical severe battery depletion in the regular B2.2 fleet. This does not yet establish normal battery lifetime over weeks or months.



\*\*Firmware compatibility:\*\* Only the exact supported Stock 2.2.4 build can be used as input.



\*\*Firmware identification:\*\* B2.2 retains the original 2.2.4 version string.



\*\*Technical scope:\*\* B2.2 includes nine selected correction components. It does not claim to fix every possible firmware defect.



See the \[README](README.md) for current testing results and \[Technical Details](docs/technical-details.md) for implementation information.



\## 9. Firmware Files and Security



This repository does not distribute original or modified Shelly firmware images.



Keep the original and generated firmware files local:



```text

target/SHTRV-01\_build\_2.2.4.gbl

target/SHTRV-01\_2.2.4\_B2.2\_EXPERIMENTAL.bin

target/SHTRV-01\_2.2.4\_B2.2\_EXPERIMENTAL.gbl

```



Do not commit these firmware files to the public repository.



The included OTA server is intended for temporary use on a trusted local network. It does not provide authentication or TLS and must not be exposed directly to the public Internet.



Stop the server after completing your update.



For security-sensitive issues, see \[SECURITY.md](SECURITY.md).



\## 10. Further Documentation



| Document | Description |

|---|---|

| \[README](README.md) | Project overview and current battery test results |

| \[Technical Details](docs/technical-details.md) | Firmware corrections and technical qualification |

| \[OTA Server](docs/ota\_server.md) | OTA transport and server behavior |

| \[Testing](tests/README.md) | Patcher verification and regression testing |

| \[Security Policy](SECURITY.md) | Responsible reporting of security issues |



\## Disclaimer



This is an independent firmware research project and is not affiliated with or endorsed by Shelly.



Firmware modification and installation involve risks, including device malfunction, interrupted heating control, loss of configuration or an unusable device.



B2.2 is beta firmware. Its long-term stability and battery lifetime have not been fully established.



\*\*Use this software at your own risk.\*\*
