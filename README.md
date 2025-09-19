The is a general frustration with the current Scoring Desk Kit for UWH in New Zealand.  The hardware is old and approaching end of life, and is prone to faults, and the current software is apparently only able to be edited by one person. It may have not updated it for years, I simply don’t know.  The mechanism for adding or replacing remote controls is a mystery to me. 

Open software is desirable, as is a redesigned user interface that is accessible, logical and easily understood by novices and is not reliant on secret buttons. 

A modern version of hardware taking advantage of newer technology is desired.  Apart from setup, it would be nice if it was totally mouse driven, like the current system.  It would be nice to not have to have a keyboard lying around during games. 

The people helping with UWH are always churning over so a User Manual, possibly online or embedded in the software is essential. 

The idea is to use a Raspberry Pi5 computer, tiny amplifier, Bluetooth or wi-fi remote control to minimise connections.  Hardware button backup for wireless remote control.  Using a Compute Module CM5 on a custom board with built in amplifier is probably beyond where we think we want to go.  The reason for gravitating to a Raspberry Pi is the HATs that are available, such as a dual channel amplifier which drastically reduces wires and connections (hopefully leading to a more robust system). It may be that a RPi5 is not grunty enough, but we will see.

The goal is to make a solution for UWN scoring that anyone can use, based on easy to obtain hardware, hence th desire to use a Raspberry Pi 5.  Aiming to use a DigiAMP+ HAT, NVMe Base for Raspberry Pi 5 for robustness of data storage, Zigbee communications between Zigbee USB dongle and Zigbee buttons for Chief Ref ability to signal, TOA SC610 8 Ohm 10W IP65 Horn Speaker for above water siren and a Lubell Labs Underwater loudspeaker (why? Because that is what we already use) LL916 is the modern version of the ones NZUWH already uses.

## GitHub Copilot Development Support

This repository includes comprehensive GitHub Copilot instructions to help developers efficiently work with the UWH scoring application:

- **[GITHUB_COPILOT_INSTRUCTIONS.md](GITHUB_COPILOT_INSTRUCTIONS.md)** - Complete development guide with context, patterns, and best practices
- **[COPILOT_QUICK_REFERENCE.md](COPILOT_QUICK_REFERENCE.md)** - Quick reference for common prompts and tasks  
- **[COPILOT_EXAMPLES.md](COPILOT_EXAMPLES.md)** - Real-world examples of adding features like penalty tracking, statistics, audio alerts, remote control, and data persistence

These guides enable both new and experienced contributors to leverage GitHub Copilot effectively for:
- Feature development and UI modifications
- Code debugging and optimization  
- Hardware integration (Raspberry Pi, audio, networking)
- Testing and validation
- Following project-specific coding patterns

### Quick Start for Developers
1. Read the [Quick Reference](COPILOT_QUICK_REFERENCE.md) for essential prompts
2. Use application-specific terms (GameManagementApp, uwh.py, scoreboard tab) in your Copilot prompts  
3. Reference the [Examples](COPILOT_EXAMPLES.md) for complex feature implementations
4. Follow the patterns in [Instructions](GITHUB_COPILOT_INSTRUCTIONS.md) for consistent code style

