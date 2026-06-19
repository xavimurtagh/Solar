"""Publication-quality figures for the report.

The Agg backend is forced before importing pyplot so the figures render in a
headless environment and the whole report regenerates deterministically.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from . import constants as C  # noqa: E402
from .sq import loss_fractions, optimal_bandgap, sq_cell, sq_curve  # noqa: E402

# A calm, colour-blind-friendly palette.
_BLUE, _ORANGE, _GREEN, _RED, _PURPLE, _GREY = (
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#7f7f7f")


def _style():
    plt.rcParams.update({
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
    })


def _outdir(outdir: str | Path) -> Path:
    p = Path(outdir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def fig1_sq_limit(spec, outdir: str | Path) -> Path:
    """Efficiency vs bandgap (left) and the loss decomposition (right)."""
    _style()
    df = sq_curve(spec, 0.5, 2.3, 0.005)
    opt = optimal_bandgap(spec)
    from .sq import optimal_tandem
    tandem = optimal_tandem(spec)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # --- (a) the famous SQ curve --------------------------------------------
    ax1.plot(df["eg_ev"], df["eta"] * 100, color=_BLUE, lw=2)
    ax1.axhline(tandem["eta"] * 100, ls="--", color=_PURPLE, lw=1.2,
                label=f"2-junction tandem limit ({tandem['eta']*100:.0f}%)")
    ax1.scatter([opt.eg_ev], [opt.eta * 100], color=_RED, zorder=5)
    ax1.annotate(f"peak {opt.eta*100:.1f}% @ {opt.eg_ev:.2f} eV",
                 (opt.eg_ev, opt.eta * 100), textcoords="offset points",
                 xytext=(8, -4), fontsize=9)
    materials = {"Si": C.SI_EG_EV, "CdTe": C.CDTE_EG_EV,
                 "GaAs": C.GAAS_EG_EV, "Perovskite": C.PEROVSKITE_EG_EV}
    for name, eg in materials.items():
        e = sq_cell(eg, spec).eta * 100
        ax1.scatter([eg], [e], color=_GREEN, s=25, zorder=4)
        ax1.annotate(name, (eg, e), textcoords="offset points",
                     xytext=(3, 6), fontsize=8, color=_GREEN)
    ax1.set_xlabel("Bandgap energy (eV)")
    ax1.set_ylabel("Maximum efficiency (%)")
    ax1.set_title("(a) The Shockley-Queisser limit")
    ax1.set_ylim(0, 50)
    ax1.legend(loc="lower center", fontsize=8)

    # --- (b) where every photon's energy goes -------------------------------
    egs = np.linspace(0.6, 2.2, 200)
    keys = ["below_gap", "thermalisation", "voltage_boltzmann",
            "fill_factor", "extracted"]
    labels = ["Sub-bandgap (transmitted)", "Thermalisation (heat)",
              "Voltage / thermodynamic", "Fill factor", "Extracted (useful)"]
    colors = [_GREY, _RED, _ORANGE, _PURPLE, _GREEN]
    stacks = {k: np.array([loss_fractions(e, spec)[k] for e in egs]) * 100
              for k in keys}
    ax2.stackplot(egs, *[stacks[k] for k in keys], labels=labels, colors=colors,
                  alpha=0.85)
    ax2.axvline(C.SI_EG_EV, color="k", ls=":", lw=1)
    ax2.annotate("Si", (C.SI_EG_EV, 4), fontsize=8)
    ax2.set_xlabel("Bandgap energy (eV)")
    ax2.set_ylabel("Share of incident energy (%)")
    ax2.set_title("(b) Where the sunlight goes")
    ax2.set_xlim(0.6, 2.2)
    ax2.set_ylim(0, 100)
    ax2.legend(loc="upper right", fontsize=7.5)

    fig.suptitle("Why a single-junction cell cannot beat ~34%", fontsize=13)
    fig.tight_layout()
    path = _outdir(outdir) / "fig1_sq_limit.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig2_waterfall(waterfall_df, outdir: str | Path) -> Path:
    """A descending step chart from incident sunlight to delivered AC energy."""
    _style()
    df = waterfall_df.reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(df))
    eta = df["eta_pct"].values

    # Floating bars showing the drop from one rung to the next.
    for i in range(1, len(df)):
        ax.bar(x[i], eta[i - 1] - eta[i], bottom=eta[i], width=0.6,
               color=_RED, alpha=0.35)
    ax.bar(x[0], eta[0], width=0.6, color=_BLUE, alpha=0.7)
    ax.bar(x[-1], eta[-1], width=0.6, color=_GREEN, alpha=0.85)
    ax.plot(x, eta, "o-", color="k", lw=1.2, ms=5)

    for i in range(len(df)):
        ax.annotate(f"{eta[i]:.1f}%", (x[i], eta[i]), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=9, fontweight="bold")
    for i in range(1, len(df)):
        drop = eta[i - 1] - eta[i]
        ax.annotate(f"-{drop:.1f}", (x[i], (eta[i] + eta[i - 1]) / 2),
                    ha="center", fontsize=7.5, color=_RED)

    ax.set_xticks(x)
    ax.set_xticklabels(df["stage"], rotation=30, ha="right", fontsize=8.5)
    ax.set_ylabel("Efficiency (% of incident energy)")
    ax.set_title("From sunlight to wall socket: the silicon efficiency waterfall")
    ax.set_ylim(0, 105)
    fig.tight_layout()
    path = _outdir(outdir) / "fig2_waterfall.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig3_history(milestones, market, outdir: str | Path) -> Path:
    """Record cells by technology over time, with the commercial module line."""
    _style()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    cells = milestones[milestones["kind"] == "cell"]
    markers = {"Silicon": "o", "GaAs": "s", "CdTe": "^", "Perovskite": "D",
               "Perovskite-Si tandem": "P", "III-V multijunction": "*"}
    for tech, g in cells.groupby("technology"):
        g = g.sort_values("year")
        ax.plot(g["year"], g["efficiency_pct"], marker=markers.get(tech, "o"),
                label=tech, lw=1.5, ms=7)

    ax.plot(market["year"], market["avg_module_eff_pct"], "k--o", lw=1.5,
            ms=4, label="Commercial module average", alpha=0.7)

    # A few defining annotations.
    notes = [(1954, 6.0, "Bell Labs\nfirst cell"),
             (2022, 47.6, "Fraunhofer 47.6%\n(concentrator)"),
             (2025, 35.0, "Perovskite-Si\ntandem 35%")]
    for yr, eff, txt in notes:
        ax.annotate(txt, (yr, eff), textcoords="offset points", xytext=(6, -6),
                    fontsize=7.5, color=_GREY)

    ax.axhspan(0, 0, color="none")
    ax.set_xlabel("Year")
    ax.set_ylabel("Record efficiency (%)")
    ax.set_title("Seventy years of solar efficiency records")
    ax.set_ylim(0, 50)
    ax.legend(loc="center left", fontsize=8, ncol=1)
    fig.tight_layout()
    path = _outdir(outdir) / "fig3_history.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig4_levers(levers_df, outdir: str | Path) -> Path:
    """Ranked horizontal bars of annual-energy improvement per lever."""
    _style()
    df = levers_df.sort_values("delta_pct")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [_GREEN if "tandem" in n.lower() or "HJT" in n or "TOPCon" in n
              else _BLUE for n in df["lever"]]
    ax.barh(df["lever"], df["delta_pct"], color=colors, alpha=0.85)
    for y, v in enumerate(df["delta_pct"]):
        ax.annotate(f"+{v:.1f}%", (v, y), textcoords="offset points",
                    xytext=(4, 0), va="center", fontsize=8.5)
    ax.set_xlabel("Annual AC energy gain vs reference PERC rooftop (%)")
    ax.set_title("How to actually improve a deployed system (ranked)")
    ax.margins(x=0.12)
    fig.tight_layout()
    path = _outdir(outdir) / "fig4_levers.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig5_seasonal(monthly, outdir: str | Path) -> Path:
    """Monthly energy (left) and the temperature penalty (right)."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    months = monthly.index
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    ax1.bar(months, monthly["e_ac_kwh"], color=_ORANGE, alpha=0.85)
    ax1.set_xticks(months)
    ax1.set_xticklabels(names, fontsize=8)
    ax1.set_ylabel("AC energy (kWh)")
    ax1.set_title("(a) Monthly energy yield")

    ax2.plot(months, monthly["mean_temp_cell_c"], "o-", color=_RED, label="Cell")
    ax2.plot(months, monthly["mean_temp_air_c"], "s--", color=_BLUE, label="Air")
    ax2.set_xticks(months)
    ax2.set_xticklabels(names, fontsize=8)
    ax2.set_ylabel("Mean temperature (degC)")
    ax2.set_title("(b) Heat is the system's enemy")
    ax2b = ax2.twinx()
    ax2b.plot(months, monthly["temp_loss_pct"], "^:", color=_GREY,
              label="Temp. loss %")
    ax2b.set_ylabel("Temperature loss (%)")
    ax2b.grid(False)
    lines = ax2.get_lines() + ax2b.get_lines()
    ax2.legend(lines, [l.get_label() for l in lines], fontsize=8, loc="upper left")

    fig.tight_layout()
    path = _outdir(outdir) / "fig5_seasonal.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part II: economics, space, and materials
