"""End-to-end tests for the Part X (space-based solar) report."""

import pytest

from solarlab.report_space import (
    build_space_report,
    collect_space_results,
    render_space_figures,
)


@pytest.fixture(scope="module")
def space():
    return collect_space_results()


def test_space_figure_renders(space, tmp_path):
    paths = render_space_figures(space, tmp_path)
    assert len(paths) == 1 and paths[0].stat().st_size > 10_000


def test_space_report_builds_and_deterministic(space, tmp_path):
    render_space_figures(space, tmp_path)
    report = build_space_report(space, tmp_path)
    text = report.read_text()
    assert "fig24_" in text
    assert "launch" in text.lower() and "SBSP" in text
    assert build_space_report(space, tmp_path).read_text() == text


def test_cli_space(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "space"]) == 0
    assert (tmp_path / "out" / "REPORT_SPACE.md").exists()
