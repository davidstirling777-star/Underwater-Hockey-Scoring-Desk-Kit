# UWH scoring hardware

Start with [Hardware assembly in the main README](../README.md#hardware-assembly) for the 30 mm board stack, wiring tables, power settings and commissioning checks.

These sources were imported from `UWH-Scoring-Hardware.zip`, supplied on 8 November 2026. Five current projects are included:

| Project folder under `Boards/` | Purpose |
|---|---|
| `UWH Power Board` | Lower board: fused supply inputs, PDMs and OR-ing module |
| `UWH Control Board` | Upper board: controller connections and audio/Pi mounting |
| `Pool_Audio_Zone` | Audio mixer, amplifier connections and speaker filters |
| `OR-ing board` | LTC4418 SELV-priority / battery-backup selector |
| `DC-DC PDM-Audio` | Adjustable DC-DC supply module; verify revision/output for each load |

Open the `.kicad_pro` file in the chosen folder from KiCad's project manager. Use KiCad 10 or a newer compatible version, with the standard symbol, footprint and 3D-model libraries installed. Keep the directory structure intact. Project-local library tables point to `../../Libraries`; custom 3D models use that same project-relative location, so an external `UWH_LIBRARIES` variable is not required for the included boards.

`Libraries/UWH.kicad_sym`, `Libraries/UWH.pretty`, `Libraries/Stack_Template.pretty` and `Libraries/UWH.3dshapes` contain the shared assets. The OR-ing project also registers its supplied local LTC4418 symbol library. Custom library definitions are supplied as received; embedded board/schematic instances may contain deliberate local edits. Review differences before updating existing instances from a library.

Import preparation repaired library-table paths and custom model paths to supplied files. It did not alter schematic connectivity, PCB tracks, pads or board outlines. The original motherboard project, automatic backups, local UI settings, old manufacturing exports and draft design documents were deliberately excluded. Generate fresh manufacturing files from the chosen project after review and ERC/DRC; this import is not manufacturing approval.

Some unused legacy library footprints refer to optional models not supplied in the ZIP (notably the WE-XHMI-6030P). These do not affect the five boards' custom model resolution. Carrier/stack STEP models are mechanical references and may not reflect every subsequent routing or silkscreen change.

Before ordering parts, check actual component MPNs, separate fuse/holder BOM entries, the JP1 header and shunt, and mating cable housings/contacts. Run KiCad ERC and DRC with zones refilled. Test the completed assembly's load, temperature, startup and supply changeover behaviour.

Import checks: all five schematic/PCB connectivity comparisons passed using an independent parser, and all custom footprints/models used by the boards resolve to included files. Native KiCad ERC/DRC was not run. The control-board JP1 schematic contains MPN `61300211121`, while its PCB MPN is blank; verify the intended three-pin selector header and separate shunt before ordering.
