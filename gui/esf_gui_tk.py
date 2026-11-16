#!/usr/bin/env python3
"""
ESF-DT :: esf_gui_tk.py
=======================
Native desktop workbench for the Electric Smelting Furnace digital twin.

    python gui/esf_gui_tk.py

Pure Tkinter + Matplotlib, no web server.  Eight notebook pages:

    1  Schematic      live scale drawing of the reactor on a Tk canvas
    2  Static inputs  every charge, target, geometry and electrical setting
    3  Mass balance   charge, products, compositions, elemental closure
    4  Energy         heat balance, SEC hierarchy, loss breakdown
    5  Refractory     lining stack, zone losses, through-wall profiles
    6  Parametric     any input swept against any KPI
    7  Dynamic        transient run, twelve-panel trajectory dashboard
    8  Event log      time-stamped additions, taps, alarms and advisories

(c) Extractmet Private Limited.  Plant references anonymised as Industry-X.
"""

from __future__ import annotations

import os
import sys
import threading
import queue
import csv

import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from esf_dt import __version__, PRODUCT, VENDOR
from esf_dt import properties as pr
from esf_dt import thermo as th
from esf_dt.static_model import (run_static, DRI_LIBRARY, FLUX_LIBRARY,
                                 CARBON_LIBRARY)
from esf_dt.dynamic_model import run_dynamic
from esf_dt.geometry import FurnaceGeometry, default_lining, heat_loss_network
from esf_dt.electrical import ElectricalConfig, solve_electrical

PAL = ["#1f4e79", "#c1121f", "#2a9d8f", "#e07a5f", "#6a4c93",
       "#f4a261", "#264653", "#8ab17d", "#b5179e", "#457b9d"]
BG = "#f4f6f8"
CARD = "#ffffff"
INK = "#12263a"
MUTED = "#5c6b7a"


# ==========================================================================
def ramp(v, lo, hi, c0, c1):
    f = 0.0 if hi <= lo else max(0.0, min(1.0, (v - lo) / (hi - lo)))
    return "#%02x%02x%02x" % tuple(int(a + (b - a) * f) for a, b in zip(c0, c1))


class Field:
    """One labelled input bound to a Tk variable."""

    def __init__(self, parent, row, label, kind, default, values=None,
                 width=16, unit=""):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w",
                                           padx=(8, 6), pady=2)
        if kind == "combo":
            self.var = tk.StringVar(value=default)
            w = ttk.Combobox(parent, textvariable=self.var, values=values,
                             width=width, state="readonly")
        elif kind == "check":
            self.var = tk.BooleanVar(value=default)
            w = ttk.Checkbutton(parent, variable=self.var)
        else:
            self.var = tk.DoubleVar(value=default)
            w = ttk.Spinbox(parent, textvariable=self.var, width=width,
                            from_=values[0], to=values[1],
                            increment=values[2], format="%.4g")
        w.grid(row=row, column=1, sticky="we", padx=(0, 4), pady=2)
        if unit:
            ttk.Label(parent, text=unit, foreground=MUTED).grid(
                row=row, column=2, sticky="w", padx=(0, 8))
        self.widget = w

    def get(self):
        return self.var.get()


