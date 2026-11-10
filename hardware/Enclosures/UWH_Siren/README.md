# UWH wireless siren enclosure

Working units were constructed using **grey PLA filament**.

| File | Part |
|---|---|
| [UWH_Siren_Screw_Cup.step](UWH_Siren_Screw_Cup.step) | Removable closed cup, with 5 mm outside and 2 mm inside bottom radii |
| [UWH_Siren_Pipe_Adaptor.step](UWH_Siren_Pipe_Adaptor.step) | Pipe adaptor with mating thread and internal pipe stop |

## Intended assembly

The pipe receiver has a **21.4 mm internal diameter** for the specified **Marley DN15 pipe with 21.34 mm outside diameter**. This provides 0.06 mm nominal diametral clearance; check the actual printed fit before assembly. The pipe insertion section is 25 mm long, the transition to the threaded collar is **10 mm long**, and the adaptor is 44 mm long overall. The mating thread and sealing groove are retained from the supplied design.

The removable cup houses the bare Aqara board, measured at 38 × 31 × 5 mm, with its 38 mm dimension along the cup. Battery and external-button wires pass through the adaptor's internal stop into the pipe. Two AA batteries sit in the pipe shaft; the external waterproof normally-open button is wired to the Aqara board's existing switch contacts.

Affix the pipe adaptor to the pipe with a material such as **RTV silicone**, to provide some water resistance while allowing relatively easy removal for AA battery replacement (which should last years). Allow it to cure before use and check the seal again after battery replacement.

**Do not use screws to secure the adaptor to the pipe: they risk penetrating an AA battery or shorting the wires.**

The STEP geometry is the authority for manufacturing dimensions. Import the files at their original scale. They contain solid geometry.
## Aqara board wiring and strain relief

The photographs below show an example of wiring added to the Aqara Zigbee button circuit board.

| Wire colour | Connection |
|---|---|
| Two white wires | Across the existing switch contacts, leading to the external waterproof button |
| Red | Positive (+) end of the two-AA battery supply in the pipe |
| Black | Negative (−) end of the two-AA battery supply in the pipe |

The two AA cells are connected in series. Route the insulated wires through the **existing holes in the Aqara circuit board** for strain relief, as shown, leaving a little slack between each hole and its solder joint so movement does not pull directly on the joint.

<img src="../../../docs/images/aqara-button-wiring-1.jpeg" alt="Aqara button circuit board with added battery and waterproof-button wires routed through existing holes for strain relief, first view" width="360">

<img src="../../../docs/images/aqara-button-wiring-2.jpeg" alt="Aqara button circuit board with added battery and waterproof-button wires routed through existing holes for strain relief, reverse view" width="360">

Pack **foam or bubble wrap at both ends inside the pipe** to stop the AA batteries sliding up and down or rattling. The wireless siren is not a child's rattle! The foam also keeps the cells secure without pulling on the wires. Leave the packing removable for battery replacement.

### Expanded assembly view

<img src="../../../docs/images/aqara-battery-wiring-expanded.jpeg" alt="Expanded wireless siren assembly showing the two AA batteries, battery wiring, waterproof button and foam pieces for both ends of the pipe" width="360">

Expanded view showing the battery wiring and suitably sized foam pieces for both ends of the pipe. When assembled, the foam keeps the two AA cells pressed together so they do not separate during use, and keeps the battery wires in contact with the terminals.

## Early working unit

<img src="../../../docs/images/early-wireless-siren-unit.jpeg" alt="Early working wireless siren unit with pipe handle, push button and grey printed enclosure" width="360">

This photograph shows an early working version, before the shortened transition and revised pipe socket described above.

## Printing and fit checks

- Test the socket on the actual pipe and check the mating threads with the intended printer settings. The small nominal clearance may require print compensation or finishing.
- Retain the joint's O-ring seal arrangement and check its sealing faces, the pipe joint and external button.
- Test water resistance without electronics installed. These prints have not been qualified for submersion but should rate at least IPX4.

Both STEP files import as one valid solid each.
