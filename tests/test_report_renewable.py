"""End-to-end tests for the Part XIII (truly renewable) report."""

from solarlab.report_renewable import (
    build_renewable_report,
    collect_renewable_results,
    render_renewable_figures,
)


def test_renewable_figure_renders(tmp_path):
    r = collect_renewable_results()
    paths = render_renewable_figures(r, tmp_path)
    assert len(paths) == 1 and paths[0].stat().st_size > 10_000


def test_renewable_report_builds_and_deterministic(tmp_path):
    r = collect_renewable_results()
    render_renewable_figures(r, tmp_path)
    report = build_renewable_report(r, tmp_path)
    text = report.read_text()
    assert "fig27_" in text
    assert "recycl" in text.lower() and "abundant" in text.lower()
    assert build_renewable_report(r, tmp_path).read_text() == text


def test_cli_renewable(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "renewable"]) == 0
    assert (tmp_path / "out" / "REPORT_RENEWABLE.md").exists()
