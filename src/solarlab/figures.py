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