# ---------------------------------------------------------------------------

def fig6_lcoe(cost_stacks: dict, lcoe_by_deployment: dict,
              outdir: str | Path) -> Path:
    """Cost stack (left) and resulting LCOE vs the Lazard band (right)."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    deployments = list(cost_stacks.keys())
    components = list(next(iter(cost_stacks.values())).index)
    comp_colors = [_BLUE, _ORANGE, _GREEN, _PURPLE, _RED, _GREY][:len(components)]
    bottom = np.zeros(len(deployments))
    for comp, col in zip(components, comp_colors):
        vals = np.array([cost_stacks[d][comp] for d in deployments])
        ax1.bar(deployments, vals, bottom=bottom, label=comp.replace("_", " "),
                color=col, alpha=0.85)
        bottom += vals
    for i, d in enumerate(deployments):
        ax1.annotate(f"${bottom[i]:.2f}/W", (i, bottom[i]),
                     textcoords="offset points", xytext=(0, 4), ha="center",
                     fontsize=9, fontweight="bold")
    ax1.set_ylabel("Installed cost ($/W)")
    ax1.set_title("(a) Where the money goes")
    ax1.legend(fontsize=7.5, loc="upper left")

    lc = [lcoe_by_deployment[d] * 1000 for d in deployments]
    bars = ax2.bar(deployments, lc, color=[_GREEN, _ORANGE, _RED], alpha=0.85)
    ax2.axhspan(38, 78, color=_BLUE, alpha=0.12,
                label="Lazard 2025 utility range\n($38-78/MWh)")
    for b, v in zip(bars, lc):
        ax2.annotate(f"${v:.0f}", (b.get_x() + b.get_width() / 2, v),
                     textcoords="offset points", xytext=(0, 4), ha="center",
                     fontsize=9, fontweight="bold")
    ax2.set_ylabel("LCOE ($/MWh)")
    ax2.set_title("(b) Levelised cost of energy")
    ax2.legend(fontsize=8)

    fig.suptitle("Energy per dollar depends far more on where than on which cell",
                 fontsize=13)
    fig.tight_layout()
    path = _outdir(outdir) / "fig6_lcoe.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig7_frontier(frontier_df, outdir: str | Path) -> Path:
    """Cost vs space vs scale: the multi-objective frontier.

    x = LCOE (cheaper is better, left), y = energy density (denser is better,
    up), bubble area = deployment ceiling (TW/yr). The Pareto front for cost-vs-
    space is traced; bubble size exposes the scale tension.
    """
    _style()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    techs = frontier_df["technology"].unique()
    cmap = {t: c for t, c in zip(techs, [_BLUE, _ORANGE, _GREEN, _PURPLE])}
    markers = {"utility": "o", "commercial": "s", "residential": "^"}

    for _, r in frontier_df.iterrows():
        size = 40 + r["tw_per_year"] * 600          # bubble area ~ scaling ceiling
        ax.scatter(r["lcoe_usd_mwh"], r["energy_density_kwh_m2_yr"],
                   s=size, color=cmap[r["technology"]],
                   marker=markers[r["deployment"]], alpha=0.7,
                   edgecolors="k", linewidths=0.5)

    pareto = frontier_df[frontier_df["pareto"]].sort_values("lcoe_usd_mwh")
    ax.plot(pareto["lcoe_usd_mwh"], pareto["energy_density_kwh_m2_yr"],
            "k--", lw=1, alpha=0.6, label="Pareto front (cost vs space)")

    # Legends: colour = technology, marker = deployment, bubble = ceiling.
    from matplotlib.lines import Line2D
    tech_handles = [Line2D([0], [0], marker="o", color="w", label=t,
                           markerfacecolor=cmap[t], markersize=9) for t in techs]
    dep_handles = [Line2D([0], [0], marker=m, color="w", label=d,
                          markerfacecolor=_GREY, markersize=9)
                   for d, m in markers.items()]
    leg1 = ax.legend(handles=tech_handles, title="Technology", fontsize=8,
                     loc="upper right")
    ax.add_artist(leg1)
    ax.legend(handles=dep_handles, title="Deployment", fontsize=8,
              loc="lower right")

    ax.set_xlabel("LCOE ($/MWh)  -  energy per dollar (<- cheaper is better)")
    ax.set_ylabel("Energy density (kWh/m²/yr)  -  space efficiency (better ->)")
    ax.set_title("Bubble size = how far it can scale (TW/yr). The cost/space "
                 "winner is scale-limited.")
    fig.tight_layout()
    path = _outdir(outdir) / "fig7_frontier.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig8_ceiling(ceiling_df, net_zero_tw: float, outdir: str | Path) -> Path:
    """The terawatt ceiling: max annual deployment per technology (log scale)."""
    _style()
    fig, ax = plt.subplots(figsize=(11, 6))
    df = ceiling_df.sort_values("tw_per_year")
    colors = [_RED if scarce else _GREEN for scarce in df["binding_is_scarce"]]
    bars = ax.barh(df["technology"], df["tw_per_year"], color=colors, alpha=0.85)
    ax.set_xscale("log")
    for b, (_, r) in zip(bars, df.iterrows()):
        ax.annotate(f"{r['tw_per_year']:.3g} TW/yr  (limited by {r['binding_element']})",
                    (r["tw_per_year"], b.get_y() + b.get_height() / 2),
                    textcoords="offset points", xytext=(6, 0), va="center",
                    fontsize=8.5)
    ax.axvline(net_zero_tw, color="k", ls="--", lw=1.3)
    ax.annotate(f"~{net_zero_tw:.0f} TW/yr\nneeded for net zero",
                (net_zero_tw, 0.2), textcoords="offset points", xytext=(4, 0),
                fontsize=8, color="k")

    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=_RED, alpha=0.85, label="Limited by a scarce element"),
                       Patch(color=_GREEN, alpha=0.85, label="Limited only by (scalable) production")],
              fontsize=8, loc="lower right")
    ax.set_xlabel("Maximum annual deployment (TW/yr, log scale; 50% of world supply)")
    ax.set_title("The terawatt ceiling: which solar materials can actually scale")
    ax.margins(x=0.25)
    fig.tight_layout()
    path = _outdir(outdir) / "fig8_ceiling.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig9_substitution(effects: list, outdir: str | Path) -> Path:
    """Before/after ceiling and material cost for key element substitutions."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5))
    labels = [f"{e['technology']}\n{_swap_label(e['swaps'])}" for e in effects]
    x = np.arange(len(effects))
    w = 0.38

    before_tw = [e["tw_per_year_before"] for e in effects]
    after_tw = [e["tw_per_year_after"] for e in effects]
    ax1.bar(x - w / 2, before_tw, w, label="Before", color=_RED, alpha=0.75)
    ax1.bar(x + w / 2, after_tw, w, label="After", color=_GREEN, alpha=0.85)
    ax1.set_yscale("log")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=8)
    ax1.set_ylabel("Deployment ceiling (TW/yr, log)")
    ax1.set_title("(a) Substitution shatters the scale ceiling")
    for i, e in enumerate(effects):
        ax1.annotate(f"x{e['ceiling_multiplier']:.0f}",
                     (i + w / 2, e["tw_per_year_after"]),
                     textcoords="offset points", xytext=(0, 3), ha="center",
                     fontsize=8, fontweight="bold")
    ax1.legend(fontsize=8)

    before_c = [e["material_cost_before"] * 1000 for e in effects]
    after_c = [e["material_cost_after"] * 1000 for e in effects]
    ax2.bar(x - w / 2, before_c, w, label="Before", color=_RED, alpha=0.75)
    ax2.bar(x + w / 2, after_c, w, label="After", color=_GREEN, alpha=0.85)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=8)
    ax2.set_ylabel("Raw material cost ($/kW)")
    ax2.set_title("(b) ...and usually cuts material cost too")
    ax2.legend(fontsize=8)

    fig.suptitle("Replacing scarce elements with abundant ones", fontsize=13)
    fig.tight_layout()
    path = _outdir(outdir) / "fig9_substitution.png"
    fig.savefig(path)
    plt.close(fig)
    return path


