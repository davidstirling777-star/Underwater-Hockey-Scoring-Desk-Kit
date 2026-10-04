"""Shared visual language for the v1.3.1 UWH operator interface.

The Scoreboard layout deliberately remains outside this visual redesign.
The helpers here are used by Game Variables, Tournament List, Screens,
Sounds, Zigbee Siren and About so those tabs share one restrained blue-accent
style without forcing a third-party GUI toolkit across the whole application.
"""

import base64
import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb


COLORS = {
    "app_bg": "#f3f7fb",
    "surface": "#ffffff",
    "surface_alt": "#f8fbff",
    "primary": "#0d6efd",
    "primary_hover": "#0b5ed7",
    "primary_soft": "#eaf4ff",
    "navy": "#0b2b66",
    "text": "#16325c",
    "muted": "#64748b",
    "border": "#cfe0f4",
    "border_strong": "#b7d2ef",
    "good": "#16a34a",
    "good_soft": "#eaf8ef",
    "warn": "#c57a00",
    "warn_soft": "#fff6df",
    "danger": "#dc2626",
    "danger_soft": "#fff0f0",
    "disabled": "#eef2f6",
}

FONT_FAMILY = "Segoe UI"
BODY_FONT = (FONT_FAMILY, 10)
SMALL_FONT = (FONT_FAMILY, 9)
SECTION_FONT = (FONT_FAMILY, 13, "bold")
TITLE_FONT = (FONT_FAMILY, 18, "bold")

# 64x64 embedded UWH stick badge used for the window/taskbar icon.
_APP_ICON_B64 = """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"""


def configure_styles(root):
    """Install the real ttkbootstrap UWH visual system.

    The original v1.3.x styling used native ttk with custom colours.  v1.3.5
    deliberately uses ttkbootstrap's Flatly theme so buttons, entries,
    checkbuttons, comboboxes, tables and scrollbars share the polished visual
    language shown in the approved mockups.
    """
    root.configure(background=COLORS["app_bg"])

    # The Tk root already exists at this point. ttkbootstrap 1.x Style takes
    # the theme name only; passing master= raises TypeError at application
    # startup.
    style = tb.Style(theme="flatly")
    root._uwh_bootstrap_style = style

    style.configure(
        "UWH.TNotebook",
        background=COLORS["app_bg"],
        borderwidth=0,
        tabmargins=(12, 4, 12, 0),
    )
    style.configure(
        "UWH.TNotebook.Tab",
        font=(FONT_FAMILY, 10, "bold"),
        padding=(18, 11),
        foreground=COLORS["navy"],
        background=COLORS["surface"],
        borderwidth=0,
    )
    style.map(
        "UWH.TNotebook.Tab",
        foreground=[
            ("selected", COLORS["primary"]),
            ("active", COLORS["primary"]),
        ],
        background=[
            ("selected", COLORS["primary_soft"]),
            ("active", "#f5f9ff"),
        ],
    )

    style.configure("UWH.Tab.TFrame", background=COLORS["app_bg"])
    style.configure("UWH.Surface.TFrame", background=COLORS["surface"])
    style.configure(
        "UWH.Card.TFrame",
        background=COLORS["surface"],
        borderwidth=1,
        relief="solid",
    )
    style.configure("UWH.Info.TFrame", background=COLORS["primary_soft"])

    style.configure(
        "UWH.Title.TLabel",
        background=COLORS["app_bg"],
        foreground=COLORS["navy"],
        font=TITLE_FONT,
    )
    style.configure(
        "UWH.Section.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["navy"],
        font=SECTION_FONT,
    )
    style.configure(
        "UWH.Body.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=BODY_FONT,
    )
    style.configure(
        "UWH.Muted.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["muted"],
        font=SMALL_FONT,
    )
    style.configure(
        "UWH.Info.TLabel",
        background=COLORS["primary_soft"],
        foreground=COLORS["primary"],
        font=BODY_FONT,
    )
    style.configure(
        "UWH.Good.TLabel",
        background=COLORS["good_soft"],
        foreground=COLORS["good"],
        font=BODY_FONT,
    )
    style.configure(
        "UWH.Danger.TLabel",
        background=COLORS["danger_soft"],
        foreground=COLORS["danger"],
        font=BODY_FONT,
    )

    style.configure(
        "UWH.TCheckbutton",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=BODY_FONT,
        padding=(2, 4),
    )
    style.configure(
        "UWH.TRadiobutton",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=BODY_FONT,
        padding=(2, 4),
    )
    style.configure(
        "UWH.TEntry",
        padding=(8, 7),
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
    )
    style.configure(
        "UWH.TCombobox",
        padding=(8, 6),
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
    )
    style.configure(
        "UWH.Treeview",
        rowheight=30,
        font=BODY_FONT,
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
        borderwidth=0,
    )
    style.configure(
        "UWH.Treeview.Heading",
        font=(FONT_FAMILY, 9, "bold"),
        foreground=COLORS["navy"],
        background=COLORS["primary_soft"],
        relief="flat",
        padding=(8, 7),
    )
    style.map(
        "UWH.Treeview",
        background=[("selected", "#dcecff")],
        foreground=[("selected", COLORS["navy"])],
    )

    return style


def apply_app_icon(root):
    """Replace Tk's feather icon with the approved UWH stick badge."""
    try:
        raw = base64.b64decode(_APP_ICON_B64)
        icon = tk.PhotoImage(data=base64.b64encode(raw).decode("ascii"))
        root.iconphoto(True, icon)
        root._uwh_app_icon = icon
        return icon
    except Exception:
        return None


