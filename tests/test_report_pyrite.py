"""End-to-end tests for the Part VI (pyrite) report and figure."""

import pytest

from solarlab.report_pyrite import (
    build_pyrite_report,
    collect_pyrite_results,
    render_pyrite_figures,
)


@pytest.fixture(scope="module")
def pyr():
    return collect_pyrite_results()


def test_pyrite_figure_renders(pyr, tmp_path):
    paths = render_pyrite_figures(pyr, tmp_path)
    assert len(paths) == 1 and paths[0].stat().st_size > 10_000


def test_pyrite_report_builds_and_deterministic(pyr, tmp_path):
    render_pyrite_figures(pyr, tmp_path)
    report = build_pyrite_report(pyr, tmp_path)
    text = report.read_text()
    assert "fig17_" in text
    assert "ERE" in text and "pyrite" in text.lower()
    assert build_pyrite_report(pyr, tmp_path).read_text() == text


def test_cli_pyrite(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "pyrite"]) == 0
    assert (tmp_path / "out" / "REPORT_PYRITE.md").exists()