_SYMBOL = {"Silver": "Ag", "Copper": "Cu", "Indium": "In", "Zinc": "Zn",
           "Lead": "Pb", "Tin": "Sn", "Tellurium": "Te", "Silicon": "Si"}


def _swap_label(swaps: dict) -> str:
    return ", ".join(f"{_SYMBOL.get(k, k)}->{_SYMBOL.get(v, v)}"
                     for k, v in swaps.items())


def fig10_sensitivity(sensitivity_df, mc_samples, outdir: str | Path) -> Path:
    """LCOE sensitivity tornado (left) and Monte-Carlo distribution (right)."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    base = float(sensitivity_df["base"].iloc[0]) * 1000

    y = np.arange(len(sensitivity_df))
    for i, (_, r) in enumerate(sensitivity_df.iterrows()):
        lo, hi = r["low"] * 1000, r["high"] * 1000
        ax1.barh(i, hi - lo, left=min(lo, hi), color=_BLUE, alpha=0.7)
    ax1.axvline(base, color="k", ls="--", lw=1.2, label=f"base ${base:.0f}/MWh")
    ax1.set_yticks(y)
    ax1.set_yticklabels(sensitivity_df["driver"], fontsize=9)
    ax1.set_xlabel("LCOE ($/MWh)")
    ax1.set_title("(a) What moves LCOE most")
    ax1.legend(fontsize=8)

    mc = np.asarray(mc_samples) * 1000
    p10, p50, p90 = np.percentile(mc, [10, 50, 90])
    ax2.hist(mc, bins=60, color=_GREEN, alpha=0.7)
    for p, lab in [(p10, "P10"), (p50, "P50"), (p90, "P90")]:
        ax2.axvline(p, color="k", ls=":", lw=1)
        ax2.annotate(f"{lab}\n${p:.0f}", (p, ax2.get_ylim()[1] * 0.82),
                     ha="center", fontsize=7.5)
    ax2.set_xlabel("LCOE ($/MWh)")
    ax2.set_ylabel("Monte-Carlo frequency")
    ax2.set_title("(b) Uncertainty in utility-scale LCOE")

    fig.tight_layout()
    path = _outdir(outdir) / "fig10_sensitivity.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part III: circularity and the urban mine
# ---------------------------------------------------------------------------

def fig11_urban_mine(flow_df, outdir: str | Path) -> Path:
    """The global fleet over time: installs, in-field stock, and retirements."""
    _style()
    fig, ax = plt.subplots(figsize=(11, 6))
    yr = flow_df["year"].values

    ax.bar(yr, flow_df["annual_gw"], color=_BLUE, alpha=0.55,
           label="Annual installs (GW)")
    ax.fill_between(yr, flow_df["retired_gw"], color=_RED, alpha=0.55,
                    label="Annual retirements (GW) — the urban mine")
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual capacity (GW/yr)")

    ax2 = ax.twinx()
    ax2.plot(yr, flow_df["stock_gw"] / 1000.0, color="k", lw=2,
             label="In-field stock (TW)")
    ax2.set_ylabel("Installed fleet (TW)")
    ax2.grid(False)

    lines = ax.get_legend_handles_labels()
    lines2 = ax2.get_legend_handles_labels()
    ax.legend(lines[0] + lines2[0], lines[1] + lines2[1], fontsize=8.5,
              loc="upper left")
    ax.set_title("Every panel installed today is feedstock tomorrow")
    fig.tight_layout()
    path = _outdir(outdir) / "fig11_urban_mine.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig12_relaxed_ceiling(flows: dict, net_zero_tw: float, crossover_year,
                          outdir: str | Path) -> Path:
    """Linear vs recycling-relaxed deployment ceilings over time.

    ``flows`` maps a label (e.g. "Silicon (silver-limited)") to a material_flow
    DataFrame. The flat linear ceiling and the rising circular ceiling are drawn
    against the ~net-zero build-rate need.
    """
    _style()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    colors = [_BLUE, _PURPLE, _ORANGE]
    for (label, df), col in zip(flows.items(), colors):
        yr = df["year"].values
        ax.plot(yr, df["ceiling_linear_tw"], ls="--", color=col, lw=1.4, alpha=0.8,
                label=f"{label}: linear (mining only)")
        ax.plot(yr, df["ceiling_circular_tw"], ls="-", color=col, lw=2.2,
                label=f"{label}: + recycling")

    ax.axhline(net_zero_tw, color="k", ls=":", lw=1.4)
    ax.annotate(f"~{net_zero_tw:.0f} TW/yr needed for net zero",
                (flows[list(flows)[0]]["year"].min() + 1, net_zero_tw + 0.08),
                fontsize=8.5)
    if crossover_year:
        ax.axvline(crossover_year, color=_GREEN, ls="-.", lw=1.2)
        ax.annotate(f"silver >50%\nrecycled ({crossover_year})",
                    (crossover_year + 1, 0.3), fontsize=8, color=_GREEN)

    ax.set_xlabel("Year")
    ax.set_ylabel("Maximum deployment rate (TW/yr)")
    ax.set_title("Recycling turns the terawatt ceiling from a wall into a rising floor")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    path = _outdir(outdir) / "fig12_relaxed_ceiling.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig13_circularity(flow_frelp, flow_standard, virgin_avoided_t,
                      outdir: str | Path) -> Path:
    """(a) circularity ratio over time, FRELP vs standard; (b) virgin avoided."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    yr = flow_frelp["year"].values
    ax1.plot(yr, flow_frelp["circularity"] * 100, color=_GREEN, lw=2.2,
             label="High-value recycling (FRELP)")
    ax1.plot(yr, flow_standard["circularity"] * 100, color=_RED, lw=2.0, ls="--",
             label="Standard mechanical recycling")
    ax1.axhline(50, color="k", ls=":", lw=1)
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Silver demand met by recycling (%)")
    ax1.set_title("(a) Closing the silver loop")
    ax1.legend(fontsize=8, loc="upper left")

    # Cumulative virgin silver avoided (FRELP), tonnes -> cumulative curve.
    cum = flow_frelp["secondary_t"].cumsum()
    ax2.fill_between(yr, cum, color=_GREEN, alpha=0.5)
    ax2.plot(yr, cum, color=_GREEN, lw=2)
    ax2.annotate(f"{virgin_avoided_t/1000:,.0f} kt of virgin silver\navoided by {yr.max()}",
                 (yr.min() + 1, cum.iloc[-1] * 0.75), fontsize=9)
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Cumulative virgin silver avoided (t)")
    ax2.set_title("(b) Mining we never have to do")

    fig.suptitle("Standard recycling loses the silver; high-value recycling closes the loop",
                 fontsize=12)
    fig.tight_layout()
    path = _outdir(outdir) / "fig13_circularity.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part IV: land use — dual-use and grid-value siting
