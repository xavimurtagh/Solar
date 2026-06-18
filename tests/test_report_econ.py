"""End-to-end tests for the Part II (economics) report and figures."""

import pytest

from solarlab.report_econ import (
    build_economics_report,
    collect_economics_results,
    render_economics_figures,
)


@pytest.fixture(scope="module")
def econ(weather):
    return collect_economics_results(weather=weather)


def test_economics_figures_render(econ, tmp_path):
    paths = render_economics_figures(econ, tmp_path)
    assert len(paths) == 5
    for p in paths:
        assert p.exists() and p.stat().st_size > 10_000


def test_economics_report_builds(econ, tmp_path):
    render_economics_figures(econ, tmp_path)
    report = build_economics_report(econ, tmp_path)
    text = report.read_text()
    for n in range(6, 11):
        assert f"fig{n}_" in text                  # figures 6-10 embedded
    assert "terawatt" in text.lower()
    assert "Tellurium" in text or "tellurium" in text


def test_economics_report_deterministic(econ, tmp_path):
    render_economics_figures(econ, tmp_path)
    first = build_economics_report(econ, tmp_path).read_text()
    second = build_economics_report(econ, tmp_path).read_text()
    assert first == second


def test_cli_economics_and_all(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "economics"]) == 0
    assert (tmp_path / "out" / "REPORT_ECONOMICS.md").exists()
    # 'all' produces every report and all figures (see test_report_circ for the
    # full count); here we just confirm Part II is among them.
    assert main(["--outdir", "out2", "all"]) == 0
    assert (tmp_path / "out2" / "REPORT.md").exists()
    assert (tmp_path / "out2" / "REPORT_ECONOMICS.md").exists()
    assert len(list((tmp_path / "out2" / "figures").glob("*.png"))) >= 10