def create_app_header(root):
    """Create the persistent UWH logo/title strip above the tab navigation."""
    header = tk.Frame(
        root,
        bg=COLORS["surface"],
        height=64,
        highlightbackground=COLORS["border"],
        highlightthickness=0,
        bd=0,
    )
    header.pack(fill="x", side="top")
    header.pack_propagate(False)

    content = tk.Frame(header, bg=COLORS["surface"])
    content.pack(fill="both", expand=True, padx=18, pady=8)

    icon = getattr(root, "_uwh_app_icon", None)
    if icon is not None:
        try:
            small_icon = icon.subsample(2, 2)
            root._uwh_header_icon = small_icon
            tk.Label(
                content,
                image=small_icon,
                bg=COLORS["surface"],
                bd=0,
            ).pack(side="left", padx=(0, 10))
        except tk.TclError:
            pass

    tk.Label(
        content,
        text="UWH Scoring Desk",
        bg=COLORS["surface"],
        fg=COLORS["navy"],
        font=(FONT_FAMILY, 20, "bold"),
        anchor="w",
    ).pack(side="left")

    separator = tk.Frame(root, bg=COLORS["border"], height=1)
    separator.pack(fill="x", side="top")
    return header


def tab_label(name):
    """Return the compact icon/text labels used by the new-look navigation."""
    icons = {
        "Scoreboard": "▣",
        "Game Variables": "⚙",
        "Tournament List": "▤",
        "Screens": "▱",
        "Sounds": "♪",
        "Zigbee Siren": "⌁",
        "About": "ⓘ",
    }
    icon = icons.get(name, "•")
    return f"{icon}  {name}"


def card(parent, *, padding=14):
    """Return a clean white card used throughout the six redesigned tabs."""
    frame = tb.Frame(
        parent,
        padding=padding,
        style="UWH.Card.TFrame",
    )
    return frame


def page_header(parent, title, subtitle=None, symbol="●"):
    """Create a compact card header matching the approved mockup hierarchy."""
    frame = card(parent, padding=12)
    frame.grid_columnconfigure(1, weight=1)

    tk.Label(
        frame,
        text=symbol,
        bg=COLORS["surface"],
        fg=COLORS["primary"],
        font=(FONT_FAMILY, 20, "bold"),
        width=2,
        anchor="w",
    ).grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 8))

    tk.Label(
        frame,
        text=title,
        bg=COLORS["surface"],
        fg=COLORS["navy"],
        font=(FONT_FAMILY, 15, "bold"),
        anchor="w",
    ).grid(row=0, column=1, sticky="ew")

    if subtitle:
        tk.Label(
            frame,
            text=subtitle,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=SMALL_FONT,
            anchor="w",
            justify="left",
        ).grid(row=1, column=1, sticky="ew", pady=(2, 0))

    return frame


def section_title(parent, text, symbol=None):
    text_value = f"{symbol}  {text}" if symbol else text
    return tk.Label(
        parent,
        text=text_value,
        bg=COLORS["surface"],
        fg=COLORS["navy"],
        font=SECTION_FONT,
        anchor="w",
    )


def body_label(parent, text="", **kwargs):
    options = {
        "text": text,
        "bg": COLORS["surface"],
        "fg": COLORS["text"],
        "font": BODY_FONT,
        "anchor": "w",
    }
    options.update(kwargs)
    return tk.Label(parent, **options)


def muted_label(parent, text="", **kwargs):
    options = {
        "text": text,
        "bg": COLORS["surface"],
        "fg": COLORS["muted"],
        "font": SMALL_FONT,
        "anchor": "w",
    }
    options.update(kwargs)
    return tk.Label(parent, **options)


def info_banner(parent, text):
    frame = tk.Frame(
        parent,
        bg=COLORS["primary_soft"],
        highlightbackground=COLORS["border"],
        highlightthickness=1,
        padx=12,
        pady=9,
    )
    tk.Label(
        frame,
        text="ⓘ",
        bg=COLORS["primary_soft"],
        fg=COLORS["primary"],
        font=(FONT_FAMILY, 12, "bold"),
    ).pack(side="left", padx=(0, 9))
    tk.Label(
        frame,
        text=text,
        bg=COLORS["primary_soft"],
        fg=COLORS["primary"],
        font=BODY_FONT,
        justify="left",
        anchor="w",
    ).pack(side="left", fill="x", expand=True)
    return frame


def primary_button(parent, text, command, *, width=None):
    return tb.Button(
        parent,
        text=text,
        command=command,
        bootstyle="primary",
        width=width,
        padding=(14, 8),
    )


def secondary_button(parent, text, command, *, width=None):
    return tb.Button(
        parent,
        text=text,
        command=command,
        bootstyle="primary-outline",
        width=width,
        padding=(12, 7),
    )


def danger_button(parent, text, command, *, width=None):
    return tb.Button(
        parent,
        text=text,
        command=command,
        bootstyle="danger-outline",
        width=width,
        padding=(12, 7),
    )


def success_button(parent, text, command, *, width=None):
    return tb.Button(
        parent,
        text=text,
        command=command,
        bootstyle="success",
        width=width,
        padding=(12, 7),
    )


def toggle_switch(parent, variable, command=None, text=""):
    """Return a modern blue round toggle matching the approved mockups."""
    return tb.Checkbutton(
        parent,
        text=text,
        variable=variable,
        command=command,
        bootstyle="primary-round-toggle",
    )


def radio_button(parent, *, text, variable, value, command=None):
    return tb.Radiobutton(
        parent,
        text=text,
        variable=variable,
        value=value,
        command=command,
        bootstyle="primary",
    )