# ---------------------------------------------------------------------------

def fig14_landuse(land_df, outdir: str | Path) -> Path:
    """Land Equivalent Ratio: energy + crop yield stacked, vs the LER=1 line."""
    _style()
    fig, ax = plt.subplots(figsize=(10, 6))
    df = land_df.sort_values("ler")
    y = np.arange(len(df))
    ax.barh(y, df["energy_fraction"], color=_ORANGE, alpha=0.85, label="Energy yield")
    ax.barh(y, df["crop_fraction"], left=df["energy_fraction"], color=_GREEN,
            alpha=0.85, label="Retained crop yield")
    ax.axvline(1.0, color="k", ls="--", lw=1.3)
    ax.annotate("LER = 1\n(single-use breakeven)", (1.0, -0.45), fontsize=8)
    for i, (_, r) in enumerate(df.iterrows()):
        ax.annotate(f"LER {r['ler']:.2f}", (r["ler"], i), textcoords="offset points",
                    xytext=(5, 0), va="center", fontsize=9, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(df["archetype"])
    ax.set_xlabel("Land Equivalent Ratio (energy fraction + crop fraction)")
    ax.set_title("Dual-use can produce ~1.5-1.8x more per hectare than single use")
    ax.legend(fontsize=8.5, loc="lower right")
    ax.margins(x=0.14)
    fig.tight_layout()
    path = _outdir(outdir) / "fig14_landuse.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig15_diurnal(profile_df, outdir: str | Path) -> Path:
    """Average-day generation shape: fixed-optimal vs vertical east-west."""
    _style()
    fig, ax = plt.subplots(figsize=(10, 6))
    h = profile_df["hour"]
    ax.plot(h, profile_df["fixed_optimal"], "o-", color=_ORANGE, lw=2,
            label="Fixed optimal tilt (midday peak)")
    ax.plot(h, profile_df["vertical_ew"], "s-", color=_BLUE, lw=2,
            label="Vertical bifacial E-W (morning + evening peaks)")
    ax.axvspan(11, 14, color=_GREY, alpha=0.12)
    ax.annotate("midday solar glut\n(low value)", (12.5, 0.2), ha="center",
                fontsize=8, color=_GREY)
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Generation (fraction of own peak)")
    ax.set_title("Vertical east-west shifts power to when the grid needs it most")
    ax.set_xticks(range(0, 24, 3))
    ax.legend(fontsize=8.5, loc="upper center")
    fig.tight_layout()
    path = _outdir(outdir) / "fig15_diurnal.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part V: the techno-economic optimiser
# ---------------------------------------------------------------------------

def fig16_optimizer(scenarios: list, outdir: str | Path) -> Path:
    """Achievable annual energy per technology under different binding constraints.

    ``scenarios`` is a list of (title, ranked_df, winner_tech). Each panel shows
    that the optimal cell flips with the binding constraint.
    """
    _style()
    n = len(scenarios)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 5.5))
    if n == 1:
        axes = [axes]
    for ax, (title, ranked, winner) in zip(axes, scenarios):
        d = ranked.sort_values("annual_kwh")
        colors = [_GREEN if t == winner else _BLUE for t in d["technology"]]
        ax.barh(d["technology"], d["annual_kwh"], color=colors, alpha=0.85)
        for i, (_, r) in enumerate(d.iterrows()):
            ax.annotate(f"{r['annual_kwh']:,.0f}", (r["annual_kwh"], i),
                        textcoords="offset points", xytext=(4, 0), va="center",
                        fontsize=8)
        ax.set_xlabel("Achievable annual energy (kWh/yr)")
        ax.set_title(title)
        ax.margins(x=0.18)
    fig.suptitle("The optimal cell flips with the binding constraint",
                 fontsize=13)
    fig.tight_layout()
    path = _outdir(outdir) / "fig16_optimizer.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part VI: the pyrite voltage problem
