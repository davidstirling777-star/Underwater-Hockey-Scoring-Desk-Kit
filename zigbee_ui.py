import tkinter as tk
from tkinter import ttk
import webbrowser

from zigbee_siren import is_mqtt_available


def create_zigbee_siren_tab(app):
    """Create the Zigbee Siren configuration tab."""
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Zigbee Siren")
