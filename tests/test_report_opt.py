"""End-to-end tests for the Part V (optimiser) report and figure."""

import pytest

from solarlab.report_opt import (
    build_optimizer_report,
    collect_optimizer_results,
    render_optimizer_figures,
)


@pytest.fixture(scope="module")
def opt(weather):
    return collect_optimizer_results(weather=weather)


def test_optimizer_figure_renders(opt, tmp_path):
    paths = render_optimizer_figures(opt, tmp_path)
    assert len(paths) == 1 and paths[0].stat().st_size > 10_000


def test_optimizer_report_builds_and_deterministic(opt, tmp_path):
    render_optimizer_figures(opt, tmp_path)
    report = build_optimizer_report(opt, tmp_path)
    text = report.read_text()
    assert "fig16_" in text
    assert "flips with the" in text.lower()
    assert build_optimizer_report(opt, tmp_path).read_text() == text


def test_cli_optimize_report_and_query(tmp_path, monkeypatch, capsys):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "optimize"]) == 0
    assert (tmp_path / "out" / "REPORT_OPTIMIZER.md").exists()
    # Custom query prints a recommendation instead of writing the report.
    assert main(["optimize", "--area", "30", "--budget", "50000",
                 "--deployment", "residential"]) == 0
    assert "Recommended" in capsys.readouterr().out
