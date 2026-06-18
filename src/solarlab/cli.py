"""Command-line entry point.

    python -m solarlab report     # compute everything, write figures + REPORT.md
    python -m solarlab figures    # just the figures
    python -m solarlab validate   # quick physics + data sanity checks
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _cmd_report(args) -> int:
    from .report import generate

    path = generate(Path(args.outdir))
    print(f"Wrote {path} and figures in {args.outdir}/figures/")
    return 0


def _cmd_figures(args) -> int:
    from .report import collect_results, render_figures

    results = collect_results()
    paths = render_figures(results, Path(args.outdir))
    for p in paths:
        print(f"Wrote {p}")
    return 0


def _cmd_economics(args) -> int:
    from .report_econ import generate_economics

    path = generate_economics(Path(args.outdir))
    print(f"Wrote {path} and economics figures in {args.outdir}/figures/")
    return 0


def _cmd_circularity(args) -> int:
    from .report_circ import generate_circularity

    path = generate_circularity(Path(args.outdir))
    print(f"Wrote {path} and circularity figures in {args.outdir}/figures/")
    return 0


def _cmd_land(args) -> int:
    from .report_land import generate_land

    path = generate_land(Path(args.outdir))
    print(f"Wrote {path} and land-use figures in {args.outdir}/figures/")
    return 0


def _cmd_all(args) -> int:
    from .report import generate
    from .report_circ import generate_circularity
    from .report_econ import generate_economics
    from .report_land import generate_land

    generate(Path(args.outdir))
    generate_economics(Path(args.outdir))
    generate_circularity(Path(args.outdir))
    generate_land(Path(args.outdir))
    print(f"Wrote all reports and figures in {args.outdir}/")
    return 0


def _cmd_validate(args) -> int:
    """Fast self-check of the physics and data without writing artifacts."""
    from . import constants as C
    from .history import load_milestones, validate_milestones
    from .spectrum import SpectrumIntegrals, load_am15g
    from .sq import optimal_bandgap, sq_cell
    from .waterfall import build_waterfall

    spec = SpectrumIntegrals(load_am15g())
    opt = optimal_bandgap(spec)
    si = sq_cell(C.SI_EG_EV, spec)
    checks = [
        ("AM1.5G integrated power ~1000 W/m^2", 995 <= spec.p_in_w_m2 <= 1005),
        ("SQ peak in 33-34%", 0.330 <= opt.eta <= 0.344),
        ("SQ silicon in 31-34%", 0.315 <= si.eta <= 0.340),
        ("milestones cited", _milestones_ok()),
    ]
    ok = True
    for name, passed in checks:
        print(f"  [{'OK ' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    print("validate:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def _milestones_ok() -> bool:
    from .history import load_milestones, validate_milestones
    try:
        validate_milestones(load_milestones())
        return True
    except ValueError:
        return False


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="solarlab", description=__doc__)
    parser.add_argument("--outdir", default="output",
                        help="output directory (default: output)")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("report", help="generate the efficiency report (Part I, default)")
    sub.add_parser("economics", help="generate the cost/materials report (Part II)")
    sub.add_parser("circularity", help="generate the recycling report (Part III)")
    sub.add_parser("land", help="generate the land-use report (Part IV)")
    sub.add_parser("all", help="generate every report and all figures")
    sub.add_parser("figures", help="generate Part I figures only")
    sub.add_parser("validate", help="run quick physics + data checks")

    args = parser.parse_args(argv)
    command = args.command or "report"
    return {"report": _cmd_report, "economics": _cmd_economics,
            "circularity": _cmd_circularity, "land": _cmd_land, "all": _cmd_all,
            "figures": _cmd_figures, "validate": _cmd_validate}[command](args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
