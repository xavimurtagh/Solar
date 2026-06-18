"""End-to-end tests for the Part IV (land-use) report and figures."""

import pytest

from solarlab.report_land import (
    build_land_report,
    collect_land_results,
    render_land_figures,
)


@pytest.fixture(scope="module")
def land(weather):
    return collect_land_results(weather=weather)


def test_land_figures_render(land, tmp_path):
    paths = render_land_figures(land, tmp_path)
    assert len(paths) == 2
    for p in paths:
        assert p.exists() and p.stat().st_size > 10_000


def test_land_report_builds_and_deterministic(land, tmp_path):
    render_land_figures(land, tmp_path)
    report = build_land_report(land, tmp_path)
    text = report.read_text()
    assert "fig14_" in text and "fig15_" in text
    assert "Land Equivalent Ratio" in text
    assert build_land_report(land, tmp_path).read_text() == text   # deterministic


def test_cli_land(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "land"]) == 0
    assert (tmp_path / "out" / "REPORT_LAND.md").exists()