# ---------------------------------------------------------------------------

def fig17_pyrite(sweep_df, markers, outdir: str | Path) -> Path:
    """Pyrite efficiency and Voc vs material quality (ERE), with key markers.

    ``markers`` is a list of (label, ere, eta, voc).
    """
    _style()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.plot(sweep_df["ere"], sweep_df["eta"] * 100, color=_BLUE, lw=2.5,
            label="Efficiency")
    ax.set_xscale("log")
    ax.set_xlabel("External radiative efficiency (ERE) — material quality →")
    ax.set_ylabel("Efficiency (%)", color=_BLUE)
    ax.tick_params(axis="y", labelcolor=_BLUE)

    ax2 = ax.twinx()
    ax2.plot(sweep_df["ere"], sweep_df["voc_v"], color=_ORANGE, lw=2, ls="--",
             label="Open-circuit voltage")
    ax2.set_ylabel("Voc (V)", color=_ORANGE)
    ax2.tick_params(axis="y", labelcolor=_ORANGE)
    ax2.grid(False)

    for label, ere, eta, voc in markers:
        ax.scatter([ere], [eta * 100], color=_RED, zorder=5, s=40)
        ax.annotate(f"{label}\n{eta*100:.0f}%", (ere, eta * 100),
                    textcoords="offset points", xytext=(0, 10), ha="center",
                    fontsize=8)
    ax.set_title("Pyrite's prize: cure the voltage and 'fool's gold' becomes a real cell")
    lines = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    labels = ["Efficiency", "Open-circuit voltage"]
    ax.legend(lines, labels, fontsize=9, loc="center left")
    fig.tight_layout()
    path = _outdir(outdir) / "fig17_pyrite.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part VII: the value of time
# ---------------------------------------------------------------------------

def fig18_value_deflation(value_df, outdir: str | Path) -> Path:
    """Value factor and curtailment vs solar penetration — the integration wall."""
    _style()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    p = value_df["penetration"] * 100
    ax.plot(p, value_df["value_factor"], "o-", color=_BLUE, lw=2.5,
            label="Value factor (capture price / average price)")
    ax.axhline(1.0, color=_GREY, ls=":", lw=1)
    ax.annotate("worth the average kWh", (1, 1.01), fontsize=8, color=_GREY)
    ax.set_xlabel("Solar share of annual demand (%)")
    ax.set_ylabel("Value factor", color=_BLUE)
    ax.tick_params(axis="y", labelcolor=_BLUE)
    ax.set_ylim(0, 1.25)

    ax2 = ax.twinx()
    ax2.fill_between(p, value_df["curtailment"] * 100, color=_RED, alpha=0.2)
    ax2.plot(p, value_df["curtailment"] * 100, color=_RED, lw=1.8, ls="--",
             label="Curtailment (% of solar spilled)")
    ax2.set_ylabel("Curtailment (%)", color=_RED)
    ax2.tick_params(axis="y", labelcolor=_RED)
    ax2.grid(False)

    # Annotate real-world markers.
    for share, lab in [(28, "California\n~today"), (45, "high-penetration\ngrid")]:
        ax.axvline(share, color="k", ls=":", lw=0.8, alpha=0.5)
        ax.annotate(lab, (share, 1.12), fontsize=7.5, ha="center", color="k")

    lines = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, fontsize=8.5, loc="upper right")
    ax.set_title("Solar eats its own lunch: each panel devalues the next at midday")
    fig.tight_layout()
    path = _outdir(outdir) / "fig18_value_deflation.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig19_duck_curve(day_low, day_high, pen_low, pen_high, outdir: str | Path) -> Path:
    """Average-day demand, solar, and price at low vs high penetration."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharex=True)
    for ax, day, pen in [(ax1, day_low, pen_low), (ax2, day_high, pen_high)]:
        h = day["hour"]
        ax.fill_between(h, day["demand"], color=_GREY, alpha=0.25, label="Demand")
        ax.plot(h, day["solar"], color=_ORANGE, lw=2, label="Solar")
        ax.plot(h, day["demand"] - day["solar"], color=_BLUE, lw=2, ls="--",
                label="Net load (the 'duck')")
        ax.set_xlabel("Hour of day")
        ax.set_title(f"{pen*100:.0f}% solar penetration")
        axp = ax.twinx()
        axp.plot(h, day["price"], color=_RED, lw=1.5, alpha=0.7)
        axp.set_ylabel("Price ($/MWh)", color=_RED, fontsize=9)
        axp.tick_params(axis="y", labelcolor=_RED)
        axp.grid(False)
        axp.set_ylim(-20, 220)
        ax.set_xticks(range(0, 24, 4))
    ax1.set_ylabel("Power (× mean demand)")
    ax1.legend(fontsize=8, loc="upper left")
    fig.suptitle("As solar grows, midday price collapses and the evening peak remains",
                 fontsize=12)
    fig.tight_layout()
    path = _outdir(outdir) / "fig19_duck_curve.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part VIII: firming the sun
# ---------------------------------------------------------------------------

def fig20_dispatch(week_df, outdir: str | Path) -> Path:
    """A 10-day slice of solar+battery dispatch serving a flat load."""
    _style()
    fig, ax = plt.subplots(figsize=(11, 6))
    h = week_df["hour"] / 24.0
    ax.fill_between(h, week_df["solar"], color=_ORANGE, alpha=0.5,
                    label="Solar generation")
    ax.axhline(1.0, color=_BLUE, lw=2, label="Flat 24/7 load")
    ax.set_xlabel("Day")
    ax.set_ylabel("Power (× mean load)")
    ax.set_ylim(0, max(3.0, week_df["solar"].max() * 1.1))

    ax2 = ax.twinx()
    ax2.plot(h, week_df["soc"], color=_GREEN, lw=2, label="Battery charge")
    ax2.set_ylabel("Battery state of charge (hours)", color=_GREEN)
    ax2.tick_params(axis="y", labelcolor=_GREEN)
    ax2.set_ylim(0, week_df["soc_max"].iloc[0] * 1.05)
    ax2.grid(False)

    lines = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    ax.legend(lines, [l.get_label() for l in lines], fontsize=8.5, loc="upper right")
    ax.set_title("Firming: the battery soaks up midday sun and releases it after dark")
    fig.tight_layout()
    path = _outdir(outdir) / "fig20_dispatch.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig21_firm_cost(moderate_df, high_df, refs: dict, outdir: str | Path) -> Path:
    """LCOSS vs reliability target, with fossil benchmarks — the cost of firmness."""
    _style()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.plot(moderate_df["reliability"] * 100, moderate_df["lcoss_usd_mwh"], "o-",
            color=_BLUE, lw=2.2, label="Firm solar+storage (moderate site)")
    ax.plot(high_df["reliability"] * 100, high_df["lcoss_usd_mwh"], "s-",
            color=_GREEN, lw=2.2, label="Firm solar+storage (high-resource site)")

    ax.axhline(refs["gas"], color=_RED, ls="--", lw=1.3, label=f"New gas (${refs['gas']:.0f})")
    ax.axhline(refs["coal"], color=_PURPLE, ls="--", lw=1.3, label=f"New coal (${refs['coal']:.0f})")
    ax.axhline(refs["unfirmed"], color=_ORANGE, ls=":", lw=1.3,
               label=f"Unfirmed solar (${refs['unfirmed']:.0f})")
    ax.axhspan(54, 82, color=_GREEN, alpha=0.08)
    ax.annotate("IRENA 2026 firm range\n$54-82/MWh", (80.5, 68), fontsize=7.5, color=_GREEN)

    ax.set_xlabel("Reliability — share of 24/7 load met by solar+storage (%)")
    ax.set_ylabel("Levelized cost of firm solar (LCOSS, $/MWh)")
    ax.set_title("Firm solar beats fossils — until the last few percent of reliability")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_ylim(0, max(moderate_df["lcoss_usd_mwh"].max() * 1.1, 200))
    fig.tight_layout()
    path = _outdir(outdir) / "fig21_firm_cost.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part IX: solar as feedstock (power-to-X)
# ---------------------------------------------------------------------------

def fig22_lcoh(curves: dict, refs: dict, ppa_band, outdir: str | Path) -> Path:
    """Levelized cost of green hydrogen vs electricity price, by scenario."""
    _style()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    colors = [_BLUE, _GREEN, _ORANGE]
    for (label, df), col in zip(curves.items(), colors):
        ax.plot(df["elec_price_usd_mwh"], df["lcoh_usd_kg"], "o-", color=col,
                lw=2, ms=4, label=label)
    ax.axhspan(refs["grey"], refs["blue"], color=_GREY, alpha=0.15)
    ax.annotate(f"fossil H2 (grey ${refs['grey']:.1f} / blue ${refs['blue']:.1f})",
                (2, refs["blue"] + 0.05), fontsize=8, color=_GREY)
    ax.axvspan(ppa_band[0], ppa_band[1], color=_GREEN, alpha=0.10)
    ax.annotate("solar PPA\n$15-25/MWh", ((ppa_band[0]+ppa_band[1])/2, 5.6),
                ha="center", fontsize=8, color=_GREEN)
    ax.set_xlabel("Electricity price ($/MWh)")
    ax.set_ylabel("Levelized cost of hydrogen ($/kg)")
    ax.set_title("Cheap solar makes cheap molecules: green hydrogen approaches fossil parity")
    ax.set_ylim(0, 6)
    ax.legend(fontsize=8.5, loc="upper left")
    fig.tight_layout()
    path = _outdir(outdir) / "fig22_lcoh.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig23_inversion(flex_df, enduse_df, cheap_price, grid_price,
                    outdir: str | Path) -> Path:
    """(a) flexible demand rescues the curtailed glut; (b) the end-use unlock."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    p = flex_df["penetration"] * 100
    ax1.fill_between(p, flex_df["curtailment_base"] * 100, color=_RED, alpha=0.25)
    ax1.plot(p, flex_df["curtailment_base"] * 100, color=_RED, lw=2,
             label="Curtailed (wasted)")
    ax1.plot(p, flex_df["curtailment_flex"] * 100, color=_GREEN, lw=2,
             label="Curtailed after flexible electrolysis")
    ax1.fill_between(p, flex_df["curtailment_flex"] * 100,
                     flex_df["curtailment_base"] * 100, color=_GREEN, alpha=0.2,
                     label="Glut captured → hydrogen")
    ax1.set_xlabel("Solar share of annual demand (%)")
    ax1.set_ylabel("Solar curtailment (%)")
    ax1.set_title("(a) Flexible demand eats the glut")
    ax1.legend(fontsize=8, loc="upper left")

    d = enduse_df.copy()
    y = np.arange(len(d))
    ax2.barh(y + 0.2, d["elec_cost_grid"], 0.4, color=_RED, alpha=0.8,
             label=f"Grid power (${grid_price:.0f}/MWh)")
    ax2.barh(y - 0.2, d["elec_cost_cheap"], 0.4, color=_GREEN, alpha=0.85,
             label=f"Cheap solar (${cheap_price:.0f}/MWh)")
    ax2.set_yticks(y)
    ax2.set_yticklabels([f"{r['product']}\n(per {r['unit']})" for _, r in d.iterrows()],
                        fontsize=7.5)
    ax2.set_xscale("log")
    ax2.set_xlabel("Electricity cost per unit of output ($, log scale)")
    ax2.set_title("(b) What near-free solar unlocks")
    ax2.legend(fontsize=8, loc="lower right")

    fig.suptitle("The inversion: shape demand around solar, and make molecules from the glut",
                 fontsize=12)
    fig.tight_layout()
    path = _outdir(outdir) / "fig23_inversion.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part X: solar off-world (space-based solar power)
