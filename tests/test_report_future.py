"""End-to-end tests for the Part XI (capstone) report."""

from solarlab.report_future import (
    build_future_report,
    collect_future_results,
    render_future_figures,
)


def test_future_figure_renders(tmp_path):
    r = collect_future_results()
    paths = render_future_figures(r, tmp_path)
    assert len(paths) == 1 and paths[0].stat().st_size > 10_000


def test_future_report_builds_and_deterministic(tmp_path):
    r = collect_future_results()
    render_future_figures(r, tmp_path)
    report = build_future_report(r, tmp_path)
    text = report.read_text()
    assert "fig25_" in text
    assert "Great Inversion" in text
    assert "[EXTRAPOLATION]" in text            # speculation is flagged
    # All eleven parts referenced in the synthesis table.
    for part in ("Circularity", "Power-to-X", "pyrite", "value wall"):
        assert part.lower() in text.lower()
    assert build_future_report(r, tmp_path).read_text() == text


def test_cli_future(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "future"]) == 0
    assert (tmp_path / "out" / "REPORT_FUTURE.md").exists()
