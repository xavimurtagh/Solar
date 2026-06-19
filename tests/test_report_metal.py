"""End-to-end tests for the Part XII (metallisation) report."""

import pytest

from solarlab.report_metal import (
    build_metal_report,
    collect_metal_results,
    render_metal_figures,
)


@pytest.fixture(scope="module")
def metal():
    return collect_metal_results()


def test_metal_figure_renders(metal, tmp_path):
    paths = render_metal_figures(metal, tmp_path)
    assert len(paths) == 1 and paths[0].stat().st_size > 10_000


def test_metal_report_builds_and_deterministic(metal, tmp_path):
    render_metal_figures(metal, tmp_path)
    report = build_metal_report(metal, tmp_path)
    text = report.read_text()
    assert "fig26_" in text
    assert "abundance" in text.lower() and "copper" in text.lower()
    assert build_metal_report(metal, tmp_path).read_text() == text


def test_cli_metal(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "metal"]) == 0
    assert (tmp_path / "out" / "REPORT_METAL.md").exists()
