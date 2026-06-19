"""End-to-end tests for the Part XVII (storage) report."""

from solarlab.report_storage import (
    build_storage_report,
    collect_storage_results,
    render_storage_figures,
)


def test_storage_figure_renders(tmp_path):
    r = collect_storage_results()
    paths = render_storage_figures(r, tmp_path)
    assert len(paths) == 1 and paths[0].stat().st_size > 10_000


def test_storage_report_builds_and_deterministic(tmp_path):
    r = collect_storage_results()
    render_storage_figures(r, tmp_path)
    report = build_storage_report(r, tmp_path)
    text = report.read_text()
    assert "fig31_" in text
    assert "duration" in text.lower() and "hydrogen" in text.lower()
    assert build_storage_report(r, tmp_path).read_text() == text


def test_cli_storage(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "storage"]) == 0
    assert (tmp_path / "out" / "REPORT_STORAGE.md").exists()
