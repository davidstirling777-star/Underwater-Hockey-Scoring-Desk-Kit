# UWH siren button enclosure

Two STEP models for the pipe-mounted Aqara Wireless Mini Switch circuit-board enclosure, supplied on 9 November 2026. Dimensions are in millimetres. These are the supplied Fusion exports, preserved without geometry changes.

## Parts and suggested materials

| File | Part | Suggested printing material |
|---|---|---|
| [UWH_Siren_Screw_Cup.step](UWH_Siren_Screw_Cup.step) | Removable closed cup | Natural/clear **translucent PETG** |
| [UWH_Siren_Pipe_Adaptor.step](UWH_Siren_Pipe_Adaptor.step) | Fixed pipe adaptor with mating thread | **PETG in any colour** |

**The cup only needs to let the circuit board's LED glow be seen from outside. Glass-like transparency and a clear view of the circuit board are not required.** A frosted or translucent appearance is acceptable. No optical polishing is required.

Use unfilled PETG for both parts as the starting material choice. Using PETG for both parts does not eliminate the need to check the mating thread fit.

## Intended assembly

The adaptor fits over a pipe with a nominal 22.0 mm outside diameter. The intended pipe is Marley 800.15PN15 PVC (DN15) pressure pipe or equivalent. A DN15 pipe is a metric nominal pipe size equivalent to a 1/2-inch imperial nominal pipe size (NPS), featuring a standard outside diameter of 21.3 mm (0.840 inches).
The removable cup houses the bare Aqara board, measured at 38 × 31 × 5 mm, with its 38 mm dimension along the cup. Battery and external-button wires pass through the adaptor's internal stop into the pipe. Two AA batteries are intended to sit in the pipe shaft; the external Jaycar button is wired to the board's existing switch contacts.

The STEP geometry is the authority for manufacturing dimensions. Import the files into Fusion or compatible CAD/slicing software at their original scale. They contain solid geometry rather than a native Fusion feature history.

## Printing and fit checks

- Check the socket against the actual pipe and test the two mating threads using the intended PETG and printer settings.
- Keep the LED's light path unobstructed by PCB packing or internal mounting material.
- Retain the joint's O-ring seal arrangement and check the sealing faces. The pipe fixing and external button also need splash sealing.
- Test splash resistance without electronics installed. These prints have not been qualified for submersion.
- Obtain estimated part weights from the printer's slicer using the actual material, wall and infill settings.

Both supplied STEP files were checked to import as one valid solid each. Physical thread fit, LED visibility and splash sealing still require a test print.
