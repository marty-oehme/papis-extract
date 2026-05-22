"""Tests for FileExporter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from papis.document import Document

from papis_extract.annotation import Annotation
from papis_extract.exporters.file_exporter import FileExporter


# -- helpers -------------------------------------------------------------


_doc = Document(data={"title": "The Book", "author": "Someone"})
_annots = [Annotation("file.pdf", content="highlighted text")]


def _make_exporter(
    *,
    file_path: Path | None = None,
    duplicates: bool = False,
    formatter=None,
) -> FileExporter:
    """Create a FileExporter with optional overrides.

    If *formatter* is not given, a simple mock is used that returns
    ``"line1\\nline2"`` for any non-empty annotation list and ``""``
    for empty lists.

    If *file_path* is not given, falls back to ``Path("/tmp/out.md")``.
    """
    if formatter is None:

        class _Fmt:
            header = ""
            document_separator = "\n"

            def __call__(self, doc, annots):
                return "line1\nline2" if annots else ""

        formatter = _Fmt()

    if file_path is None:
        file_path = Path("/tmp/out.md")

    return FileExporter(formatter=formatter, file_path=file_path, duplicates=duplicates)


# -- run() orchestration -------------------------------------------------


class TestRun:
    """Orchestration tests for ``FileExporter.run()``.

    Uses ``tmp_path`` for file paths and mocks
    ``write_annotations_to_file`` to avoid real file I/O.
    """

    @pytest.fixture
    def exporter(self, tmp_path):
        return _make_exporter(file_path=tmp_path / "out.md")

    # ---- smoke / empty ----

    def test_empty_doc_list(self, exporter):
        """Smoketest: does not crash on empty list."""
        with patch(
            "papis_extract.exporters.file_exporter.write_annotations_to_file"
        ) as mock_write:
            exporter.run([])
        mock_write.assert_not_called()

    def test_single_doc_empty_annotations_skipped(self, exporter):
        """Empty annotations → formatter returns '' → write not called."""
        with patch(
            "papis_extract.exporters.file_exporter.write_annotations_to_file"
        ) as mock_write:
            exporter.run([(_doc, [])])
        mock_write.assert_not_called()

    # ---- single doc ----

    def test_single_doc_with_annotations(self, exporter):
        """Formatted annotations passed to write_annotations_to_file."""
        with patch(
            "papis_extract.exporters.file_exporter.write_annotations_to_file"
        ) as mock_write:
            exporter.run([(_doc, _annots)])

        mock_write.assert_called_once()
        # First positional arg: path
        assert mock_write.call_args[0][0] == exporter.file_path
        # Second positional arg: formatted lines
        assert mock_write.call_args[0][1] == ["line1", "line2"]
        # Keyword args: defaults
        assert mock_write.call_args[1]["duplicates"] is False
        assert "minimum_similarity" in mock_write.call_args[1]

    # ---- multiple docs ----

    def test_multiple_docs(self, exporter):
        """Two docs → write_annotations_to_file called twice."""
        with patch(
            "papis_extract.exporters.file_exporter.write_annotations_to_file"
        ) as mock_write:
            exporter.run([(_doc, _annots), (_doc, _annots)])
        assert mock_write.call_count == 2

    def test_multiple_docs_same_path(self, exporter):
        """Both calls use the same file path."""
        with patch(
            "papis_extract.exporters.file_exporter.write_annotations_to_file"
        ) as mock_write:
            exporter.run([(_doc, _annots), (_doc, _annots)])
        for call in mock_write.call_args_list:
            assert call[0][0] == exporter.file_path

    # ---- duplicates flag ----

    def test_duplicates_flag_passed(self, tmp_path):
        """duplicates=True propagates to write_annotations_to_file."""
        exporter = _make_exporter(file_path=tmp_path / "out.md", duplicates=True)
        with patch(
            "papis_extract.exporters.file_exporter.write_annotations_to_file"
        ) as mock_write:
            exporter.run([(_doc, _annots)])
        assert mock_write.call_args[1]["duplicates"] is True
        assert "minimum_similarity" in mock_write.call_args[1]

    # ---- headers ----

    def test_header_prepended_to_output(self, tmp_path):
        """formatter.header is prepended before splitting."""

        class _Fmt:
            header = "COL1,COL2"
            document_separator = "\n"

            def __call__(self, doc, annots):
                return "row1" if annots else ""

        exporter = _make_exporter(file_path=tmp_path / "out.md", formatter=_Fmt())
        with patch(
            "papis_extract.exporters.file_exporter.write_annotations_to_file"
        ) as mock_write:
            exporter.run([(_doc, _annots)])
        # "COL1,COL2\nrow1".split("\n") = ["COL1,COL2", "row1"]
        assert mock_write.call_args[0][1] == ["COL1,COL2", "row1"]

    def test_header_but_empty_formatter_output(self, tmp_path):
        """Empty output → skip doc even when header is set."""

        class _Fmt:
            header = "COL1,COL2"
            document_separator = "\n"

            def __call__(self, doc, annots):
                return ""

        exporter = _make_exporter(file_path=tmp_path / "out.md", formatter=_Fmt())
        with patch(
            "papis_extract.exporters.file_exporter.write_annotations_to_file"
        ) as mock_write:
            exporter.run([(_doc, [])])
        mock_write.assert_not_called()

    def test_formatter_output_only_whitespace(self, tmp_path):
        """Edge case: output is only newlines → split gives non-empty list."""

        class _Fmt:
            header = ""
            document_separator = "\n"

            def __call__(self, doc, annots):
                return "\n\n"

        exporter = _make_exporter(file_path=tmp_path / "out.md", formatter=_Fmt())
        with patch(
            "papis_extract.exporters.file_exporter.write_annotations_to_file"
        ) as mock_write:
            exporter.run([(_doc, _annots)])
        # "\n\n".split("\n") = ["", "", ""] → truthy → called
        mock_write.assert_called_once()


# -- file I/O (integration with _io) -------------------------------------


class TestFileIO:
    """Integration tests that actually write to files via _io."""

    @pytest.fixture(autouse=True)
    def _set_similarity(self, monkeypatch):
        """Default similarity threshold for fuzzy dedup."""
        monkeypatch.setattr("papis.config.getfloat", lambda k, s: 0.75)

    def test_creates_file(self, tmp_path):
        """Single doc → file created with formatted output."""
        p = tmp_path / "output.md"
        exporter = _make_exporter(file_path=p)
        exporter.run([(_doc, _annots)])
        assert p.read_text() == "line1\n\nline2"

    def test_creates_parent_directories(self, tmp_path):
        """Nested path → parent directories created automatically."""
        p = tmp_path / "sub" / "deep" / "out.md"
        exporter = _make_exporter(file_path=p)
        exporter.run([(_doc, _annots)])
        assert p.read_text() == "line1\n\nline2"

    def test_appends_to_existing_file(self, tmp_path):
        """Second run appends without overwriting."""
        p = tmp_path / "out.md"
        p.write_text("existing\n")
        exporter = _make_exporter(file_path=p)
        exporter.run([(_doc, _annots)])
        assert p.read_text() == "existing\n\nline1\n\nline2"

    def test_multi_doc_accumulates(self, tmp_path):
        """Two docs with different output → both written to same file."""
        p = tmp_path / "out.md"

        # Formatter that returns completely different output per doc.
        class _Fmt:
            header = ""
            document_separator = "\n"

            def __init__(self):
                self._calls = 0

            def __call__(self, doc, annots):
                self._calls += 1
                if not annots:
                    return ""
                if self._calls == 1:
                    return "introspection\n\ndream of reason"
                return "another universe\n\ninfinitely improbable"

        exporter = _make_exporter(file_path=p, formatter=_Fmt())
        exporter.run([(_doc, _annots), (_doc, _annots)])
        content = p.read_text()
        assert "introspection" in content
        assert "dream of reason" in content
        assert "another universe" in content
        assert "infinitely improbable" in content

    def test_empty_annotations_not_written(self, tmp_path):
        """Doc with no annotations → nothing written."""
        p = tmp_path / "out.md"
        exporter = _make_exporter(file_path=p)
        exporter.run([(_doc, [])])
        assert not p.exists()

    def test_skips_duplicates(self, tmp_path):
        """Existing content → duplicate not appended (threshold 0.75)."""
        p = tmp_path / "out.md"
        p.write_text("line1\n")
        exporter = _make_exporter(file_path=p, duplicates=False)
        exporter.run([(_doc, _annots)])
        # "line1" is a fuzzy duplicate of "line1\n" → filtered.
        # Only "line2" appended.
        assert p.read_text() == "line1\n\nline2"

    def test_duplicates_flag_writes_all(self, tmp_path):
        """duplicates=True → duplicates written anyway."""
        p = tmp_path / "out.md"
        p.write_text("line1\n")
        exporter = _make_exporter(file_path=p, duplicates=True)
        exporter.run([(_doc, _annots)])
        assert p.read_text() == "line1\n\nline1\n\nline2"

    def test_empty_run_no_output(self, tmp_path):
        """No docs → file not created."""
        p = tmp_path / "out.md"
        exporter = _make_exporter(file_path=p)
        exporter.run([])
        assert not p.exists()
