"""End-to-end tests for the Part VIII (firming) report."""

import pytest

from solarlab.report_firming import (
    build_firming_report,
    collect_firming_results,
    render_firming_figures,
)


@pytest.fixture(scope="module")
def firm(weather):
    return collect_firming_results(weather=weather)


def test_firming_figures_render(firm, tmp_path):
    paths = render_firming_figures(firm, tmp_path)
    assert len(paths) == 2
    for p in paths:
        assert p.exists() and p.stat().st_size > 10_000


def test_firming_report_builds_and_deterministic(firm, tmp_path):
    render_firming_figures(firm, tmp_path)
    report = build_firming_report(firm, tmp_path)
    text = report.read_text()
    assert "fig20_" in text and "fig21_" in text
    assert "LCOSS" in text or "firm" in text.lower()
    assert build_firming_report(firm, tmp_path).read_text() == text


def test_cli_firming(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "firming"]) == 0
    assert (tmp_path / "out" / "REPORT_FIRMING.md").exists()
