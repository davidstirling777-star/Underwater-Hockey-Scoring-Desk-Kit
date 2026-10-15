# Hardware setup — UWH Scoring Desk Kit

This document describes the **current Raspberry Pi 5 test installation** and distinguishes it from the **motherboard/production hardware still being developed**. It is a hardware companion to [README.md](README.md), which contains the current software installation, screen, sounds and Zigbee instructions.

> [!IMPORTANT]
> The earlier NeoPixel stick and Arduino battery-voltage-divider experiments are **not part of the present hardware**. They are intentionally omitted here. Do not use old prototype photographs or wiring instructions as build instructions for the current UWH motherboard.

## 1. Current tested configuration (October 2026)

| Item | Present setup / status |
| --- | --- |
| Scoring computer | **Raspberry Pi 5, 8 GB RAM**, running UWH |
| Operating system | **Raspberry Pi OS Bookworm Desktop (64-bit), X11** |
| RAM usage | Approximately **1.7 GB observed with UWH running** on the 8 GB Pi |
| 2 GB Pi 5 | **Expected to be sufficient** for this workload from the observed memory use, but **not yet separately tested**; verify headroom under the full intended display, audio, USB and Zigbee workload |
| Audio output | **PiFi DAC+ v2.0 HAT**, recognised under the HiFiBerry DAC+ / `snd_rpi_hifiberry_dacplus` driver |
| Audio interconnect | **Stereo 3.5 mm TRS cable** from the DAC audio output to the pool-audio input |
| Amplifier | **FUSUPI XH-M562** stereo amplifier module on the Pool Audio Zones board |
| AIR speaker | **TOA SC-615, 8 Ω** horn (the low-impedance model, **not** the 70/100 V transformer version) |
| Pool-audio board power | **16.0 V DC** at the amplifier in the latest bench test |
| Level adjustments | Pool-audio **R3 (AIR)** and **R4 (WATER)** potentiometers; application sound-file trims; RP5 system output level |
| Wired siren input | Arduino/serial siren-button path supported by UWH; consult the actual installed motherboard wiring/Arduino firmware before copying a pinout |
| Wireless inputs | Optional Zigbee referee buttons via coordinator, Zigbee2MQTT and MQTT; Windows configuration has been tested with up to three working buttons |

The current 8 GB machine has demonstrated that the application does **not** need 8 GB solely to accommodate its observed RAM use. The proposed 2 GB configuration still needs a full real-world check; the 1.7 GB observation is **not** a guaranteed maximum and leaves less margin for the desktop, caches and other services.

For final production installation, the selected monitors, mounting and power arrangement must be checked against the as-built motherboard. Do not treat proposed monitor models or daughterboard designs as a verified equipment list.

## 2. Raspberry Pi 5 software and displays

The tested system uses **Bookworm + X11**. In earlier two-display testing, moving the pointer over the Game Variables controls under Wayland could make GPU usage approach 98% and cause jerky mouse movement. X11 substantially improved responsiveness.

To select X11:

1. Open Terminal and run `sudo raspi-config`.
2. Select **6 Advanced Options → A7 Wayland → W1 X11**.
3. Finish and reboot.
4. Verify with `echo $XDG_SESSION_TYPE` (expected: `x11`).

