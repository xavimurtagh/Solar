"""End-to-end tests for the Part VII (value of time) report."""

import pytest

from solarlab.report_value import (
    build_value_report,
    collect_value_results,
    render_value_figures,
)


@pytest.fixture(scope="module")
def val(weather):
    return collect_value_results(weather=weather)


def test_value_figures_render(val, tmp_path):
    paths = render_value_figures(val, tmp_path)
    assert len(paths) == 2
    for p in paths:
        assert p.exists() and p.stat().st_size > 10_000


def test_value_report_builds_and_deterministic(val, tmp_path):
    render_value_figures(val, tmp_path)
    report = build_value_report(val, tmp_path)
    text = report.read_text()
    assert "fig18_" in text and "fig19_" in text
    assert "value factor" in text.lower()
    assert build_value_report(val, tmp_path).read_text() == text


def test_cli_value(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "value"]) == 0
    assert (tmp_path / "out" / "REPORT_VALUE.md").exists()
