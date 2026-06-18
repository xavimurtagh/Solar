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
