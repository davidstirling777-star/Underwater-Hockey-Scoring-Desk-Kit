# Underwater Hockey Scoring Desk Kit

A project to allow the use of a computer, modern computer languages, custom printed circuit boards and readily available Arduino or Raspberry Pi 5 hardware to make a scoring and siren system for Underwater Hockey.

**This README is the user manual for the software and hardware assembly.** It combines installation, normal operation, tournament files, two-court results synchronisation, screens, sounds and Zigbee siren setup in one place. The separate `MAINTAINERS.md` is for people modifying the Python source.

The hardware is still being developed but a working prototype has been tested and it does work well. See [Hardware assembly](#hardware-assembly) for the custom control and power PCB build and [`hardware/`](hardware/README.md) for editable KiCad sources for the five custom PCBs you will need to make the system work in totality. `HARDWARE_SETUP.md` preserves earlier bench-test notes; use this README for the current assembly wiring.

The software has an operator-facing Underwater Hockey Game Management App and player-facing and/or spectator-facing Display Window(s). The operator window defaults to opening on the **Game Variables** tab, with six other main tabs: **Scoreboard**, **Tournament List**, **Screens**, **Sounds**, **Siren Control**, and **About**.

## Contents

- [How the application works](#how-the-application-works)
- [Hardware assembly](#hardware-assembly)
- [Known working setups](#known-working-setups)
- [Windows 11 installation](#downloading-and-installing-uwh-on-windows)
- [Raspberry Pi 5 installation](#downloading-and-installing-uwh-on-a-raspberry-pi-5)
- [Game Variables tab](#game-variables-tab)
- [Tournament List tab](#tournament-list-tab)
- [Game Sequence](#game-sequence)
- [Two-court tournament results synchronisation](#two-court-tournament-results-synchronisation)
- [Screens tab](#screens-tab)
- [Sounds tab](#sounds-tab)
- [Scoreboard tab](#scoreboard-tab)
- [Other game behaviour](#other-game-behaviour)
- [Zigbee2MQTT wireless siren setup and operation](#zigbee2mqtt-wireless-siren-setup-and-operation)
- [About tab](#about-tab)
- [Other installation and packaging notes](#other-installation-and-packaging-notes)

## How the application works

UWH separates **match setup**, **live match control**, **public display**, **audio**, and **optional wireless control** so the operator can configure a game before play and then work mainly from the Scoreboard tab.

A normal operating flow is:

1. Start UWH and allow the startup self-test to complete.
2. In the **Game Variables** tab, load a preset or enter the match timings and rules.
3. If a tournament draw is being used, use the **Tournament List** tab to select the draw, starting game and any results synchronisation settings.
4. In the **Screens** tab, select the operator layout and open the required player/spectator Display Window(s). Use **Auto Detect Screens** and **Test Displays** when setting up a new computer or monitor arrangement.
5. In the **Sounds** tab, select and test the siren and pip sounds, per-file trims (to ensure the different sounds are balanced or acceptable) and siren timing.
6. If wireless Zigbee referee buttons are being used, configure and test them in the **Siren Control** tab. The wired siren supports Arduino USB and, on Pi 5, GPIO17, independently or together (see [wired siren setup](#wired-siren-on-raspberry-pi-5--gpio17-and-optional-arduino-usb)). Test each connected wired input and check its ON/OFF events in the **Siren Control → Activity Log**.
7. Use the **Scoreboard** tab during the match for goals, penalties, team time-outs and manual timer control. The player/spectator Display Window follows the live match state.
8. At the end of a tournament game, UWH saves the completed result to a separate results CSV before clearing the live match and advancing to the next selected game. If shared two-court sync is enabled, the local save happens first and network upload happens afterwards in the background (Yet to be tested).

The game clock progresses through First Half, Half Time and Second Half, with optional Overtime and Sudden Death when enabled. The detailed sequence and the special rules for goals recorded during breaks are described later in this manual.

## Hardware assembly

The editable KiCad projects and shared libraries are in [`hardware/`](hardware/README.md). These are development hardware sources, not a claim of completed production or thermal certification. The control and power boards as designed for **1 oz copper** as this seems to be significantly cheaper than 2 oz.

The DC-DC PDMs are populated by the PCB manufacturer as they use tiny SMD components, but unless you are will to pay for them to fit the pin header and viable resistor, you will have to solder them yourself.  I could not bring myself to pay the extra.

### Fit only the PDMs you need

**Only fit DC-DC PDM boards for loads that this assembly will power.** The minimum configuration uses **one PDM: the audio supply at power J15**, for a system with the power board, audio board and wired siren. The control circuit receives backed 24 V separately through power J11 → control J21; it does not need another PDM.

- If you supply your own computer instead of the onboard Raspberry Pi 5, omit the Pi PDM at **J18** and its Pi power harness. Use the external computer's audio output (via a 3.5 mm male to male cable between the computer audio socket and the Pool Audio Board 3.5 mm jack) and the Arduino USB pathway for the wired siren.
- If you are going to use the monitors own external power supplies, omit their screen PDMs at **J2/J5/J7/J9** and the corresponding screen-power leads. Fit only as many screen PDMs as there are monitors powered by this assembly.
- Fit the Raspberry Pi PDM only when powering the onboard Raspberry Pi and fit the audio PDM in every configuration described here. Unused PDM positions can remain empty.

### Board stack and assembly order

1. Open each `.kicad_pro` from KiCad's project manager. Install the standard KiCad libraries; the supplied project library tables locate the shared UWH libraries. Refill copper zones and run ERC/DRC before fabrication.
2. Assemble and inspect the power board, DC-DC PDMs and OR-ing board first. Fit the OR-ing module to **power J16**, matching numbered pins and the pin-1 marks; its two-row connector can otherwise be reversed. The supplied 2×5 assignment is SELV on pins 1–2, GND on 3–4 and 7–8, backed output on 5–6, and battery on 9–10. SELV feeds the PDMs controller (a LTC4418) pin V1 and remains the preferred source, even when the battery voltage is higher.
3. Fit only the required PDMs: screen supplies at **J2/J5/J7/J9**, the audio supply at **J15**, and the optional Pi supply at **J18**. Use **DC-DC PDM-Audio Rev D or later for the Pi supply** as eariler versions (which are opaque to you) could not get down to 5V1 required to the Raspberry Pi. **Set and measure outputs** with a multimeter before connecting loads: **19 V** for the specified screens, **16 V nominal and never above 18 V** for audio, and **5.1 V** for the Pi. Verify against each actual load's rating if you can.
4. Fit the components to the Control Board. Fit **both control-board optocouplers U1 and U2**, even if only one controller is used: their input LEDs are in series. Set JP1 **1–2 for Nano ESP32 (3.3 V)** or **2–3 for Nano Every (5 V)** before powering the Arduino. The Pi has its own 3.3 V pull-up through R13.
5. Fit the components to the audio board and the controller hardware required for your configuration: the Pi 5 stack (recommended Pimoroni NVMe Base (you can use a MicroSD at your **increased** risk), active cooler and DAC+), the Arduino, or both, on the upper assembly. Use the matching audio mounting holes.  Do not populate the **audio J5** or **control J10** header unless you are changing the board design. Audio power arrives separately by two wires at audio J19; the mating J5/J10 header still carries the same audio supply and GND, so it is not an electrically isolated mounting connector. So don't fit them.
6. Make the wire harnesses below, check polarity and continuity with power removed, then energise and test one load at a time. Do not connect another USB-C power supply to a Pi already powered through its GPIO header.
7. Mount the **control board above the power board using 30 mm standoffs** at the matching mounting holes. Support the boards without bending them; check screw length and clearance from copper, component leads and the underside of daughterboards. Keep the lower board's terminal-access edge accessible.

### Supply location and wiring sizes

**Suggested 24 V SELV PSU: Mean Well XDR-480E-24.** This model has been tested successfully with the UWH unit and has ample power headroom for the tested configuration.

Locate the **24 V SELV PSU near the 230 V power outlet**, and run several metres of twinned **4 mm² finely multistranded copper cable (approximately AWG 11)**, for 24 V positive and GND, from the PSU to the UWH siren hardware. Check the loaded supply voltage using the procedure below. Keep mains connections at the PSU end. **Containment of the boards to IPX5 is a minimum expectation.**

**24 V supply cable acceptance check:** use **24.0 V nominal at the PSU** and a recommended **maximum 1.0 V drop** from the PSU's DC output terminals to power-board J1 at the highest intended simultaneous load. This is a commissioning target for the supply wiring, **not a verified absolute undervoltage limit for the boards**.

1. With power off, disconnect the backup battery for this test so it cannot mask a weak SELV supply. Connect the equipment that this installation will actually power.
2. Run the connected screens at their highest intended brightness, exercise the computer, and sound the siren at its intended maximum operating level. Use this simultaneous operating load rather than an idle measurement.
3. Set the multimeter to **DC volts**. Measure across the PSU's accessible **+V and −V DC terminals** and record `V_PSU`. At the same steady load, measure across power-board **J1 pin 1 (+24 V) and pin 2 (GND)** and record `V_J1`. Measure only the low-voltage DC side; keep clear of the mains terminals.
4. Calculate **voltage drop = V_PSU − V_J1**. This difference already includes the positive wire, return wire and their connections; do not double it. With **24.0 V measured at the PSU**, the target is **at least 23.0 V at J1**. For example, 24.0 V at the PSU and 23.4 V at J1 gives a **0.6 V drop: pass**. A reading of 22.7 V gives **1.3 V: investigate and correct**.
5. If the PSU itself sags appreciably below its nominal 24 V, investigate its load, adjustment and temperature/derating first. If the cable drop exceeds 1.0 V, power off and inspect the ferrules, terminal tightness and connections; then increase conductor cross-sectional area using compatible, rated terminations. Do not remove strands to fit a terminal or raise the PSU voltage simply to hide cable loss. Repeat the loaded test after correcting it.
6. Confirm that the PDM outputs remain at their required voltages and that startup/siren operation causes no resets, screen blanking or unintended battery takeover. A multimeter's steady reading does not rule out brief dips; investigate any such symptoms even if the steady cable-drop test passes. Reconnect the battery with power off, then test backup operation separately.

Power-board **J1 is Phoenix Contact 1714971**. **4 mm² finely multistranded cable fits the terminals with a bootlace ferrule formed using a ferrule crimper**. Phoenix Contact publishes a **4 mm² maximum for flexible conductors, including ferruled conductors**. Do not trim away strands. Check the actual PSU terminal rating separately. Protect the long cable at its source as appropriate to the cable and PSU; the board fuse cannot protect a short upstream of itself.

Use flexible copper for internal harnesses. The following starting sizes assume maximum internal runs of **up to 250 mm one way**, Use terminations rated for the selected conductor and current. The TB007-508 terminals are specified for up to **2.5 mm²**; GPIO crimp contacts require their own wire-size check.

| Connection | Pin-to-pin wiring | Suggested conductor area, each wire |
|---|---|---|
| PSU to power board | J1 **1 = +24 V**, **2 = GND** | **4 mm² (approx. AWG 11)** |
| 24 V battery to power board | J14 **1 = battery +**, **2 = GND** | **2.5 mm² (approx. AWG 14)**; battery-source protection close to the battery |
| Power board to control board | J11 **1 → J21.1**, **2 → J21.2**: backed 24 V / GND | **0.5 mm² (approx. AWG 20)** for the control circuit only |
| Power board to audio board | J10 **1 → audio J19.1**, **2 → audio J19.2**: audio supply / GND | **1.0 mm² (approx. AWG 17)** |
| Power board to Pi power harness | J17 **1 = +5.1 V**, **2 = GND** | **1.5 mm² (approx. AWG 15)** trunk for each polarity |
| Pi harness branches | +5.1 V to physical **2 and 4**; GND to physical **6 and 9** | Two short **0.5 mm² (approx. AWG 20)** branches per polarity, with suitable current-rated contacts |
| Pi siren signal | Control J19 **1 → Pi physical 11 (BCM GPIO17)** | **0.25 mm² (approx. AWG 24)** |
| Pi pull-up supply | Pi physical **1 (3.3 V) → control J19.2** | **0.25 mm² (approx. AWG 24)** |
| Remote normally open siren button | Across control **J20 pins 1 and 2** | In-use cable: **30 metres of Cat 6a Ethernet patch cable**, plugs cut off, with **four conductors connected in parallel for each leg**, using all eight conductors |

For the remote button cable, join the same group of four conductors together at **both ends** of each leg. Connect one group between **J20 pin 1** and one button terminal, and the other group between **J20 pin 2** and the other button terminal. The normally open button closes the loop when pressed. This cable is used only as button wiring, not as an Ethernet connection.

Wind the 30 metre button cable onto a **spearfishing float-line winder** for tidy storage and easy deployment. The example below is the type used in this setup.

<img src="docs/images/spearfishing-line-winder.jpg" alt="Example spearfishing float-line winder for storing the siren button cable" width="320">

*Example line winder. Product photo: Ocean Hunter.*

Split the Pi power trunk using a rated splice/distribution connection; do not try to force the trunk wire into a small GPIO contact. Use both listed 5 V contacts and both ground contacts. With the DAC+ installed, use a suitable pass-through header/interposer rather than disturbing the HAT connections. An example cable connector is the **Harwin M20-1070600**, a **2×6-position, 2.54 mm female crimp housing**, fitted with separately supplied **M20-1180042** contacts. It can connect the harness to accessible mating pins covering Pi physical pins **1–12**, which include all the power, ground, 3.3 V and GPIO17 connections listed above. The housing is not itself a pass-through interposer: confirm mating-pin length, clearance and pin-1 orientation with the DAC+ fitted, and leave unused positions unwired. The M20-1180042 contacts accept **0.05–0.33 mm² (30–22 AWG)** wire, so the table's **0.5 mm² (approximately AWG 20)** power branches cannot be crimped directly into them. For this connector, use short **0.33 mm² (22 AWG)** power tails from rated splices, retaining both 5 V and both GND contacts, and verify voltage drop and temperature at the intended load. Measure 5 V at the Pi under load; do not compensate for excessive cable loss by raising the PDM above 5.1 V.

**Control J19 pin 2 is 3.3 V, not GND.** J20 is a button-loop connection, not a positive/GND supply connector. Keep these distinct from the power terminals' pin-1-positive/pin-2-GND convention. The boards share GND; the optocouplers separate the controller signal voltages but do not provide whole-system galvanic isolation.

Screen outputs are power **J3 = screen 1**, **J4 = screen 2**, **J6 = screen 3**, and **J8 = screen 4**, with positive on pin 1 and GND on pin 2. Use **1.0 mm² (approx. AWG 17)** for short screen-power leads, increasing area as needed for external cable length. Only **screen 1**, audio, Pi and the control supply are backed up by teh battery via the OR-ing board; screens 2–4 use the SELV supply directly through their PDMs.

### DAC+ audio cable and volume limit

Use a straight four-conductor cable from DAC+ P6 to audio J6. Short **0.25 mm² (approx. AWG 24)** conductors are suitable; keep the audio cable away from PDM switching components and power wiring.

| DAC+ P6 | Audio J6 | Signal / audio-board destination |
|---|---|---|
| 1 | 1 | Left audio — J1 tip / R2 pad 1 |
| 2 | 2 | Ground |
| 3 | 3 | Right audio — J1 ring / R1 pad 1 |
| 4 | 4 | Ground |

For the tested **DAC+ (PCB version 003R5)**, **YOU MUST** insert an **unwired 3.5 mm plug in the DAC+ socket** to operate headphone detect. Leave **P6 pin 5 externally unconnected**: measurements show that without a plug it is directly connected to 3.3 V, so **do not bridge it to pin 4/GND**. Use one audio source at a time.

RV5 sets the maximum WATER-zone level. Looking at its adjustment screw from above, turn **anticlockwise to lower the maximum volume**. The Bourns 3296W-1-502LF has approximately 25 turns of effective adjustment and an idling wiper at the endpoints, not a hard rotational stop. Start with a low limit and set the operating level deliberately. Follow the audio schematic's two-transformer underwater-speaker wiring. Neither side of a BTL amplifier output may be connected to GND.

### Fuses and hot-climate operation

Keep the current **5 A recommendation** for power-board **F2 (battery)**, **F3 (SELV feed into the OR-ing path)** and audio-board **F2**. A **6 A fuse may need to be considered for hot climates**, subject to availability of a correctly rated part and verification of the protected wiring, connector, MOSFET and PCB paths. This is a conditional engineering review, not an instruction to increase a fuse merely because it opens.

The battery backed up load budget is **55 W screen + 30 W audio + 19.8 W Pi stack = 104.8 W**. At an assumed 90% conversion efficiency that is approximately **4.85 A at 24 V** or **5.29 A at 22 V**, before startup transients and small auxiliary loads. Retaining 5 A therefore requires checking actual simultaneous load, startup and hot-enclosure behaviour; it is not a guarantee of continuous operation at all nameplate maxima.

The separate **20 A main SELV fuse** has alternative MINI **F1 / Keystone 3568** and MAXI **F4 / Keystone 3555-2** positions. **Fit only one of F1 and F4.** The **Keystone MAXI fuse holder may need to be used in hot climates because of derating in the MINI fuse and holder**. This alternative applies to the main input fuse; it does not make the 5 A branch positions MAXI-compatible. Check both fuse and holder derating at the actual internal temperature. Record the actual fuse MPN separately from its holder MPN.

### First power-up checks

Before fitting the Pi or connecting speakers, verify each PDM's voltage and polarity. Confirm SELV is selected with both supplies present, then test battery takeover and return to SELV under the intended backed load. Check for Pi undervoltage or resets and measure connector, fuse-holder and narrow-trace temperatures during a sustained-load test. Test GPIO17 and optional Arduino USB press/release events separately and together in **Siren Control → Activity Log**. GPIO17 uses the external R13 pull-up, with internal pulls disabled; LOW means pressed. See [wired siren setup](#wired-siren-on-raspberry-pi-5--gpio17-and-optional-arduino-usb) for software behaviour.

Component references: [Phoenix 1714971](https://www.phoenixcontact.com/en-us/products/1714971), [Same Sky TB007-508 datasheet](https://www.sameskydevices.com/product/resource/tb007-508.pdf), [Littelfuse MINI fuse derating](https://www.littelfuse.com/assetdocs/littelfuse-datasheet-mini?assetguid=231dbb04-2bf5-4da4-ac3e-23aa05c4339b), [Bourns 3296 datasheet](https://www.bourns.com/data/global/pdfs/3296.pdf).

## Known working setups

## Windows 11: tested configuration (September 2026)

The Windows 11 UWH application, wired Arduino siren, Mosquitto MQTT broker and Zigbee2MQTT have been tested together with **up to three working Zigbee buttons** on one coordinator. The preferred deployment button is now the **Aqara WXKG11LM**, tested on 6 November 2026 with `single`, `double`, `hold` and `release`. Other previously tested types have limited functionality (no hold or release signals); UWH's per-button Action Mapping determines the siren response. Zigbee2MQTT was also confirmed to restart through PM2 and Windows Task Scheduler after a Windows reboot. See [the Zigbee section](#zigbee2mqtt-wireless-siren-setup-and-operation) for installation and button-mapping instructions. Do not re-pair a working button to a second coordinator just to share it with another UWH computer.

## Raspberry Pi 5: tested configuration (October 2026)

Raspberry Pi OS Desktop based on Debian 12 Bookworm (listed as Raspberry Pi OS Legacy), Python 3.11, and the X11 desktop session. Two maximised displays, mouse movement, game timers and score updates have been tested on this combination. This Raspberry Pi 5 setup has successfully run a tournament.

Why X11 matters for this application: On the tested Pi 5, moving the pointer over Game Variables checkboxes under Wayland caused GPU utilisation to reach about 98% and the mouse became jerky. A separate note: Raspberry Pi recommends Wayland generally, but X11 was demonstrably better for this GUI.

> [!IMPORTANT]
> **Recommended Pi 5 configuration:** Stay with **Bookworm + X11** until a different combination has been tested with UWH. Raspberry Pi recommends Wayland generally, but X11 was demonstrably better for the Scoring Desk Kit's GUI performance on Bookworm.

#### Select X11 on Raspberry Pi OS
1. Open Terminal and run `sudo raspi-config`.
2. Select **6 Advanced Options** → **A7 Wayland** → **W1 X11**.
3. Select Finish and reboot when prompted.
4. After reboot, run:
   ```bash
   echo $XDG_SESSION_TYPE
   ```
   It should print `x11`. If it prints `wayland`, check the selection and reboot again. To switch back later, use **W2 Labwc** in the same menu.

## Downloading and installing UWH on Windows

### Download the program
1. Open the UWH Scoring Desk Kit repository on GitHub.
2. On the right-hand side of the repository page, find **Releases**.
3. Click Releases, then select the latest release.
4. Scroll down to the **Assets** section.
5. Click the Windows ZIP file. Its name will resemble: `UnderwaterHockeyScoringDesk-v1.2.123-Windows.zip`
   (The version and build numbers will vary.)
6. The ZIP file will download to your computer, normally into your Downloads folder.

> [!IMPORTANT]
> Do not select **Source code (zip)** or use the green **Code → Download ZIP** button. Those download the Python source code, not the ready-to-run Windows application.

### Extract the program
1. Open Windows File Explorer and navigate to Downloads.
2. Right-click the downloaded ZIP file.
3. Select **Extract All...**
4. Choose a permanent folder, such as `Documents\UWH Scoring Desk`.
5. Click Extract.

The extracted folder contains `UnderwaterHockeyScoringDesk.exe`, the visible `Tournament data` and `Sounds` folders, and its supporting files. Keep these together.

### Run the application
1. Open the extracted folder.
2. Double-click `UnderwaterHockeyScoringDesk.exe`.
3. The startup self-test will run before the application opens.
4. The Game Management window will appear.
5. Use the **Screens** tab's **Display Screen Options** to open a player-facing or crowd-facing display, if required. Choose a supported Standard or Widescreen layout. Closing a Display Window with its **X** closes it and queues the closed state for the next automatic settings save (about one minute after the first change, or on normal program exit). Check your monitor assignments with **Auto Detect Screens** and **Test Displays**.

You can create a desktop shortcut by right-clicking the executable and selecting **Show more options → Send to → Desktop (create shortcut)**.

### Installing future updates

Download the newer release and extract it into a **separate folder** first. Do not overwrite a working installation without a backup.

> [!WARNING]
> **Back up `settings.json` before every update.** It includes your **Zigbee button-name list** (for example, `siren_button, siren_button_2, siren_button_3`), MQTT settings, sound preferences, screen layout and the remembered Display Window open/closed state. Back up tournament CSVs, custom sounds in the app-level `Sounds` folder, and game logs too. Replacing UWH's settings can lose button names **or action mappings**, even though the buttons remain paired to Zigbee2MQTT.

After updating, confirm the **Siren Control → Button Device Names** field and test every configured button and its action mapping before using the system at a match. The lower-right corner of the **Game Variables** panel shows the running UWH version so you can confirm which download is actually open. Windows and Raspberry Pi 5 release builds show the same `1.2.<build>` number used in their release ZIP names; source installations show a source-build identifier. Do not blindly replace a new-format `settings.json` with a very old version; compare and carry forward your customised values where the format has changed. Zigbee2MQTT has a **separate** `data/` directory that should be backed up before Zigbee2MQTT updates; see [the Zigbee section](#zigbee2mqtt-wireless-siren-setup-and-operation).

## Downloading and installing UWH on a Raspberry Pi 5

The normal Raspberry Pi 5 installation now uses the ready-to-run **Linux ARM64 release ZIP** produced by GitHub Actions. A keyboard, mouse and 64-bit Raspberry Pi OS Desktop are needed; the Lite edition does not include the graphical desktop. The release bundle includes the Python runtime and UWH Python dependencies, so ordinary users do **not** need to create a virtual environment or run `pip install`.

### Raspberry Pi 5 power supply configurations

Raspberry Pi 5 can be powered in several ways, but the power source affects how much current the firmware makes available to the board and to USB peripherals. Raspberry Pi recommends a **5 V / 5 A** supply for full capability. A good **5 V / 3 A** supply can run a Pi 5, but the total current available to downstream USB peripherals is normally limited to **600 mA** instead of **1.6 A**.

| Power arrangement | Pi 5 behaviour | Required configuration |
|---|---|---|
| **UWH Scoring Desk production power board — 5.1 V / at least 5 A through the GPIO header** | No USB-C Power Delivery negotiation occurs. The motherboard provides the high-current 5 V rail directly. | **Set `PSU_MAX_CURRENT=5000` in the Pi 5 bootloader EEPROM.** |
| **Official Raspberry Pi 27 W USB-C supply, or another compatible USB-PD source that negotiates 5 V / 5 A** | The Pi detects the 5 A supply through USB-PD and automatically enables the higher power budget. | No `PSU_MAX_CURRENT` override is normally required. |
| **Good-quality 5 V / 3 A USB-C supply** | The Pi 5 can operate, but downstream USB power is normally limited to 600 mA. | Do **not** claim 5 A with `PSU_MAX_CURRENT=5000` unless the supply and complete power path really can provide it. |
| **Other verified 5 V / 5 A non-PD supply or bench supply connected through GPIO** | Electrically similar to the UWH GPIO-powered case: there is no USB-PD negotiation to report the available current. | `PSU_MAX_CURRENT=5000` may be used only when the source, wiring and connectors are genuinely capable of supplying 5 A. |

#### UWH Scoring Desk production hardware

> [!IMPORTANT]
> **The UWH Scoring Desk power board provides the Raspberry Pi 5 with a regulated 5.1 V supply capable of at least 5 A through the GPIO header. The dedicated PDM-Audio DC-DC supply uses the LMQ61460 regulator. The regulator specifies 3.5–7 ms from its first switching pulse to 90% of the selected output voltage, with a typical 0.7 ms enable-to-first-switching-pulse delay. This keeps the regulator's designed start-up to near operating voltage below 10 ms. The assembled production board should still be checked under load during hardware validation.**

The production power board feeds the Pi 5 through the **5 V GPIO power pins rather than through USB-C**. This deliberately bypasses USB-C Power Delivery negotiation. Most users are expected to provide their own Raspberry Pi 5, so each Pi powered by the production power board must have its bootloader configured to recognise the available **5000 mA** supply.

For the UWH power board, edit the Pi 5 bootloader EEPROM configuration:

```bash
sudo rpi-eeprom-config --edit
```

Add or change:

```text
PSU_MAX_CURRENT=5000
```

Save the configuration and reboot:

```bash
sudo reboot
```

After rebooting, verify the setting:

```bash
rpi-eeprom-config | grep PSU_MAX_CURRENT
```

The result should include:

```text
PSU_MAX_CURRENT=5000
```

`PSU_MAX_CURRENT=5000` tells the Pi 5 firmware to **skip USB Power Delivery negotiation and assume that a 5 A source is available**. It does not increase the capability of the power supply itself. On the UWH power board this is appropriate because the dedicated PDM-Audio supply and its power path are designed for the Pi 5 load.

Raspberry Pi also provides a `usb_max_current_enable=1` setting that raises the USB peripheral limit from 600 mA to 1.6 A. **It does not need to be added separately for the UWH power board:** Raspberry Pi documents that this higher USB-current setting is enabled automatically when `PSU_MAX_CURRENT=5000` is set.

> [!CAUTION]
> **Do not use `PSU_MAX_CURRENT=5000` merely to remove a low-power warning.** Only use it when the complete 5 V supply path is genuinely capable of supplying 5 A. If a Pi 5 is removed from the UWH power board and later used with a lower-current supply, review or remove this EEPROM override. Also avoid connecting a second USB-C power supply while the Pi is already being powered from the UWH power board's GPIO 5 V rail.

#### If the Pi 5 is powered through USB-C instead

A Pi 5 supplied from an official Raspberry Pi 27 W USB-C supply negotiates **5 V / 5 A** using USB Power Delivery, so the firmware knows that the higher current is available and no UWH-specific EEPROM override is required.

A Pi 5 can also run from a suitable **5 V / 3 A** USB-C source. In that configuration Raspberry Pi normally restricts the total power available to downstream USB devices to **600 mA**. With a recognised 5 V / 5 A source—or with the UWH power board correctly configured using `PSU_MAX_CURRENT=5000`—the USB peripheral limit rises to **1.6 A**.

The production UWH power board uses GPIO power injection rather than USB-C because its dedicated regulated 5.1 V supply is already part of the scoring-desk hardware; implementing a separate USB-C 5 A source would otherwise require a suitable USB-C/USB-PD power-source arrangement.

The dedicated PDM-Audio supply also makes a future independent Pi 5 hard-reset function practical, but **the dedicated supply by itself does not provide a reset**. A hard-reset/recovery button would need to be added to the PDM-Audio daughterboard (or otherwise wired to its regulator enable/control path) so that the Pi's 5.1 V output can be deliberately switched off and restarted. Without that additional hardware, recovery from a completely locked Pi still requires an external power cycle or use of the Pi's own controls.

Official references:

- [Raspberry Pi 5 power-supply requirements](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#power-supply)
- [Raspberry Pi: USB Power Delivery on Raspberry Pi 5](https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-009856-WP-1-USB%20Power%20delivery%20on%20Raspberry%20Pi%205.pdf)
- [Raspberry Pi bootloader configuration — `PSU_MAX_CURRENT`](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#PSU_MAX_CURRENT)
- [Texas Instruments LMQ61460 product page](https://www.ti.com/product/LMQ61460)

### 1. Prepare Raspberry Pi OS

For a Pi 5 based on the tested setup, use **Raspberry Pi OS Bookworm 64-bit Desktop** and select X11 using the [instructions above](#select-x11-on-raspberry-pi-os). The ready-to-run UWH package is ARM64 and is not intended for a 32-bit Raspberry Pi OS installation.

Open Terminal and make sure the basic archive utility is available:

```bash
sudo apt update
sudo apt install unzip
```

The packaged application includes its own Python runtime and Python packages. You do not need `python3-venv`, `pip install`, or a project `.venv` for the normal release installation.

### 2. Download the Raspberry Pi 5 release ZIP

1. Open Chromium (or another browser) on the Raspberry Pi.
2. Open the [UWH Scoring Desk Kit repository](https://github.com/davidstirling777-star/Underwater-Hockey-Scoring-Desk-Kit).
3. Open **Releases** and select the latest release.
4. Under **Assets**, download the file whose name resembles:
   `UnderwaterHockeyScoringDesk-v1.2.123-RaspberryPi5.zip`
   (the version/build number will vary).
5. Save the ZIP to the Pi's Downloads folder.

> [!IMPORTANT]
> Do **not** choose GitHub's automatically generated **Source code (zip)** and do not use **Code → Download ZIP** when you want the ready-to-run Pi application. Those are source-code archives. Also, if downloading on another computer, copy the **ZIP itself** to the Pi and extract it on the Pi. The Linux package can contain symbolic links and executable permissions that should not be reconstructed by Windows.

### 3. Extract and run UWH

The following example installs the release in `~/UWH-Scoring-Desk`. Replace the ZIP filename with the version you downloaded:

```bash
rm -rf ~/UWH-Scoring-Desk-new
mkdir -p ~/UWH-Scoring-Desk-new
cd ~/UWH-Scoring-Desk-new
unzip ~/Downloads/UnderwaterHockeyScoringDesk-v1.2.123-RaspberryPi5.zip
chmod +x Start-UWH.sh UnderwaterHockeyScoringDesk
./Start-UWH.sh
```

The startup self-test should run, followed by the operator interface. The extracted folder is a **one-folder application**: keep `UnderwaterHockeyScoringDesk`, `Start-UWH.sh`, the `_internal` directory and the other supplied files together.

On its first run, UWH places writable files such as `settings.json` and the sample tournament draw beside the executable as required. It also writes `debug_log.txt` beside the executable for packaged-build diagnostics.

Use **Screens → Display Screen Options** to open player-facing or crowd-facing displays. Position each window on its intended monitor. Use **Auto Detect Screens** and **Test Displays** to identify the monitors.

If startup fails, run `./Start-UWH.sh` from Terminal. For the packaged build, also inspect:

```bash
tail -n 100 debug_log.txt
```

### 4. Optional: create a desktop shortcut

Once the packaged application starts correctly, move/rename the tested folder to a permanent location if required. For example:

```bash
rm -rf "$HOME/UWH-Scoring-Desk"
mv "$HOME/UWH-Scoring-Desk-new" "$HOME/UWH-Scoring-Desk"
```

Then create a desktop launcher:

```bash
cat > "$HOME/Desktop/UWH-Scoring-Desk.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=UWH Scoring Desk
Comment=Underwater Hockey scoring and siren application
Exec=$HOME/UWH-Scoring-Desk/Start-UWH.sh
Path=$HOME/UWH-Scoring-Desk
Terminal=false
Categories=Game;
EOF
chmod +x "$HOME/Desktop/UWH-Scoring-Desk.desktop"
```

If the desktop asks you to **Allow Launching** or mark the shortcut as trusted, do so.

### 5. Updating an existing Raspberry Pi installation safely

Download the newer `-RaspberryPi5.zip` and extract it into a **separate folder first**. Do not unzip it over a working installation.

> [!WARNING]
> Before changing versions, back up `settings.json`, both tournament draw/results CSV files, custom sounds in the app-level `Sounds` folder, game logs, and any other locally edited files. In particular, `settings.json` contains the Zigbee button names/action mappings, MQTT settings, sound selections/trims and screen settings.

Run the new version once and confirm its startup self-test, screens, audio and configured siren buttons. Then copy your required user data/settings into the new installation deliberately. Do not copy the old `_internal` directory into a new release.

The lower-right version display uses the same `1.2.<build>` value as the Raspberry Pi release ZIP, just as the Windows release does.

### 6. Advanced/developer alternative: run from Python source

Developers can still use the source-code ZIP or a Git checkout. On Bookworm, install source dependencies in a project virtual environment rather than into the system Python:

```bash
sudo apt update
sudo apt install python3-venv python3-tk python3-pip
cd ~/Downloads/Underwater-Hockey-Scoring-Desk-Kit-main
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python uwh.py
```

Do not use `sudo pip install` or `pip install --break-system-packages` for the source installation. This source method is useful for development and troubleshooting; ordinary Pi users should prefer the versioned `-RaspberryPi5.zip` under GitHub Releases.

### Installing the Arduino siren code

This is required only when using the **Arduino USB wired-siren pathway**. A Pi using GPIO17 alone does not need an Arduino sketch. Uploading the sketch is separate from installing or updating the UWH application; it remains on the Arduino when power is removed.

The sketch supports the **Arduino Nano Every and Arduino Nano ESP32**, selecting the ADC method at compile time. On the ESP32 it uses named pins and calibrated millivolt readings. Set control-board JP1 to **1–2 for Nano ESP32 (3.3 V)** or **2–3 for Nano Every (5 V)** before powering the hardware; ESP32 inputs must never receive 5 V.

1. On a computer used for programming, install the [Arduino IDE](https://www.arduino.cc/en/software/).
2. Open [`assets/arduino_siren_button.ino`](assets/arduino_siren_button.ino) on GitHub and use **Download raw file**. Save it as `arduino_siren_button.ino`, not a web page or a `.txt` file. Put it inside a folder named **`arduino_siren_button`**.
3. Open that file in Arduino IDE. If the IDE offers to create a matching sketch folder and move the file into it, accept.
4. In **Boards Manager**, install **Arduino megaAVR Boards** for the **Arduino Nano Every**, or **Arduino ESP32 Boards** for the **Arduino Nano ESP32**. Select the board you actually have. The ESP32 sketch uses named pins A4, A3 and D2, so either Nano ESP32 pin-numbering setting can be used.
5. In **Library Manager**, search for and install **Adafruit NeoPixel** by Adafruit, accepting any required dependencies. This library is required to compile the supplied sketch even if you have not fitted the LED stick.
6. Close UWH and any other serial-port programs. Connect the Arduino with a **USB data cable**, then select its port in the IDE's board selector or **Tools → Port**. On Windows this is a `COM` port; unplugging and reconnecting the board helps identify the correct one.
7. Click **Verify** (tick) to compile, then **Upload** (right arrow). Wait for the IDE to report completion. A missing `Adafruit_NeoPixel.h` error means the library is not installed; upload failures commonly mean the wrong board/port, a charge-only cable, or another program holding the port.
8. With the board connected through the documented control-board siren interface, open **Serial Monitor** at **9600 baud**. Press and hold the wired button: expect `SIREN_ON`, repeated about every 0.5 seconds. Release it: expect `SIREN_OFF`. Check the **JP1 setting for your board** before powering the assembled hardware.
9. **Close Serial Monitor** before starting UWH. Connect the Arduino by USB to the computer running UWH, press and release the physical button, and confirm the Arduino ON/OFF events in **Siren Control → Activity Log**, together with audible start/stop. Port detection alone does not prove the sketch or button is working.

The sketch also contains NeoPixel and battery-monitor functions. **Users must work out their own voltage divider** and enter the actual R1/R2 values in the sketch, with calibration and warning thresholds appropriate to their battery. The retained 10 kΩ / 3.3 kΩ values are legacy Nano Every settings, not an ESP32 divider recommendation. Keep the ESP32 A3 input below 3.3 V and within its ADC measurement range (about 3.1 V at the configured 11 dB attenuation), including at maximum charging voltage. Do not connect the battery bank directly to A3.

Official help: [Nano Every setup](https://docs.arduino.cc/tutorials/nano-every/getting-started/), [uploading a sketch](https://support.arduino.cc/hc/en-us/articles/4733418441116-Upload-a-sketch-in-Arduino-IDE), [installing libraries](https://support.arduino.cc/hc/en-us/articles/5145457742236-Install-libraries-in-the-Arduino-IDE).

### Wired siren on Raspberry Pi 5 — GPIO17 and optional Arduino USB

UWH automatically starts a wired GPIO listener on a **Raspberry Pi 5**. The app
configures **BCM GPIO17 (physical header pin 11)** as an **input with both internal
pull-up and pull-down disabled**. No GPIO BIOS/bootloader setting is needed.
The control board's **R13 (11 kΩ) supplies the external pull-up using 3.3 V from the Pi**, brought back through J19.
Do not connect the Arduino's 5 V siren signal to this pin.

| Board connection | Raspberry Pi 40-pin header | Function |
|---|---|---|
| Control J19 — siren signal | Physical **11**, **BCM GPIO17** | LOW = pressed; HIGH (about 3.3 V) = released |
| Control J19 — 3V3 | Physical **1**, **3.3 V** | From Pi to control-board R13; do not feed an external supply into this pin |
| Power J17 — GND | Physical **6 and 9** | Common ground/power return |
| Power J17 — `RP5_5V` from the Rev D DC-DC-PDM board | Physical **2 and 4** | Regulated **5.1 V** power; never connect to a signal GPIO |

This is the four-conductor arrangement using power-board J17 for power/GND and control-board J19 for siren/3.3 V. The power pair branches to two contacts per polarity at the Pi. See the [assembly wiring table](#supply-location-and-wiring-sizes).

The power contacts share current; size the cable and connectors for the intended
5 A supply and follow the Pi power guidance above.
GPIO17 is separate from the Raspberry Pi DAC+'s I2C/I2S pins. Access the header
through a suitable pass-through connector/interposer when the DAC+ is fitted.
The optocouplers separate the signal voltages, but the boards share GND;
this is **not full galvanic isolation**. Fit **both U1 and U2**, whose input LEDs
are in series, even if only one controller is used.

The GPIO worker samples every 5 ms and accepts a press or release only after
**50 ms of stable level**. A held button produces one ON event; it does not
retrigger repeatedly. A button already held at app startup is recognised after
the same debounce interval. The siren follows press/hold/release, like the
Arduino input, rather than issuing a timed Zigbee pulse.

**Arduino USB remains active alongside GPIO17.** The Arduino's `SIREN_ON` and
`SIREN_OFF` messages and the GPIO button each have their own pressed state. The
first active input starts the siren; it stops when **all active wired inputs have
released**. The **Siren Control → Activity Log** records each GPIO17 and
Arduino USB ON/OFF transition separately, even when the other input keeps the
siren sounding. Repeated reports of the same state do not fill the log.
Duplicate ON reports do not restart playback. A GPIO read failure
releases only the GPIO state; a serial disconnect releases only the Arduino
state. Neither cancels the other input while it is held.

GPIO events use the same local audio and optional MQTT siren output as Arduino
USB, with all sound/UI work handled on the main application thread. Windows
continues to use USB/Arduino without loading a GPIO library.

**Installation and diagnostics:** the ARM Linux requirements include `lgpio`,
and the Raspberry Pi release build bundles it. Source users should reinstall
`requirements.txt` in their project virtual environment after updating. If pip
needs to compile `lgpio`, install its build prerequisites first with
`sudo apt install swig build-essential python3-dev`, then run
`PYPI=1 python -m pip install -r requirements.txt` to include liblgpio in the
extension. The
listener finds the RP1 controller by its `pinctrl-rp1` label, accommodating both
`gpiochip0` and `gpiochip4` numbering. Startup success or a missing-library,
permission, or busy-pin error appears in the **Siren Control Activity Log**.
A failure leaves Arduino USB and the rest of UWH available. Check `/dev/gpiochip*`
permissions and GPIO group membership if access is denied; close other programs
claiming GPIO17. Restart UWH after correcting a GPIO startup/read error.

**Pi installations without this wired input:** do not leave an enabled GPIO17
floating. Set `UWH_GPIO_SIREN=0` when launching, for example:

```bash
UWH_GPIO_SIREN=0 ./Start-UWH.sh
```

For the motherboard circuit above, leave that override unset and connect the
3.3 V return conductor for R13; keep the internal pulls disabled. Before use, verify idle
3.3 V and pressed LOW at pin 11, then test GPIO alone, Arduino USB alone, and
both together. Software tests use simulated GPIO; actual Pi/cable/button testing
is still required.

### Raspberry Pi troubleshooting

| Symptom | Check |
|---------|-------|
| Jerky mouse when passing over Game Variables checkboxes | Run `echo $XDG_SESSION_TYPE`. If it shows `wayland`, test the X11 option described [above](#select-x11-on-raspberry-pi-os). |
| `./Start-UWH.sh: Permission denied` | Run `chmod +x Start-UWH.sh UnderwaterHockeyScoringDesk`, then try `./Start-UWH.sh` again. |
| Executable reports the wrong architecture / does not run | Confirm `uname -m` reports `aarch64` and that you downloaded the `-RaspberryPi5.zip`, not the Windows ZIP or source ZIP. |
| Packaged application closes or appears not to start | Launch `./Start-UWH.sh` from Terminal and inspect `debug_log.txt` in the extracted UWH folder. |
| A library error appears at startup | Keep the complete extracted release folder together, especially `_internal`. Re-extract the ZIP **on the Pi** into a fresh directory before changing OS packages. |
| Desktop icon appears but program does not start | Run `./Start-UWH.sh` from Terminal; check the desktop shortcut's `Exec=` and `Path=` entries. |
| Display Window is missing or opens on the wrong monitor | Check **Screens → Display Screen Options**, run **Auto Detect Screens** and **Test Displays**, and position the window on the intended monitor. |
| Zigbee siren unavailable | See the Zigbee section below; a detected USB/COM port is not proof that the Zigbee button is paired or communicating. |
| Source/developer install shows `ModuleNotFoundError` | In a source checkout, check that `.venv/bin/python -m pip install -r requirements.txt` completed successfully and launch with `.venv/bin/python uwh.py`. |
| Need to check OS package updates | Run `sudo apt update` followed by `apt list --upgradable`. An empty list means no upgrades are offered by the configured repositories, not that you are on the newest Raspberry Pi OS release. |

## Game Variables tab

Here, you can set most of the parameters of the games and select whether Team Time-Outs, Overtime and Sudden Death aspects of the game are allowed.

Most period-duration boxes accept decimal **minutes**, e.g. `1.5` (or `1,5`) = 1 minute and 30 seconds. **Crib Time** is in seconds; **Time to Start First Game** is a 24-hour clock time, not a duration.

**Time to Start First Game** schedules the first game against the computer's local clock. Enter a 24-hour time as `H:MM` or `HH:MM`: both `9:36` and `09:36` mean 09:36. The minutes must have two digits (for example, `9:06`). If the selected time has already passed today, the app schedules it for tomorrow.

**First Game Starts In:** is another way to set when the first game starts, in 'minutes from now'. Entering a value here will wipe the time from 'Time to Start First Game'.

**Team Time-Outs** are enabled by the checkbox beside **Team Time-Out Period**. When selected, the Team Time-Out buttons in the Scoreboard tab are enabled and the Team Time-Out Period value box can be edited. When it is off, the Team Time-Out Period value is greyed out and disabled.

**Team Time-Out Period** is the value in minutes allowed for the Team Time-Out. Its row also contains the Team Time-Out enable checkbox.

**Half Period:** The time in minutes of the first and second halves.

**Half Time Break:** The time in minutes of the half time break.

**Overtime** is enabled by the checkbox beside **Overtime Game Break:**. When selected, the program may enter Overtime if the scores are tied at the end of normal play. When it is off, the Overtime Game Break, Overtime Half Period and Overtime Half Time Break values are greyed out and disabled.

**Overtime Game Break:** The time in minutes of the break between the end of the second half and the start of Overtime. Its row also contains the Overtime enable checkbox.

**Overtime Half Period:** The time in minutes of the Overtime halves.

**Overtime Half Time Break:** The time in minutes of the Overtime half time break.

**Sudden Death Game Break:** has both a checkbox that, when selected, enables the program to enter Sudden Death if the scores are tied at the end of Overtime play, and a value box where the time in minutes of the break before Sudden Death can be entered.

**Between Game Break:** The time in minutes of the break between the end of the game and the start of the next game. This time can be shortened by "Crib Time" (see below).

**Record Scorers Cap Number:** enables a popup dialogue box to appear when a goal is scored, where the cap number of the player scoring the goal can be entered. There is also the option of 'Unknown' and 'Penalty Goal'.

**Crib Time:** has both a checkbox that, when selected, enables the program to shorten the 'Between Game Break' by this value until Court Time is aligned with Local Computer Time, and a value box where the adjustment is entered in **seconds**.

**Reset Timer** transfers the entered values to the program and starts the timer again with the new values.

### Presets

Here, **nine** buttons are available for commonly used settings. Holding a preset button for **three seconds** opens its editor, where the button name and saved settings can be changed. Click the stored button to load those settings back into the Game Variables.

## Tournament List tab

Tournament draw selection and results synchronisation are on the **Tournament List** tab

Tournament files live in the visible **`Tournament data`** folder beside the application. The release package includes a demo `Tournament_Draw.csv` and matching `Tournament_Results.csv` there. On first run after upgrading from an older version, UWH copies legacy root-level CSVs into `Tournament data` when a file of the same name is not already present; the old files are left untouched.

The CSV File dropdown automatically refreshes when clicked. New original draw CSV files copied into `Tournament data` can be selected without restarting the application. Generated `_Results.csv` files are excluded from the draw dropdown.

### Create a draw manually

For club nights or other simple local events, the lower part of **Tournament List** contains **Create Tournament Draw Manually**. Enter a **Draw Name** and fill the three-column table headed **Game number**, **White** and **Black**. All three cells are editable. Game numbers and team names accept up to **16 characters including spaces**. The table provides twenty rows; unused rows are ignored as long as both team-name cells are blank.

Click **Save Draw** to create a new `<Draw Name>_Draw.csv` and its separate `<Draw Name>_Results.csv` in `Tournament data`. Existing files are never overwritten. The new draw is then selected automatically in the Tournament List dropdown.

**Expected CSV headers:** `date,#,White,WScore,Black,BScore,Referees,Penalties,Comments`

Where `#` is the Game Number (but this can also be `game`, `game#` or `game_number`).

> [!IMPORTANT]
> The selected **draw is an input file** and is not modified by UWH. Selecting it creates a sibling results CSV only if one does not already exist; an existing results file is **never reset**. `Tournament_Draw.csv` produces `Tournament_Results.csv`; `Court_A_Draw.csv` produces `Court_A_Results.csv`. Other names produce `<name>_Results.csv`. A newly created results file starts as a complete copy of the draw, then receives scores and penalty data. UWH hides generated `_Results.csv` files from the draw selector.

**If a results file with the expected name already exists in the same folder, UWH reuses it**, including after an application restart. For example, selecting `Court_A_Draw.csv` when `Court_A_Results.csv` already exists keeps the saved results; it does not create a blank replacement or a second numbered results file. Each subsequent game export updates only that game's scores, penalties and scorer comments, leaving other games' results intact. **Exporting the same game again replaces that game's previously saved result fields**, so check the selected game number before continuing.

The filename alone is not enough: UWH checks that the existing results file has the same headers, row count and non-result fields (including game numbers, teams and schedule) as the selected draw. If they do not match, UWH refuses to export and leaves the existing results file unchanged. Back up both files and resolve the mismatch before continuing. For a separate tournament, use a distinct draw filename so it has its own results file.

Scores are written to `WScore` and `BScore`, penalised cap numbers to `Penalties`, and (when **Record Scorers Cap Number** is enabled) scorer information to `Comments` **in the results file**. Scorer entries use forms such as `W#7(2)`, `W#PG(1)` (Penalty Goal) and `B#UNK(1)` (Unknown). Team names, game numbers and the rest of the draw are carried through unchanged. Team names containing commas or quotes must be properly quoted in CSV.

During **Between Game Break**, UWH attempts to export the completed game **just before the countdown reaches 00:30**. It atomically replaces the existing results CSV, never the input draw. If saving fails, the live game remains available for correction and retry: scores, penalties and scorer records are not discarded. If the original draw's schedule or teams no longer match an existing results file, UWH refuses to export rather than overwriting results. Back up both CSVs and resolve the difference before resuming.

When updating UWH or changing machines, back up **both** the original draw and its `_Results.csv` file. A newer ZIP must not be allowed to replace an ongoing results file. If the old version has already written results directly into the original draw, keep a backup: the first results file will preserve any values already present in that draw.

The 'Starting Game #' will show a list of Game Numbers in the CSV file selected above. This could be useful if the app crashes and the games need to be restarted, or if multiple days' games are in the same file.

At the completion of each game, the application automatically advances to the next game number in the selected Tournament CSV file and updates the displayed team names. There is a drop down box to select the starting game number.

## Game Sequence

The **Game Sequence** explanation remains on the **Game Variables** tab and now occupies the space previously used by Tournament List.

The normal game sequence is:

1. **First Game Starts In / Time to Start First Game** runs once to start the first scheduled match.
2. **First Half** → **Half Time** → **Second Half**.
3. If the score is tied and Overtime is enabled: **Overtime Game Break** → **Overtime First Half** → **Overtime Half Time** → **Overtime Second Half**.
4. If the score is still tied and Sudden Death is enabled: **Sudden Death Game Break** → **Sudden Death**.
5. **Between Game Break** follows the completed game and then the application advances to the next tournament game when tournament mode is active.

**First Game Starts In** transitions directly to First Half. **Crib Time**, when enabled, is subtracted from the Between Game Break to help bring court time back into alignment with local computer time.

## Two-court tournament results synchronisation

This optional feature lets Windows 11 and Raspberry Pi 5 scoring computers
operate independently while a third computer maintains one combined results
CSV. It uses Python's standard HTTP library, with **one remote writer** rather
than two courts concurrently editing a shared CSV over SMB.

### Files and ownership

| Computer | Original draw | Results |
| --- | --- | --- |
| Court 1 (even games) | Local Tournament_Draw.csv | Local Tournament_Results.csv |
| Court 2 (odd games) | Identical local Tournament_Draw.csv | Independent local Tournament_Results.csv |
| Results computer | Identical Tournament_Draw.csv | Combined Tournament_Results.csv |

The draw must be **byte-for-byte identical** on all three machines. Do not edit
its game numbers, teams or schedule during a tournament. The court and server
both refuse to merge against a changed draw.

The courts do **not** mount or edit the third computer's CSV. They send one
completed game at a time to a Python service. An SMB share is unnecessary for
uploading results, though you can separately share the folder for read-only
viewing.

### Safety rules

- Each court's complete result is saved **locally first**, independent of the
  network. Network failure cannot block normal game progression.
- A background worker retries after ten seconds when offline. It also wakes
  immediately after a local export or when **Sync Now** is pressed. The
  networking code never touches Tk widgets or runs on the timer thread.
- The results server processes one game write at a time under a lock. It
  stages a complete replacement CSV, then atomically replaces only its
  results file. No caller can supply a filesystem path.
- An identical repeat submission is acknowledged without rewriting. A
  different result for an already-completed game raises a visible CONFLICT;
  neither value is silently overwritten.
- A small local .uwh_sync_*.json file remembers which game results the server
  acknowledged. If it is missing after a crash, submissions are reconstructed
  from the completed local results CSV, and duplicate submissions are safe.
- Zero–zero is a completed result: both score cells contain the string "0".
  Any row with a blank score remains unsubmitted.
- A locked CSV, missing server, wrong token or disk error means **pending**,
  never "synced." Retrying the same game does not erase other games.
- An even/odd or consecutive court selection is applied by the existing
  local Tournament List control. The server merges by game number.

### 1. Set up the third results computer

Windows 11 or Raspberry Pi/Linux can run the service. Use Python 3.11+ and a
permanent folder containing the **source ZIP** files:

    tournament_results_server.py
    tournament_files.py
    csv_export.py
    Tournament data/Tournament_Draw.csv

The easiest route is to extract the full updated GitHub source ZIP on the
third computer and put the same original draw in its `Tournament data` folder.
The packaged Windows UWH application (`UnderwaterHockeyScoringDesk.exe`) is
the court/operator program and cannot run the shared tournament-results
server. On the third results computer, download/extract the GitHub source ZIP
and run `tournament_results_server.py` with Python.

Generate a long, unpredictable secret once, and record it securely:

    python -c "import secrets; print(secrets.token_urlsafe(32))"

If Windows reports that `python` is not recognised, use `py -3` in place
of `python` in the commands below.

Enter exactly the same shared results token on the two courts. The recommended
command above generates a long, unpredictable token (typically about 43
characters). The results server rejects tokens shorter than 16 characters as a
basic safeguard against weak manually chosen passwords; 16 characters is only
a minimum length check, not a special cryptographic threshold. Using the
generated random token is strongly recommended.

#### Windows 11 results computer

In PowerShell in the extracted project folder (for example C:\UWH):

    cd C:\UWH
    $env:UWH_SYNC_TOKEN = Read-Host "Shared results token"
    python tournament_results_server.py --draw "C:\UWH\Tournament data\Tournament_Draw.csv" --bind 0.0.0.0 --port 8765

The 0.0.0.0 option lets other computers connect; the default is localhost
only. On a **private LAN** you may need an administrator PowerShell to allow
TCP port 8765 through Windows Firewall:

    New-NetFirewallRule -DisplayName "UWH Results" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765 -Profile Private -RemoteAddress LocalSubnet

For example, if the third computer has the IP address 192.168.1.50, courts
would enter http://192.168.1.50:8765 into the UWH widget.

#### Raspberry Pi/Linux results computer

In a Terminal in the extracted project folder:

    cd /home/uwh/UWH
    read -r -s -p "Shared results token: " UWH_SYNC_TOKEN
    echo
    export UWH_SYNC_TOKEN
    python3 tournament_results_server.py --draw "/home/uwh/UWH/Tournament data/Tournament_Draw.csv" --bind 0.0.0.0 --port 8765

Adapt the path to where you extracted the source. On Linux, also restrict
firewall access to the scoring computers on the local network. The service
runs in the Terminal until Ctrl+C; make it a startup service only after
testing. Back up the server's combined results CSV periodically.

**Security:** HTTP on port 8765 is unencrypted. Use a trusted, isolated LAN,
or HTTPS/VPN for untrusted networks. Do not forward the port to the public
internet. The masked access token is stored in each court's settings.json;
protect that file from other users and back it up.

### 2. Configure the two court computers

Copy the same original draw into each updated court installation's `Tournament data` folder. Back up each
court's settings.json, original draw and any existing local results file
before installing a new release/source ZIP.

In Game Variables → Tournament List:

1. Check Use Tournament List? and choose Tournament_Draw.csv.
2. Choose the starting game and select **even** on one court, **odd** on the
   other. Existing game/period rules remain unchanged.
3. Verify the read-only **Tournament Results** box shows
   Tournament_Results.csv, the LOCAL results output derived from the draw.
4. Under Results sync, select **Shared server**.
5. Enter the server URL, such as http://192.168.1.50:8765, and the same
   shared access token on both courts.
6. Press **Save & Sync** to save this machine's settings and begin submitting
   completed games. **Sync Now** wakes a pending retry immediately.
7. Watch the status text for pending, synced, server-unavailable or conflict
   messages. The original draw remains read-only from the app.

To disable uploads, choose **Local only** and press Save & Sync. Results
continue to be saved on that court, and the other court is unaffected.

**The server URL is not a Windows UNC path or a mapped drive letter.** It is
the address of the single-writer service. No SMB mount is needed on the RP5.
Windows and Raspberry Pi both use the same URL, even though the server's
CSV file may be stored in a Windows or Linux folder.

### 3. Test before a live tournament

Use a copy of the draw, not a live tournament:

1. Submit even Game 2 from Court 1, then odd Game 1 from Court 2. Both must
   appear in the combined server CSV without modifying either original draw.
2. Stop the server/network; finish another game. The court's local CSV must
   contain it, the timer must still advance, and the status must remain
   pending/offline.
3. Restore the server. The result must appear automatically after a retry
   without erasing either earlier game.
4. Restart a court: previous games must remain saved and acknowledged.
5. In disposable files, submit two **different** results for the same game.
   The second must report CONFLICT and preserve both copies for review.
6. On Windows, temporarily hold the server CSV open in a program that
   exclusively locks it. A failed write must leave local data safe and retry
   after the lock is released.

Only test on production hardware after the headless tests pass. If CONFLICT
appears, back up the local and server result files and reconcile the affected
game manually. The software must not guess which court's score is correct.

### 4. Status messages

| Message | Action |
| --- | --- |
| Local results saved · network sync off | Shared upload is disabled; enable it and Save & Sync if required. |
| Network unavailable · retry in 10 s | Check server, LAN address and firewall. Local results remain safe. |
| Sync blocked (HTTP 401) | Correct the access token on this court. |
| Sync blocked (HTTP 503) | Server results file is locked, disk full or unwritable; fix then retry. |
| CONFLICT game N | Different existing result or draw mismatch. Stop and reconcile manually. |
| All completed games synced | Every completed game this court knows about has a server acknowledgement. |

The court files do **not** need to contain the other court's games. The
results computer's combined CSV is the tournament's combined record.

## Screens tab

**Operator Screen** selects the standard or widescreen arrangement of the operator's own window. This is distinct from whether the player/crowd Display Window is currently open.

**Display Screen Options** offers Single/Dual Standard or Widescreen display layouts, subject to the monitors attached to the computer. Use these options to open the player-facing or crowd-facing window(s). **Closing a Display Window with its X** closes that window; its closed state is queued for automatic saving (about one minute after the first change, or on normal exit) and should remain closed after a normal restart. The selected layout is retained for the next time the display is opened. Do not assume changing the operator layout is an instruction to reopen a deliberately closed display.

**Show Team Names** controls whether team names are shown on the operator and display screens.

**Auto Detect Screens** refreshes the monitor information shown under **These screens were detected**. Windows uses the native monitor list; on the tested Raspberry Pi Bookworm/X11 configuration, monitor detection uses `xrandr`. If automatic detection cannot establish a layout, select the required layout manually.

**Test Displays** labels the detected screens for approximately eight seconds. Dismiss the labels by clicking or pressing **Esc**. The controls and screen placement should be tested on the actual monitors before a match.

## Sounds tab

The Sounds tab reports **Audio output in use**. On Raspberry Pi/Linux it identifies the PipeWire system-default output selected when UWH started, including a HiFiBerry DAC+ or compatible I2S DAC when detected; on Windows it reports that the Windows system-default output is in use. UWH does not change the operating system's audio default. If you change the OS default while UWH is running, **restart UWH** so pygame opens the newly selected output.

**Save Settings** stores the selected pip and siren files, their per-file **Trim %** values, the separate 30-second warning sound/trim/duration, the Enable Sound setting and siren timing settings in the JSON file stored beside the application.

The Pips and Sirens tables each show up to **8 sound files**, with the columns **Use**, **Sound File** and **Trim %**:

- The **Pips** table lists supported `.MP3` and `.WAV` files from the app-level `Sounds` folder whose filename contains `pip` (case-insensitive). For clarity, custom pip files should use names such as `pip-short-beep.mp3` or `pip-countdown.wav`.
- The **Sirens** table lists supported files whose filename contains `siren` (case-insensitive). For clarity, custom siren files should use names such as `siren-air-horn.wav` or `siren-classic.mp3`.
- A sound file that does not contain `pip` or `siren` in its filename will not appear in the corresponding table.
- Each of the 8 rows has a radio-button position on the left. Exactly **one countdown Pip** and **one Siren** can be selected at a time. Rows without a sound file remain visible but their radio button and Trim % field are disabled/greyed, keeping the table layout consistent. The selections are stored as `pips_sound` and `siren_sound` in `settings.json` and are restored when UWH starts.
- Click the enabled radio button (or the filename) to make that file the active pip or siren. **Double-click** a filename to preview it using its current Trim %.
- New sound files default to **100% Trim**.

Between the two tables is a **30-second period warning** selector with a single dropdown of available `pip`-named files, its own **Trim %** column (the same width as in the two tables), a **Use** radio button matching the Pips and Sirens tables, and a **Play** preview button in the adjacent **Test** column. Selecting a filename from the dropdown updates the radio selection automatically. This warning is emitted just before the timer displays **00:30** during break periods. Its file choice and trim are **independent of the 10-to-1-second countdown**, even when the same recording is selected in both places. For example, countdown pips can remain trimmed to 30% while the one-off 30-second warning plays at 100%. The warning trim defaults to **100%**, without changing the countdown pips' existing trim.

Under **Siren timing**, **Number of milliseconds to play timed period warning (30 second warning) signal** sets how long the warning is heard, in whole milliseconds (**50–5000 ms**, default **1000 ms**). A short pip recording loops up to that duration; a longer recording is stopped at the configured duration. The 10-to-1-second countdown pips still play their selected file once each, at their normal file length.

**Trim %** is an attenuation-only correction for differences in the apparent loudness of individual sound files. The accepted range is **0–100%**: `100%` plays the file at its native level, `50%` attenuates it to half the playback amplitude used by UWH, and `0%` mutes that file. UWH deliberately does not boost files above their native level, avoiding a digital-gain stage that could introduce clipping.

A practical way to balance a set of sounds is to use the **quietest native file as the reference**, leave it at 100%, trim the louder files down until they sound similar, and then raise or lower the overall **hardware/DAC/operating-system master volume** to suit the pool or venue. If a source file itself needs to be made louder, normalized, compressed or otherwise processed, edit that file in suitable specialist audio software and then place the revised file in the `Sounds` folder.

There are no longer separate **Pips Vol** or **Siren Vol** master sliders in UWH. Overall level is controlled by the downstream audio hardware or operating-system/DAC level; **Trim %** is only for matching individual files to one another.

The **Open Sounds Folder** button, immediately to the right of **Save Settings**, opens the visible app-level `Sounds` folder so sound files can be added or replaced.

### Raspberry Pi 5: duinotech Digital Audio Converter / HiFiBerry-compatible DAC HAT

The **duinotech Digital Audio Converter** has been tested on a Raspberry Pi 5 running Raspberry Pi OS Bookworm. The red LED on the HAT only confirms that the board has power; it does not prove that Linux has loaded an audio driver.

With the Pi shut down, fit the DAC to the 40-pin GPIO header. On Bookworm, the boot configuration file is `/boot/firmware/config.txt`. Back it up and edit it:

```bash
sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.before-dac
sudo nano /boot/firmware/config.txt
```

Add these lines, and remove an older plain `dtoverlay=hifiberry-dacplus` line if one was previously added:

```text
dtparam=i2s=on
dtoverlay=hifiberry-dacplus-std
```

Save and reboot:

```bash
sudo reboot
```

After reboot, confirm that ALSA can see the DAC:

```bash
aplay -l
cat /proc/asound/cards
```

A working setup should contain a card similar to:

```text
sndrpihifiberry
HiFiBerry DAC+ HiFi pcm512x-hifi-0
```

The card number is not guaranteed. On the tested Pi it appeared as **card 2**. To test the left and right outputs directly, first turn down the amplifier/headphones because the ALSA test tone can be very loud, then run either the card-name form:

```bash
speaker-test -D plughw:CARD=sndrpihifiberry,DEV=0 -c 2 -t sine -l 1
```

or, if the card is shown as card 2:

```bash
speaker-test -D plughw:2,0 -c 2 -t sine -l 1
```

The tone should alternate between left and right. Stop it with **Ctrl+C** if needed.

Raspberry Pi OS Bookworm uses PipeWire/WirePlumber for the desktop audio default. Show the available sinks with:

```bash
wpctl status
```

Find the sink corresponding to the DAC. The numeric sink ID can change, so do not permanently assume the tested value of `66`. Set the current DAC sink as the default and set a comfortable system level; for example, if its current ID is 66:

```bash
wpctl set-default 66
wpctl set-volume 66 0.50
wpctl get-volume 66
```

Here `0.50` means **50%**. After changing the default audio sink, **completely close and restart UWH**. pygame chooses the system-default output when UWH starts. The Sounds tab then reports **Audio output in use** so the operator can see whether the app started on the DAC or HDMI.

#### DAC troubleshooting

- **Red LED on the HAT, but `aplay -l` shows only HDMI:** the DAC is powered but its driver/overlay is not active. Recheck `/boot/firmware/config.txt`, use `dtoverlay=hifiberry-dacplus-std` on the Pi 5, and reboot.
- **The direct `speaker-test` works, but UWH is silent:** run `wpctl status`. If the asterisk is still beside an HDMI sink, make the DAC sink the default with `wpctl set-default <sink-id>`, then restart UWH.
- **UWH plays through the wrong output:** read **Audio output in use** on the Sounds tab. It reports the default that was selected when UWH started. Change the OS default and restart UWH.
- **Audio is too loud or too quiet overall:** change the PipeWire sink volume, for example `wpctl set-volume <sink-id> 0.50`, or adjust the downstream DAC/amplifier hardware. Use each file's **Trim %** only to match its apparent loudness to the other pip/siren files.
- **The DAC disappears after an OS/configuration change:** repeat `aplay -l`, `cat /proc/asound/cards`, and `wpctl status` before changing UWH settings. This separates a Linux audio problem from an application problem.

Useful references: [Raspberry Pi `config.txt` documentation](https://www.raspberrypi.com/documentation/computers/config_txt.html), [HiFiBerry Pi 5 driver/overlay change](https://www.hifiberry.com/blog/changes-in-hifiberry-drivers/), and the [duinotech Digital Audio Converter product page](https://www.jaycar.co.nz/digital-audio-converter-raspberry-pi-compatible/p/XC9048).

UWH uses the per-file **Trim %** values for relative cue levels. The operating system, DAC/amplifier or other downstream hardware is the overall master volume. On Raspberry Pi OS/PipeWire, use `wpctl` for that master level; on Windows, use the normal Windows output and volume controls.

**Pips** play at pre-determined periods.

**Siren** plays at pre-determined periods and also when the Chief Referee activates the button to stop or start play.

**Number of seconds to play App-generated Siren** sets the requested duration of game-period sirens and also supplies the per-cycle duration for mapped Zigbee timed sirens. If the selected file is shorter, playback loops as needed. **Maximum Timed Siren Duration — App & Zigbee (seconds)** independently caps each timed blast (default 10 seconds; allowed 1–30 seconds), including when the requested duration is longer. The wired Arduino/GPIO hold-to-sound inputs do not use this timer.

**Hardwired button (Arduino USB or Pi 5 GPIO17):** the siren sounds while a wired input is held and stops when all active wired inputs have released. GPIO17 uses 50 ms debounce on both press and release. This differs from timed Zigbee actions; Zigbee continuous hold/release mappings have their own safety cutoff.

**Zigbee buttons (MQTT):** When **Button Action Mapping** assigns them accordingly, `single` sounds one timed cycle and `double` sounds two consecutive timed cycles **without a programmed pause**. The preferred **Aqara WXKG11LM** also sends separate `hold` and `release` actions: map these to **Start continuous siren** and **Stop continuous siren** respectively. Other previously tested types have limited functionality (no hold or release signals); a button that publishes `emergency` must have that action mapped separately. See [the Zigbee section](#zigbee2mqtt-wireless-siren-setup-and-operation) for setup and Auto-add From Log.

### Sound timing table

The system automatically plays audio cues during different periods:

| Period Type | Period Name | 30s Remaining | 10s–1s Remaining | 0s (End) |
|---|---|---|---|---|
| **Break Periods** | First Game Starts In | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| | Between Game Break | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| | Half Time | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| | Overtime Game Break | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| | Overtime Half Time | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| | Sudden Death Game Break | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| **Game Periods** | First Half | – | – | Siren (at 0s) |
| | Second Half | – | – | Siren (at 0s) |
| | Overtime First Half | – | – | Siren (at 0s) |
| | Overtime Second Half | – | – | Siren (at 0s) |
| | Sudden Death | – | – | – |

#### Notes:

- At **00:30 remaining in a break**, the single warning uses the **30-second period warning** dropdown, its own **Trim %** and the configured millisecond duration.
- At **10–1 seconds remaining**, countdown pip sounds use the **Pips** table's selected file and its per-file **Trim %**.
- Siren sounds use the selected file in the **Sirens** table and that file's **Trim %**. The operating-system/DAC/amplifier volume remains the overall master level.
- **Timed siren playback:** A short sound file loops until the configured duration is reached, subject to **Maximum Siren Duration**. The hardwired Arduino/Raspberry Pi 5 siren instead follows press/hold/release; when both inputs are active, the final wired release stops it.
- Game periods (halves) only play siren at the end, no countdown pips
- Sudden Death periods have no automatic audio cues. The Sudden Death timer counts upwards from 00:00. A goal scored during Sudden Death immediately ends the game. Sudden Death Start and Sudden Death End messages are logged but do not trigger audio.

## Scoreboard tab

**Court Time:** In this widget is the Court Time. This is synchronised to the 'Local Computer Time' when the app first opens. If the 'Crib Time' is selected, the Court Time, which may have been extended by break periods, is progressively shortened until it aligns with the Local Computer Time.

**Game Sequence:** The next row is where the Game Sequence is announced. Breaks are 'Red', Play is 'Light Coral Blue'.

**Game Number:** Under that is the Game Number, picked up from the CSV file (if this is selected from the Tournament list).

**Team names:** Then are the Team names, picked up from the CSV file (if this is selected from the Tournament list).

**Scores:** The Scores, which will get written to the CSV file when the 'Between Game Break' timer reaches 30 seconds after a game ends, are displayed next.

If the checkbox beside **Team Time-Out Period** is selected, the Team Time-Out buttons are selectable. Only one team time-out per half is permitted; no team time-outs are permitted in Overtime or Sudden Death according to CMAS rules.

**Add Goal White** adds a goal to White and, if the 'Record Scorers Cap Number' checkbox is ticked, opens a popup dialogue box where the cap number of the player scoring the goal can be entered. Unknown and Penalty Goal options are provided.

**Add Goal Black** adds a goal to Black and, if the 'Record Scorers Cap Number' checkbox is ticked, opens the same scorer popup for the Black team. Unknown and Penalty Goal options are provided.

**Minus Goal White** removes one goal from White after confirmation. It does nothing if White's score is already zero. If used during a break, Team Time-Out or Referee Time-Out, an additional warning is shown before the score is changed.

**Minus Goal Black** removes one goal from Black after confirmation. It does nothing if Black's score is already zero. If used during a break, Team Time-Out or Referee Time-Out, an additional warning is shown before the score is changed.

**CMAS final-two-minute clock procedure:** The software cannot infer from a siren whether the referee is stopping play or restarting it. When the referee directs that the clock be stopped (including the special final-two-minute situation), the operator uses **Referee Time-Out** and releases it on the referee's restart instruction. No automatic final-two-minute siren interpretation is planned. **Team timeouts:** At the end of a team timeout, the existing programmed siren and automatic return to game timing remain unchanged, following referee consultation. No rapid-buzz substitute is being implemented. See [CMAS timing and local sound preferences](CMAS_TIMING.md).\n\n**Referee Time-Out** pauses:
- Court Time
- The active game timer
- Team Time-Out timers
- Penalty timers

When Referee Time-Out is released, the interrupted period(s) resumes from the exact point at which it was paused, including Sudden Death periods.

**Penalties** is enabled during play but greyed out for breaks (as you cannot award a Penalty when play cannot be stopped [section 17.1.1 of CMAS rules]) but if the 'Referee Time-Out' button is pushed, the Penalties button becomes active (that is for you KD).

## Other game behaviour

### Coping with Errors (like when a goal is scored right on the buzzer!)

Summary of what happens when goals are added during the three "break" periods:

### Goals added during breaks

This table explains the results and progression rules when a goal is added during a break period:

| Break Period | Scores After Goal is Added | What Happens |
|---|---|---|
| Between Game Break | Even | Progress to Overtime Game Break (if Overtime allowed) OR Sudden Death Game Break (if Sudden Death allowed and Overtime not allowed). |
| | Uneven | Remain in Between Game Break. No progression; continue as normal. |
| Overtime Game Break | Even | Remain in Overtime Game Break. Proceed to overtime periods according to schedule. |
| | Uneven | Skip Overtime! Progress directly to Between Game Break. |
| Sudden Death Game Break | Even | Remain in Sudden Death Game Break. Proceed to Sudden Death period as scheduled. |
| | Uneven | Progress directly to Between Game Break. (Skips Sudden Death period.) |

This logic ensures the correct flow for tournament progression based on goals recorded during break periods.

## Zigbee2MQTT wireless siren setup and operation

This guide covers the wireless siren in the **Underwater Hockey Scoring Desk Kit (UWH)**: installation on **Windows 11** or **Raspberry Pi 5 / Raspberry Pi OS Bookworm**, MQTT configuration for Python, pairing and naming buttons, and using more than one computer. The Windows MQTT setup has been tested with **up to three working Zigbee buttons** on one coordinator (`siren_button`, `siren_button_2` and `siren_button_3`). The preferred **Aqara WXKG11LM** has been tested with `single`, `double`, `hold` and `release`; individual buttons may publish different actions, and the mapping for each action is configured in UWH. The Raspberry Pi 5 setup on **Bookworm + X11** has also successfully run a tournament.

> [!IMPORTANT]
> **A button joins one Zigbee network at a time. Do not re-pair an existing match button to another coordinator merely to use a second computer.** A second UWH computer can subscribe to the *same MQTT broker*, receiving events from the original Zigbee2MQTT instance. Re-pairing to a different Zigbee network generally removes the button from the original network and requires a reset and rejoin when moving it back. See [Using two computers](#using-two-computers-with-the-same-buttons).
>
> **Two UWH applications listening for the same button can BOTH activate their local sirens.** Decide which computer controls the live PA/amplifier and test the routing before a match.

> [!WARNING]
> **Back up `settings.json` before every UWH upgrade.** Its Zigbee button list is separate from Zigbee2MQTT's device database. Losing `settings.json` does *not* unpair a button, but UWH may stop recognising additional button names until they are re-entered.

### How the system works

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
- **Arduino/Raspberry Pi 5 hardwired siren:** Arduino USB (`SIREN_ON`/`SIREN_OFF`) and Raspberry Pi 5 GPIO17 can trigger local press/hold/release audio independently of MQTT. They can operate together: the first active wired input starts the siren and the final release stops it. If an optional MQTT siren output is configured, UWH also sends ON/OFF commands to that separate output for either input pathway. See [wired siren setup and diagnostics](#wired-siren-on-raspberry-pi-5--gpio17-and-optional-arduino-usb).

For the simple local installation, all three software components run on one machine, and the MQTT broker is `localhost:1883`. For a second UWH computer, set its **MQTT Broker** field to the hostname or LAN IP address of the existing broker; `localhost` would point to the *second* computer, not the first.

**USB-adapter caution:** A COM port identified as `CP210x` or `FTDI` describes a USB/serial interface, not proof that the device is a supported Zigbee coordinator. Check the actual adapter model and firmware against [Zigbee2MQTT's supported adapters](https://www.zigbee2mqtt.io/guide/adapters/). Zigbee2MQTT and a second program must not both try to open the same coordinator serial port.

### Raspberry Pi 5: Mosquitto, Python MQTT and Zigbee2MQTT

This section assumes the UWH source checkout and its virtual environment are installed as described in the installation section of this manual. The tested UWH desktop uses **Raspberry Pi OS Bookworm + Python 3.11 + X11**; Python 3.12 is **not** a prerequisite for that setup. These Zigbee installation commands are adapted from the current official Linux guidance; check the [upstream instructions](https://www.zigbee2mqtt.io/guide/installation/01_linux.html) for any later changes.

#### 1. Install and test the Mosquitto broker

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

#### 2. Install the Python MQTT client in the UWH virtual environment

From your **actual UWH checkout directory** (the README's example is shown below):

```bash
cd ~/Downloads/Underwater-Hockey-Scoring-Desk-Kit-main
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install paho-mqtt
.venv/bin/python -c "import paho.mqtt.client; print('Python MQTT OK')"
```

`paho-mqtt` may already be present in `requirements.txt`; the explicit install is a way to confirm it is installed in **this** `.venv`. Avoid `sudo pip install` and `--break-system-packages` on Bookworm. The UWH app can be launched with `.venv/bin/python uwh.py` as explained in the README.

#### 3. Install and start Zigbee2MQTT

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

#### 4. Optional: start Zigbee2MQTT automatically on Pi boot

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

### Windows 11: Mosquitto, Python MQTT and Zigbee2MQTT

The **tested Windows path is Mosquitto + native Windows Zigbee2MQTT + UWH over MQTT**. WSL2 is not required. Directly opening the Zigbee coordinator's COM port from UWH is **not** a substitute for Zigbee2MQTT pairing and is not the verified wireless-button path.

#### 1. Install and test Mosquitto on Windows

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

#### 2. Install Zigbee2MQTT natively on Windows

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

#### 3. Python MQTT for Windows source installations

If you run **`uwh.py` from Python** rather than the published Windows ZIP, install the project's requirements and `paho-mqtt` in the interpreter or virtual environment actually used for UWH:

```cmd
py -m pip install -r requirements.txt
py -m pip install paho-mqtt
py -c "import paho.mqtt.client; print('Python MQTT OK')"
```

Run those commands from the project directory, using your selected interpreter if `py` is not the correct one. **Users running the packaged UWH `.exe` normally do not install Python or `paho-mqtt` separately**; the executable must have been built with the needed dependencies.

#### 4. Tested Windows automatic startup: PM2 and Task Scheduler

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

### Preferred Zigbee button and other tested devices

**Preferred device to deploy: Aqara WXKG11LM wireless button**, as identified by Zigbee2MQTT for the unit tested on **6 November 2026**. It paired successfully in the Zigbee2MQTT frontend, and all four actions were confirmed working in UWH: `single`, `double`, `hold` and `release`.

**Specifications:** Aqara Wireless Mini Switch, model **WXKG11LM**, using Zigbee wireless communication. For UWH deployment, choose a version that reports `single`, `double`, `hold` and `release` through Zigbee2MQTT, as verified on the tested unit.

**UWH referee-button construction:** The original casing is removed, and wires soldered to the battery terminals connect the unit to two AA batteries. Wires soldered across the onboard switch connect it to an external waterproof push-button sourced from Jaycar. The assembly is housed in 15 mm PVC pressure pipe, with the button fitted into an end that has been heated to soften and form the pipe around it.

| Device | Deployment status | Tested functionality |
|---|---|---|
| **Aqara WXKG11LM** | **Preferred** | `single`, `double`, `hold` and `release`; supports timed cycles and hold-to-sound with a separate release signal |
| **Tuya IH-K663 and other previously tested button types** | Also tested but with limited functionality (no hold or release signals) | Use the timed-cycle mappings for the actions actually received; unsuitable for continuous hold-to-sound |

For the preferred button, map `single` to **One siren cycle**, `double` to **Two siren cycles**, `hold` to **Start continuous siren**, and `release` to **Stop continuous siren**. Save the mappings and test all four actions. Continuous operation remains subject to the configured maximum hold time and audio cutoff.

The tested unit's friendly name was `Siren_button2`; this is a user-assigned name, not the model number. Enter the exact name shown by your own frontend in UWH's **Button Device Names**. These are observed results for the tested unit, **not universal button behaviours**; verify the model and four actions when commissioning another unit from the listing.

### Pairing and naming buttons in the frontend

These steps apply to **both** platforms and are performed on the **single Zigbee2MQTT instance that owns the coordinator**.

1. Open the Zigbee2MQTT frontend: `http://localhost:8080` if browsing on the Zigbee2MQTT host, or `http://HOST-IP:8080` if its frontend is deliberately accessible on your LAN. The UWH **Open Zigbee2MQTT Frontend** button targets `localhost`; on a second computer, use the host's LAN address directly.
2. Use **Permit join** in the frontend (currently in the top navigation area). Current Zigbee2MQTT documentation says this opens joining for **254 seconds**; close it earlier when finished. The timing/UI wording can change with releases.
3. Put the button into pairing/reset mode **using the instructions for its exact model**. Do not assume a universal hold duration or LED pattern.
4. Wait for the device to join and finish its interview. If joining fails, follow the model's factory reset instructions and retry nearer the coordinator.
5. Open the device's page in the frontend and edit its **friendly name** (usually accessible from the device details or rename action). Use simple unique names **without `/`**, e.g. `siren_button`, `siren_button_2` and `siren_button_3` for one system, or perhaps `Blue_1`, `Blue_2` for buttons paired to one controller (which may be colour-coded blue) and `Orange_1`, `Orange_2` for buttons paired to another controller (which may be colour-coded orange).
![Zigbee2MQTT Devices page showing three paired siren buttons](docs/images/zigbee2mqtt-devices-three-buttons.png)

*Example Zigbee2MQTT Devices page showing three paired buttons with unique friendly names.*

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

### Configure the UWH Siren Control tab

Open UWH → **Siren Control**. Configure the application against the broker you actually use:

| UWH field | One-computer setup | Second computer sharing the same broker |
|---|---|---|
| **MQTT Broker** | `localhost` | Existing broker's **LAN IP address or DNS name** |
| **MQTT Port** | `1883` | Broker's listener port, normally `1883` |
| **MQTT Username/Password** | Leave empty only if that broker allows local unauthenticated access | Enter the broker credentials (recommended) |
| **MQTT Topic** | `zigbee2mqtt/+` | Same, if the host publishes the normal base topic |
| **Button Device Names (comma-separated)** | Enter the buttons in use; up to three have been tested together: `siren_button, siren_button_2, siren_button_3` | Names this UWH computer should respond to |
| **Siren Device Name** | Leave unchanged for ordinary **local audio** triggering | Not the input button-name list |

1. Enter any already-known friendly names in **Button Device Names**, separated by commas; enter only the buttons this UWH computer should use.
2. Click **Save Configuration** after changing the broker, topic or manually entered device names. If you changed connection details while connected, reconnect or restart UWH so the active connection uses the new configuration.
3. Click **Test App Siren** to check the selected local sound independently of Zigbee reception.
4. Press each physical button and inspect **Activity Log**. A brand-new button may initially be logged as **Ignored Zigbee button ... device is not in Button Device Names**. That observation is still captured for discovery and cannot sound the siren yet.
5. Click **Auto-add From Log**. For a newly observed button, UWH adds its friendly name to **Button Device Names** and adds the observed action to **Button Action Mapping** as **Ignore**. For an already listed button with a new action, only the new Ignore mapping is added. Select **Edit Mapping** and choose the intended response, such as **One siren cycle**.
6. Click **Save Action Mappings**. This saves both the displayed button-name allow-list and the action mappings created by Auto-add. Test each button again and confirm its intended response. A newly discovered button stays silent until you deliberately map and save its action. For example, one tested button publishes `emergency` rather than `single`.
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

### Button actions and siren playback

The table describes **observed actions and their tested mappings**, not a universal set of button commands. UWH responds only when the device and exact received action have been configured:

| Observed Zigbee2MQTT `action` | Example UWH mapping |
|---|---|
| `single` | **One siren cycle** of **Number of seconds to play App-generated Siren** |
| `double` | **Two siren cycles**, consecutive, with no deliberately programmed pause |
| `hold` | **Start continuous siren** for the preferred Aqara WXKG11LM |
| `release` | **Stop continuous siren** for the preferred Aqara WXKG11LM |
| `emergency` | A separately configured mapping, such as **One siren cycle**, for a button that publishes `emergency` |

For example, a configured duration of **1.5 seconds** gives approximately 1.5 seconds for one timed cycle and two consecutive cycles for a mapped `double`. Actual audio-start/stop overhead may cause a small transition between cycles. Different models publish different long-press and release values: inspect each button's log rather than assuming the table applies automatically.

**Important:** The preferred Aqara WXKG11LM sends separate `hold` and `release` actions, verified with **Start continuous siren** and **Stop continuous siren**. Continuous operation starts when the button reports `hold`, and is bounded by the hold timer and audio cutoff. Other previously tested button types have no hold or release signals and should use timed-cycle mappings. The **hardwired Arduino/Raspberry Pi 5 button inputs** sound locally while held, independently of MQTT, and stop when all active wired inputs have released. Timed game and wireless sirens use the selected **Sounds** file and duration, subject to **Maximum Siren Duration (seconds)** (default 10; allowed 1–30 seconds).

### Using two computers with the same buttons

**Advanced users only — untested with UWH:** sharing one MQTT broker between multiple UWH applications is a possible configuration, but has not been tested with this project. Most deployments are expected to have their own **SONOFF Zigbee USB receiver/coordinator**, Zigbee2MQTT instance and local MQTT broker, with their own buttons paired to that coordinator.

#### Untested shared-broker arrangement: one Zigbee network, multiple MQTT clients

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

In this advanced, **untested shared-broker arrangement**, the two UWH applications can be on **Windows, Raspberry Pi, or a mixture** and can each subscribe to the same broker. This is not the expected setup for most deployments. The button is paired **once**, to the **one** coordinator. The second computer does not require another Zigbee USB dongle or a second Zigbee2MQTT instance merely to receive those button messages.

**Example:** Zigbee2MQTT and Mosquitto run on Windows PC 1, whose broker is reachable at `192.168.1.50` (illustrative address only). UWH on PC 1 uses `MQTT Broker: localhost`. UWH on the Raspberry Pi/PC 2 uses `MQTT Broker: 192.168.1.50`, the same port and the same relevant button names. Both subscribe to the existing Zigbee2MQTT topics. The broker must be configured for authenticated LAN access; `localhost` on PC 2 would not reach PC 1.

> [!CAUTION]
> **Shared-button siren hazard:** If both UWH applications listen for `siren_button` and both computers are connected to an audible amplifier, pressing the button can activate **two sirens**. Each UWH instance has its own sound state and is *not* automatically synchronised with the other's game clock. If the intention is one live siren, configure only the designated controlling application to accept that button (or otherwise isolate/mute the secondary audio output). Test this with the actual PA before play. Do not assume MQTT provides automatic active/standby failover.

#### Different arrangement: moving a button to another Zigbee coordinator

If the second computer has a **different Zigbee coordinator and different Zigbee network**, a standard Zigbee button cannot normally remain joined to **both** networks. Moving it usually involves a model-specific reset and joining the second network. This can make it disappear from the first coordinator's working network until moved back. **Do not do this to a live referee button just to get a second UWH display or client.** See the [official Zigbee2MQTT FAQ](https://www.zigbee2mqtt.io/guide/faq/) for the one-coordinator/one-network limitation.

Running two *independent* Zigbee2MQTT networks on one broker also requires different `base_topic` values; the corresponding UWH topic must match. This is a separate advanced deployment, not a way to pair one button to both radios simultaneously.

### Network access and security

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

### Updates, backups and troubleshooting

#### What to back up

| Item | What it contains | Important distinction |
|---|---|---|
| **UWH `settings.json`** | Siren files/duration, MQTT broker, button-name list, **action mappings**, display settings and other app preferences | Restoring its names **and mappings** can recover UWH recognition without re-pairing. Back it up before replacing a UWH ZIP; UWH also retains up to five recent `settings_old_*.json` backups. |
| **`Tournament data/`, `Sounds/`, logs** | Draws/results, custom audio and local records | These folders sit beside the app so operators can find and back them up easily. A UWH update must not overwrite operator-created files. |
| **Zigbee2MQTT `data/` folder** | Zigbee2MQTT configuration and network/device database | Back up before changing Zigbee2MQTT or moving installations; preserving the coordinator/network data matters for retained pairing. |
| **PM2 process list on Windows** | Saved Zigbee2MQTT startup process for that Windows user | Run `pm2 save` after setup. A Task Scheduler task alone does not recreate a missing PM2 saved process. |

#### Troubleshooting checklist

| Observation | What to check |
|---|---|
| Frontend does not open at `localhost:8080` | Is Zigbee2MQTT actually running? On the **Windows computer that runs Zigbee2MQTT**, open **Command Prompt** or **PowerShell** while signed in as the **same Windows account that was used to set up and save the PM2 process list**, then type `pm2 list` to see whether the `zigbee2mqtt` process is online. Type `pm2 logs zigbee2mqtt` to view its recent/startup log messages; press **Ctrl+C** when you have finished viewing the live log. Also check Task Scheduler's **Last Run Result** for the Zigbee2MQTT startup task. On Raspberry Pi/Linux, open a Terminal and run `systemctl status zigbee2mqtt`. Check frontend enablement and port as well. |
| UWH displays **Connected** but no button appears in the activity log | **Connected** means the MQTT broker session is up, not that a button is paired or mapped. Press the button and inspect Zigbee2MQTT's log; compare the **friendly name**, MQTT topic (`zigbee2mqtt/+`), and **Button Device Names**. UWH's Arduino/USB labels report **Detected** ports, not proof that an Arduino COM port was opened. |
| One button works but another does not | Press the non-working button and check **Activity Log**. If UWH logs **Ignored Zigbee button ... device is not in Button Device Names** or **Unmapped action**, click **Auto-add From Log**. UWH will add an observed new button name and/or action as a safe **Ignore** entry. Edit it to the desired response and click **Save Action Mappings**. Missing UWH settings do not necessarily mean the device needs re-pairing. |
| Zigbee2MQTT publishes `{"battery":...}` but UWH is silent | A battery-only update has **no `action`**; it is device status rather than a button press. |
| A newly named button stops working | A frontend rename changes the device MQTT topic. Update UWH's exact friendly-name list. |
| One PC sees the events, the other does not | PC 2 must connect to PC 1's *LAN broker address*, not its own `localhost`. Check Mosquitto listener/authentication, firewall, subnet and MQTT topic. |
| Both PCs sound their sirens | Both subscribed to the same button; this is expected, not a pairing fault. Configure the standby application's allowed button names or audio routing. |
| Windows broker works but Zigbee2MQTT does not start after boot | Set Mosquitto **Automatic**; confirm `pm2 save` under the task's Windows account and correct `pm2.cmd`/working directory; inspect Scheduler history. Do not run two PM2 instances. |
| Pi MQTT fails with `ModuleNotFoundError` | Check `.venv/bin/python -m pip show paho-mqtt`, then run UWH using that same virtual environment. |
| Frontend says adapter missing / port busy | Find the actual COM port or `/dev/serial/by-id`; confirm adapter type and permissions, and close any other program using the coordinator. |
| Audible siren works but timing or level is different | Check the selected siren file and its **Trim %** in the **Sounds** tab, **Number of seconds to play App-generated Siren**, **Maximum Siren Duration**, and the operating-system/DAC/amplifier master volume. Arduino USB and Raspberry Pi 5 GPIO17 hold-to-sound differ from Zigbee timed actions; if a wired siren stays on, check whether the other wired input is still active in **Siren Control → Activity Log**. |

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

### Official references

- [Zigbee2MQTT getting started and onboarding](https://www.zigbee2mqtt.io/guide/getting-started/)
- [Zigbee2MQTT Linux installation](https://www.zigbee2mqtt.io/guide/installation/01_linux.html)
- [Zigbee2MQTT Windows installation](https://www.zigbee2mqtt.io/guide/installation/05_windows.html)
- [Pairing devices / Permit join](https://www.zigbee2mqtt.io/guide/usage/pairing_devices.html)
- [MQTT topics, friendly names and device rename](https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html)
- [Zigbee2MQTT FAQ: one coordinator and one network per device](https://www.zigbee2mqtt.io/guide/faq/)
- [Mosquitto downloads](https://mosquitto.org/download/), [Windows service instructions](https://github.com/eclipse-mosquitto/mosquitto/blob/master/README-windows.txt), [MQTT authentication](https://mosquitto.org/documentation/authentication-methods/)
- [Eclipse Paho Python client](https://pypi.org/project/paho-mqtt/)

## About tab

The **About** tab shows the running application version and the project credits. It includes clickable links to the local `README.md` in the installed UWH folder, the project repository, and the project contact email.

This app was started in Google AI, made workable by GitHub Copilot and extensively refactored, tweaked, improved, expanded and tested by ChatGPT. Conducted by David Stirling (who can't write code), davidstirling777@gmail.com.

The conductor seems to be the star of the show, even though they do not make any noise. They even get to come on to the stage all on their own, to rapturous applause.

This app can be downloaded free from:  
https://github.com/davidstirling777-star/Underwater-Hockey-Scoring-Desk-Kit

## Other installation and packaging notes

### Running on other systems

The source remains a Python/Tkinter program and can be run from a virtual environment on other supported systems. For normal installations, however, use the prepared platform package when one is available:

- **Windows x64:** `UnderwaterHockeyScoringDesk-v<version>-Windows.zip`
- **Raspberry Pi 5 / Linux ARM64:** `UnderwaterHockeyScoringDesk-v<version>-RaspberryPi5.zip`

Both packages are produced from the same commit and use the same displayed `1.2.<build>` version. Windows 11 has been tested end-to-end with Zigbee2MQTT. The Raspberry Pi 5 setup on Bookworm + X11 has successfully run a tournament.

For a source installation on Raspberry Pi OS Bookworm, use a project virtual environment rather than a system-wide `pip install`. `paho-mqtt` is the Python MQTT client, not the MQTT broker; Zigbee2MQTT remains a separate Node.js program.

### Standalone release builds

The repository uses PyInstaller's **one-folder** format. The GitHub Actions release workflow builds the application separately on each native platform:

- Windows is built on the GitHub-hosted `windows-2022` x64 runner.
- Raspberry Pi 5 is built on the GitHub-hosted `ubuntu-22.04-arm` ARM64 runner.
- The Pi build is checked with `file` to confirm an **ARM64/aarch64** executable and with `ldd` to detect unresolved shared libraries in the build environment.
- Both ZIPs must build successfully before the publish job creates the GitHub Release.
- Pull requests run both platform builds but do **not** publish a release.

The Raspberry Pi ZIP contains `Start-UWH.sh` as a convenient launcher. Keep each extracted one-folder application intact; do not copy only the main executable away from its `_internal` directory.

Source/PyInstaller builds are still possible for developers, but ordinary users should use **Releases → Assets** rather than GitHub's automatically generated source archives.

### Startup self-test

The application includes a startup diagnostic window and a Siren Control activity log. Device/COM-port detection is a diagnostic, **not** proof of Zigbee pairing or an audible siren. For a Pi 5 wired input, confirm GPIO17 readiness and press/release events in **Siren Control → Activity Log**; Arduino USB events are logged separately. Test each wired path individually and then together to verify that the siren stops after the final release. The Windows MQTT path has been tested by pressing the physical buttons and hearing the local siren; use the same end-to-end test on any new computer.

### Useful references

- [Raspberry Pi OS downloads](https://www.raspberrypi.com/software/) — Bookworm-based Raspberry Pi OS Legacy desktop images.
- [Raspberry Pi OS documentation](https://www.raspberrypi.com/documentation/computers/os.html) — OS updates and Python virtual environments.
- [Raspberry Pi desktop configuration](https://www.raspberrypi.com/documentation/computers/configuration.html) — switching between X11 and Wayland using `raspi-config`.
- [GitHub: downloading files](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives-and-directories) — using Code → Download ZIP.
- [Zigbee2MQTT wireless siren setup and operation](#zigbee2mqtt-wireless-siren-setup-and-operation) — Mosquitto, Python/Paho, Zigbee2MQTT, pairing, multi-computer warnings and troubleshooting.
- `HARDWARE_SETUP.md` — wired Arduino/physical hardware, where supplied.
