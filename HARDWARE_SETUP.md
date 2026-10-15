# Hardware setup — UWH Scoring Desk Kit

This document describes the **current Raspberry Pi 5 test installation** and distinguishes it from the **motherboard/production hardware still being developed**. It is a hardware companion to [README.md](README.md), which contains the current software installation, screen, sounds and Zigbee instructions.

> [!IMPORTANT]
> The earlier NeoPixel stick and Arduino battery-voltage-divider experiments are **not part of the present hardware**. They are intentionally omitted here. Do not use old prototype photographs or wiring instructions as build instructions for the current UWH motherboard.

## 1. Current tested configuration (October 2026)

| Item | Present setup / status |
| --- | --- |
| Scoring computer | **Raspberry Pi 5, 8 GB RAM**, running UWH |
| Storage / boot | **NVMe SSD via an NVMe Base**, with the RP5 booting from the SSD |
| Motherboard | **UWH Scoring Desk motherboard Rev B** (current assembly) |
| PDM DC-DC revision | **Rev B currently installed**; **Rev C or later is required** for the RP5 5.1 V power-supply option |
| Current RP5 power | **Separate USB-C power supply**, not yet powered by the motherboard/PDM |
| Display currently used | **LG 24MP400-B** monitor |
| Other LG displays considered | **LG 29U511A-B (29-inch ultrawide)** and **LG 32U631A-B (31.5-inch QHD)**; candidate options, not confirmed installed |
| Zigbee coordinator | **SONOFF Zigbee 3.0 USB Dongle Plus (ZBDongle-P)** plugged into the RP5 |
| Operating system | **Raspberry Pi OS Bookworm Desktop (64-bit), X11** |
| RAM usage | Approximately **1.7 GB observed with UWH running** on the 8 GB Pi |
| 2 GB Pi 5 | **Expected to be sufficient** for this workload from the observed memory use, but **not yet separately tested**; verify headroom under the full intended display, audio, USB and Zigbee workload |
| Prototype/test audio DAC | **PiFi DAC+ v2.0 HAT**, recognised under the HiFiBerry DAC+ / `snd_rpi_hifiberry_dacplus` driver |
| Production audio DAC | **Genuine Raspberry Pi DAC+ HAT** (planned replacement for the prototype PiFi DAC+ v2.0; production unit not yet tested) |
| Current audio interconnect — required | **3.5 mm stereo TRS male-to-male cable** (stereo-to-stereo, two insulating rings on **each** plug) between the **PiFi DAC+ v2.0 HAT** and **Pool Audio Zones Rev 2** stereo input J1 |
| Pool-audio board | **Pool Audio Zones Rev 2**, fitted with the **FUSUPI XH-M562** stereo amplifier module |
| AIR speaker | **TOA SC-615, 8 Ω** horn (the low-impedance model, **not** the 70/100 V transformer version) |
| Pool-audio board power | **16.0 V DC** at the amplifier in the latest bench test |
| Level adjustments | Pool-audio **R3 (AIR)** and **R4 (WATER)** potentiometers; application sound-file trims; RP5 system output level |
| Wired siren input | Arduino/serial siren-button path supported by UWH; consult the actual installed motherboard wiring/Arduino firmware before copying a pinout |
| Wireless inputs | Optional Zigbee referee buttons via coordinator, Zigbee2MQTT and MQTT; Windows configuration has been tested with up to three working buttons |

The current 8 GB machine has demonstrated that the application does **not** need 8 GB solely to accommodate its observed RAM use. The proposed 2 GB configuration still needs a full real-world check; the 1.7 GB observation is **not** a guaranteed maximum and leaves less margin for the desktop, caches and other services.

**Monitor status:** the current display is an **LG 24MP400-B**. Two other LG models have been discussed as alternatives: **LG 29U511A-B**, a 29-inch ultrawide option for an operator display, and **LG 32U631A-B**, a 31.5-inch QHD option for larger viewing. These are **possibilities, not tested or fitted monitors** in the present assembly. The proposed motherboard 19 V monitor-output arrangement and monitor DC connector/polarity/current requirements must be verified for each exact model before wiring; do not assume that the present LG 24MP400-B is powered from the motherboard.

