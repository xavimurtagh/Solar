"""End-to-end tests: figures render, the report builds, and reruns are stable."""

from pathlib import Path

import pytest

from solarlab import figures as figs
from solarlab.report import build_report, collect_results, render_figures


@pytest.fixture(scope="module")
def results(weather):
    return collect_results(weather=weather)


def test_all_figures_render(results, tmp_path):
    paths = render_figures(results, tmp_path)
    assert len(paths) == 5
    for p in paths:
        assert p.exists()
        assert p.stat().st_size > 10_000      # a real plot, not a blank canvas


def test_report_builds_and_references_figures(results, tmp_path):
    render_figures(results, tmp_path)
    report = build_report(results, tmp_path)
    assert report.exists()
    text = report.read_text()
    for n in range(1, 6):
        assert f"fig{n}_" in text                # every figure is embedded
    # Key computed numbers appear in the prose.
    assert "33.4%" in text or "33.7%" in text


def test_report_is_deterministic(results, tmp_path):
    render_figures(results, tmp_path)
    first = build_report(results, tmp_path).read_text()
    second = build_report(results, tmp_path).read_text()
    assert first == second                       # byte-identical reruns


def test_cli_report_command(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    rc = main(["--outdir", "out", "report"])
    assert rc == 0
    assert (tmp_path / "out" / "REPORT.md").exists()
    assert len(list((tmp_path / "out" / "figures").glob("*.png"))) == 5


def test_cli_validate_command(capsys):
    from solarlab.cli import main

    rc = main(["validate"])
    assert rc == 0
    assert "PASS" in capsys.readouterr().out
