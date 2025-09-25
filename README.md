The is a general frustration with the current Scoring Desk Kit for UWH in New Zealand.  The hardware is old and approaching end of life, and is prone to faults, and the current software is apparently only able to be edited by one person. It may have not updated it for years, I simply don’t know.  The mechanism for adding or replacing remote controls is a mystery to me. 

Open software is desirable, as is a redesigned user interface that is accessible, logical and easily understood by novices and is not reliant on secret buttons. 

A modern version of hardware taking advantage of newer technology is desired.  Apart from setup, it would be nice if it was totally mouse driven, like the current system.  It would be nice to not have to have a keyboard lying around during games. 

The people helping with UWH are always churning over so a User Manual, possibly online or embedded in the software is essential. 

The idea is to use a Raspberry Pi5 computer, tiny amplifier, Bluetooth or wi-fi remote control to minimise connections.  Hardware button backup for wireless remote control.  Using a Compute Module CM5 on a custom board with built in amplifier is probably beyond where we think we want to go.  The reason for gravitating to a Raspberry Pi is the HATs that are available, such as a dual channel amplifier, will drastically reduces wires and connections (hopefully leading to a more robust system). It may be that a RPi5 is not grunty enough, but we will see.

The goal is to make a solution for UWH scoring that anyone can use, based on easy to obtain hardware, hence th desire to use a Raspberry Pi 5.  Aiming to use a DigiAMP+ HAT, NVMe Base for Raspberry Pi 5 for robustness of data storage, Zigbee communications between Zigbee USB dongle and Zigbee buttons for Chief Ref ability to signal, TOA SC610 8 Ohm 10W IP65 Horn Speaker for above water siren and a Lubell Labs Underwater loudspeaker (why? Because that is what we already use) LL916 is the modern version of the ones NZUWH already uses.

summary of what happens when goals are added during the three "break" periods:
Between Game Break
Scores After Goal	is added: What Happens
Even	Progress to Overtime Game Break (if Overtime allowed)<br>OR Sudden Death Game Break (if Sudden Death allowed and Overtime not allowed)
Uneven	Remain in Between Game Break. No progression; continue as normal.

Overtime Game Break
Scores After Goal	is added: What Happens
Even	Remain in Overtime Game Break. Proceed to overtime periods according to schedule.
Uneven	Skip Overtime! Progress directly to Between Game Break.

Sudden Death Game Break
Scores After Goal	is added: What Happens
Even	Remain in Sudden Death Game Break. Proceed to Sudden Death period as scheduled.
Uneven	Progress directly to Between Game Break. (Skips Sudden Death period.)
