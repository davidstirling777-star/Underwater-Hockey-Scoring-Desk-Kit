# Hardware setup — UWH Scoring Desk Kit

This document describes the **currently installed Raspberry Pi 5 UWH Scoring Desk hardware**, together with clearly identified hardware options still being developed. It is a companion to [README.md](README.md), which contains software installation, screens, sounds and Zigbee instructions.

## 1. Current tested configuration (October 2026)

| Item | Present setup / status |
| --- | --- |
| Scoring computer | **Raspberry Pi 5, 8 GB RAM**, running UWH |
| Storage / boot | **NVMe SSD via an NVMe Base**, with the RP5 booting from the SSD |
| Motherboard | **UWH Scoring Desk motherboard Rev B** (current assembly) |
| PDM DC-DC revision | **Rev B currently installed**; **Rev C or later is required** for the RP5 5.1 V power-supply option |
| Current RP5 power | **Separate USB-C power supply**, not yet powered by the motherboard/PDM |
| Display currently used | **LG 24MP400-B** monitor |
| Current monitor power | **19 V DC** from a motherboard-mounted PDM through a custom DC cable. **Centre-positive at the monitor plug and matching supply connector** has been tested and works; verify connector dimensions and current rating before making additional cables |
| Other LG displays considered | **LG 29U511A-B (29-inch ultrawide)** and **LG 32U631A-B (31.5-inch QHD)**; candidate options, not confirmed installed |
| Zigbee coordinator | **SONOFF Zigbee 3.0 USB Dongle Plus (ZBDongle-P)** plugged into the RP5 |
| Operating system | **Raspberry Pi OS Bookworm Desktop (64-bit), X11** |
| RAM usage | Approximately **1.7 GB observed with UWH running** on the 8 GB Pi |
| 2 GB Pi 5 | **Expected to be sufficient** for this workload from the observed memory use, but **not yet separately tested**; verify headroom under the full intended display, audio, USB and Zigbee workload |
| Audio DAC currently fitted | **PiFi DAC+ v2.0 HAT**, recognised under the HiFiBerry DAC+ / `snd_rpi_hifiberry_dacplus` driver |
| Planned production audio DAC | **Genuine Raspberry Pi DAC+ HAT**; confirm the actual connectors and driver configuration before installing |
| Current audio interconnect — required | **3.5 mm stereo TRS male-to-male cable** (stereo-to-stereo, two insulating rings on **each** plug) between the **PiFi DAC+ v2.0 HAT** and **Pool Audio Zones Rev 2** stereo input J1 |
| Pool-audio board | **Pool Audio Zones Rev 2**, fitted with the **FUSUPI XH-M562** stereo amplifier module |
| AIR speaker | **TOA SC-615, 8 Ω** horn (the low-impedance model, **not** the 70/100 V transformer version) |
| Pool-audio board power | **16.0 V DC** at the amplifier in the latest bench test |
| Level adjustments | Pool-audio **R3 (AIR)** and **R4 (WATER)** potentiometers; application sound-file trims; RP5 system output level |
| Wired siren input | Arduino/serial siren-button path supported by UWH; consult the actual installed motherboard wiring/Arduino firmware before copying a pinout |
| Wireless inputs | **SONOFF ZBDongle-P + Zigbee2MQTT + MQTT + referee buttons: end-to-end tested and working on the RP5**; includes a modified **Tuya IH-K663** smart button (`TS0041`, `_TZ3000_fa9mlvja`) with external waterproof pushbutton |

The current 8 GB machine has demonstrated that the application does **not** need 8 GB solely to accommodate its observed RAM use. The proposed 2 GB configuration still needs a full real-world check; the 1.7 GB observation is **not** a guaranteed maximum and leaves less margin for the desktop, caches and other services.

**Monitor status:** the current display is an **LG 24MP400-B**. Two other LG models have been discussed as alternatives: **LG 29U511A-B**, a 29-inch ultrawide option for an operator display, and **LG 32U631A-B**, a 31.5-inch QHD option for larger viewing. These are **possibilities, not tested or fitted monitors** in the present assembly. The **LG 24MP400-B is powered at 19 V DC from a PDM DC-DC board mounted on the motherboard, using a custom-made power cable**. The **centre-positive to centre-positive cable arrangement has been tested successfully**: **+19 V on the inner/centre contact** and **GND (negative) on the outer contact** at the monitor plug, with corresponding polarity at the mating supply connector. This is a verified wiring arrangement for the fitted LG 24MP400-B, **not** a blanket guarantee of connector dimensions or polarity for other LG models. Before reproducing the cable, verify its connectors, insulation, current rating and polarity with a multimeter while the monitor is disconnected. The other proposed monitor models may have different DC power requirements; do not assume the existing cable or supply is suitable for them.

For final production installation, the selected monitors, mounting and power arrangement must be checked against the as-built motherboard. Do not treat proposed monitor models or daughterboard designs as a verified equipment list.

## 2. Raspberry Pi 5 software and displays

The tested system uses **Bookworm + X11**. Under Wayland, moving the pointer over the Game Variables controls with two display windows could drive GPU usage near 98% and cause jerky mouse movement. X11 substantially improved responsiveness.