For final production installation, the selected monitors, mounting and power arrangement must be checked against the as-built motherboard. Do not treat proposed monitor models or daughterboard designs as a verified equipment list.

## 2. Raspberry Pi 5 software and displays

The tested system uses **Bookworm + X11**. In earlier two-display testing, moving the pointer over the Game Variables controls under Wayland could make GPU usage approach 98% and cause jerky mouse movement. X11 substantially improved responsiveness.

To select X11:

1. Open Terminal and run `sudo raspi-config`.
2. Select **6 Advanced Options → A7 Wayland → W1 X11**.
3. Finish and reboot.
4. Verify with `echo $XDG_SESSION_TYPE` (expected: `x11`).

UWH supports operator and external display windows; the currently used monitor is the LG 24MP400-B, while the LG 29U511A-B ultrawide and LG 32U631A-B QHD are options under consideration, not confirmed equipment. Select the required layout in the **Screens** tab and use **Auto Detect Screens** and **Test Displays** to check the actual monitor assignments. See [README.md](README.md#raspberry-pi-5-tested-configuration-september-2026) and its Screens instructions for details.

## 3. Audio hardware and connections

The **current tested prototype** audio path is:

```text
UWH application on Raspberry Pi 5
              |
       PipeWire/WirePlumber
              |
        PiFi DAC+ v2.0 HAT
              |
  3.5 mm stereo TRS male-to-male cable
        (two rings on each plug)
              |
 Pool Audio Zones Rev 2, J1 stereo input
       R1/R2 mix L + R to mono
              |
       +------+------+
       |             |
     R3 AIR        R4 WATER
       |             |
  XH-M562 AIR    XH-M562 WATER
       |             |
 TOA SC-615      WATER audio path
  8 Ω horn       (isolation transformer
                  hardware as designed)
```

### Audio cable requirement and production DAC

> [!IMPORTANT]
> **Current PiFi DAC+ v2.0 HAT to Pool Audio Zones Rev 2 board:** use a **stereo-to-stereo 3.5 mm TRS male-to-male audio cable**. Both plugs must have **two insulating rings** (tip = left, ring = right, sleeve = common). **Do not use a mono TS cable or mono adapter.**

Although the audio is ultimately mixed to mono through R1/R2 on the **Pool Audio Zones Rev 2** board, its input is stereo. A mono plug inserted into a stereo DAC output can short one channel to ground, potentially causing poor sound, distortion or abnormal loading. In October 2026 bench testing, replacing a mono cable with a stereo cable coincided with an increase in RP5 software volume; because both changed, the improvement cannot be attributed to the cable alone. The stereo-to-stereo connection is nevertheless the correct wiring.

**Production hardware will use the genuine Raspberry Pi DAC+ HAT**, in place of the PiFi DAC+ v2.0 used for current testing. Preserve the **left, right and signal-ground stereo input** to Pool Audio Zones Rev 2. Check the genuine DAC+'s actual available output connectors and use the correct adapter if necessary; **do not assume the production DAC has an identical 3.5 mm socket to the PiFi board**. If using separate left/right RCA outputs, the production interconnect must combine them correctly into a **stereo TRS connector** at the Pool Audio Zones input, not short them together. Verify and document the production DAC driver's audio-device settings before deployment; the PiFi/HiFiBerry-compatible test settings are not automatically guaranteed to be correct for the genuine Raspberry Pi DAC+.

### AIR and WATER output safety

The XH-M562 is a bridged-output amplifier. **Do not connect either speaker output wire to ground, chassis, earth or pool bonding.** Follow the Pool Audio Zones schematic for the WATER output isolation-transformer wiring, including transformer ratings and matching taps. Do not assume an ordinary grounded amplifier output.

Keep the amplifier's AIR and WATER level controls separate. The TOA SC-615 is an efficient horn and can become dangerously loud; begin tests with both controls down and keep people away from its acoustic axis.

## 4. Tested audio level settings — starting point, not fixed calibration

During October 2026 bench testing:

- The 16.0 V amplifier supply stayed at **16.0 V measured directly across XH-M562 pin 3 (+ supply) and pin 2 (power ground)** while the siren sounded.
- The **same siren MP3** played through a Windows laptop was loud and clear on the amplifier, showing that the audio hardware has ample output.
- On the Raspberry Pi, the PiFi DAC+ ALSA controls were already at **100%, 0.00 dB** (`Digital` and `Analogue`). The unexpectedly quiet siren was traced to the OS software sink level and was also investigated alongside replacement of the mono interconnect cable.
- The RP5 PipeWire level was increased and ultimately set to **0.80 (80%)**; this placed R3 and R4 around the useful middle of their adjustment range in the bench setup.
- The selected pip sound (`pip-beep.mp3`) was trimmed to **30%**, compared with `siren-car-honk.mp3`, because the pip sounded disproportionately loud.
- The previously tested 0.50 PipeWire setting **persisted across a Raspberry Pi reboot**. Recheck persistence after changing to 0.80.

**These are provisional workshop settings.** Confirm AIR and WATER volume at the pool. Do not raise or lower the 16.0 V amplifier supply just to compensate for a software volume mismatch.

### Check and set audio output

```bash
cat /proc/asound/cards
wpctl status
wpctl get-volume @DEFAULT_AUDIO_SINK@
```

On the tested RP5, HDMI appeared as cards 0 and 1, and the DAC as **ALSA card 2**. Card and PipeWire sink numbers can change, so identify them each time rather than hard-coding them in scripts.

To set the presently selected default audio sink to the **tested 80% starting point**:

```bash
wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.80
wpctl get-volume @DEFAULT_AUDIO_SINK@
```

Check that `wpctl status` shows the DAC as the **default sink**. UWH selects the audio device when it starts; if you change the default device, **close and restart UWH**. The **Sounds** tab reports the audio output in use.

The per-file **Trim %** fields balance cues relative to each other. They are not replacements for the overall OS/DAC/amplifier volume control. Use lower trims where needed; excessive horn levels can damage hearing.

For DAC driver configuration, audio troubleshooting and software installation, see the [Sounds section of README.md](README.md#sounds-tab).

## 5. Siren triggers

### Wired Arduino button

The software retains a wired Arduino serial input for the referee's momentary siren button. With the current application, the hardwired button's siren sounds while it is pressed and stops when released. This is separate from the timed Zigbee action mappings.

The early standalone Arduino/NeoPixel/voltage-monitoring demonstration is **obsolete** as an installation example. The current motherboard's Arduino Nano Every wiring and firmware are the source of truth for the production button circuit. Do not add the old A3 battery divider, NeoPixel LEDs or their resistors to the current hardware.

### Optional Zigbee referee buttons

**Hardware currently connected to the RP5:** a **SONOFF Zigbee 3.0 USB Dongle Plus (ZBDongle-P)** coordinator. Zigbee input also requires a correctly configured Zigbee2MQTT service, an MQTT broker and UWH's **Zigbee Siren** settings. Merely plugging in the dongle does **not** establish that the complete RP5 Zigbee/MQTT system has passed a full operational test.

On Windows 11, UWH has been tested with **up to three working Zigbee buttons** on one coordinator. The Raspberry Pi coordinator/broker setup should be validated separately before relying on it at a competition.

Each Zigbee device belongs to one coordinator network at a time. Different button models emit different events; map each device's actual actions in the UWH interface. Read the [Zigbee section of README.md](README.md#zigbee2mqtt-wireless-siren-setup-and-operation) for tested behaviour, pairing and maintenance.

### USB/serial device detection

UWH scans for candidate Arduino serial ports and Zigbee adapters and remembers relevant settings, but USB adapter descriptions alone do not prove that a device is the correct coordinator. Serial device naming differs between Windows COM ports and Linux `/dev/tty*` devices. Use the app's detection/troubleshooting controls and verify the actual attached device.

## 6. Motherboard and DC-DC supplies — design versus test status

The **current motherboard assembly is Rev B**, with the **Rev B PDM power-supply board**. These are *different boards*: a motherboard revision is not the same as a PDM revision. The project includes plug-in power/audio circuitry with separate DC-DC outputs for the monitor(s), pool audio and the future integrated RP5 supply. The designs remain under development, so not every proposed supply is present or verified in the current bench assembly.

**Current RP5 storage:** the Raspberry Pi 5 boots from an **NVMe SSD mounted on an NVMe Base**.

**Current RP5 test power:** the Raspberry Pi 5 is presently powered through its **own USB-C power supply**, not yet through the proposed motherboard 5.1 V GPIO feed. The **current Rev B PDM is not suitable for the intended RP5 low-voltage supply option**; **PDM Rev C or later is required** to provide that option. The latest suitable PDM revision has **not yet been obtained and tested**.

**Production power plan:** with a suitable **PDM Rev C or later**, the motherboard design is intended to provide a regulated **5.1 V at least 5 A** to the RP5's 5 V GPIO header pins from a dedicated **LMQ61460-based PDM-Audio DC-DC daughterboard**. The PDM revision is a **necessary design requirement, not proof** that the assembled output has passed voltage, load and startup testing. This power approach bypasses USB-C power negotiation. The README explains the required bootloader configuration, including `PSU_MAX_CURRENT=5000`, and the warning not to claim 5 A unless the **entire** power path has been verified.

> [!WARNING]
> Do not use the proposed GPIO power arrangement until its voltage, current capability, start-up behaviour and all relevant connections have been verified. Do not power the Pi simultaneously through the proposed GPIO feed and another USB-C supply.

Other PDM boards, fused 24 V inputs, monitor supplies, battery-backup switching and mounting arrangements are part of the hardware design and must be documented against the final manufactured assembly before making a production wiring guide. The **currently fitted Rev B motherboard and Rev B PDM** must not be represented as an already validated 5.1 V RP5 GPIO supply. The existing CAD and schematic files take precedence over old prototype photos or assumptions.

For full power supply setup and bootloader commands, consult [README.md — Raspberry Pi 5 power supply configurations](README.md#raspberry-pi-5-power-supply-configurations).

## 7. Commissioning checklist

- [ ] Confirm Bookworm **X11** and test the operator and display windows.
- [ ] Verify the DAC is recognised and selected in `wpctl status`; restart UWH after changing the default audio sink.
- [ ] For the current **PiFi DAC+ v2.0 → Pool Audio Zones Rev 2** connection, fit a **3.5 mm stereo TRS male-to-male cable** (two rings on both ends); never use the mono TS cable.
- [ ] For the planned **genuine Raspberry Pi DAC+** production HAT, verify the DAC output connectors and left/right/ground mapping to the Pool Audio Zones Rev 2 stereo input; verify audio device/driver setup on that HAT.
- [ ] Check RP5 audio level (currently **0.80** in workshop testing) and adjust R3/R4 gently from low volume.
- [ ] Set pip/siren file trims in **Sounds** and test both cues at the actual venue.
- [ ] Confirm the hardwired siren button and any mapped Zigbee actions.
- [ ] Check both amplifier outputs and all isolation/grounding requirements.
- [ ] Check the **Rev B motherboard** and **Rev B PDM** against their actual fitted components; do not connect RP5 GPIO power until a **Rev C or later PDM** is installed and its 5.1 V / 5 A output is validated.
- [ ] Confirm the attached **SONOFF ZBDongle-P** is recognised and verify full Zigbee2MQTT/MQTT/button operation if used.
- [ ] Verify supply rails and fuses against the **actual as-built** board rather than inferred power figures.
- [ ] Repeat volume and output-selection checks after a reboot.

## 8. Details still to confirm for the finished hardware specification

The present document intentionally avoids claiming unverified production details. **Confirmed now:** motherboard **Rev B**; PDM **Rev B** fitted (**Rev C or later required** for RP5 power); RP5 boots from an **NVMe Base SSD** and remains **USB-C powered**; monitor **LG 24MP400-B**; and a **SONOFF ZBDongle-P** is plugged into the RP5. Still to verify: the finished motherboard and daughterboard connector/fuse inventory, whether the monitor is powered externally or from the motherboard, the final **5.1 V / at least 5 A PDM Rev C+ hardware**, the production **genuine Raspberry Pi DAC+ HAT** connectors/driver configuration, and operational status of the **RP5 Zigbee2MQTT/MQTT services and button tests**. The two other LG displays listed above remain **candidate models only**.

For operating instructions, see [README.md](README.md). For software internals, see [MAINTAINERS.md](MAINTAINERS.md).