# ---------------------------------------------------------------------------

def fig24_sbsp(curves: dict, refs: dict, markers: dict, outdir: str | Path) -> Path:
    """SBSP LCOE vs launch cost, against firm-terrestrial benchmarks."""
    _style()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    colors = [_GREEN, _BLUE, _PURPLE]
    for (label, df), col in zip(curves.items(), colors):
        ax.plot(df["launch_cost_per_kg"], df["lcoe_usd_mwh"], "-", color=col,
                lw=2.2, label=f"SBSP — {label}")
    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.axhline(refs["firm_high"], color=_ORANGE, ls="--", lw=1.4,
               label=f"Firm terrestrial, high-resource (${refs['firm_high']:.0f})")
    ax.axhline(refs["firm_moderate"], color=_RED, ls="--", lw=1.4,
               label=f"Firm terrestrial, moderate (${refs['firm_moderate']:.0f})")
    ax.axhline(refs["raw"], color=_GREY, ls=":", lw=1.2,
               label=f"Raw daytime solar (${refs['raw']:.0f})")

    for label, x in markers.items():
        ax.axvline(x, color="k", ls="-.", lw=1, alpha=0.6)
        ax.annotate(label, (x, ax.get_ylim()[1] * 0.7), rotation=90,
                    fontsize=7.5, ha="right", va="top")

    ax.set_xlabel("Launch cost to orbit ($/kg, log scale)")
    ax.set_ylabel("Levelized cost of energy ($/MWh, log scale)")
    ax.set_title("Solar where the sun never sets: SBSP undercuts firm solar at low launch cost")
    ax.legend(fontsize=7.8, loc="upper left")
    fig.tight_layout()
    path = _outdir(outdir) / "fig24_sbsp.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part XI: the trajectory (Wright's law)
# ---------------------------------------------------------------------------