UWH supports operator and external display windows; select the required layout in the **Screens** tab and use **Auto Detect Screens** and **Test Displays** to check the actual monitor assignments. See [README.md](README.md#raspberry-pi-5-tested-configuration-september-2026) and its Screens instructions for details.

## 3. Audio hardware and connections

The current audio path is:

```text
UWH application on Raspberry Pi 5
              |
       PipeWire/WirePlumber
              |
        PiFi DAC+ v2.0 HAT
              |
     stereo 3.5 mm TRS cable
              |
   Pool Audio Zones J1 (stereo input)
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

### Stereo cable is required

**Use a stereo TRS cable (two insulating rings on a 3.5 mm plug), not a mono TS plug.** Although the sound is ultimately mixed to mono by the Pool Audio Zones board, the DAC and board input have separate left and right connections. A mono plug in a stereo output can short one output channel to ground, potentially affecting sound and loading the DAC improperly.

Use the correct mating connector arrangement for the actual DAC version: the tested installation now uses the stereo 3.5 mm interconnect.

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

Zigbee inputs use a compatible USB coordinator, Zigbee2MQTT, an MQTT broker and UWH's **Zigbee Siren** settings. On Windows 11, UWH has been tested with **up to three working Zigbee buttons** on one coordinator. A complete equivalent Raspberry Pi coordinator/broker deployment should be validated separately before relying on it at a competition.

Each Zigbee device belongs to one coordinator network at a time. Different button models emit different events; map each device's actual actions in the UWH interface. Read the [Zigbee section of README.md](README.md#zigbee2mqtt-wireless-siren-setup-and-operation) for tested behaviour, pairing and maintenance.

### USB/serial device detection

UWH scans for candidate Arduino serial ports and Zigbee adapters and remembers relevant settings, but USB adapter descriptions alone do not prove that a device is the correct coordinator. Serial device naming differs between Windows COM ports and Linux `/dev/tty*` devices. Use the app's detection/troubleshooting controls and verify the actual attached device.

## 6. Motherboard and DC-DC supplies — design versus test status

The project includes a custom UWH motherboard and plug-in power/audio circuitry, including separate DC-DC outputs for the monitor(s), pool audio and the future integrated RP5 supply. These are evolving hardware designs, not all of which are present in or verified by the current bench installation.

**Current RP5 test power:** the Raspberry Pi 5 is presently powered through its **own USB-C power supply**, not yet through the proposed motherboard 5.1 V GPIO feed.

**Production power plan:** the motherboard is designed to provide a regulated **5.1 V at least 5 A** to the RP5's 5 V GPIO header pins from a dedicated **LMQ61460-based PDM-Audio DC-DC daughterboard**. This bypasses USB-C power negotiation. The README explains the required bootloader configuration, including `PSU_MAX_CURRENT=5000`, and the warning not to claim 5 A unless the **entire** power path has been verified.

> [!WARNING]
> Do not use the proposed GPIO power arrangement until its voltage, current capability, start-up behaviour and all relevant connections have been verified. Do not power the Pi simultaneously through the proposed GPIO feed and another USB-C supply.

Other PDM boards, fused 24 V inputs, monitor supplies, battery-backup switching and mounting arrangements are part of the hardware design and must be documented against the final manufactured assembly before making a production wiring guide. The existing CAD and schematic files take precedence over old prototype photos or assumptions.

For full power supply setup and bootloader commands, consult [README.md — Raspberry Pi 5 power supply configurations](README.md#raspberry-pi-5-power-supply-configurations).

## 7. Commissioning checklist

- [ ] Confirm Bookworm **X11** and test the operator and display windows.
- [ ] Verify the DAC is recognised and selected in `wpctl status`; restart UWH after changing the default audio sink.
- [ ] Fit the correct **stereo TRS** interconnect; do not use a mono plug in the DAC's stereo output.
- [ ] Check RP5 audio level (currently **0.80** in workshop testing) and adjust R3/R4 gently from low volume.
- [ ] Set pip/siren file trims in **Sounds** and test both cues at the actual venue.
- [ ] Confirm the hardwired siren button and any mapped Zigbee actions.
- [ ] Check both amplifier outputs and all isolation/grounding requirements.
- [ ] Verify supply rails and fuses against the **actual as-built** board rather than inferred power figures.
- [ ] Repeat volume and output-selection checks after a reboot.

## 8. Details still to confirm for the finished hardware specification

The present document intentionally avoids claiming unverified production details. Before turning it into a definitive assembly/wiring guide, confirm the **final fitted motherboard revision and board connectors**, **actual monitor models and supply rails**, **RP5 boot medium and finished 5.1 V power implementation**, and **whether Zigbee2MQTT/coordinator hardware is installed locally on the RP5 or remains on another computer**.

For operating instructions, see [README.md](README.md). For software internals, see [MAINTAINERS.md](MAINTAINERS.md).
