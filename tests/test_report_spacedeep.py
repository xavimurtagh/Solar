"""End-to-end tests for the Part XV (space deep-dive) report."""

from solarlab.report_spacedeep import (
    build_spacedeep_report,
    collect_spacedeep_results,
    render_spacedeep_figures,
)


def test_spacedeep_figure_renders(tmp_path):
    r = collect_spacedeep_results()
    paths = render_spacedeep_figures(r, tmp_path)
    assert len(paths) == 1 and paths[0].stat().st_size > 10_000


def test_spacedeep_report_builds_and_deterministic(tmp_path):
    r = collect_spacedeep_results()
    render_spacedeep_figures(r, tmp_path)
    report = build_spacedeep_report(r, tmp_path)
    text = report.read_text()
    assert "fig29_" in text
    assert "rectenna" in text.lower() and "launches" in text.lower()
    assert build_spacedeep_report(r, tmp_path).read_text() == text


def test_cli_spacedeep(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "spacedeep"]) == 0
    assert (tmp_path / "out" / "REPORT_SPACEDEEP.md").exists()