# ==========================================================================
class SchematicCanvas(tk.Canvas):
    """Scale drawing of the furnace, redrawn from the model state."""

    def __init__(self, master, **kw):
        super().__init__(master, bg=BG, highlightthickness=0, **kw)
        self.state = {}
        self.bind("<Configure>", lambda e: self.redraw())

    def set_state(self, st):
        self.state = dict(st or {})
        self.redraw()

    # ------------------------------------------------------------------
    def redraw(self):
        self.delete("all")
        s = self.state
        g = s.get
        W = max(700, self.winfo_width())
        H = max(430, self.winfo_height())

        T_m = float(g("T_metal_C", 1500))
        T_s = float(g("T_slag_C", 1560))
        T_g = float(g("T_gas_C", 1650))
        T_p = float(g("T_pile_C", 600))
        n_el = int(g("n_electrodes", 6))
        imm = float(g("immersion_m", 0.45))
        arc = float(g("arc_length_m", 0.09))
        frz = float(g("freeze_mm", 75))
        dm = float(g("metal_depth_m", 0.90))
        ds = float(g("slag_depth_m", 1.35))
        pile_t = float(g("m_pile_t", 0.0))

        self.create_text(18, 16, anchor="w", text="Electric Smelting Furnace "
                         "- live process schematic",
                         font=("Segoe UI", 13, "bold"), fill=INK)
        self.create_text(18, 34, anchor="w", fill=MUTED,
                         font=("Segoe UI", 8),
                         text=f"{PRODUCT} digital twin - {VENDOR} - "
                              f"reference plant: Industry-X")

        panel_w = 236
        x0, x1 = 92, W - panel_w - 40
        if x1 - x0 < 260:
            x1 = x0 + 260
        top, bot = 128, H - 108
        il, ir = x0 + 26, x1 - 26
        it, ib = top + 20, bot - 30

        usable = (ib - it) - 78
        hm_px = max(12, usable * dm / (dm + ds + 1.5))
        hs_px = max(14, usable * ds / (dm + ds + 1.5))
        y_m = ib - hm_px
        y_s = y_m - hs_px

        # shell and lining
        self.create_rectangle(x0, top, x1, bot, fill="#cfd6dd",
                              outline="#8c99a6", width=2)
        self.create_rectangle(x0 + 8, top + 7, x1 - 8, bot - 7,
                              fill="#e6ded2", outline="#b9ad9c")
        self.create_rectangle(x0 + 17, top + 14, x1 - 17, bot - 14,
                              fill="#d9c7ad", outline="#b09a78")
        self.create_rectangle(il, it, ir, ib,
                              fill=ramp(T_g, 1100, 1800, (40, 42, 54),
                                        (120, 62, 56)), outline="")

        # freeze lining
        fz = max(2, min(20, frz / 6.0))
        self.create_rectangle(il, y_s, il + fz, y_s + hs_px, fill="#9fb8c8",
                              outline="#6d8c9e")
        self.create_rectangle(ir - fz, y_s, ir, y_s + hs_px, fill="#9fb8c8",
                              outline="#6d8c9e")

        # baths
        self.create_rectangle(il + fz, y_s, ir - fz, y_s + hs_px,
                              fill=ramp(T_s, 1440, 1620, (128, 44, 24),
                                        (240, 150, 60)), outline="")
        self.create_rectangle(il, y_m, ir, ib,
                              fill=ramp(T_m, 1400, 1580, (196, 92, 20),
                                        (255, 214, 120)), outline="#3b1c06")

        self.create_text(il + 10, y_m + hm_px / 2, anchor="w",
                         font=("Segoe UI", 9, "bold"), fill="#2b1200",
                         text=f"HOT METAL  {g('m_metal_t', 0):.1f} t "
                              f"- {T_m:.0f} \u00b0C")
        self.create_text(il + 10, y_s + hs_px / 2, anchor="w",
                         font=("Segoe UI", 9, "bold"), fill="#2b1200",
                         text=f"SLAG  {g('m_slag_t', 0):.1f} t - {T_s:.0f} "
                              f"\u00b0C - B2 {g('B2', 1.1):.2f}")

        # electrodes with brush arcs
        span = ir - il
        ew = min(26, span / (n_el * 2.4))
        y_top = 62
        for k in range(n_el):
            cx = il + span * (k + 0.5) / n_el
            tip = y_s + max(3, min(hs_px - 5, imm / max(ds, 0.2) * hs_px))
            gap = max(3, arc * 70)
            self.create_rectangle(cx - ew / 2, y_top, cx + ew / 2, tip - gap,
                                  fill="#3b3b3b", outline="#1c1c1c")
            self.create_rectangle(cx - ew / 2 - 3, y_top + 12,
                                  cx + ew / 2 + 3, y_top + 26,
                                  fill="#b08d57", outline="#7d6337")
            self.create_oval(cx - ew * 0.9, tip - gap * 1.9, cx + ew * 0.9,
                             tip + gap * 0.2, fill="#ffd166", outline="")
            self.create_text(cx, y_top - 9, text=f"E{k+1}", fill=INK,
                             font=("Segoe UI", 7))

        # feed pile
        if pile_t > 0.02:
            pw = max(40, min(span * 0.4, 26 + pile_t * 6))
            px = il + span * 0.30
            ph = max(12, min(48, 8 + pile_t * 2))
            self.create_polygon(px - pw / 2, y_s, px - pw / 4, y_s - ph * 0.8,
                                px, y_s - ph, px + pw / 4, y_s - ph * 0.8,
                                px + pw / 2, y_s, fill="#6b6257",
                                outline="#463f36", smooth=True)
            self.create_text(px, y_s - ph - 8, fill="#e8eef4",
                             font=("Segoe UI", 7),
                             text=f"feed pile {pile_t:.1f} t - {T_p:.0f} "
                                  f"\u00b0C")

        # feed chutes and off-gas
        feeds = [("DRI/HBI", g("dri_feed_t_h", 0), 0.16),
                 ("Carbon", g("carbon_feed_t_h", 0), 0.32),
                 ("Flux", g("flux_feed_t_h", 0), 0.48)]
        for i, (nm, v, fx) in enumerate(feeds):
            cx = il + span * fx
            yl = 44 + i * 0
            self.create_line(cx, yl + 4, cx, top - 3, fill="#1f4e79",
                             width=3, arrow=tk.LAST)
            self.create_text(cx + 5, yl - 4 - i * 12, anchor="w",
                             fill="#1f4e79", font=("Segoe UI", 7),
                             text=f"{nm} {v:.1f} t/h")
        self.create_line(ir - 30, top - 3, ir - 30, 44, fill="#c1121f",
                         width=3, arrow=tk.LAST)
        self.create_text(ir - 34, 36, anchor="e", fill="#c1121f",
                         font=("Segoe UI", 7),
                         text=f"off-gas {g('offgas_Nm3_h', 0):,.0f} "
                              f"Nm\u00b3/h - {T_g:.0f} \u00b0C")

        # tap holes
        self.create_rectangle(x1 - 4, y_m + hm_px * 0.45, x1 + 24,
                              y_m + hm_px * 0.45 + 10, fill="#8a4b12",
                              outline="#4d2a08")
        self.create_line(x1 + 24, y_m + hm_px * 0.5, x1 + 56,
                         y_m + hm_px * 0.5 + 22, fill="#ffb347", width=5)
        self.create_text(x1 + 6, y_m + hm_px * 0.5 + 34, anchor="w",
                         fill="#8a4b12", font=("Segoe UI", 7),
                         text="metal tap-hole")
        self.create_rectangle(x0 - 24, y_s + hs_px * 0.35, x0 + 4,
                              y_s + hs_px * 0.35 + 10, fill="#7a3a2a",
                              outline="#40190f")
        self.create_line(x0 - 24, y_s + hs_px * 0.4, x0 - 56,
                         y_s + hs_px * 0.4 + 22, fill="#e07a5f", width=5)
        self.create_text(x0 - 56, y_s + hs_px * 0.4 - 8, anchor="w",
                         fill="#7a3a2a", font=("Segoe UI", 7),
                         text="slag tap-hole")

        # cooling arrows
        for yy in (top + 26, top + 58, top + 90):
            self.create_line(x1 + 2, yy, x1 + 30, yy, fill="#2a9d8f",
                             width=2, arrow=tk.LAST)
        self.create_text(x1 + 4, top + 106, anchor="w", fill="#2a9d8f",
                         font=("Segoe UI", 7),
                         text=f"cooling {g('heat_loss_MW', 0):.1f} MW")

        # freeboard callout
        self.create_line(x0 - 6, it + 22, il + 4, it + 22, fill=MUTED)
        self.create_text(x0 - 10, it + 14, anchor="e", fill=MUTED,
                         font=("Segoe UI", 7), text="FREEBOARD")
        self.create_text(x0 - 10, it + 27, anchor="e", fill=MUTED,
                         font=("Segoe UI", 7),
                         text=f"{T_g:.0f} \u00b0C CO/CO\u2082")

        # legend + dimensions
        for i, (nm, col) in enumerate([("Steel shell", "#cfd6dd"),
                                       ("Safety lining", "#e6ded2"),
                                       ("Working refractory", "#d9c7ad"),
                                       ("Freeze lining", "#9fb8c8")]):
            yy = bot + 16 + (i % 2) * 16
            xx = x0 + (i // 2) * 180
            self.create_rectangle(xx, yy - 8, xx + 12, yy + 1, fill=col,
                                  outline="#8c99a6")
            self.create_text(xx + 18, yy - 3, anchor="w", fill="#3c4a57",
                             font=("Segoe UI", 7), text=nm)
        self.create_text(x0, bot + 56, anchor="w", fill=MUTED,
                         font=("Segoe UI", 7),
                         text=f"hearth {g('length_m', 35):.1f} x "
                              f"{g('width_m', 11):.1f} m - slag {ds:.2f} m - "
                              f"metal {dm:.2f} m - freeze {frz:.0f} mm - "
                              f"{n_el} electrodes, immersion {imm:.2f} m, "
                              f"arc {arc*1000:.0f} mm")

        # KPI panel
        px0 = W - panel_w - 14
        self.create_rectangle(px0, 56, W - 14, bot + 40, fill=CARD,
                              outline="#d5dbe1")
        self.create_text(px0 + 12, 74, anchor="w", fill=INK,
                         font=("Segoe UI", 9, "bold"), text="LIVE KPIs")
        kpi = [("Active power", f"{g('power_MW', 0):.1f} MW"),
               ("Slag Joule", f"{g('P_slag_MW', 0):.1f} MW"),
               ("Brush arc", f"{g('P_arc_MW', 0):.1f} MW"),
               ("Current", f"{g('current_kA', 0):.1f} kA"),
               ("Tap voltage", f"{g('voltage_V', 0):.0f} V"),
               ("Lining loss", f"{g('heat_loss_MW', 0):.1f} MW"),
               ("SEC", f"{g('SEC_kWh_t', 0):,.0f} kWh/tHM"),
               ("Slag rate", f"{g('slag_rate_kg_t', 0):.0f} kg/tHM"),
               ("[C]", f"{g('C_pct', 0):.2f} wt%"),
               ("[Si]", f"{g('Si_pct', 0):.3f} wt%"),
               ("[Mn]", f"{g('Mn_pct', 0):.3f} wt%"),
               ("[P]", f"{g('P_pct', 0):.3f} wt%"),
               ("[S]", f"{g('S_pct', 0):.3f} wt%"),
               ("(FeO)", f"{g('FeO_pct', 0):.2f} wt%"),
               ("(SiO2)", f"{g('SiO2_pct', 0):.1f} wt%"),
               ("(CaO)", f"{g('CaO_pct', 0):.1f} wt%"),
               ("(Al2O3)", f"{g('Al2O3_pct', 0):.1f} wt%"),
               ("(MgO)", f"{g('MgO_pct', 0):.1f} wt%"),
               ("Shell T max", f"{g('shell_T_C', 0):.0f} \u00b0C"),
               ("Hot face", f"{g('hotface_C', 0):.0f} \u00b0C")]
        for i, (k, v) in enumerate(kpi):
            yy = 94 + i * 17
            if yy > bot + 30:
                break
            self.create_text(px0 + 12, yy, anchor="w", fill=MUTED,
                             font=("Segoe UI", 8), text=k)
            self.create_text(W - 26, yy, anchor="e", fill=INK,
                             font=("Segoe UI", 8, "bold"), text=v)

        # alarm banner
        al = g("alarm", "")
        self.create_rectangle(18, H - 44, W - 18, H - 14,
                              fill="#fdecec" if al else "#eef7f2",
                              outline="#c1121f" if al else "#2a9d8f")
        self.create_text(32, H - 29, anchor="w",
                         fill="#c1121f" if al else "#1d6f63",
                         font=("Segoe UI", 8, "bold" if al else "normal"),
                         text=("! " + al) if al else
                              "All monitored variables inside the operating "
                              "window.")


# ==========================================================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{PRODUCT} v{__version__} - Electric Smelting Furnace "
                   f"digital twin - {VENDOR}")
        self.geometry("1500x940")
        self.configure(bg=BG)
        self.R = None
        self.D = None
        self.q = queue.Queue()

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook.Tab", padding=(14, 7))
        style.configure("TLabelframe", background=BG)
        style.configure("TLabelframe.Label", foreground=INK,
                        font=("Segoe UI", 9, "bold"))
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=INK)
        style.configure("Card.TFrame", background=CARD)

        self._build_toolbar()
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._page_schematic()
        self._page_inputs()
        self._page_mass()
        self._page_energy()
        self._page_refractory()
        self._page_parametric()
        self._page_dynamic()
        self._page_events()

        self.solve_static()
        self.after(200, self._pump)

    # ------------------------------------------------------------------
    def _build_toolbar(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="Solve static", command=self.solve_static
                   ).pack(side="left")
        ttk.Button(bar, text="Run dynamic", command=self.solve_dynamic
                   ).pack(side="left", padx=6)
        ttk.Button(bar, text="Export results...", command=self.export
                   ).pack(side="left")
        self.status = ttk.Label(bar, text="ready", foreground=MUTED)
        self.status.pack(side="right")

    # ------------------------------------------------------------------
    def _page_schematic(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="1  Schematic")
        self.canvas_sch = SchematicCanvas(f)
        self.canvas_sch.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    def _page_inputs(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="2  Static inputs")
        cols = ttk.Frame(f)
        cols.pack(fill="both", expand=True, padx=8, pady=8)
        self.F = {}

        def box(parent, title, col):
            lf = ttk.Labelframe(parent, text=title)
            lf.grid(row=0, column=col, sticky="nsew", padx=6, pady=4)
            lf.columnconfigure(1, weight=1)
            return lf

        for c in range(4):
            cols.columnconfigure(c, weight=1)

        b = box(cols, "Feed", 0)
        self.F["dri"] = Field(b, 0, "DRI grade", "combo",
                              list(DRI_LIBRARY)[0], list(DRI_LIBRARY), 22)
        self.F["MR"] = Field(b, 1, "Metallisation", "num", 94.0,
                             (70, 100, 0.5), unit="%")
        self.F["Tdri"] = Field(b, 2, "DRI temperature", "num", 600.0,
                               (25, 800, 25), unit="degC")
        self.F["scrap"] = Field(b, 3, "Scrap fraction", "num", 0.0,
                                (0, 60, 5), unit="wt%")
        self.F["carbon"] = Field(b, 4, "Carburiser", "combo",
                                 list(CARBON_LIBRARY)[0],
                                 list(CARBON_LIBRARY), 22)
        self.F["flux1"] = Field(b, 5, "Primary flux", "combo",
                                list(FLUX_LIBRARY)[0], list(FLUX_LIBRARY), 22)
        self.F["flux2"] = Field(b, 6, "Secondary flux", "combo",
                                list(FLUX_LIBRARY)[1], list(FLUX_LIBRARY), 22)

        b = box(cols, "Product targets", 1)
        self.F["Ttap"] = Field(b, 0, "Tapping temperature", "num", 1500.0,
                               (1380, 1560, 5), unit="degC")
        self.F["C"] = Field(b, 1, "Target [C]", "num", 3.5, (0.5, 4.5, 0.1),
                            unit="wt%")
        self.F["B2"] = Field(b, 2, "Target B2", "num", 1.10, (0.7, 1.6, 0.02))
        self.F["MgO"] = Field(b, 3, "Target slag MgO", "num", 8.0,
                              (4, 14, 0.5), unit="wt%")
        self.F["dTs"] = Field(b, 4, "Slag superheat", "num", 60.0,
                              (20, 120, 5), unit="K")
        self.F["Tgas"] = Field(b, 5, "Off-gas temperature", "num", 1450.0,
                               (900, 1800, 25), unit="degC")
        self.F["prod"] = Field(b, 6, "Productivity", "num", 143.0,
                               (5, 400, 1), unit="tHM/h")

        b = box(cols, "Geometry", 2)
        self.F["L"] = Field(b, 0, "Hearth length", "num", 35.0, (8, 60, 0.5),
                            unit="m")
        self.F["W"] = Field(b, 1, "Hearth width", "num", 11.0, (4, 20, 0.5),
                            unit="m")
        self.F["nel"] = Field(b, 2, "Electrodes", "num", 6.0, (3, 9, 1))
        self.F["del"] = Field(b, 3, "Electrode diameter", "num", 1.70,
                              (0.6, 2.2, 0.05), unit="m")
        self.F["pitch"] = Field(b, 4, "Electrode pitch", "num", 4.60,
                                (1.5, 8, 0.1), unit="m")
        self.F["imm"] = Field(b, 5, "Immersion", "num", 0.45,
                              (0.05, 1.2, 0.01), unit="m")
        self.F["arc"] = Field(b, 6, "Brush-arc length", "num", 0.09,
                              (0, 0.3, 0.01), unit="m")
        self.F["dslag"] = Field(b, 7, "Slag depth", "num", 1.35,
                                (0.4, 2.5, 0.05), unit="m")
        self.F["dmetal"] = Field(b, 8, "Metal depth", "num", 0.90,
                                 (0.3, 2.0, 0.05), unit="m")
        self.F["fbh"] = Field(b, 9, "Freeboard height", "num", 3.2,
                              (1, 6, 0.1), unit="m")

        b = box(cols, "Electrical / losses / cost", 3)
        self.F["V"] = Field(b, 0, "Secondary voltage", "num", 420.0,
                            (150, 900, 10), unit="V")
        self.F["pf"] = Field(b, 1, "Power factor", "num", 0.86,
                             (0.6, 0.98, 0.01))
        self.F["etael"] = Field(b, 2, "Electrical-to-bath eff.", "num", 0.90,
                                (0.7, 0.99, 0.01))
        self.F["etath"] = Field(b, 3, "Thermal utilisation", "num", 1.0,
                                (0.6, 1.0, 0.01))
        self.F["simode"] = Field(b, 11, "Silicon basis", "combo", "kinetic",
                                 ["kinetic", "equilibrium"], 22)
        self.F["siceil"] = Field(b, 12, "Si kinetic ceiling", "num", 0.45,
                                 (0.2, 1.2, 0.05), unit="wt%")
        self.F["feofloor"] = Field(b, 13, "Residual slag FeO", "num", 0.65,
                                   (0.0, 3.0, 0.05), unit="wt%")
        self.F["hlmode"] = Field(b, 4, "Heat-loss model", "combo", "geometry",
                                 ["geometry", "fraction"], 22)
        self.F["hlfrac"] = Field(b, 5, "Loss fraction", "num", 0.10,
                                 (0.02, 0.4, 0.01))
        self.F["ppow"] = Field(b, 6, "Power price", "num", 55.0,
                               (5, 250, 1), unit="USD/MWh")
        self.F["pcarb"] = Field(b, 7, "Carburiser price", "num", 320.0,
                                (50, 900, 5), unit="USD/t")
        self.F["plime"] = Field(b, 8, "Flux price", "num", 95.0, (20, 400, 5),
                                unit="USD/t")
        self.F["pel"] = Field(b, 9, "Electrode price", "num", 1150.0,
                              (200, 4000, 50), unit="USD/t")
        self.F["gef"] = Field(b, 10, "Grid emission factor", "num", 120.0,
                              (0, 1200, 10), unit="kg/MWh")

        out = ttk.Labelframe(f, text="Key performance indicators")
        out.pack(fill="both", expand=True, padx=14, pady=(4, 10))
        self.kpi_tree = self._tree(out, ("KPI", "value"), (360, 200))

    # ------------------------------------------------------------------
    @staticmethod
    def _tree(parent, cols, widths, height=None):
        fr = ttk.Frame(parent)
        fr.pack(fill="both", expand=True, padx=6, pady=6)
        t = ttk.Treeview(fr, columns=cols, show="headings",
                         height=height or 14)
        for c, w in zip(cols, widths):
            t.heading(c, text=c)
            t.column(c, width=w, anchor="w")
        vs = ttk.Scrollbar(fr, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=vs.set)
        t.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")
        return t

    @staticmethod
    def _fill(tree, rows):
        tree.delete(*tree.get_children())
        for r in rows:
            tree.insert("", "end", values=[
                (f"{v:,.4g}" if isinstance(v, float) else v) for v in r])

    # ------------------------------------------------------------------
    def _page_mass(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="3  Mass balance")
        top = ttk.Frame(f)
        top.pack(fill="both", expand=True)
        for i in range(4):
            top.columnconfigure(i, weight=1)
        top.rowconfigure(0, weight=1)
        names = ["Charge and products", "Hot metal", "Tapped slag",
                 "Off-gas, dust and closure"]
        self.mass_trees = []
        for i, n in enumerate(names):
            lf = ttk.Labelframe(top, text=n)
            lf.grid(row=0, column=i, sticky="nsew", padx=5, pady=6)
            self.mass_trees.append(
                self._tree(lf, ("item", "value", "unit"), (150, 90, 60)))
        self.fig_mass = self._mpl(f, 3.0)

    def _mpl(self, parent, height):
        fr = ttk.Frame(parent)
        fr.pack(fill="both", expand=True, padx=6, pady=4)
        fg = Figure(figsize=(12, height), dpi=100, facecolor=CARD)
        cv = FigureCanvasTkAgg(fg, master=fr)
        cv.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(cv, fr).update()
        return fg, cv

    # ------------------------------------------------------------------
    def _page_energy(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="4  Energy")
        lf = ttk.Labelframe(f, text="Heat balance (MJ per tonne of hot metal)")
        lf.pack(fill="both", expand=False, padx=8, pady=6)
        self.energy_tree = self._tree(lf, ("term", "MJ/tHM"), (420, 140), 12)
        self.fig_energy = self._mpl(f, 3.4)

    # ------------------------------------------------------------------
    def _page_refractory(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="5  Refractory")
        top = ttk.Frame(f)
        top.pack(fill="both", expand=False)
        for i in range(2):
            top.columnconfigure(i, weight=1)
        lf = ttk.Labelframe(top, text="Lining stack")
        lf.grid(row=0, column=0, sticky="nsew", padx=5, pady=6)
        self.lin_tree = self._tree(lf, ("zone", "material", "mm"),
                                   (110, 180, 60), 10)
        lf = ttk.Labelframe(top, text="Zone heat losses")
        lf.grid(row=0, column=1, sticky="nsew", padx=5, pady=6)
        self.zone_tree = self._tree(
            lf, ("zone", "area m2", "q kW/m2", "Q MW", "hot face C",
                 "shell C", "freeze mm"), (95, 70, 75, 65, 80, 65, 75), 10)
        self.fig_refr = self._mpl(f, 3.4)

    # ------------------------------------------------------------------
    def _page_parametric(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="6  Parametric")
        bar = ttk.Frame(f)
        bar.pack(fill="x", padx=8, pady=6)
        self.sweep_var = tk.StringVar(value="metallisation_pct")
        opts = ["metallisation_pct", "tap_temperature_C",
                "target_C_in_HM_pct", "target_basicity_B2",
                "scrap_fraction_pct", "dri_temperature_C",
                "target_MgO_in_slag_pct", "slag_superheat_C"]
        ttk.Label(bar, text="Sweep").pack(side="left", padx=(0, 6))
        ttk.Combobox(bar, textvariable=self.sweep_var, values=opts, width=26,
                     state="readonly").pack(side="left")
        self.sw_lo = tk.DoubleVar(value=80.0)
        self.sw_hi = tk.DoubleVar(value=100.0)
        self.sw_n = tk.IntVar(value=13)
        for lab, v, w in (("from", self.sw_lo, 8), ("to", self.sw_hi, 8),
                          ("points", self.sw_n, 5)):
            ttk.Label(bar, text=lab).pack(side="left", padx=(10, 3))
            ttk.Entry(bar, textvariable=v, width=w).pack(side="left")
        ttk.Button(bar, text="Run sweep", command=self.run_sweep
                   ).pack(side="left", padx=12)
        self.fig_sweep = self._mpl(f, 6.4)

    # ------------------------------------------------------------------
    def _page_dynamic(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="7  Dynamic")
        bar = ttk.Frame(f)
        bar.pack(fill="x", padx=8, pady=6)
        self.DF = {}
        specs = [("duration_min", "Duration (min)", 180.0, (30, 1440, 30)),
                 ("dt_s", "dt (s)", 10.0, (2, 60, 1)),
                 ("dri_feed_t_h", "DRI feed (t/h)", 160.0, (5, 500, 5)),
                 ("carbon_feed_kg_t_dri", "C (kg/t)", 55.0, (10, 150, 1)),
                 ("lime_feed_kg_t_dri", "Lime (kg/t)", 73.0, (0, 200, 1)),
                 ("dolo_feed_kg_t_dri", "Dolo (kg/t)", 36.0, (0, 150, 1)),
                 ("power_MW", "Rated power (MW)", 116.0, (5, 300, 1)),
                 ("target_metal_T_C", "T setpoint (degC)", 1500.0,
                  (1400, 1560, 5)),
                 ("metal_tap_mass_t", "Metal tap (t)", 150.0, (5, 400, 5)),
                 ("metal_tap_interval_min", "every (min)", 60.0,
                  (10, 240, 5)),
                 ("slag_tap_mass_t", "Slag tap (t)", 24.0, (2, 120, 1)),
                 ("slag_tap_interval_min", "every (min)", 30.0, (5, 180, 5))]
        for i, (k, lab, d, rng) in enumerate(specs):
            ttk.Label(bar, text=lab).grid(row=i // 6, column=(i % 6) * 2,
                                          sticky="e", padx=(8, 3), pady=2)
            v = tk.DoubleVar(value=d)
            ttk.Spinbox(bar, textvariable=v, from_=rng[0], to=rng[1],
                        increment=rng[2], width=9).grid(
                row=i // 6, column=(i % 6) * 2 + 1, sticky="w", pady=2)
            self.DF[k] = v
        ttk.Button(bar, text="Run", command=self.solve_dynamic).grid(
            row=0, column=12, rowspan=2, padx=14)
        self.fig_dyn = self._mpl(f, 7.6)

    # ------------------------------------------------------------------
    def _page_events(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="8  Event log")
        bar = ttk.Frame(f)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Label(bar, text="Filter").pack(side="left")
        self.ev_filter = tk.StringVar(value="ALL")
        ttk.Combobox(bar, textvariable=self.ev_filter,
                     values=["ALL", "TAP-METAL", "TAP-SLAG", "ALARM",
                             "WARNING", "START", "END"], width=16,
                     state="readonly").pack(side="left", padx=6)
        ttk.Button(bar, text="Apply", command=self._refresh_events
                   ).pack(side="left")
        ttk.Button(bar, text="Export CSV", command=self.export_events
                   ).pack(side="left", padx=8)
        self.ev_tree = self._tree(
            f, ("clock", "t (min)", "type", "message", "detail"),
            (80, 70, 120, 520, 300), 30)
        sum_lf = ttk.Labelframe(f, text="Charge additions in force")
        sum_lf.pack(fill="x", padx=8, pady=6)
        self.add_tree = self._tree(
            sum_lf, ("stream", "rate", "unit", "cumulative (t)"),
            (170, 110, 80, 140), 6)

    # ==================================================================
    def _inputs(self):
        F = self.F
        geo = FurnaceGeometry(length=F["L"].get(), width=F["W"].get(),
                              n_electrodes=int(F["nel"].get()),
                              electrode_diameter=F["del"].get(),
                              electrode_pitch=F["pitch"].get(),
                              electrode_immersion=F["imm"].get(),
                              arc_length=F["arc"].get(),
                              slag_depth=F["dslag"].get(),
                              metal_depth=F["dmetal"].get(),
                              freeboard_height=F["fbh"].get())
        elec = ElectricalConfig(n_electrodes=int(F["nel"].get()),
                                electrode_diameter_m=F["del"].get(),
                                secondary_voltage_V=F["V"].get(),
                                power_factor=F["pf"].get())
        kw = dict(dri_name=F["dri"].get(), metallisation_pct=F["MR"].get(),
                  dri_temperature_C=F["Tdri"].get(),
                  scrap_fraction_pct=F["scrap"].get(),
                  carbon_source=F["carbon"].get(),
                  flux_primary=F["flux1"].get(),
                  flux_secondary=F["flux2"].get(),
                  tap_temperature_C=F["Ttap"].get(),
                  target_C_in_HM_pct=F["C"].get(),
                  target_basicity_B2=F["B2"].get(),
                  target_MgO_in_slag_pct=F["MgO"].get(),
                  slag_superheat_C=F["dTs"].get(),
                  offgas_temperature_C=F["Tgas"].get(),
                  heat_loss_mode=F["hlmode"].get(),
                  heat_loss_fraction=F["hlfrac"].get(),
                  productivity_tHM_h=F["prod"].get(),
                  electrical_to_bath_efficiency=F["etael"].get(),
                  thermal_utilisation_efficiency=F["etath"].get(),
                  silicon_mode=F["simode"].get(),
                  silicon_ceiling_wt_pct=F["siceil"].get(),
                  residual_FeO_floor_wt_pct=F["feofloor"].get(),
                  power_price_USD_MWh=F["ppow"].get(),
                  carbon_price_USD_t=F["pcarb"].get(),
                  lime_price_USD_t=F["plime"].get(),
                  electrode_price_USD_t=F["pel"].get(),
                  grid_emission_factor_kgCO2_MWh=F["gef"].get(),
                  geometry=geo, electrical=elec)
        return kw, geo, elec

    # ------------------------------------------------------------------
    def solve_static(self):
        try:
            kw, geo, elec = self._inputs()
            R = run_static(**kw)
        except ValueError as exc:
            # impossible configuration: say so plainly and keep the old
            # solution off the screen
            self.R = None
            messagebox.showerror("Configuration rejected", str(exc))
            self.status.config(text="configuration rejected - see message")
            return
        except Exception as exc:            # noqa: BLE001
            messagebox.showerror("Static solver", str(exc))
            return
        self.R, self.geo = R, geo
        self._refresh_static()
        warns = R.get("warnings", [])
        if warns:
            messagebox.showwarning("Advisory", "\n\n".join(warns))
        self.status.config(
            text=f"static solved - "
                 f"SEC {R['KPI']['SEC_operating_kWh_tHM']:.0f} kWh/tHM"
                 + (f"  ({len(warns)} advisory)" if warns else ""))

    # ------------------------------------------------------------------
    def _refresh_static(self):
        R = self.R
        from esf_dt.schematic import state_from_static
        st = state_from_static(R, self.geo)
        st["electrode_dia_m"] = self.geo.electrode_diameter
        self.canvas_sch.set_state(st)

        self._fill(self.kpi_tree, [(k, v) for k, v in R["KPI"].items()])

        rows = [("--- INPUTS (kg) ---", "", "")]
        rows += [(k, v, "kg") for k, v in R["inputs_kg"].items()]
        rows += [("--- OUTPUTS (kg) ---", "", "")]
        rows += [(k, v, "kg") for k, v in R["outputs_kg"].items()]
        rows += [("--- TEMPERATURES ---", "", "")]
        rows += [(k, v, "degC") for k, v in R["temperatures_C"].items()]
        self._fill(self.mass_trees[0], rows)
        self._fill(self.mass_trees[1],
                   [(k, v, "wt%") for k, v in R["hot_metal_wt_pct"].items()]
                   + [("--- properties ---", "", "")]
                   + [(k, v, "") for k, v in R["metal_properties"].items()])
        self._fill(self.mass_trees[2],
                   [(k, v, "wt%") for k, v in R["slag_wt_pct"].items()]
                   + [("--- properties ---", "", "")]
                   + [(k, v, "") for k, v in R["slag_properties"].items()])
        self._fill(self.mass_trees[3],
                   [(k, v, "kg") for k, v in R["offgas_kg"].items()]
                   + [("--- dust ---", "", "")]
                   + [(k, v, "kg") for k, v in R["dust_kg"].items()]
                   + [("--- closure ---", "", "")]
                   + [(k, v, "%") for k, v in R["closure"].items()])

        fg, cv = self.fig_mass
        fg.clear()
        ax = fg.add_subplot(131)
        ins = {k: v for k, v in R["inputs_kg"].items() if k != "Total charge"}
        ax.bar(range(len(ins)), list(ins.values()), color=PAL[0])
        ax.set_xticks(range(len(ins)))
        ax.set_xticklabels(list(ins), rotation=25, ha="right", fontsize=7)
        ax.set_ylabel("kg")
        ax.set_title("Charge", fontsize=9)
        ax = fg.add_subplot(132)
        ax.bar(range(len(R["outputs_kg"])), list(R["outputs_kg"].values()),
               color=PAL[1])
        ax.set_xticks(range(len(R["outputs_kg"])))
        ax.set_xticklabels(list(R["outputs_kg"]), rotation=25, ha="right",
                           fontsize=7)
        ax.set_title("Products", fontsize=9)
        ax = fg.add_subplot(133)
        sl = {k: v for k, v in R["slag_wt_pct"].items() if v > 0.05}
        ax.bar(range(len(sl)), list(sl.values()), color=PAL[2])
        ax.set_xticks(range(len(sl)))
        ax.set_xticklabels(list(sl), rotation=35, ha="right", fontsize=7)
        ax.set_ylabel("wt%")
        ax.set_title("Slag composition", fontsize=9)
        fg.tight_layout()
        cv.draw()

        hb = R["heat_balance_MJ_per_tHM"]
        self._fill(self.energy_tree, [(k, v) for k, v in hb.items()])
        fg, cv = self.fig_energy
        fg.clear()
        ax = fg.add_subplot(121)
        items = ["  Hot metal sensible+fusion", "  Hot metal dissolution",
                 "  Slag sensible (to liquidus)", "  Slag latent (solution)",
                 "  Slag superheat", "Refractory + shell loss"]
        vals = [abs(hb.get(k, 0.0)) for k in items]
        ax.barh([k.strip() for k in items], vals, color=PAL[:len(items)])
        ax.set_xlabel("MJ/tHM")
        ax.set_title("Energy split", fontsize=9)
        ax.tick_params(labelsize=7)
        ax = fg.add_subplot(122)
        secs = {"reversible": R["KPI"]["SEC_reversible_kWh_tHM"],
                "equilibrium basis": R["KPI"]["SEC_thermodynamic_kWh_tHM"],
                "operating": R["KPI"]["SEC_operating_kWh_tHM"]}
        ax.bar(range(3), list(secs.values()), color=PAL[3:6])
        ax.set_xticks(range(3))
        ax.set_xticklabels(list(secs), fontsize=7)
        ax.set_ylabel("kWh/tHM")
        ax.set_title("SEC hierarchy", fontsize=9)
        fg.tight_layout()
        cv.draw()

        lay = [(z, l_.material, l_.thickness * 1000)
               for z, ls in default_lining().items() for l_ in ls]
        self._fill(self.lin_tree, lay)
        hl = R.get("heat_loss")
        if hl:
            self._fill(self.zone_tree, [
                (z, v["area_m2"], v["q_flux_W_m2"] / 1e3, v["Q_W"] / 1e6,
                 v["T_hotface_K"] - 273.15, v["T_shell_K"] - 273.15,
                 v["freeze_thickness_m"] * 1000)
                for z, v in hl["zones"].items()])
            fg, cv = self.fig_refr
            fg.clear()
            ax = fg.add_subplot(121)
            for j, (z, v) in enumerate(hl["zones"].items()):
                xs, x = [0.0], 0.0
                for _, t_ in v["layers"]:
                    x += t_
                    xs.append(x)
                ax.plot(np.array(xs) * 1000,
                        np.array(v["T_nodes_K"]) - 273.15, "-o", ms=3,
                        color=PAL[j], label=z)
            ax.set_xlabel("mm from hot face")
            ax.set_ylabel("degC")
            ax.set_title("Lining profiles", fontsize=9)
            ax.legend(fontsize=7)
            ax = fg.add_subplot(122)
            ax.bar(range(len(hl["zones"])),
                   [v["Q_W"] / 1e6 for v in hl["zones"].values()],
                   color=PAL[:len(hl["zones"])])
            ax.set_xticks(range(len(hl["zones"])))
            ax.set_xticklabels(list(hl["zones"]), rotation=20, fontsize=7)
            ax.set_ylabel("MW")
            ax.set_title(f"Zone losses - total {hl['Q_total_W']/1e6:.1f} MW",
                         fontsize=9)
            fg.tight_layout()
            cv.draw()
        else:
            self._fill(self.zone_tree, [("switch heat-loss model to "
                                         "'geometry'", "", "", "", "", "",
                                         "")])

    # ------------------------------------------------------------------
    def run_sweep(self):
        try:
            kw, geo, elec = self._inputs()
            key = self.sweep_var.get()
            xs = np.linspace(self.sw_lo.get(), self.sw_hi.get(),
                             max(3, int(self.sw_n.get())))
            out = {k: [] for k in ("SEC_rev", "SEC_eq", "SEC_op", "slag",
                                   "carbon", "Si", "Mn", "FeO", "visc",
                                   "power", "opex", "co2")}
            for x in xs:
                k2 = dict(kw)
                k2[key] = float(x)
                r = run_static(**k2)
                out["SEC_rev"].append(r["KPI"]["SEC_reversible_kWh_tHM"])
                out["SEC_eq"].append(r["KPI"]["SEC_thermodynamic_kWh_tHM"])
                out["SEC_op"].append(r["KPI"]["SEC_operating_kWh_tHM"])
                out["slag"].append(r["KPI"]["Slag_rate_kg_tHM"])
                out["carbon"].append(r["KPI"]["Carbon_consumed_kg_tHM"])
                out["Si"].append(r["hot_metal_wt_pct"].get("Si", 0))
                out["Mn"].append(r["hot_metal_wt_pct"].get("Mn", 0))
                out["FeO"].append(r["slag_wt_pct"].get("FeO", 0))
                out["visc"].append(r["slag_properties"]["Viscosity (Pa.s)"])
                out["power"].append(r["KPI"]["Power_demand_MW"])
                out["opex"].append(r["KPI"]["Specific_OPEX_USD_tHM"])
                out["co2"].append(r["KPI"]["CO2_total_t_tHM"])
        except Exception as exc:            # noqa: BLE001
            messagebox.showerror("Sweep", str(exc))
            return
        fg, cv = self.fig_sweep
        fg.clear()
        panels = [("SEC (kWh/tHM)", ["SEC_rev", "SEC_eq", "SEC_op"]),
                  ("Slag rate (kg/tHM)", ["slag"]),
                  ("Carbon (kg/tHM)", ["carbon"]),
                  ("Hot-metal solutes (wt%)", ["Si", "Mn"]),
                  ("Slag FeO (wt%)", ["FeO"]),
                  ("Slag viscosity (Pa.s)", ["visc"]),
                  ("Power (MW)", ["power"]),
                  ("OPEX (USD/tHM)", ["opex"]),
                  ("CO2 (t/tHM)", ["co2"])]
        for i, (title, keys) in enumerate(panels):
            ax = fg.add_subplot(3, 3, i + 1)
            for j, k in enumerate(keys):
                ax.plot(xs, out[k], "-o", ms=3, color=PAL[j], label=k)
            ax.set_title(title, fontsize=8)
            ax.set_xlabel(self.sweep_var.get(), fontsize=7)
            ax.tick_params(labelsize=7)
            if len(keys) > 1:
                ax.legend(fontsize=6)
        fg.tight_layout()
        cv.draw()
        self.status.config(text=f"sweep of {self.sweep_var.get()} complete")

    # ------------------------------------------------------------------
    def solve_dynamic(self):
        self.status.config(text="running dynamic simulation...")

        def work():
            try:
                kw, geo, elec = self._inputs()
                D = run_dynamic(
                    duration_min=self.DF["duration_min"].get(),
                    dt_s=self.DF["dt_s"].get(), log_every_s=60.0,
                    dri_name=kw["dri_name"],
                    metallisation_pct=kw["metallisation_pct"],
                    dri_temperature_C=kw["dri_temperature_C"],
                    carbon_source=kw["carbon_source"],
                    flux_primary=kw["flux_primary"],
                    flux_secondary=kw["flux_secondary"],
                    dri_feed_t_h=self.DF["dri_feed_t_h"].get(),
                    carbon_feed_kg_t_dri=self.DF["carbon_feed_kg_t_dri"].get(),
                    lime_feed_kg_t_dri=self.DF["lime_feed_kg_t_dri"].get(),
                    dolo_feed_kg_t_dri=self.DF["dolo_feed_kg_t_dri"].get(),
                    power_MW=self.DF["power_MW"].get(),
                    target_metal_T_C=self.DF["target_metal_T_C"].get(),
                    target_basicity_B2=kw["target_basicity_B2"],
                    metal_tap_mass_t=self.DF["metal_tap_mass_t"].get(),
                    metal_tap_interval_min=self.DF["metal_tap_interval_min"].get(),
                    slag_tap_mass_t=self.DF["slag_tap_mass_t"].get(),
                    slag_tap_interval_min=self.DF["slag_tap_interval_min"].get(),
                    geometry=geo, electrical=elec)
                self.q.put(("dyn", D))
            except Exception as exc:        # noqa: BLE001
                self.q.put(("err", str(exc)))

        threading.Thread(target=work, daemon=True).start()

    def _pump(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "err":
                    messagebox.showerror("Dynamic solver", payload)
                    self.status.config(text="dynamic run failed")
                else:
                    self.D = payload
                    self._refresh_dynamic()
        except queue.Empty:
            pass
        self.after(200, self._pump)

    # ------------------------------------------------------------------
    def _refresh_dynamic(self):
        D = self.D
        T = D["trajectory"]
        from esf_dt.schematic import state_from_dynamic
        al = [e for e in D["events"] if e["type"] in ("ALARM", "WARNING")]
        st = state_from_dynamic(T, -1, self.geo,
                                alarm=al[-1]["message"] if al else "")
        st["electrode_dia_m"] = self.geo.electrode_diameter
        self.canvas_sch.set_state(st)

        fg, cv = self.fig_dyn
        fg.clear()
        panels = [
            ("Temperatures (degC)", ["T_metal_C", "T_slag_C", "T_gas_C",
                                     "T_pile_C"]),
            ("Power (MW)", ["power_MW", "P_slag_MW", "P_arc_MW",
                            "heat_loss_MW"]),
            ("Inventory (t)", ["m_metal_t", "m_slag_t", "m_pile_t", "char_t"]),
            ("Hot metal (wt%)", ["C_pct", "Si_pct", "Mn_pct", "Ti_pct"]),
            ("Residuals (wt%)", ["P_pct", "S_pct"]),
            ("Slag oxides (wt%)", ["SiO2_pct", "CaO_pct", "Al2O3_pct",
                                   "MgO_pct", "FeO_pct"]),
            ("Basicity", ["B2", "B3", "B4"]),
            ("Rates (kg/s)", ["r_FeO_kg_s", "r_Si_kg_s", "r_Mn_kg_s",
                              "r_Cdiss_kg_s"]),
            ("Electrical", ["current_kA", "resistance_mohm",
                            "sigma_slag_S_m"]),
            ("Superheat (K)", ["slag_superheat_C", "metal_superheat_C"]),
            ("Lining", ["freeze_mm", "shell_T_C", "hotface_slagwall_C"]),
            ("Production", ["metal_tapped_t", "slag_tapped_t",
                            "SEC_cum_kWh_t"]),
        ]
        for i, (title, keys) in enumerate(panels):
            ax = fg.add_subplot(4, 3, i + 1)
            for j, k in enumerate(keys):
                ax.plot(T["t_min"], T[k], color=PAL[j % len(PAL)], lw=1.1,
                        label=k)
            ax.set_title(title, fontsize=8)
            ax.tick_params(labelsize=6.5)
            ax.legend(fontsize=5.6, ncol=2)
            if i >= 9:
                ax.set_xlabel("time (min)", fontsize=7)
        fg.tight_layout()
        cv.draw()

        self._refresh_events()
        s = D["summary"]
        self.status.config(text=f"dynamic run complete - "
                                f"SEC {s['SEC (kWh/tHM)']:.0f} kWh/tHM, "
                                f"slag {s['Slag rate (kg/tHM)']:.0f} kg/tHM, "
                                f"{s['Productivity (tHM/h)']:.0f} tHM/h")

    # ------------------------------------------------------------------
    def _refresh_events(self):
        if not self.D:
            return
        want = self.ev_filter.get()
        rows = []
        for e in self.D["events"]:
            if want != "ALL" and e["type"] != want:
                continue
            det = ", ".join(f"{k}={v}" for k, v in e.items()
                            if k not in ("t_min", "clock", "type", "message"))
            rows.append((e["clock"], e["t_min"], e["type"], e["message"], det))
        self._fill(self.ev_tree, rows)
        T = self.D["trajectory"]
        c = self.D["cumulative"]
        self._fill(self.add_tree, [
            ("DRI", T["dri_feed_t_h"][-1], "t/h", c["dri_charged_t"]),
            ("Carburiser", T["carbon_feed_t_h"][-1], "t/h", c["C_charged_t"]),
            ("Fluxes", T["flux_feed_t_h"][-1], "t/h", c["flux_charged_t"]),
            ("Metal tapped", 0.0, "t", c["metal_tapped_t"]),
            ("Slag tapped", 0.0, "t", c["slag_tapped_t"]),
            ("Electrode consumed", 0.0, "kg", c["electrode_kg"] / 1000.0)])

    # ------------------------------------------------------------------
    def export_events(self):
        if not self.D:
            messagebox.showinfo("Export", "Run a dynamic simulation first.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".csv",
                                         initialfile="esf_event_log.csv")
        if not p:
            return
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["t_min", "clock", "type",
                                              "message"],
                               extrasaction="ignore")
            w.writeheader()
            w.writerows(self.D["events"])
        messagebox.showinfo("Export", f"Event log written to\n{p}")

    def export(self):
        if not self.R:
            return
        p = filedialog.asksaveasfilename(defaultextension=".csv",
                                         initialfile="esf_static_results.csv")
        if not p:
            return
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["section", "item", "value"])
            for sec in ("KPI", "inputs_kg", "outputs_kg", "hot_metal_wt_pct",
                        "slag_wt_pct", "offgas_kg", "slag_properties",
                        "metal_properties", "heat_balance_MJ_per_tHM",
                        "closure", "temperatures_C"):
                for k, v in self.R[sec].items():
                    w.writerow([sec, k, v])
        if self.D:
            p2 = os.path.splitext(p)[0] + "_trajectory.csv"
            T = self.D["trajectory"]
            with open(p2, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(list(T))
                for i in range(len(T["t_min"])):
                    w.writerow([T[k][i] for k in T])
        messagebox.showinfo("Export", f"Results written to\n{p}")


# ==========================================================================
if __name__ == "__main__":
    App().mainloop()
