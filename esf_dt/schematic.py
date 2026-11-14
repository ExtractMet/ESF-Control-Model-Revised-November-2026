"""
ESF-DT :: schematic.py
======================
Parametric, data-driven schematic of the Electric Smelting Furnace.

`furnace_svg(state)` returns a standalone SVG string in which every
dimension, colour and label is driven by the live model state: bath levels,
electrode immersion, arc length, freeze-lining thickness, temperatures,
compositions, power split, feed and tap streams.

The same function is used by the Streamlit app and by the standalone HTML
console, so the picture the operator sees is always the picture the model
is solving.
"""

from __future__ import annotations

from typing import Dict, Optional

W, H = 1180, 780


def _c(v, lo, hi, c0=(30, 78, 121), c1=(193, 18, 31)):
    """Linear colour ramp between c0 and c1 for value v in [lo, hi]."""
    f = 0.0 if hi <= lo else max(0.0, min(1.0, (v - lo) / (hi - lo)))
    return "#%02x%02x%02x" % tuple(int(a + (b - a) * f) for a, b in zip(c0, c1))


def _fmt(v, n=1):
    try:
        return f"{float(v):,.{n}f}"
    except Exception:
        return str(v)


def furnace_svg(s: Optional[Dict] = None) -> str:
    """
    Build the schematic.  `s` accepts (all optional):

        T_metal_C, T_slag_C, T_gas_C, T_pile_C, m_metal_t, m_slag_t,
        m_pile_t, metal_depth_m, slag_depth_m, freeze_mm, power_MW,
        P_slag_MW, P_arc_MW, current_kA, voltage_V, immersion_m,
        arc_length_m, n_electrodes, C_pct, Si_pct, Mn_pct, S_pct, P_pct,
        FeO_pct, B2, SiO2_pct, CaO_pct, Al2O3_pct, MgO_pct,
        dri_feed_t_h, flux_feed_t_h, carbon_feed_t_h, offgas_Nm3_h,
        heat_loss_MW, shell_T_C, hotface_C, SEC_kWh_t, slag_rate_kg_t,
        length_m, width_m, alarm
    """
    s = dict(s or {})
    g = s.get

    T_m = float(g("T_metal_C", 1500.0))
    T_s = float(g("T_slag_C", 1560.0))
    T_g = float(g("T_gas_C", 1600.0))
    T_p = float(g("T_pile_C", 600.0))
    n_el = int(g("n_electrodes", 6))
    imm = float(g("immersion_m", 0.45))
    arc = float(g("arc_length_m", 0.09))
    frz = float(g("freeze_mm", 75.0))
    m_depth = float(g("metal_depth_m", 0.90))
    s_depth = float(g("slag_depth_m", 1.35))
    pile_t = float(g("m_pile_t", 11.0))
    alarm = g("alarm", "")

    # ---- drawing frame --------------------------------------------------
    x0, x1 = 130, 858
    shell_top, shell_bot = 200, 590
    inner_l, inner_r = x0 + 34, x1 - 34
    inner_top, inner_bot = shell_top + 26, shell_bot - 44

    total_depth = max(0.4, m_depth + s_depth)
    usable = inner_bot - inner_top - 96          # freeboard reserved
    h_metal = max(14.0, usable * m_depth / (total_depth + 1.6))
    h_slag = max(18.0, usable * s_depth / (total_depth + 1.6))
    y_metal_top = inner_bot - h_metal
    y_slag_top = y_metal_top - h_slag

    metal_col = _c(T_m, 1400, 1580, (196, 92, 20), (255, 214, 120))
    slag_col = _c(T_s, 1440, 1620, (128, 44, 24), (240, 150, 60))
    gas_col = _c(T_g, 1100, 1800, (60, 60, 78), (150, 70, 60))

    p = []
    A = p.append
    A(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
      f'width="100%" style="max-width:{W}px;font-family:Inter,Segoe UI,'
      f'Helvetica,Arial,sans-serif">')
    A('<defs>'
      '<linearGradient id="mg" x1="0" y1="0" x2="0" y2="1">'
      f'<stop offset="0%" stop-color="{metal_col}"/>'
      '<stop offset="100%" stop-color="#7a3a06"/></linearGradient>'
      '<linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">'
      f'<stop offset="0%" stop-color="{slag_col}"/>'
      '<stop offset="100%" stop-color="#5c2410"/></linearGradient>'
      '<linearGradient id="fb" x1="0" y1="0" x2="0" y2="1">'
      f'<stop offset="0%" stop-color="#22242e"/>'
      f'<stop offset="100%" stop-color="{gas_col}"/></linearGradient>'
      '<radialGradient id="arcg"><stop offset="0%" stop-color="#fffbe6"/>'
      '<stop offset="55%" stop-color="#ffd166"/>'
      '<stop offset="100%" stop-color="#ff8c1a" stop-opacity="0"/>'
      '</radialGradient>'
      '<marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3.2" '
      'orient="auto"><path d="M0,0 L8,3.2 L0,6.4 z" fill="#1f4e79"/></marker>'
      '<marker id="ar2" markerWidth="9" markerHeight="9" refX="7" refY="3.2" '
      'orient="auto"><path d="M0,0 L8,3.2 L0,6.4 z" fill="#c1121f"/></marker>'
      '</defs>')
    A(f'<rect width="{W}" height="{H}" fill="#f7f8fa"/>')
    A('<text x="26" y="34" font-size="19" font-weight="700" fill="#12263a">'
      'Electric Smelting Furnace (open slag bath) &#8212; live process '
      'schematic</text>')
    A('<text x="26" y="54" font-size="11.5" fill="#5c6b7a">'
      'ESF-DT digital twin &#183; Extractmet Private Limited &#183; '
      'reference plant: Industry-X</text>')

    # ---- steel shell and lining ----------------------------------------
    A(f'<rect x="{x0}" y="{shell_top}" width="{x1-x0}" height="{shell_bot-shell_top}" '
      f'rx="12" fill="#cfd6dd" stroke="#8c99a6" stroke-width="2"/>')
    A(f'<rect x="{x0+10}" y="{shell_top+9}" width="{x1-x0-20}" '
      f'height="{shell_bot-shell_top-18}" rx="9" fill="#e6ded2" '
      f'stroke="#b9ad9c"/>')
    A(f'<rect x="{x0+22}" y="{shell_top+18}" width="{x1-x0-44}" '
      f'height="{shell_bot-shell_top-34}" rx="6" fill="#d9c7ad" '
      f'stroke="#b09a78"/>')
    A(f'<rect x="{inner_l}" y="{inner_top}" width="{inner_r-inner_l}" '
      f'height="{inner_bot-inner_top}" fill="url(#fb)"/>')

    # ---- freeze lining --------------------------------------------------
    fz_px = max(2.0, min(26.0, frz / 5.0))
    for xx, sgn in ((inner_l, 1), (inner_r - fz_px, 1)):
        A(f'<rect x="{xx}" y="{y_slag_top}" width="{fz_px}" height="{h_slag}" '
          f'fill="#9fb8c8" stroke="#6d8c9e" stroke-width="0.8"/>')
    A(f'<text x="{inner_l+fz_px+6}" y="{y_slag_top+13}" font-size="10" '
      f'fill="#dfe9ef">freeze lining {frz:.0f} mm</text>')

    # ---- baths ----------------------------------------------------------
    A(f'<rect x="{inner_l+fz_px}" y="{y_slag_top}" '
      f'width="{inner_r-inner_l-2*fz_px}" height="{h_slag}" fill="url(#sg)"/>')
    A(f'<rect x="{inner_l}" y="{y_metal_top}" width="{inner_r-inner_l}" '
      f'height="{h_metal}" fill="url(#mg)"/>')
    A(f'<line x1="{inner_l}" y1="{y_metal_top}" x2="{inner_r}" '
      f'y2="{y_metal_top}" stroke="#3b1c06" stroke-width="1.6"/>')

    # slag surface ripple
    A(f'<path d="M{inner_l} {y_slag_top} ' +
      " ".join(f"q 18 -6 36 0 t 36 0"
               for _ in range(int((inner_r - inner_l) / 72))) +
      f'" fill="none" stroke="#ffd9a0" stroke-width="1.4" opacity="0.8"/>')

    # The masses drawn inside the bath are the liquid inventories held in the
    # furnace, which is not the same thing as the production rate; both are
    # now stated on the drawing so that the two cannot be confused.  The
    # basicity shown is the computed value, not the target.
    A(f'<text x="{inner_l+10}" y="{y_metal_top+h_metal/2+1}" font-size="11.5" '
      f'font-weight="600" fill="#2b1200">HOT METAL in furnace  '
      f'{_fmt(g("m_metal_t",450))} t &#183; {T_m:.0f} &#176;C</text>')
    A(f'<text x="{inner_l+10}" y="{y_metal_top+h_metal/2+15}" font-size="10" '
      f'fill="#3d1e00">tapped {_fmt(g("metal_rate_t_h", 143.0),1)} t/h</text>')
    A(f'<text x="{inner_l+10}" y="{y_slag_top+h_slag/2+1}" font-size="11.5" '
      f'font-weight="600" fill="#2b1200">SLAG in furnace  '
      f'{_fmt(g("m_slag_t",210))} t &#183; {T_s:.0f} &#176;C &#183; '
      f'B2 {_fmt(g("B2",1.10),2)} (computed)</text>')
    A(f'<text x="{inner_l+10}" y="{y_slag_top+h_slag/2+15}" font-size="10" '
      f'fill="#3d1e00">tapped {_fmt(g("slag_rate_t_h", 39.0),1)} t/h '
      f'&#183; {_fmt(g("slag_rate_kg_t", 278),0)} kg/tHM</text>')
    A(f'<line x1="{x0-6}" y1="{inner_top+26}" x2="{inner_l+4}" '
      f'y2="{inner_top+26}" stroke="#5c6b7a" stroke-width="1"/>')
    A(f'<text x="{x0-10}" y="{inner_top+22}" font-size="10" '
      f'text-anchor="end" fill="#5c6b7a">FREEBOARD</text>')
    A(f'<text x="{x0-10}" y="{inner_top+36}" font-size="10" '
      f'text-anchor="end" fill="#5c6b7a">{T_g:.0f} &#176;C CO/CO&#8322;</text>')

    # ---- electrodes -----------------------------------------------------
    span = inner_r - inner_l
    el_w = min(30, span / (n_el * 2.4))
    y_el_top = 112
    for k in range(n_el):
        cx = inner_l + span * (k + 0.5) / n_el
        tip = y_slag_top + max(4.0, min(h_slag - 6.0, imm / max(s_depth, 0.2)
                                        * h_slag))
        gap = max(3.0, arc * 90.0)
        A(f'<rect x="{cx-el_w/2:.1f}" y="{y_el_top}" width="{el_w:.1f}" '
          f'height="{tip-gap-y_el_top:.1f}" rx="3" fill="#3b3b3b" '
          f'stroke="#1c1c1c"/>')
        A(f'<rect x="{cx-el_w/2-4:.1f}" y="{y_el_top+16}" width="{el_w+8:.1f}" '
          f'height="16" rx="3" fill="#b08d57" stroke="#7d6337"/>')
        # brush arc
        A(f'<ellipse cx="{cx:.1f}" cy="{tip-gap/2:.1f}" rx="{el_w*0.95:.1f}" '
          f'ry="{gap*0.95:.1f}" fill="url(#arcg)" opacity="0.95"/>')
        A(f'<text x="{cx:.1f}" y="{y_el_top-7}" font-size="9.5" '
          f'text-anchor="middle" fill="#12263a">E{k+1}</text>')
    A(f'<text x="{x0}" y="{shell_bot+112}" font-size="10.5" fill="#5c6b7a">'
      f'{n_el} &#215; Soderberg electrodes, {_fmt(g("electrode_dia_m",1.7),2)} m dia '
      f'&#183; immersion {imm:.2f} m &#183; brush arc {arc*1000:.0f} mm '
      f'&#183; {_fmt(g("current_kA",78))} kA at {_fmt(g("voltage_V",430),0)} V</text>')

    # ---- feed pile ------------------------------------------------------
    pw = max(48.0, min(span * 0.42, 30.0 + pile_t * 6.0))
    px = inner_l + span * 0.30
    ph = max(16.0, min(58.0, 10.0 + pile_t * 2.0))
    A(f'<path d="M{px-pw/2:.0f} {y_slag_top} Q {px:.0f} {y_slag_top-ph:.0f} '
      f'{px+pw/2:.0f} {y_slag_top} Z" fill="#6b6257" stroke="#463f36"/>')
    A(f'<text x="{px:.0f}" y="{y_slag_top-ph-6:.0f}" font-size="10" '
      f'text-anchor="middle" fill="#e8eef4">feed pile {pile_t:.1f} t '
      f'&#183; {T_p:.0f} &#176;C</text>')

    # ---- feed chutes ----------------------------------------------------
    feeds = [("DRI / HBI", g("dri_feed_t_h", 160.0), "t/h", 0.16),
             ("Carbon", g("carbon_feed_t_h", 8.8), "t/h", 0.30),
             ("Flux", g("flux_feed_t_h", 17.4), "t/h", 0.44)]
    for i, (nm, v, u, fx) in enumerate(feeds):
        cx = inner_l + span * fx
        y_lbl = 74 + i * 15
        A(f'<line x1="{cx:.0f}" y1="{y_lbl+4}" x2="{cx:.0f}" '
          f'y2="{shell_top-4}" stroke="#1f4e79" stroke-width="3" '
          f'marker-end="url(#ar)"/>')
        A(f'<text x="{cx+8:.0f}" y="{y_lbl}" font-size="10" '
          f'fill="#1f4e79">{nm} &#183; {_fmt(v)} {u}</text>')

    # ---- off-gas --------------------------------------------------------
    A(f'<line x1="{inner_r-40}" y1="{shell_top-4}" x2="{inner_r-40}" y2="72" '
      f'stroke="#c1121f" stroke-width="3" marker-end="url(#ar2)"/>')
    A(f'<text x="{inner_r-150}" y="66" font-size="10" fill="#c1121f">'
      f'Off-gas {_fmt(g("offgas_Nm3_h", 14000), 0)} Nm&#179;/h &#183; '
      f'{T_g:.0f} &#176;C</text>')

    # ---- tap holes ------------------------------------------------------
    A(f'<rect x="{x1-6}" y="{y_metal_top+h_metal*0.45:.0f}" width="34" '
      f'height="12" fill="#8a4b12" stroke="#4d2a08"/>')
    A(f'<line x1="{x1+28}" y1="{y_metal_top+h_metal*0.51:.0f}" x2="{x1+62}" '
      f'y2="{y_metal_top+h_metal*0.51+24:.0f}" stroke="#ffb347" '
      f'stroke-width="6" stroke-linecap="round"/>')
    A(f'<text x="{x1+2}" y="{y_metal_top+h_metal*0.51+56:.0f}" font-size="10" '
      f'fill="#8a4b12">Metal tap-hole</text>')
    A(f'<rect x="{x0-28}" y="{y_slag_top+h_slag*0.35:.0f}" width="34" '
      f'height="12" fill="#7a3a2a" stroke="#40190f"/>')
    A(f'<line x1="{x0-28}" y1="{y_slag_top+h_slag*0.41:.0f}" x2="{x0-96}" '
      f'y2="{y_slag_top+h_slag*0.41+34:.0f}" stroke="#e07a5f" '
      f'stroke-width="6" stroke-linecap="round"/>')
    A(f'<text x="{x0-96}" y="{y_slag_top+h_slag*0.41-8:.0f}" font-size="10" '
      f'fill="#7a3a2a">Slag tap-hole</text>')

    # ---- cooling / heat-loss arrows -------------------------------------
    # Set on two short lines inside the drawing area.  A single long label
    # ran under the KPI panel and was clipped.
    A(f'<text x="{x1+12}" y="{shell_top+4}" font-size="10" fill="#2a9d8f">'
      f'Water-cooled</text>')
    A(f'<text x="{x1+12}" y="{shell_top+16}" font-size="10" fill="#2a9d8f">'
      f'panels</text>')
    for yy in (shell_top + 34, shell_top + 74, shell_top + 114):
        A(f'<line x1="{x1+4}" y1="{yy}" x2="{x1+52}" y2="{yy}" '
          f'stroke="#2a9d8f" stroke-width="2.4" marker-end="url(#ar)"/>')
    A(f'<text x="{x1+12}" y="{shell_top+134}" font-size="10" fill="#2a9d8f">'
      f'{_fmt(g("heat_loss_MW", 30.0))} MW</text>')

    # ---- lining legend ---------------------------------------------------
    lay = [("Steel shell", "#cfd6dd"), ("Safety lining", "#e6ded2"),
           ("Working refractory", "#d9c7ad"), ("Freeze lining", "#9fb8c8")]
    for i, (nm, col) in enumerate(lay):
        yy = shell_bot + 24 + (i % 2) * 17
        xoff = (i // 2) * 190
        A(f'<rect x="{x0+xoff}" y="{yy-10}" width="14" height="11" '
          f'fill="{col}" stroke="#8c99a6"/>')
        A(f'<text x="{x0+xoff+22}" y="{yy}" font-size="10" '
          f'fill="#3c4a57">{nm}</text>')

    # ---- KPI panel -------------------------------------------------------
    panel_x = 946
    A(f'<rect x="{panel_x}" y="104" width="212" height="534" rx="10" '
      f'fill="#ffffff" stroke="#d5dbe1"/>')
    A(f'<text x="{panel_x+14}" y="128" font-size="12.5" font-weight="700" '
      f'fill="#12263a">LIVE KPIs</text>')
    kpi = [
        ("Active power", f'{_fmt(g("power_MW", 101))} MW'),
        ("Slag Joule", f'{_fmt(g("P_slag_MW", 62))} MW'),
        ("Brush arc", f'{_fmt(g("P_arc_MW", 32))} MW'),
        ("Current", f'{_fmt(g("current_kA", 78))} kA'),
        ("Tap voltage", f'{_fmt(g("voltage_V", 430), 0)} V'),
        ("Lining loss", f'{_fmt(g("heat_loss_MW", 30))} MW'),
        ("SEC", f'{_fmt(g("SEC_kWh_t", 698), 0)} kWh/tHM'),
        ("Slag rate", f'{_fmt(g("slag_rate_kg_t", 278), 0)} kg/tHM'),
        ("[C]", f'{_fmt(g("C_pct", 3.4), 2)} wt%'),
        ("[Si]", f'{_fmt(g("Si_pct", 0.33), 3)} wt%'),
        ("[Mn]", f'{_fmt(g("Mn_pct", 0.52), 3)} wt%'),
        ("[P]", f'{_fmt(g("P_pct", 0.05), 3)} wt%'),
        ("[S]", f'{_fmt(g("S_pct", 0.01), 3)} wt%'),
        ("(FeO)", f'{_fmt(g("FeO_pct", 1.9), 2)} wt%'),
        ("(SiO2)", f'{_fmt(g("SiO2_pct", 36), 1)} wt%'),
        ("(CaO)", f'{_fmt(g("CaO_pct", 38), 1)} wt%'),
        ("(Al2O3)", f'{_fmt(g("Al2O3_pct", 13.5), 1)} wt%'),
        ("(MgO)", f'{_fmt(g("MgO_pct", 8), 1)} wt%'),
        ("Shell T max", f'{_fmt(g("shell_T_C", 190), 0)} &#176;C'),
        ("Hot face", f'{_fmt(g("hotface_C", 1400), 0)} &#176;C'),
        ("Freeboard T", f'{_fmt(T_g, 0)} &#176;C'),
        ("Feed pile", f'{_fmt(pile_t, 1)} t'),
    ]
    for i, (k, v) in enumerate(kpi):
        yy = 152 + i * 21.5
        A(f'<text x="{panel_x+14}" y="{yy:.0f}" font-size="10.5" '
          f'fill="#5c6b7a">{k}</text>')
        A(f'<text x="{panel_x+198}" y="{yy:.0f}" font-size="10.5" '
          f'font-weight="600" text-anchor="end" fill="#12263a">{v}</text>')

    # ---- alarm banner ----------------------------------------------------
    if alarm:
        A(f'<rect x="26" y="{H-48}" width="{W-52}" height="34" rx="7" '
          f'fill="#fdecec" stroke="#c1121f"/>')
        A(f'<text x="42" y="{H-26}" font-size="12" font-weight="600" '
          f'fill="#c1121f">&#9888; {alarm}</text>')
    else:
        A(f'<rect x="26" y="{H-48}" width="{W-52}" height="34" rx="7" '
          f'fill="#eef7f2" stroke="#2a9d8f"/>')
        A(f'<text x="42" y="{H-26}" font-size="12" fill="#1d6f63">'
          f'All monitored variables inside the operating window.</text>')

    # ---- dimension callouts ---------------------------------------------
    A(f'<text x="{x0}" y="{shell_bot+96}" font-size="10.5" fill="#5c6b7a">'
      f'Hearth {_fmt(g("length_m",35),1)} m &#215; {_fmt(g("width_m",11),1)} m '
      f'&#183; slag depth {s_depth:.2f} m &#183; metal depth {m_depth:.2f} m '
      f'&#183; freeze lining {frz:.0f} mm</text>')
    A('</svg>')
    return "".join(p)


def svg_data_uri(svg: str) -> str:
    import base64
    return "data:image/svg+xml;base64," + \
        base64.b64encode(svg.encode("utf-8")).decode("ascii")


def state_from_static(res: Dict, geo=None) -> Dict:
    """Map a static-model result onto the schematic state dictionary."""
    k = res.get("KPI", {})
    hm = res.get("hot_metal_wt_pct", {})
    sl = res.get("slag_wt_pct", {})
    el = res.get("electrical", {})
    hl = res.get("heat_loss") or {}
    t = res.get("temperatures_C", {})
    z = (hl.get("zones") or {}).get("slag_wall", {})
    return dict(
        T_metal_C=t.get("Hot metal tap", 1500), T_slag_C=t.get("Slag", 1560),
        T_gas_C=t.get("Off-gas", 1500), T_pile_C=t.get("DRI feed", 600),
        m_metal_t=res.get("outputs_kg", {}).get("Hot metal", 1035) / 1000.0,
        m_slag_t=res.get("outputs_kg", {}).get("Slag", 280) / 1000.0,
        m_pile_t=0.0,
        power_MW=k.get("Power_demand_MW", 0.0),
        P_slag_MW=el.get("P_slag_joule_MW", 0.0),
        P_arc_MW=el.get("P_arc_MW", 0.0),
        current_kA=el.get("current_A", 0.0) / 1000.0,
        voltage_V=el.get("tap_voltage_V", 0.0),
        heat_loss_MW=(hl.get("Q_total_W", 0.0) or 0.0) / 1e6,
        SEC_kWh_t=k.get("SEC_operating_kWh_tHM", 0.0),
        slag_rate_kg_t=k.get("Slag_rate_kg_tHM", 0.0),
        # tapping rates, distinct from the liquid inventories above
        metal_rate_t_h=k.get("Productivity_tHM_h", 0.0),
        slag_rate_t_h=k.get("Productivity_tHM_h", 0.0)
        * k.get("Slag_rate_kg_tHM", 0.0) / 1000.0,
        C_pct=hm.get("C", 0), Si_pct=hm.get("Si", 0), Mn_pct=hm.get("Mn", 0),
        P_pct=hm.get("P", 0), S_pct=hm.get("S", 0),
        FeO_pct=sl.get("FeO", 0), SiO2_pct=sl.get("SiO2", 0),
        CaO_pct=sl.get("CaO", 0), Al2O3_pct=sl.get("Al2O3", 0),
        MgO_pct=sl.get("MgO", 0),
        B2=res.get("slag_properties", {}).get("B2 (CaO/SiO2)", 1.1),
        freeze_mm=(hl.get("freeze_thickness_m", 0.075) or 0.075) * 1000.0,
        shell_T_C=(hl.get("T_shell_max_K", 460) or 460) - 273.15,
        hotface_C=(z.get("T_hotface_K", 1673) or 1673) - 273.15,
        n_electrodes=getattr(geo, "n_electrodes", 6) if geo else 6,
        immersion_m=getattr(geo, "electrode_immersion", 0.45) if geo else 0.45,
        arc_length_m=getattr(geo, "arc_length", 0.09) if geo else 0.09,
        slag_depth_m=getattr(geo, "slag_depth", 1.35) if geo else 1.35,
        metal_depth_m=getattr(geo, "metal_depth", 0.90) if geo else 0.90,
        length_m=getattr(geo, "length", 35.0) if geo else 35.0,
        width_m=getattr(geo, "width", 11.0) if geo else 11.0,
    )


def state_from_dynamic(traj: Dict, idx: int = -1, geo=None,
                       alarm: str = "") -> Dict:
    def v(k, d=0.0):
        try:
            return traj[k][idx]
        except Exception:
            return d
    st = dict(
        T_metal_C=v("T_metal_C", 1500), T_slag_C=v("T_slag_C", 1560),
        T_gas_C=v("T_gas_C", 1700), T_pile_C=v("T_pile_C", 520),
        m_metal_t=v("m_metal_t", 450), m_slag_t=v("m_slag_t", 210),
        m_pile_t=v("m_pile_t", 11), power_MW=v("power_MW", 101),
        P_slag_MW=v("P_slag_MW", 62), P_arc_MW=v("P_arc_MW", 32),
        current_kA=v("current_kA", 78), voltage_V=v("voltage_V", 430),
        immersion_m=v("immersion_m", 0.45),
        heat_loss_MW=v("heat_loss_MW", 30), SEC_kWh_t=v("SEC_cum_kWh_t", 700),
        slag_rate_kg_t=v("slag_rate_kg_t", 278),
        # Tapping rates derived from the cumulative tapped masses over the
        # elapsed campaign time, so that the figure states a production rate
        # as well as the liquid inventories held in the furnace.
        metal_rate_t_h=v("metal_tapped_t", 0.0) / max(v("t_min", 60.0) / 60.0,
                                                      1e-6),
        slag_rate_t_h=v("slag_tapped_t", 0.0) / max(v("t_min", 60.0) / 60.0,
                                                    1e-6),
        C_pct=v("C_pct", 3.4), Si_pct=v("Si_pct", 0.25),
        Mn_pct=v("Mn_pct", 0.52), P_pct=v("P_pct", 0.05),
        S_pct=v("S_pct", 0.01), FeO_pct=v("FeO_pct", 1.9),
        SiO2_pct=v("SiO2_pct", 36), CaO_pct=v("CaO_pct", 38),
        Al2O3_pct=v("Al2O3_pct", 13.5), MgO_pct=v("MgO_pct", 8),
        B2=v("B2", 1.1), freeze_mm=v("freeze_mm", 75),
        shell_T_C=v("shell_T_C", 190), hotface_C=v("hotface_slagwall_C", 1400),
        offgas_Nm3_h=v("CO_Nm3_h", 14000),
        dri_feed_t_h=v("dri_feed_t_h", 160),
        flux_feed_t_h=v("flux_feed_t_h", 17),
        carbon_feed_t_h=v("carbon_feed_t_h", 8.8),
        alarm=alarm,
    )
    if geo is not None:
        st.update(n_electrodes=geo.n_electrodes, arc_length_m=geo.arc_length,
                  slag_depth_m=geo.slag_depth, metal_depth_m=geo.metal_depth,
                  length_m=geo.length, width_m=geo.width)
    return st


__all__ = ["furnace_svg", "svg_data_uri", "state_from_static",
           "state_from_dynamic"]
