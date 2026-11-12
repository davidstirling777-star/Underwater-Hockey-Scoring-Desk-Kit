# UWH scoring hardware

Start with [Hardware assembly in the main README](../README.md#hardware-assembly) for the Cower and Control board stack, wiring tables, power settings and commissioning checks.

Five current projects are included:

| Project folder under `Boards/` | Purpose |  Copper Weight |
|---|---|
| `UWH Power Board` | Lower board: fused supply inputs, PDMs and OR-ing module |  **2 oz copper on both F.Cu and B.Cu**  |
| `UWH Control Board` | Upper board: controller connections, Arduino footprint (sometimes optional) and audio/Pi mounting |  1 oz copper on both F.Cu and B.Cu  |
| `Pool_Audio_Zone` | Audio mixer, amplifier connections and speaker filters |  1 oz copper on both F.Cu and B.Cu  |
| `OR-ing board` | LTC4418 SELV-priority / battery-backup selector |  **2 oz** copper on both F.Cu and B.Cu  |
| `DC-DC PDM-Audio` | Adjustable DC-DC supply module; verify revision/output for each load |  **2 oz** copper on both F.Cu and B.Cu  |

Open the `.kicad_pro` file in the chosen folder from KiCad's project manager. Use KiCad 10 or a newer compatible version, with the standard symbol, footprint and 3D-model libraries installed. Keep the directory structure intact. Project-local library tables point to `../../Libraries`.

`Libraries/UWH.kicad_sym`, `Libraries/UWH.pretty`, `Libraries/Stack_Template.pretty` and `Libraries/UWH.3dshapes` contain the shared assets. The OR-ing project also registers its supplied local LTC4418 symbol library. Custom library definitions are supplied; embedded board/schematic instances may contain deliberate local edits. Review differences before updating existing instances from a library.

Generate fresh manufacturing files from the chosen project after review and ERC/DRC; this import is not manufacturing approval nor a guarentee of perfection.


Some unused legacy library footprints refer to optional models not supplied (notably the WE-XHMI-6030P). These do not affect the five boards' custom model resolution. Carrier/stack STEP models are mechanical references and may not reflect every subsequent routing or silkscreen change.

Before ordering parts, check actual component MPNs, separate fuse/holder BOM entries, the JP1 header and shunt, and mating cable housings/contacts. Run KiCad ERC and DRC with zones refilled. Test the completed assembly's load, temperature, startup and supply changeover behaviour.


## Printed siren button enclosure

The [UWH siren enclosure](Enclosures/UWH_Siren/README.md) contains the pipe adaptor and removable cup STEP files, assembly guidance and an early working-unit photo. Working units were constructed using grey PLA filament.
