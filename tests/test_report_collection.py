"""End-to-end tests for the Part XVI (collection) report."""

from solarlab.report_collection import (
    build_collection_report,
    collect_collection_results,
    render_collection_figures,
)


def test_collection_figure_renders(tmp_path):
    r = collect_collection_results()
    paths = render_collection_figures(r, tmp_path)
    assert len(paths) == 1 and paths[0].stat().st_size > 10_000


def test_collection_report_builds_and_deterministic(tmp_path):
    r = collect_collection_results()
    render_collection_figures(r, tmp_path)
    report = build_collection_report(r, tmp_path)
    text = report.read_text()
    assert "fig30_" in text
    assert "collection" in text.lower() and "WEEE" in text
    assert build_collection_report(r, tmp_path).read_text() == text


def test_cli_collection(tmp_path, monkeypatch):
    from solarlab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--outdir", "out", "collection"]) == 0
    assert (tmp_path / "out" / "REPORT_COLLECTION.md").exists()