def fig25_trajectory(hist_fit, proj_df, fit, milestones, outdir: str | Path) -> Path:
    """(a) Wright's law log-log fit; (b) module price & LCOE trajectory to 2050."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # (a) Wright's law: price vs cumulative capacity (log-log).
    h = hist_fit
    ax1.scatter(h["cumulative_gw"], h["module_price_usd_per_w"], color=_BLUE,
                zorder=5, label="Historical (2010-2024)")
    xs = np.logspace(np.log10(h["cumulative_gw"].min()),
                     np.log10(proj_df["cumulative_gw"].max()), 50)
    ax1.plot(xs, np.exp(fit["a"]) * xs ** fit["b"], color=_RED, lw=2,
             label=f"Wright's law (LR {fit['learning_rate']*100:.0f}%/doubling)")
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlabel("Cumulative installed capacity (GW, log)")
    ax1.set_ylabel("Module price ($/W, log)")
    ax1.set_title("(a) Fifty years on one line: Wright's law")
    ax1.legend(fontsize=8)

    # (b) trajectory vs year (from 2010, where real data and sane projections live).
    recent = proj_df[proj_df["year"] >= 2010]
    hist = recent[recent["kind"] == "actual"]
    proj = recent[recent["kind"] == "projected"]
    ax2.plot(hist["year"], hist["module_price_usd_per_w"], color=_BLUE, lw=2)
    ax2.plot(proj["year"], proj["module_price_usd_per_w"], color=_BLUE, lw=2,
             ls="--", label="Module price ($/W)")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Module price ($/W)", color=_BLUE)
    ax2.tick_params(axis="y", labelcolor=_BLUE)
    ax2.set_ylim(0, hist["module_price_usd_per_w"].max() * 1.1)

    ax2b = ax2.twinx()
    ax2b.plot(hist["year"], hist["lcoe_usd_mwh"], color=_GREEN, lw=2)
    ax2b.plot(proj["year"], proj["lcoe_usd_mwh"], color=_GREEN, lw=2, ls="--",
              label="Utility LCOE ($/MWh)")
    ax2b.set_ylabel("Utility LCOE ($/MWh)", color=_GREEN)
    ax2b.tick_params(axis="y", labelcolor=_GREEN)
    ax2b.grid(False)
    ax2b.set_ylim(0, recent["lcoe_usd_mwh"].max() * 1.1)

    for t, yr in milestones.items():
        if yr:
            ax2b.annotate(f"<${t:.0f}/MWh\n{yr}", (yr, t), fontsize=7.5,
                          color=_GREEN, ha="center")
    ax2.set_title("(b) The panel becomes nearly free; LCOE floors on balance-of-system")
    lines = ax2.get_legend_handles_labels()[0] + ax2b.get_legend_handles_labels()[0]
    ax2.legend(lines, [l.get_label() for l in lines], fontsize=8, loc="upper right")

    fig.suptitle("Where solar is going: the cheapest energy humanity has ever made",
                 fontsize=12)
    fig.tight_layout()
    path = _outdir(outdir) / "fig25_trajectory.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part XII: the copper question (metallisation)
# ---------------------------------------------------------------------------

def fig26_metallization(comp_df, sweep_df, breakeven, outdir: str | Path) -> Path:
    """(a) LCOE of silver vs copper metallisation; (b) the razor-thin margin."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    colors = [_GREY, _GREEN, _RED]
    bars = ax1.bar(range(len(comp_df)), comp_df["lcoe_usd_mwh"], color=colors,
                   alpha=0.85)
    ax1.set_xticks(range(len(comp_df)))
    ax1.set_xticklabels([n.replace(" (", "\n(") for n in comp_df["name"]], fontsize=8)
    ax1.set_ylabel("LCOE ($/MWh)")
    ax1.set_ylim(0, comp_df["lcoe_usd_mwh"].max() * 1.15)
    for b, v in zip(bars, comp_df["lcoe_usd_mwh"]):
        ax1.annotate(f"${v:.1f}", (b.get_x() + b.get_width() / 2, v),
                     textcoords="offset points", xytext=(0, 3), ha="center",
                     fontsize=9, fontweight="bold")
    ax1.set_title("(a) On LCOE, copper barely wins — and only if reliable")

    ax2.plot(sweep_df["copper_degradation"] * 100, sweep_df["copper_lcoe"], "-",
             color=_GREEN, lw=2.2, label="Copper LCOE")
    ax2.axhline(sweep_df["silver_lcoe"].iloc[0], color=_GREY, ls="--", lw=1.5,
                label="Proven silver LCOE")
    be = breakeven["breakeven_copper_degradation"] * 100
    ax2.axvline(be, color=_RED, ls=":", lw=1.4)
    ax2.annotate(f"break-even\n{be:.2f}%/yr", (be, sweep_df["silver_lcoe"].iloc[0]),
                 textcoords="offset points", xytext=(6, 20), fontsize=8, color=_RED)
    ax2.axvline(0.5, color=_BLUE, ls=":", lw=1, alpha=0.6)
    ax2.annotate("silver's\n0.5%/yr", (0.5, sweep_df["copper_lcoe"].max()),
                 textcoords="offset points", xytext=(4, -6), fontsize=7.5, color=_BLUE)
    ax2.set_xlabel("Copper degradation rate (%/yr)")
    ax2.set_ylabel("LCOE ($/MWh)")
    ax2.set_title("(b) A 0.05%/yr reliability slip erases the saving")
    ax2.legend(fontsize=8.5, loc="upper left")

    fig.suptitle("Copper vs silver: the real case for copper is abundance, not LCOE",
                 fontsize=12)
    fig.tight_layout()
    path = _outdir(outdir) / "fig26_metallization.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part XIII: truly renewable (closed-loop materials)
# ---------------------------------------------------------------------------