To select X11:

1. Open Terminal and run `sudo raspi-config`.
2. Select **6 Advanced Options → A7 Wayland → W1 X11**.
3. Finish and reboot.
4. Verify with `echo $XDG_SESSION_TYPE` (expected: `x11`).

UWH supports operator and external display windows; the currently used monitor is the LG 24MP400-B, while the LG 29U511A-B ultrawide and LG 32U631A-B QHD are options under consideration, not confirmed equipment. Select the required layout in the **Screens** tab and use **Auto Detect Screens** and **Test Displays** to check the actual monitor assignments. See [README.md](README.md#raspberry-pi-5-tested-configuration-september-2026) and its Screens instructions for details.

## 3. Audio hardware and connections

The current audio path is:

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

Although the audio is ultimately mixed to mono through R1/R2 on the **Pool Audio Zones Rev 2** board, its input is stereo. A mono plug inserted into a stereo DAC output can short one channel to ground, potentially causing poor sound, distortion or abnormal loading. The **stereo-to-stereo TRS connection** is the required wiring for the currently fitted PiFi DAC and Pool Audio Zones Rev 2 input.

**Production hardware is planned to use the genuine Raspberry Pi DAC+ HAT**. The present installation uses the PiFi DAC+ v2.0. Preserve the **left, right and signal-ground stereo input** to Pool Audio Zones Rev 2. Check the genuine DAC+'s actual available output connectors and use the correct adapter if necessary; **do not assume the production DAC has an identical 3.5 mm socket to the PiFi board**. If using separate left/right RCA outputs, the production interconnect must combine them correctly into a **stereo TRS connector** at the Pool Audio Zones input, not short them together. Verify and document the production DAC driver's audio-device settings before deployment; the PiFi/HiFiBerry-compatible test settings are not automatically guaranteed to be correct for the genuine Raspberry Pi DAC+.

### AIR and WATER output safety

The XH-M562 is a bridged-output amplifier. **Do not connect either speaker output wire to ground, chassis, earth or pool bonding.** Follow the Pool Audio Zones schematic for the WATER output isolation-transformer wiring, including transformer ratings and matching taps. Do not assume an ordinary grounded amplifier output.

Keep the amplifier's AIR and WATER level controls separate. The TOA SC-615 is an efficient horn and can become dangerously loud; begin tests with both controls down and keep people away from its acoustic axis.

## 4. Tested audio level settings — starting point, not fixed calibration

During October 2026 bench testing:

- The 16.0 V amplifier supply stayed at **16.0 V measured directly across XH-M562 pin 3 (+ supply) and pin 2 (power ground)** while the siren sounded.
- The PiFi DAC+ ALSA controls were set to **100%, 0.00 dB** (`Digital` and `Analogue`).
- The RP5 PipeWire output level was set to **0.80 (80%)**; this placed R3 and R4 around the useful middle of their adjustment ranges in workshop tests.
- The selected pip sound (`pip-beep.mp3`) was trimmed to **30%** relative to the selected siren (`siren-car-honk.mp3`) because the pip sounded disproportionately loud.
- Verify that the preferred PipeWire volume and sound-file trims remain appropriate after restart and at the pool.

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

Use the installed motherboard's Arduino Nano Every wiring and firmware when identifying button connections. Check the actual board pinout rather than assuming a generic Arduino connection.

### Zigbee referee buttons — end-to-end tested on the RP5

**Confirmed working (October 2026):** the Zigbee input system has been **tested end to end on the Raspberry Pi 5**. The **SONOFF Zigbee 3.0 USB Dongle Plus (ZBDongle-P)** is connected to the RP5, and **Zigbee2MQTT, MQTT and the referee buttons work together with UWH**. Do not describe this installation as awaiting Zigbee/MQTT validation. Separately, the Windows 11 setup has been tested with **up to three working Zigbee buttons** on one coordinator; that figure should not be assumed to be the verified button count on this RP5.

#### Modified waterproof-button assembly

A **Tuya IH-K663 smart button**, identified as Zigbee model **`TS0041`** with manufacturer string **`_TZ3000_fa9mlvja`**, has been modified for a remotely operated referee pushbutton. See [Zigbee2MQTT's IH-K663 device page](https://www.zigbee2mqtt.io/devices/IH-K663.html#tuya-ih-k663).

The existing electronics were **removed from their original housing**. The modified assembly uses:

- **Two AA batteries in series**, giving approximately **3.0 V nominal** when using 1.5 V cells, to supply the button PCB. Observe polarity; the exact voltage depends on the battery chemistry and state of charge.
- A separate **Jaycar SP0732 30 mm waterproof momentary SPST pushbutton**, with its two switch contacts soldered **in parallel across the original button contacts**, so pressing the remote switch performs the original button operation. [Jaycar SP0732 product page](https://www.jaycar.co.nz/5a-dc-spst-waterproof-momentary-pushbutton-switch-30mm-diameter/p/SP0732).
- A **PVC plumbing pressure-pipe enclosure** containing the modified Zigbee PCB, batteries and wiring.

This is a **working, user-modified Zigbee assembly**, not a factory-rated waterproof button. The switch's waterproof description does **not** establish a waterproof rating for the **complete home-built assembly**, cable penetrations, pipe joints, or battery compartment. Inspect seals and wiring and perform appropriate leak/operational testing before exposing it to poolside spray or immersion; do not assume it can safely be submerged. Keep the battery supply isolated from any other power source.

Button event names depend on the model and its Zigbee2MQTT mapping. Test the configured action in UWH before a match. Each Zigbee device joins only one Zigbee coordinator network at a time; pairing a working button to a different coordinator can remove it from the original network.

For coordinator configuration, pairing, MQTT and UWH button-action mapping, see the [Zigbee section of README.md](README.md#zigbee2mqtt-wireless-siren-setup-and-operation).

### USB/serial device detection

UWH scans for candidate Arduino serial ports and Zigbee adapters and remembers relevant settings, but USB adapter descriptions alone do not prove that a device is the correct coordinator. Serial device naming differs between Windows COM ports and Linux `/dev/tty*` devices. Use the app's detection/troubleshooting controls and verify the actual attached device.

## 6. Motherboard and DC-DC supplies — design versus test status

The **current motherboard assembly is Rev B**, with a **Rev B PDM power-supply board**; a PDM board on the motherboard is already supplying the **LG 24MP400-B monitor at 19 V DC through a custom-made DC cable**. These are *different boards*: a motherboard revision is not the same as a PDM revision. The fact that a PDM powers the monitor does **not** mean the current PDM can supply the RP5 at 5.1 V. The project includes plug-in power/audio circuitry with separate DC-DC outputs for the monitor(s), pool audio and the future integrated RP5 supply. The designs remain under development, so not every proposed supply is present or verified in the current bench assembly.

**Current RP5 storage:** the Raspberry Pi 5 boots from an **NVMe SSD mounted on an NVMe Base**.

**Current RP5 test power:** the Raspberry Pi 5 is presently powered through its **own USB-C power supply**, not yet through the proposed motherboard 5.1 V GPIO feed. The **current Rev B PDM is not suitable for the intended RP5 low-voltage supply option**; **PDM Rev C or later is required** to provide that option. The latest suitable PDM revision has **not yet been obtained and tested**.

**Production power plan:** with a suitable **PDM Rev C or later**, the motherboard design is intended to provide a regulated **5.1 V at least 5 A** to the RP5's 5 V GPIO header pins from a dedicated **LMQ61460-based PDM-Audio DC-DC daughterboard**. The PDM revision is a **necessary design requirement, not proof** that the assembled output has passed voltage, load and startup testing. This power approach bypasses USB-C power negotiation. The README explains the required bootloader configuration, including `PSU_MAX_CURRENT=5000`, and the warning not to claim 5 A unless the **entire** power path has been verified.

> [!WARNING]
> Do not use the proposed GPIO power arrangement until its voltage, current capability, start-up behaviour and all relevant connections have been verified. Do not power the Pi simultaneously through the proposed GPIO feed and another USB-C supply.

Other PDM boards, fused 24 V inputs, monitor supplies, battery-backup switching and mounting arrangements are part of the hardware design and must be documented against the final manufactured assembly before making a production wiring guide. The **currently fitted Rev B motherboard and Rev B PDM** must not be represented as an already validated 5.1 V RP5 GPIO supply. Confirm wiring against the actual board and current schematic before assembly.

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
- [ ] Recheck the **already end-to-end-tested RP5 SONOFF ZBDongle-P → Zigbee2MQTT → MQTT → UWH referee-button** operation before each event, including the modified IH-K663 switch and battery condition.
- [ ] Confirm the **LG 24MP400-B** receives **19 V DC** from the motherboard-mounted PDM through its **tested centre-positive to centre-positive custom cable**; check **centre = +19 V, outer = GND** and verify connector fit, polarity and current rating before reproducing it.
- [ ] Verify supply rails and fuses against the **actual as-built** board rather than inferred power figures.
- [ ] Repeat volume and output-selection checks after a reboot.

## 8. Details still to confirm for the finished hardware specification

The present document intentionally avoids claiming unverified production details. **Confirmed now:** motherboard **Rev B**; PDM **Rev B** fitted (**Rev C or later required** for RP5 power); RP5 boots from an **NVMe Base SSD** and remains **USB-C powered**; monitor **LG 24MP400-B**; and a **SONOFF ZBDongle-P** is plugged into the RP5. Still to verify: the finished motherboard and daughterboard connector/fuse inventory, the custom monitor cable's mechanical connector dimensions and current rating (its **19 V DC centre-positive polarity has been tested**), the final **5.1 V / at least 5 A PDM Rev C+ hardware**, and the production **genuine Raspberry Pi DAC+ HAT** connectors/driver configuration. **The RP5 Zigbee2MQTT, MQTT and referee buttons have already passed end-to-end functional testing.** The two other LG displays listed above remain **candidate models only**.

For operating instructions, see [README.md](README.md). For software internals, see [MAINTAINERS.md](MAINTAINERS.md).
