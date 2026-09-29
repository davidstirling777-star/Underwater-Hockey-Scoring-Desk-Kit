# Zigbee2MQTT Wireless Siren Setup Guide

This guide covers the wireless siren in the **Underwater Hockey Scoring Desk Kit (UWH)**: installation on **Windows 11** or **Raspberry Pi 5 / Raspberry Pi OS Bookworm**, MQTT configuration for Python, pairing and naming buttons, and using more than one computer. The Windows MQTT setup has been tested with **up to three working Zigbee buttons** on one coordinator (`siren_button`, `siren_button_2` and `siren_button_3`). Observed action values include `single`, `double`, `hold` and `emergency`; **individual buttons may publish different actions**, and the mapping for each action is configured in UWH. The Raspberry Pi 5 **UWH desktop application** has been tested on Bookworm + X11; the full Pi Zigbee/MQTT installation procedure remains a deployment guide to verify on the target Pi.

> [!IMPORTANT]
> **A button joins one Zigbee network at a time. Do not re-pair an existing match button to another coordinator merely to use a second computer.** A second UWH computer can subscribe to the *same MQTT broker*, receiving events from the original Zigbee2MQTT instance. Re-pairing to a different Zigbee network generally removes the button from the original network and requires a reset and rejoin when moving it back. See [Using two computers](#using-two-computers-with-the-same-buttons).
>
> **Two UWH applications listening for the same button can BOTH activate their local sirens.** Decide which computer controls the live PA/amplifier and test the routing before a match.

> [!WARNING]
> **Back up `settings.json` before every UWH upgrade.** Its Zigbee button list is separate from Zigbee2MQTT's device database. Losing `settings.json` does *not* unpair a button, but UWH may stop recognising additional button names until they are re-entered.

## Contents

- [How the system works](#how-the-system-works)
- [Raspberry Pi 5: Mosquitto, Python MQTT and Zigbee2MQTT](#raspberry-pi-5-mosquitto-python-mqtt-and-zigbee2mqtt)
- [Windows 11: Mosquitto, Python MQTT and Zigbee2MQTT](#windows-11-mosquitto-python-mqtt-and-zigbee2mqtt)
- [Pairing and naming buttons in the frontend](#pairing-and-naming-buttons-in-the-frontend)
- [Configure the UWH Zigbee Siren tab](#configure-the-uwh-zigbee-siren-tab)
- [Button actions and siren playback](#button-actions-and-siren-playback)
- [Using two computers with the same buttons](#using-two-computers-with-the-same-buttons)
- [Network access and security](#network-access-and-security)
- [Updates, backups and troubleshooting](#updates-backups-and-troubleshooting)
- [Official references](#official-references)

## How the system works

```text
Zigbee button(s)
       |  Zigbee radio (not Wi-Fi / not MQTT)
       v
Zigbee USB coordinator -- Zigbee2MQTT (Node.js)
                                 |
                                 | MQTT publish
                                 v
                        Mosquitto MQTT broker
                                 |
                      MQTT subscribers (Python / UWH)
                                 |
                    UWH siren sound on this computer
```

- **Zigbee2MQTT** manages the physical Zigbee network. It uses **Node.js**, *not Python*.
- **Mosquitto** is the MQTT message broker. The broker and Zigbee2MQTT can run on the same computer, or on different computers if properly configured.
- **Python `paho-mqtt`** is the MQTT *client library* used by a source-code UWH installation. Installing it does **not** install a broker or Zigbee2MQTT.
- **UWH** subscribes to button messages. The selected *Siren* audio file is played by UWH on its own audio output; a separate Zigbee siren device is **not** needed for this use case.
- **Arduino hardwired siren:** its local press/hold/release audio path is independent of MQTT. If an optional MQTT siren output is configured, the Arduino can also send ON/OFF commands to that separate output.

For the simple local installation, all three software components run on one machine, and the MQTT broker is `localhost:1883`. For a second UWH computer, set its **MQTT Broker** field to the hostname or LAN IP address of the existing broker; `localhost` would point to the *second* computer, not the first.

**USB-adapter caution:** A COM port identified as `CP210x` or `FTDI` describes a USB/serial interface, not proof that the device is a supported Zigbee coordinator. Check the actual adapter model and firmware against [Zigbee2MQTT's supported adapters](https://www.zigbee2mqtt.io/guide/adapters/). Zigbee2MQTT and a second program must not both try to open the same coordinator serial port.

## Raspberry Pi 5: Mosquitto, Python MQTT and Zigbee2MQTT

This section assumes the UWH source checkout and its virtual environment are installed as described in [README.md](README.md). The tested UWH desktop uses **Raspberry Pi OS Bookworm + Python 3.11 + X11**; Python 3.12 is **not** a prerequisite for that setup. These Zigbee installation commands are adapted from the current official Linux guidance; check the [upstream instructions](https://www.zigbee2mqtt.io/guide/installation/01_linux.html) for any later changes.

### 1. Install and test the Mosquitto broker

In a Pi terminal:

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
systemctl status mosquitto --no-pager
```

For a first test, open **terminal A**, then **terminal B**:

```bash
# Terminal A: wait for ONE test message
mosquitto_sub -h localhost -t uwh/test -C 1
```

```bash
# Terminal B: send it
mosquitto_pub -h localhost -t uwh/test -m 'MQTT working'
```

Terminal A should print `MQTT working`. Use different terminals: a subscriber started *after* a non-retained message was sent will miss that message. An ordinary local-only broker needs no network listener or external firewall rule. See [Network access and security](#network-access-and-security) before allowing remote clients.

### 2. Install the Python MQTT client in the UWH virtual environment

From your **actual UWH checkout directory** (the README's example is shown below):

```bash
cd ~/Downloads/Underwater-Hockey-Scoring-Desk-Kit-main
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install paho-mqtt
.venv/bin/python -c "import paho.mqtt.client; print('Python MQTT OK')"
```

`paho-mqtt` may already be present in `requirements.txt`; the explicit install is a way to confirm it is installed in **this** `.venv`. Avoid `sudo pip install` and `--break-system-packages` on Bookworm. The UWH app can be launched with `.venv/bin/python uwh.py` as explained in the README.

### 3. Install and start Zigbee2MQTT

Install the Node.js version recommended by the [current Zigbee2MQTT Linux instructions](https://www.zigbee2mqtt.io/guide/installation/01_linux.html). At the time of this guide, their installation flow is:

```bash
sudo apt-get install -y curl
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs git make g++ gcc libsystemd-dev
sudo corepack enable
node --version
```

Now install Zigbee2MQTT. The commands use `/opt/zigbee2mqtt`; change the location if you already have an installation:

```bash
sudo mkdir -p /opt/zigbee2mqtt
sudo chown -R "$USER":"$USER" /opt/zigbee2mqtt
git clone --depth 1 https://github.com/Koenkk/zigbee2mqtt.git /opt/zigbee2mqtt
cd /opt/zigbee2mqtt
pnpm install --frozen-lockfile
pnpm start
```

On a **new** install, open `http://localhost:8080` in the Pi's browser and complete onboarding: choose the coordinator, set the MQTT server to `mqtt://localhost:1883`, and enable the frontend. When the UI is already configured, the relevant settings in `/opt/zigbee2mqtt/data/configuration.yaml` resemble:

```yaml
mqtt:
  base_topic: zigbee2mqtt
  server: 'mqtt://localhost:1883'
frontend:
  enabled: true
```

Do **not** replace an existing `configuration.yaml` with this fragment: preserve its network and serial settings. Newer Zigbee2MQTT versions may add a `version` key or other settings during onboarding. Use **one** coordinator, detected automatically where supported; if discovery fails, consult [adapter settings](https://www.zigbee2mqtt.io/guide/configuration/adapter-settings.html) and, on the Pi, check `ls -l /dev/serial/by-id/`. Do not assume a particular `/dev/ttyUSB0` or adapter type.

### 4. Optional: start Zigbee2MQTT automatically on Pi boot

Only after `pnpm start` works, stop that foreground instance with **Ctrl+C**. The official Linux guide documents [running Zigbee2MQTT under systemd](https://www.zigbee2mqtt.io/guide/installation/01_linux.html). For a normal `/opt/zigbee2mqtt` install, create a service with the correct local username and Node path (`command -v node`):

```bash
sudo nano /etc/systemd/system/zigbee2mqtt.service
```

```ini
[Unit]
Description=Zigbee2MQTT
Wants=network-online.target
After=network-online.target mosquitto.service

[Service]
Type=simple
User=YOUR_LINUX_USERNAME
WorkingDirectory=/opt/zigbee2mqtt
ExecStart=/usr/bin/node /opt/zigbee2mqtt/index.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_LINUX_USERNAME` with the output of `whoami` and check that `/usr/bin/node` agrees with `command -v node`. Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now zigbee2mqtt
systemctl status zigbee2mqtt --no-pager
# For diagnostic messages:
sudo journalctl -u zigbee2mqtt -n 50 --no-pager
```

Do not also leave a manual `pnpm start` instance running against the same coordinator. Boot-time operation on a particular Pi must still be tested after reboot.

## Windows 11: Mosquitto, Python MQTT and Zigbee2MQTT

The **tested Windows path is Mosquitto + native Windows Zigbee2MQTT + UWH over MQTT**. WSL2 is not required. Directly opening the Zigbee coordinator's COM port from UWH is **not** a substitute for Zigbee2MQTT pairing and is not the verified wireless-button path.

### 1. Install and test Mosquitto on Windows

1. Download the Windows installer from [Eclipse Mosquitto](https://mosquitto.org/download/). Install it with its Windows service enabled.
2. Open **Services** (`services.msc`). Find **Mosquitto Broker** (service name commonly `mosquitto`), set **Startup type → Automatic**, and make sure it is **Running**.
3. Open two Command Prompt windows. The executable locations below assume the default install folder; use your actual install path if different.

Command Prompt A:

```cmd
"C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -t uwh/test -C 1
```

Command Prompt B:

```cmd
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t uwh/test -m "MQTT working"
```

Prompt A should print `MQTT working`. If the service does not exist, review the Mosquitto installer and [Windows service instructions](https://github.com/eclipse-mosquitto/mosquitto/blob/master/README-windows.txt). **Do not start a second Mosquitto process on the same port** while the service is running. On a local-only installation, UWH and Zigbee2MQTT both use `localhost`.

### 2. Install Zigbee2MQTT natively on Windows

Install **Node.js 22 LTS** (or the version named in the [current Windows instructions](https://www.zigbee2mqtt.io/guide/installation/05_windows.html)) and Git. In a new **Command Prompt**:

```cmd
node --version
corepack enable
git clone --depth 1 https://github.com/Koenkk/zigbee2mqtt.git C:\zigbee2mqtt
cd /d C:\zigbee2mqtt
pnpm install --frozen-lockfile
pnpm start
```

`C:\zigbee2mqtt` matches the tested Windows installation. If it already exists, **do not clone over it or delete its `data` directory**. Follow the upstream update procedure instead.

Open `http://localhost:8080`. Complete the new-install onboarding or, for an existing installation, ensure `C:\zigbee2mqtt\data\configuration.yaml` includes the appropriate existing settings:

```yaml
mqtt:
  base_topic: zigbee2mqtt
  server: 'mqtt://localhost:1883'
frontend:
  enabled: true
```

Check that your actual USB Zigbee coordinator is found. If it is not, open **Device Manager → Ports (COM & LPT)**, identify its COM port, and use the Zigbee2MQTT [serial/adapter settings](https://www.zigbee2mqtt.io/guide/configuration/adapter-settings.html) to specify the correct port and adapter for *your* model. Seeing a `CP210x` device alone does not establish coordinator compatibility.

### 3. Python MQTT for Windows source installations

If you run **`uwh.py` from Python** rather than the published Windows ZIP, install the project's requirements and `paho-mqtt` in the interpreter or virtual environment actually used for UWH:

```cmd
py -m pip install -r requirements.txt
py -m pip install paho-mqtt
py -c "import paho.mqtt.client; print('Python MQTT OK')"
```

Run those commands from the project directory, using your selected interpreter if `py` is not the correct one. **Users running the packaged UWH `.exe` normally do not install Python or `paho-mqtt` separately**; the executable must have been built with the needed dependencies.

### 4. Tested Windows automatic startup: PM2 and Task Scheduler

Once manual `pnpm start` works, stop it with **Ctrl+C**. From the Windows account that will own PM2:

```cmd
npm install -g pm2
cd /d C:\zigbee2mqtt
pm2 start index.js --name zigbee2mqtt
pm2 save
pm2 list
```

`pm2 save` stores the process list under that account's `.pm2` folder. If PM2 has an empty process list after reboot, **`pm2 resurrect`** restores the saved processes; `pm2 restart zigbee2mqtt` cannot restart a process that does not yet exist in that daemon.

> [!NOTE]
> On Windows, `pm2 startup` can fail with **“Init system not found”**. The tested solution uses **Windows Task Scheduler** instead.

Create a Task Scheduler **Create Task...** entry:

| Task field | Tested setup |
|---|---|
| General → Name | `Start Zigbee2MQTT` |
| General → Security | Use the **same Windows account** that ran `pm2 save`; select **Run whether user is logged on or not**. A Windows *account password* may be required (not the sign-in PIN). |
| Trigger | **At startup**; delay **1 minute** so the broker and system can start first |
| Action | **Start a program** |
| Program/script | `C:\Windows\System32\cmd.exe` |
| Add arguments | `/d /c "C:\Users\YOUR_WINDOWS_USER\AppData\Roaming\npm\pm2.cmd resurrect"` |
| Start in | `C:\zigbee2mqtt` |
| Conditions | Do not require idle time, AC power, or a specific network connection |
| Settings | Allow on-demand runs; run after a missed scheduled start; optionally retry failures; **Do not start a new instance** |

Use `where pm2` to find **your actual** `pm2.cmd` path, replacing `YOUR_WINDOWS_USER` (and the entire path if necessary). Leave **“Do not store password”** unchecked if Windows prompts for the account password. Disable **“Stop the task if it runs longer than...”**. In **Services**, keep Mosquitto set to **Automatic**. Only one PM2 instance should control this Zigbee2MQTT process.

**Verify:** reboot Windows, wait about two minutes, then open `http://localhost:8080` **before** manually running PM2. In the tested setup, the frontend and wireless button reception returned after restarting Windows. A separate sign-in test with a second Windows account has not yet been documented.

## Pairing and naming buttons in the frontend

These steps apply to **both** platforms and are performed on the **single Zigbee2MQTT instance that owns the coordinator**.

1. Open the Zigbee2MQTT frontend: `http://localhost:8080` if browsing on the Zigbee2MQTT host, or `http://HOST-IP:8080` if its frontend is deliberately accessible on your LAN. The UWH **Open Zigbee2MQTT Frontend** button targets `localhost`; on a second computer, use the host's LAN address directly.
2. Use **Permit join** in the frontend (currently in the top navigation area). Current Zigbee2MQTT documentation says this opens joining for **254 seconds**; close it earlier when finished. The timing/UI wording can change with releases.
3. Put the button into pairing/reset mode **using the instructions for its exact model**. Do not assume a universal hold duration or LED pattern.
4. Wait for the device to join and finish its interview. If joining fails, follow the model's factory reset instructions and retry nearer the coordinator.
5. Open the device's page in the frontend and edit its **friendly name** (usually accessible from the device details or rename action). Use simple unique names **without `/`**, e.g. `siren_button`, `siren_button_2` and `siren_button_3`.
6. Close **Permit join**. Press each button and watch its device page or Zigbee2MQTT log. A successful button event produces an MQTT topic corresponding to its friendly name:

```text
zigbee2mqtt/siren_button
zigbee2mqtt/siren_button_2
zigbee2mqtt/siren_button_3
```

Example message payloads:

```json
{"action":"single","battery":93,"linkquality":98,"voltage":2900}
```

The `action` value is what UWH uses. Battery/link-quality-only updates do **not** request a siren. If you rename `siren_button_2` to `referee_two`, its MQTT topic becomes `zigbee2mqtt/referee_two`; **update the UWH button list too**. A Zigbee device may send other action strings; check the actual MQTT message before assuming they map to UWH siren actions.

**Why simple names?** UWH's current subscription example is `zigbee2mqtt/+` and the current handler extracts the **last segment** of the topic. A Zigbee2MQTT friendly name containing `/` creates a deeper MQTT topic and will not match that configuration reliably. Avoid spaces and keep names identical between Zigbee2MQTT and UWH.

## Configure the UWH Zigbee Siren tab

Open UWH → **Zigbee Siren**. Configure the application against the broker you actually use:

| UWH field | One-computer setup | Second computer sharing the same broker |
|---|---|---|
| **MQTT Broker** | `localhost` | Existing broker's **LAN IP address or DNS name** |
| **MQTT Port** | `1883` | Broker's listener port, normally `1883` |
| **MQTT Username/Password** | Leave empty only if that broker allows local unauthenticated access | Enter the broker credentials (recommended) |
| **MQTT Topic** | `zigbee2mqtt/+` | Same, if the host publishes the normal base topic |
| **Button Device Names (comma-separated)** | Enter the buttons in use; up to three have been tested together: `siren_button, siren_button_2, siren_button_3` | Names this UWH computer should respond to |
| **Siren Device Name** | Leave unchanged for ordinary **local audio** triggering | Not the input button-name list |

1. Enter the exact friendly names in **Button Device Names**, separated by commas; enter only the buttons in use.
2. Click **Save Configuration**. If you changed the broker, topic or device names while connected, reconnect or restart UWH so the active connection uses the new configuration.
3. Click **Test App Siren** to check the selected local sound independently of Zigbee reception.
4. Press each physical button and inspect **Activity Log**. For example, `Button 'siren_button_2' action 'single' received via Zigbee/MQTT.` confirms UWH received that message, **not** that the action is mapped to make sound.
5. In **Button Action Mapping**, find the row for the exact button name and received action. To add an unfamiliar action, press that configured button and click **Auto-add From Log**. The new row is deliberately set to **Ignore**; select **Edit Mapping** and choose the intended action, such as **One siren cycle**.
6. Click **Save Action Mappings**. This is distinct from saving the device-name list with **Save Configuration**. Test each button again and confirm its intended response. For a new button, check what it actually publishes; for example, a tested button uses `emergency` rather than `single`.
7. For a continuous-press mapping, provide the correct release action as a separate **Stop continuous siren** mapping and check the **Maximum hold (s)** cutoff (default 10; allowed 1–30 seconds). Only use that mode after checking the device's actual press/release messages.

UWH stores these values in the **`zigbeeSettings` section of `settings.json`**. A representative extract is:

```json
{
  "zigbeeSettings": {
    "mqtt_broker": "localhost",
    "mqtt_port": 1883,
    "mqtt_topic": "zigbee2mqtt/+",
    "siren_button_devices": ["siren_button", "siren_button_2", "siren_button_3"],
    "siren_button_device": "siren_button"
  }
}
```

This is a **partial example**, not a replacement for the complete `settings.json`. The actual file also holds **`action_mappings`**; the list of button names alone does not specify which received actions should sound the siren. The legacy `siren_button_device` entry may coexist with the multi-device list; use the UI to save the full configuration. Keep the **UWH configuration** (`settings.json`) and **Zigbee2MQTT's own `data` directory** backed up separately.

## Button actions and siren playback

The table describes **observed actions and their tested mappings**, not a universal set of button commands. UWH responds only when the device and exact received action have been configured:

| Observed Zigbee2MQTT `action` | Example UWH mapping |
|---|---|
| `single` | **One siren cycle** of **Number of seconds to play Siren** |
| `double` | **Two siren cycles**, consecutive, with no deliberately programmed pause |
| `hold` | **One siren cycle** for the tested button, which sends `hold` on release |
| `emergency` | A separately configured mapping, such as **One siren cycle**, for a button that publishes `emergency` |

For example, a configured duration of **1.5 seconds** gives approximately 1.5 seconds for one timed cycle and two consecutive cycles for a mapped `double`. Actual audio-start/stop overhead may cause a small transition between cycles. Different models publish different long-press and release values: inspect each button's log rather than assuming the table applies automatically.

**Important:** On the tested button, the `hold` action arrives **on release**; mapping that action to **One siren cycle** is not continuous press-to-sound. The Zigbee mapping table also offers **Start continuous siren** and **Stop continuous siren**, but these require actual matching press/release messages and are bounded by the hold timer and audio cutoff. The **hardwired Arduino button** instead sounds locally while physically held and stops on release. Timed game and wireless sirens use the selected **Sounds** file and duration, subject to **Maximum Siren Duration (seconds)** (default 10; allowed 1–30 seconds). Confirm Air/Water routing on the actual hardware.

## Using two computers with the same buttons

### Supported arrangement: one Zigbee network, multiple MQTT clients

```text
                           ONE Zigbee network
button 1 -----\
button 2 ------> Coordinator + Zigbee2MQTT ----> MQTT broker
button 3 -----/
                                                   |           |
                                     MQTT client A |           | MQTT client B
                                                   v           v
                                                UWH PC 1    UWH PC 2
```

The two UWH applications can be on **Windows, Raspberry Pi, or a mixture**; they can each subscribe to the same broker. The button is paired **once**, to the **one** coordinator. The second computer does not require another Zigbee USB dongle or a second Zigbee2MQTT instance merely to receive those button messages.

**Example:** Zigbee2MQTT and Mosquitto run on Windows PC 1, whose broker is reachable at `192.168.1.50` (illustrative address only). UWH on PC 1 uses `MQTT Broker: localhost`. UWH on the Raspberry Pi/PC 2 uses `MQTT Broker: 192.168.1.50`, the same port and the same relevant button names. Both subscribe to the existing Zigbee2MQTT topics. The broker must be configured for authenticated LAN access; `localhost` on PC 2 would not reach PC 1.

> [!CAUTION]
> **Shared-button siren hazard:** If both UWH applications listen for `siren_button` and both computers are connected to an audible amplifier, pressing the button can activate **two sirens**. Each UWH instance has its own sound state and is *not* automatically synchronised with the other's game clock. If the intention is one live siren, configure only the designated controlling application to accept that button (or otherwise isolate/mute the secondary audio output). Test this with the actual PA before play. Do not assume MQTT provides automatic active/standby failover.

### Different arrangement: moving a button to another Zigbee coordinator

If the second computer has a **different Zigbee coordinator and different Zigbee network**, a standard Zigbee button cannot normally remain joined to **both** networks. Moving it usually involves a model-specific reset and joining the second network. This can make it disappear from the first coordinator's working network until moved back. **Do not do this to a live referee button just to get a second UWH display or client.** See the [official Zigbee2MQTT FAQ](https://www.zigbee2mqtt.io/guide/faq/) for the one-coordinator/one-network limitation.

Running two *independent* Zigbee2MQTT networks on one broker also requires different `base_topic` values; the corresponding UWH topic must match. This is a separate advanced deployment, not a way to pair one button to both radios simultaneously.

## Network access and security

**On the same computer:** use `localhost` for MQTT; do not expose broker port **1883** or frontend port **8080** to the internet. New Mosquitto installations without a configured listener commonly accept only local connections.

**For a second computer:** the broker must accept connections from the trusted LAN, and all MQTT clients (Zigbee2MQTT and UWH) must use its actual network address. Configure a listener, authentication and firewall restrictions *before* exposing port 1883. Mosquitto 2.x does **not** automatically accept remote anonymous connections when a listener is added.

A typical **Debian/Raspberry Pi** authenticated listener can be configured by creating a password file and `/etc/mosquitto/conf.d/uwh.conf`:

```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd uwh_mqtt
sudo chown root:mosquitto /etc/mosquitto/passwd
sudo chmod 640 /etc/mosquitto/passwd
sudo nano /etc/mosquitto/conf.d/uwh.conf
```

```conf
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```

```bash
sudo systemctl restart mosquitto
```

Enter `uwh_mqtt` and its chosen password into **both** Zigbee2MQTT's MQTT configuration (`mqtt.user` and `mqtt.password`) and UWH's MQTT fields. If your Mosquitto already has authentication or a listener, **adapt the existing configuration** rather than defining a conflicting second listener.

For an **optional Windows LAN broker**, first back up the service's existing `mosquitto.conf`. In an **Administrator Command Prompt**, create an authentication file (the `-c` option creates/overwrites it; do **not** use `-c` on an existing password file containing other users):

```cmd
mkdir C:\ProgramData\UWH
"C:\Program Files\mosquitto\mosquitto_passwd.exe" -c "C:\ProgramData\UWH\mqtt.passwd" uwh_mqtt
```

Add or adapt these settings in the **existing** `mosquitto.conf` used by the Mosquitto Windows service, usually in its installation directory:

```conf
listener 1883
allow_anonymous false
password_file C:/ProgramData/UWH/mqtt.passwd
```

Restart the **Mosquitto Broker** service using `services.msc`. Configure its credentials in **both** UWH and Zigbee2MQTT; **otherwise even a formerly working local connection will be rejected**. The service account must be able to read the password file. Test a local MQTT client first, then PC 2 using the Windows host's LAN IP address. Restrict Windows Firewall **TCP 1883** access to the trusted local network; do **not** open it on a public network. Read the [Mosquitto authentication documentation](https://mosquitto.org/documentation/authentication-methods/) before modifying a production installation.

Plain MQTT on port **1883 is not encrypted**; use a trusted LAN, or TLS/VPN for less trusted connections. Never publish broker passwords in public GitHub documentation, screenshots or bug reports.

The frontend on port 8080 is **separate from MQTT**. Opening a webpage on PC 2 does not establish an MQTT client connection, and UWH's **Open Zigbee2MQTT Frontend** button opens `localhost:8080` on **that** PC. Access the host frontend by the host address only when intentionally configured and secured for LAN use.

## Updates, backups and troubleshooting

### What to back up

| Item | What it contains | Important distinction |
|---|---|---|
| **UWH `settings.json`** | Siren files/duration, MQTT broker, button-name list, **action mappings**, display settings and other app preferences | Restoring its names **and mappings** can recover UWH recognition without re-pairing. Back it up before replacing a UWH ZIP; UWH also retains up to five recent `settings_old_*.json` backups. |
| **UWH tournament CSVs, custom `assets/` sounds, logs** | Tournament/game data and custom audio | A UWH update must not overwrite them. |
| **Zigbee2MQTT `data/` folder** | Zigbee2MQTT configuration and network/device database | Back up before changing Zigbee2MQTT or moving installations; preserving the coordinator/network data matters for retained pairing. |
| **PM2 process list on Windows** | Saved Zigbee2MQTT startup process for that Windows user | Run `pm2 save` after setup. A Task Scheduler task alone does not recreate a missing PM2 saved process. |

### Troubleshooting checklist

| Observation | What to check |
|---|---|
| Frontend does not open at `localhost:8080` | Is Zigbee2MQTT actually running? On Windows, check `pm2 list`, `pm2 logs zigbee2mqtt` and Task Scheduler's **Last Run Result**; on Pi check `systemctl status zigbee2mqtt`. Check frontend enablement and port. |
| UWH displays **Connected** but no button appears in the activity log | **Connected** means the MQTT broker session is up, not that a button is paired or mapped. Press the button and inspect Zigbee2MQTT's log; compare the **friendly name**, MQTT topic (`zigbee2mqtt/+`), and **Button Device Names**. UWH's Arduino/USB labels report **Detected** ports, not proof that an Arduino COM port was opened. |
| One button works but another does not | Check that each button's exact friendly name appears in **Button Device Names** and click **Save Configuration**. Press it and check the **Activity Log**. If it says **Unmapped action**, use **Auto-add From Log**, change **Ignore** to the desired response and **Save Action Mappings**. Missing settings do not necessarily mean the device needs re-pairing. |
| Zigbee2MQTT publishes `{"battery":...}` but UWH is silent | A battery-only update has **no `action`**; it is device status rather than a button press. |
| A newly named button stops working | A frontend rename changes the device MQTT topic. Update UWH's exact friendly-name list. |
| One PC sees the events, the other does not | PC 2 must connect to PC 1's *LAN broker address*, not its own `localhost`. Check Mosquitto listener/authentication, firewall, subnet and MQTT topic. |
| Both PCs sound their sirens | Both subscribed to the same button; this is expected, not a pairing fault. Configure the standby application's allowed button names or audio routing. |
| Windows broker works but Zigbee2MQTT does not start after boot | Set Mosquitto **Automatic**; confirm `pm2 save` under the task's Windows account and correct `pm2.cmd`/working directory; inspect Scheduler history. Do not run two PM2 instances. |
| Pi MQTT fails with `ModuleNotFoundError` | Check `.venv/bin/python -m pip show paho-mqtt`, then run UWH using that same virtual environment. |
| Frontend says adapter missing / port busy | Find the actual COM port or `/dev/serial/by-id`; confirm adapter type and permissions, and close any other program using the coordinator. |
| Audible siren works but time/volume is different | Check the **Sounds** tab's siren file, **Number of seconds to play Siren**, **Maximum Siren Duration**, and hardware audio routing. Arduino hold-to-sound differs from Zigbee timed actions. |

**Useful diagnostic commands** (use the correct host and authentication options for your broker):

```bash
# Pi / Linux: view button events while pressing a button
mosquitto_sub -h localhost -t 'zigbee2mqtt/+' -v

# Pi / Linux: check broker service and Zigbee2MQTT service
systemctl status mosquitto --no-pager
systemctl status zigbee2mqtt --no-pager
```

```cmd
REM Windows Command Prompt: change path if Mosquitto is installed elsewhere
"C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -t "zigbee2mqtt/+" -v
pm2 list
pm2 logs zigbee2mqtt
```

If MQTT authentication is enabled, use authenticated client options or the UWH UI's credentials; do not paste credentials into screenshots or public GitHub issues. If the frontend shows button actions but UWH is silent, verify the sound with **Test App Siren**, then confirm the button is listed **and** its received action has a saved mapping. An Arduino `Access is denied` COM-port error is a separate serial-access problem: close other serial monitors or programs holding that port.

## Official references

- [Zigbee2MQTT getting started and onboarding](https://www.zigbee2mqtt.io/guide/getting-started/)
- [Zigbee2MQTT Linux installation](https://www.zigbee2mqtt.io/guide/installation/01_linux.html)
- [Zigbee2MQTT Windows installation](https://www.zigbee2mqtt.io/guide/installation/05_windows.html)
- [Pairing devices / Permit join](https://www.zigbee2mqtt.io/guide/usage/pairing_devices.html)
- [MQTT topics, friendly names and device rename](https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html)
- [Zigbee2MQTT FAQ: one coordinator and one network per device](https://www.zigbee2mqtt.io/guide/faq/)
- [Mosquitto downloads](https://mosquitto.org/download/), [Windows service instructions](https://github.com/eclipse-mosquitto/mosquitto/blob/master/README-windows.txt), [MQTT authentication](https://mosquitto.org/documentation/authentication-methods/)
- [Eclipse Paho Python client](https://pypi.org/project/paho-mqtt/)

**Project documentation:** [README.md](README.md) covers downloading/running UWH, screen layouts, sounds, and the scoring interface. [HARDWARE_SETUP.md](HARDWARE_SETUP.md), where supplied, covers the wired hardware.