def fig27_renewable(runway_df, outdir: str | Path) -> Path:
    """(a) material runway by scenario; (b) virgin demand vs world production."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    df = runway_df.copy()
    cap = 1e5
    disp = df["runway_years"].clip(upper=cap)
    colors = [_RED, _ORANGE, _BLUE, _GREEN]

    bars = ax1.barh(df["scenario"], disp, color=colors, alpha=0.85)
    ax1.set_xscale("log")
    for b, (_, r) in zip(bars, df.iterrows()):
        lab = "effectively infinite" if r["runway_years"] >= cap else f"{r['runway_years']:.0f} yr"
        ax1.annotate(lab, (min(r["runway_years"], cap), b.get_y() + b.get_height() / 2),
                     textcoords="offset points", xytext=(5, 0), va="center", fontsize=8.5)
    ax1.set_xlabel("Material runway (years of reserves, log scale)")
    ax1.set_title("(a) How long until we run out?")
    ax1.margins(x=0.3)

    share = df["virgin_share_of_production"] * 100
    cbar = ax2.barh(df["scenario"], share.clip(upper=120), color=colors, alpha=0.85)
    ax2.axvline(100, color="k", ls="--", lw=1.3)
    ax2.annotate("100% of world\nproduction", (100, -0.4), fontsize=7.5, ha="center")
    ax2.axvspan(0, 30, color=_GREEN, alpha=0.08)
    ax2.annotate("sustainable\nzone", (15, 3.2), fontsize=7.5, color=_GREEN, ha="center")
    for b, v in zip(cbar, share):
        ax2.annotate(f"{v:.1f}%", (min(v, 120), b.get_y() + b.get_height() / 2),
                     textcoords="offset points", xytext=(4, 0), va="center", fontsize=8.5)
    ax2.set_xlabel("Annual virgin metal demand (% of world production)")
    ax2.set_title("(b) Are we mining within our means?")

    fig.suptitle("Truly renewable solar = a tight recycling loop + abundant metals",
                 fontsize=12)
    fig.tight_layout()
    path = _outdir(outdir) / "fig27_renewable.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part XIV: cracking pyrite (the voltage roadmap)
# ---------------------------------------------------------------------------

def fig28_pyrite_roadmap(roadmap_df, outdir: str | Path) -> Path:
    """An ascending ladder: efficiency unlocked by each voltage-repair step."""
    _style()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    df = roadmap_df.reset_index(drop=True)
    x = np.arange(len(df))
    eta = df["eta"].values * 100

    # Climbing bars + connecting line.
    colors = [_RED] + [_ORANGE] * (len(df) - 2) + [_GREEN]
    ax.bar(x, eta, width=0.6, color=colors, alpha=0.8)
    ax.plot(x, eta, "o-", color="k", lw=1.2, ms=5)
    for i in range(len(df)):
        ax.annotate(f"{eta[i]:.0f}%\nVoc {df.iloc[i]['voc_v']:.2f}V\nERE {df.iloc[i]['ere']:.0e}",
                    (x[i], eta[i]), textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=7.5)
    # Reference: silicon-grade commercial cell.
    ax.axhline(22, color=_BLUE, ls="--", lw=1.2)
    ax.annotate("today's commercial silicon (~22%)", (0, 22.6), fontsize=8, color=_BLUE)

    ax.set_xticks(x)
    ax.set_xticklabels([s.replace("+ ", "+\n") for s in df["stage"]], fontsize=8)
    ax.set_ylabel("Efficiency (%)")
    ax.set_ylim(0, 32)
    ax.set_title("Cracking pyrite: each voltage repair turns 'fool's gold' more golden")
    fig.tight_layout()
    path = _outdir(outdir) / "fig28_pyrite_roadmap.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part XV: space solar, seriously
# ---------------------------------------------------------------------------

def fig29_spacedeep(beam_df, scale_df, outdir: str | Path) -> Path:
    """(a) the orbit->ground beaming chain; (b) launch cadence vs SBSP scale."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # (a) cumulative efficiency cascade.
    stages = ["Orbit DC"] + list(beam_df["stage"])
    cum = [1.0] + list(beam_df["cumulative_eff"])
    ax1.step(range(len(cum)), [c * 100 for c in cum], where="post", color=_BLUE, lw=2)
    ax1.fill_between(range(len(cum)), [c * 100 for c in cum], step="post",
                     color=_BLUE, alpha=0.15)
    ax1.set_xticks(range(len(cum)))
    ax1.set_xticklabels(["Orbit\nDC", "TX", "Atmos", "Rectenna", "Ground\nDC"],
                        fontsize=8)
    for i, c in enumerate(cum):
        ax1.annotate(f"{c*100:.0f}%", (i, c * 100), textcoords="offset points",
                     xytext=(0, 5), ha="center", fontsize=8.5)
    ax1.set_ylabel("Cumulative efficiency (%)")
    ax1.set_ylim(0, 105)
    ax1.set_title("(a) Getting the energy down: ~60% end-to-end")

    # (b) launches/day vs scale.
    ax2.plot(scale_df["target_tw"], scale_df["launches_per_day"], "o-",
             color=_PURPLE, lw=2)
    ax2.axhline(1, color=_GREEN, ls="--", lw=1.2, label="~today's whole-world cadence (~1/day)")
    ax2.axhline(10, color=_ORANGE, ls="--", lw=1.2, label="mature Starship (~10/day, heroic)")
    ax2.axvspan(0, 1, color=_GREEN, alpha=0.08)
    ax2.annotate("credible premium\nslice", (0.45, 60), fontsize=8, color=_GREEN, ha="center")
    ax2.annotate("'power the world'\n(20 TW): ~240/day", (10, 150), fontsize=8,
                 color=_RED, ha="center")
    ax2.set_xlabel("SBSP capacity built (TW)")
    ax2.set_ylabel("Launches per day, sustained 30 yr")
    ax2.set_yscale("log")
    ax2.set_title("(b) Scalability: a slice, not the whole pie")
    ax2.legend(fontsize=8, loc="lower right")

    fig.suptitle("Space solar, seriously: clean to launch, hard to scale to the whole world",
                 fontsize=12)
    fig.tight_layout()
    path = _outdir(outdir) / "fig29_spacedeep.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Part XVI: the collection problem
# ---------------------------------------------------------------------------

def fig30_collection(runway_df, thrift_df, regional, econ, outdir: str | Path) -> Path:
    """(a) runway vs collection rate; (b) recycling margin vs silver content."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    c = runway_df["collection"] * 100
    ax1.plot(c, runway_df["runway_years"], "o-", color=_BLUE, lw=2.2)
    ax1.fill_between(c, runway_df["runway_years"], color=_BLUE, alpha=0.12)
    ax1.axvspan(0, 50, color=_RED, alpha=0.07)
    ax1.annotate("below ~50% collection:\nbarely better than\nno recycling",
                 (12, runway_df["runway_years"].max() * 0.62), fontsize=8, color=_RED)
    for label, rate in regional.items():
        ax1.axvline(rate * 100, color=_GREY, ls=":", lw=1)
        ax1.annotate(label, (rate * 100, runway_df["runway_years"].max() * 0.95),
                     rotation=90, fontsize=7, va="top", ha="right", color=_GREY)
    ax1.set_xlabel("End-of-life collection rate (%)")
    ax1.set_ylabel("Material runway (years)")
    ax1.set_title("(a) Collection — not the recycler — is the swing factor")

    ag = thrift_df["silver_mg_per_w"]
    x = range(len(ag))
    ax2.bar(x, thrift_df["recovered_value_t"], color=_GREEN, alpha=0.6,
            label="Recovered material value")
    ax2.bar(x, thrift_df["net_value_t"], color=_GREEN, alpha=0.95,
            label="Net of recycling cost")
    ax2.axhline(econ["recycle_cost"], color=_ORANGE, ls="--", lw=1.3,
                label=f"Recycling cost (${econ['recycle_cost']:.0f}/t)")
    ax2.axhline(econ["landfill_cost"], color=_RED, ls=":", lw=1.3,
                label=f"Landfill (${econ['landfill_cost']:.0f}/t) — the cheap exit")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels([f"{a:.0f} mg/W\nsilver" if a > 0 else "copper\n(0 silver)"
                         for a in ag], fontsize=8)
    ax2.set_ylabel("Value ($ per tonne of modules)")
    ax2.set_title("(b) Thrifting silver to copper fades the recycling incentive")
    ax2.legend(fontsize=7.5, loc="upper right")

    fig.suptitle("The urban mine only pays off if we actually dig it up",
                 fontsize=12)
    fig.tight_layout()
    path = _outdir(outdir) / "fig30_collection.png"
    fig.savefig(path)
    plt.close(fig)
    return path
