"""End-to-end tests for the Part IX (power-to-X) report."""

import pytest

from solarlab.report_power2x import (
    build_power2x_report,
    collect_power2x_results,
    render_power2x_figures,
)


@pytest.fixture(scope="module")
def p2x(weather):
    return collect_power2x_results(weather=weather)


def test_power2x_figures_render(p2x, tmp_path):
    paths = render_power2x_figures(p2x, tmp_path)
    assert len(paths) == 2
    for p in paths:
        assert p.exists() and p.stat().st_size > 10_000


def test_power2x_report_builds_and_deterministic(p2x, tmp_path):
    render_power2x_figures(p2x, tmp_path)
    report = build_power2x_report(p2x, tmp_path)
    text = report.read_text()
    assert "fig22_" in text and "fig23_" in text
    assert "hydrogen" in text.lower()
    assert build_power2x_report(p2x, tmp_path).read_text() == text


def test_cli_power2x(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "power2x"]) == 0
    assert (tmp_path / "out" / "REPORT_POWER2X.md").exists()
