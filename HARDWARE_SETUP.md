# Hardware setup — UWH Scoring Desk Kit

This guide summarises the current hardware choices and useful commissioning observations. For the definitive board-to-board wiring tables, supply settings and assembly sequence, use [Hardware assembly in the main README](README.md#hardware-assembly). Editable KiCad projects and library instructions are in [hardware/README.md](hardware/README.md).

## 1. Current hardware and design status (November 2026)

| Item | Setup / status |
| --- | --- |
| Scoring computer | Raspberry Pi 5; the tested machine has 8 GB RAM |
| Storage / boot | NVMe SSD via Pimoroni NVMe Base |
| Operating system | Raspberry Pi OS Bookworm Desktop (64-bit), X11; successfully used at a tournament |
| Audio DAC currently fitted | **Genuine Raspberry Pi DAC+ HAT**; the PiFi has been removed |
| Previous audio DAC | **PiFi DAC+ v2.0** seemed to work just fine in the earlier setup |
| Current board design | Separate **UWH Control Board above UWH Power Board**, using **30 mm standoffs** and **1 oz copper**; replaces the original motherboard design |
| Pi power option | Dedicated **DC-DC PDM-Audio Rev D or later**, set to **5.1 V**, with the GPIO power harness described in the main README; verify the completed power path under load |
| Main supply | **Mean Well XDR-480E-24**, a tested 24 V SELV PSU with ample headroom for the tested unit |
| Backup | Two 12 V SLA batteries in series; LTC4418 OR-ing board gives SELV priority |
| Backed loads | Screen 1, audio, Pi and control supply; screens 2–4 are SELV-only |
| Pool-audio board | Current **Pool_Audio_Zone** project with FUSUPI XH-M562 amplifier; separate two-wire power input at audio J19 |
| Audio supply | **16 V nominal**, never above **18 V**; check the actual amplifier rating |
| Audio interconnect | Current board wiring uses **DAC+ P6 → audio J6**, a straight four-conductor cable; see section 3 |
| AIR speaker | TOA SC-615, 8 Ω low-impedance horn |
| Wired siren | **Raspberry Pi BCM GPIO17 (physical pin 11)** and/or **Arduino USB serial** |
| Arduino options | Nano Every (5 V logic) or Nano ESP32 (3.3 V-only logic), with the matching JP1 selection and firmware |
| Zigbee coordinator | SONOFF Zigbee 3.0 USB Dongle Plus (ZBDongle-P), with Zigbee2MQTT and MQTT |
| Preferred wireless button | **Aqara WXKG11LM**, tested with single, double, hold and release actions |

The board files document the current design; they do not by themselves establish that every assembled board has passed production, load or thermal testing. The old Rev B motherboard/PDM and separate USB-C test supply are no longer the specification for the split-board build.

Approximately **1.7 GB RAM** was observed in earlier testing on the 8 GB Pi. A 2 GB Pi has not been separately verified with the full workload; that observation is not a guaranteed maximum.

## 2. Raspberry Pi 5 software and displays

The tested system uses **Bookworm + X11**. Under Wayland, moving the pointer over the Game Variables controls with two display windows could drive GPU usage near 98% and cause jerky mouse movement. X11 substantially improved responsiveness.

To select X11:

1. Open Terminal and run `sudo raspi-config`.
2. Select **6 Advanced Options → A7 Wayland → W1 X11**.
3. Finish and reboot.
4. Verify with `echo $XDG_SESSION_TYPE` (expected: `x11`).

Use the **Screens** tab's **Auto Detect Screens** and **Test Displays** controls to check monitor assignments. See the [tested Raspberry Pi configuration](README.md#raspberry-pi-5-tested-configuration-october-2026) for installation details. The LG 24MP400-B was used in earlier bench tests; monitor choice and DC requirements must be checked for each deployment.

## 3. Audio hardware and connections

The fitted audio path is UWH on the Raspberry Pi 5, through PipeWire/WirePlumber and the **Raspberry Pi DAC+**, to the Pool Audio board's mixer and separate AIR/WATER level controls, then the XH-M562 amplifier and the respective speaker circuits.

### DAC+ connection

Use the [DAC+ audio cable and volume-limit instructions](README.md#dac-audio-cable-and-volume-limit) for the current **P6-to-J6** pin mapping. This replaces the earlier PiFi stereo-jack cable arrangement in the split-board design.

For the tested **DAC+ PCB version 003R5**, insert an **unwired 3.5 mm plug** into the DAC+ socket to operate headphone detect when using P6. Leave **P6 pin 5 externally unconnected**. It was measured as directly connected to 3.3 V without a plug, so **do not bridge pin 5 to pin 4/GND**.

For an external computer using the audio board's J1 socket, use a **stereo TRS male-to-male cable**, with two insulating rings on each plug. Do not use a mono TS plug, which can short one DAC output channel to ground. Use only one audio source at a time.

Audio power arrives separately through **power J10 → audio J19**, with positive on pin 1 and GND on pin 2. Do not fit audio J5 or control J10 in this build; use the main README's assembly instructions.

### AIR and WATER outputs

The XH-M562 has bridged speaker outputs. **Neither speaker output wire may be connected to GND, chassis, earth or pool bonding.** Follow the current audio schematic's two-transformer WATER output wiring.

Keep the AIR and WATER level controls separate. **RV5 limits the maximum WATER level**; looking at its screw from above, turn anticlockwise to reduce the maximum. Begin with low levels and set them at the venue.

## 4. Earlier audio tests and current commissioning

These October 2026 observations were made with the earlier PiFi-based setup. The PiFi DAC+ v2.0 seemed to work just fine, but it has now been removed and replaced by the Raspberry Pi DAC+. Recheck levels and audio-device selection with the fitted DAC+:

- The 16.0 V amplifier supply stayed at **16.0 V measured directly across XH-M562 pin 3 (+ supply) and pin 2 (power ground)** while the siren sounded.
- The PiFi DAC+ ALSA controls were set to **100%, 0.00 dB** (`Digital` and `Analogue`).
- The RP5 PipeWire output level was **0.80 (80%)** in workshop tests, but at the **October 2026 tournament the siren was too quiet**. The resulting venue starting point was **1.00 (100%)**, with cautious adjustment of the AIR/WATER amplifier controls.
- The selected pip sound (`pip-beep.mp3`) was trimmed to **30%** relative to the selected siren (`siren-car-honk.mp3`) because the pip sounded disproportionately loud.
- The tournament test confirmed that separate **pip trims are useful** and the **30-second warning pip requires independent file selection and trim** to remain audible over pool noise.
- Verify that the selected PipeWire volume, cues and amplifier levels remain appropriate after restarting and at the venue.

**These are commissioning starting points, not fixed calibration values.** Check AIR and WATER levels at the venue. Do not raise or lower the 16.0 V amplifier supply just to compensate for a software volume mismatch.

### Check and set audio output

```bash
cat /proc/asound/cards
wpctl status
wpctl get-volume @DEFAULT_AUDIO_SINK@
```

On the tested RP5, HDMI appeared as cards 0 and 1, and the DAC as **ALSA card 2**. Card and PipeWire sink numbers can change, so identify them each time rather than hard-coding them in scripts.

To set the presently selected default audio sink to the **100% starting point chosen after tournament testing**:

```bash
wpctl set-volume @DEFAULT_AUDIO_SINK@ 1.00
wpctl get-volume @DEFAULT_AUDIO_SINK@
```

Check that `wpctl status` shows the DAC as the **default sink**. UWH selects the audio device when it starts; if you change the default device, **close and restart UWH**. The **Sounds** tab reports the audio output in use.

The per-file **Trim %** fields balance cues relative to each other. They are not replacements for the overall OS/DAC/amplifier volume control. Use lower trims where needed; excessive horn levels can damage hearing.

For DAC driver configuration, audio troubleshooting and software installation, see the [Sounds section of README.md](README.md#sounds-tab).

## 5. Siren triggers

### Wired Raspberry Pi and Arduino inputs

The application accepts **both GPIO17 and Arduino USB serial**. Configure **BCM GPIO17 (physical pin 11)** as an input with internal pull-up/pull-down disabled: **R13 supplies the external 3.3 V pull-up**. LOW means pressed and HIGH means released, with 50 ms debounce on both edges.

The siren sounds while a wired input remains active and stops after all active wired inputs have released. Press/release and siren on/off events are reported in **Siren Control → Activity Log**, identifying the pathway. Test GPIO17 and Arduino USB independently and together.

Control **J19.1 carries GPIO17** and **J19.2 carries the Pi's 3.3 V pull-up supply, not GND**. Follow the [wiring table](README.md#supply-location-and-wiring-sizes) for the common ground and Pi power harness.

For the Arduino, set JP1 **1–2 for Nano ESP32 (3.3 V)** or **2–3 for Nano Every (5 V)** before applying power. Fit both control-board optocouplers even if only one controller is used, because their input LEDs are in series. The supplied firmware supports both Nano variants; follow the Arduino installation instructions in the main README. The Nano ESP32 battery-monitor divider must be designed for its input range; do not copy the Nano Every divider unchanged.

The remote normally open wired button connects across control J20. The in-use lead is **30 m of Cat 6a cable**, with plugs removed and **four conductors paralleled for each leg**, stored on a spearfishing float-line winder.

### Wireless referee buttons

**Aqara WXKG11LM is the preferred deployment device**, tested with `single`, `double`, `hold` and `release`. Other previously tested button types, including the Tuya IH-K663, are **also tested but with limited functionality (no hold or release signals)**.

Map single/double to timed cycles and hold/release to start/stop continuous siren in UWH. The received actions must be checked for the actual button and its Zigbee2MQTT mapping.

The modified Aqara uses **two AA batteries in series** and a **Jaycar SP0732 waterproof momentary button** wired across the PCB switch. The [wireless siren enclosure guide](hardware/Enclosures/UWH_Siren/README.md) contains the printable cup/adaptor, wiring photographs, existing-hole strain relief, foam packing and removable pipe-joint instructions. Working units were constructed using grey PLA filament.

The SONOFF coordinator, Zigbee2MQTT, MQTT and referee buttons have been tested end to end on the Pi. Windows has also been tested with up to three working buttons. Most deployments are expected to have their **own SONOFF receiver**; sharing a broker between UWH computers is an **advanced, untested arrangement**.

For pairing, device detection and action mapping, see [Zigbee setup in the main README](README.md#zigbee2mqtt-wireless-siren-setup-and-operation).

## 6. Power and board assembly

Follow [Hardware assembly](README.md#hardware-assembly) for connector assignments and conductor sizes in mm² with AWG equivalents. In particular:

- Fit only the PDMs needed for the loads powered by this assembly. The minimum is **one audio PDM**; an external computer or independently powered monitors do not need their corresponding PDMs.
- Use **Rev D or later** for the Pi PDM. Verify 5.1 V before connection, loaded voltage at the Pi, startup behaviour and connector temperature. Do not power the Pi simultaneously from GPIO and another USB-C supply.
- Locate the SELV PSU near the mains outlet, with several metres of **4 mm² finely multistranded cable (approximately AWG 11)** to the hardware. This size has been fitted in the input terminals using crimped bootlace ferrules.
- Use the main README's loaded cable-drop check: a recommended maximum **1.0 V drop**, including both conductors, from PSU to power-board J1. With 24.0 V at the PSU, the target is at least 23.0 V at J1.
- Keep the **5 A branch-fuse recommendations**. A **6 A fuse may need consideration in hot climates**, only after checking the protected circuit. The **Keystone MAXI holder option** applies to the main SELV input, where MINI fuse/holder derating may matter; do not fit both alternative main fuse positions.
- The Pi-stack estimated peak load is **19.8 W**. The backed-load budget uses **55 W for one screen** and **30 W for audio** in addition; verify actual simultaneous current and thermal behaviour.
- Screen PDM outputs have 1000 µF capacitors. The audio board has its own 1000 µF capacitor, so its PDM does not need a duplicate solely for that purpose.
- **IPX5 containment is the minimum expectation** for the boards.

The GPIO power configuration, including bootloader current settings, is documented under [Raspberry Pi 5 power supply configurations](README.md#raspberry-pi-5-power-supply-configurations). Configure it only for the capability actually verified across the complete supply and harness.

## 7. Commissioning

Use the main README's [first power-up checks](README.md#first-power-up-checks), then:

- Verify the Raspberry Pi DAC+ is recognised and selected as the default audio sink; restart UWH after changing it.
- Check the P6 cable orientation and headphone-detect plug before testing audio.
- Start AIR/WATER levels low, check the RV5 limit, and test all selected sound cues at the venue.
- Check each wired siren pathway separately and together in the activity log.
- Test Aqara single/double/hold/release mappings and battery contact retention.
- Test SELV priority, battery takeover and return, plus all fitted loads together.
- Repeat the checks after rebooting.

The earlier LG 24MP400-B monitor was successfully powered at **19 V, centre-positive**, through a custom cable. Do not assume its connector, polarity or voltage applies to another screen. Confirm the requirements of every monitor actually fitted.

For operating instructions, see [README.md](README.md). For software internals, see [MAINTAINERS.md](MAINTAINERS.md).
