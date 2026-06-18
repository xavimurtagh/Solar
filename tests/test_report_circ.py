"""End-to-end tests for the Part III (circularity) report and figures."""

import pytest

from solarlab.report_circ import (
    build_circularity_report,
    collect_circularity_results,
    render_circularity_figures,
)


@pytest.fixture(scope="module")
def circ():
    return collect_circularity_results()


def test_circularity_figures_render(circ, tmp_path):
    paths = render_circularity_figures(circ, tmp_path)
    assert len(paths) == 3
    for p in paths:
        assert p.exists() and p.stat().st_size > 10_000


def test_circularity_report_builds(circ, tmp_path):
    render_circularity_figures(circ, tmp_path)
    report = build_circularity_report(circ, tmp_path)
    text = report.read_text()
    for n in (11, 12, 13):
        assert f"fig{n}_" in text
    assert "urban mine" in text.lower()
    assert "FRELP" in text


def test_circularity_report_deterministic(circ, tmp_path):
    render_circularity_figures(circ, tmp_path)
    first = build_circularity_report(circ, tmp_path).read_text()
    second = build_circularity_report(circ, tmp_path).read_text()
    assert first == second


def test_cli_circularity_and_all(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "circularity"]) == 0
    assert (tmp_path / "out" / "REPORT_CIRCULARITY.md").exists()
    # 'all' now produces three reports and all thirteen figures.
    assert main(["--outdir", "out2", "all"]) == 0
    for name in ("REPORT.md", "REPORT_ECONOMICS.md", "REPORT_CIRCULARITY.md"):
        assert (tmp_path / "out2" / name).exists()
    assert len(list((tmp_path / "out2" / "figures").glob("*.png"))) == 13
