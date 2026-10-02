"""Small, user-visible UWH application version identifier.

Source installations show the committed source revision below. The release
workflow replaces APP_VERSION independently in the Windows and Raspberry Pi 5
build workspaces with the published v1.2.<GitHub Actions run number>, so both
ready-to-run ZIPs display the same version as their GitHub Release.
"""

APP_VERSION = "1.2.source.20261002.2"
