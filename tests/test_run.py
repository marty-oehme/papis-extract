"""Tests for ``run()`` exporter dispatching and wiring."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from papis.document import Document

from papis_extract import run as run_fn


_doc = Document(data={"title": "T", "author": "A"})
_annots = [MagicMock()]  # annotation mock — just need non-empty list


def _mock_extractors():
    """Return a list with one mock extractor that can process everything."""
    return [
        MagicMock(
            can_process=MagicMock(return_value=True),
            run=MagicMock(return_value=_annots),
        )
    ]


class TestRunDispatch:
    """Tests for ``run()`` exporter selection based on *write_mode*."""

    @pytest.fixture(autouse=True)
    def _patch_extract(self, monkeypatch):
        """Avoid real extraction — return canned (doc, annots) pairs."""
        monkeypatch.setattr(
            "papis_extract.extraction.extract_all",
            lambda docs, exts: [(_doc, _annots)],
        )

    @staticmethod
    def _patch_exporters(monkeypatch):
        """Replace ``all_exporters`` with MagicMock entries.

        Returns the mock dict so callers can assert on constructor kwargs.
        """
        mocks = {
            "stdout": MagicMock(return_value=MagicMock()),
            "notes": MagicMock(return_value=MagicMock()),
            "file": MagicMock(return_value=MagicMock()),
        }
        monkeypatch.setattr("papis_extract.all_exporters", mocks)
        return mocks

    # ---- stdout ----

    def test_write_mode_none_uses_stdout(self, monkeypatch):
        """write_mode=None → StdoutExporter instantiated."""
        mocks = self._patch_exporters(monkeypatch)
        run_fn(
            [_doc], format_name="count", extractors=_mock_extractors(), write_mode=None
        )
        mocks["stdout"].assert_called_once()
        mocks["notes"].assert_not_called()
        mocks["file"].assert_not_called()

    def test_write_mode_none_default_format_is_atx_setext(self, monkeypatch):
        """No format given + stdout → formatter has setext style."""
        mocks = self._patch_exporters(monkeypatch)
        run_fn([_doc], format_name=None, extractors=_mock_extractors(), write_mode=None)

        # StdoutExporter was called with a formatter that uses setext headings.
        kwargs = mocks["stdout"].call_args[1]
        fmt = kwargs["formatter"]
        assert fmt._headings == "setext"

    # ---- notes ----

    def test_write_mode_notes_uses_notes_exporter(self, monkeypatch):
        """write_mode='notes' → NotesExporter instantiated."""
        mocks = self._patch_exporters(monkeypatch)
        run_fn(
            [_doc],
            format_name="count",
            extractors=_mock_extractors(),
            write_mode="notes",
        )
        mocks["notes"].assert_called_once()
        mocks["stdout"].assert_not_called()
        mocks["file"].assert_not_called()

    def test_write_mode_notes_passes_flags(self, monkeypatch):
        """edit, git, duplicates propagate to NotesExporter."""
        mocks = self._patch_exporters(monkeypatch)
        run_fn(
            [_doc],
            format_name="count",
            extractors=_mock_extractors(),
            write_mode="notes",
            edit=True,
            git=True,
            duplicates=True,
        )
        kwargs = mocks["notes"].call_args[1]
        assert kwargs["edit"] is True
        assert kwargs["git"] is True
        assert kwargs["duplicates"] is True

    def test_write_mode_notes_default_format_is_atx(self, monkeypatch):
        """No format given + notes → formatter has atx style."""
        mocks = self._patch_exporters(monkeypatch)
        run_fn(
            [_doc], format_name=None, extractors=_mock_extractors(), write_mode="notes"
        )

        kwargs = mocks["notes"].call_args[1]
        fmt = kwargs["formatter"]
        assert fmt._headings == "atx"

    # ---- file ----

    def test_write_mode_path_uses_file_exporter(self, monkeypatch):
        """write_mode='/some/path' → FileExporter instantiated."""
        mocks = self._patch_exporters(monkeypatch)
        run_fn(
            [_doc],
            format_name="count",
            extractors=_mock_extractors(),
            write_mode="/tmp/out.md",
        )
        mocks["file"].assert_called_once()
        mocks["stdout"].assert_not_called()
        mocks["notes"].assert_not_called()

    def test_write_mode_path_passes_correct_args(self, monkeypatch):
        """FileExporter gets the right file_path and duplicates flag."""
        mocks = self._patch_exporters(monkeypatch)
        run_fn(
            [_doc],
            format_name="count",
            extractors=_mock_extractors(),
            write_mode="/tmp/out.md",
            duplicates=True,
        )
        kwargs = mocks["file"].call_args[1]
        assert kwargs["file_path"] == Path("/tmp/out.md")
        assert kwargs["duplicates"] is True

    def test_write_mode_path_default_format_is_atx(self, monkeypatch):
        """No format given + file → formatter has atx style."""
        mocks = self._patch_exporters(monkeypatch)
        run_fn(
            [_doc],
            format_name=None,
            extractors=_mock_extractors(),
            write_mode="/tmp/out.md",
        )

        kwargs = mocks["file"].call_args[1]
        fmt = kwargs["formatter"]
        assert fmt._headings == "atx"

    # ---- edge cases ----

    def test_write_mode_empty_string_falls_through_to_stdout(self, monkeypatch):
        """Empty string is falsy → treated as None → stdout."""
        mocks = self._patch_exporters(monkeypatch)
        run_fn(
            [_doc], format_name="count", extractors=_mock_extractors(), write_mode=""
        )
        mocks["stdout"].assert_called_once()
        mocks["notes"].assert_not_called()
        mocks["file"].assert_not_called()

    def test_explicit_format_overrides_default(self, monkeypatch):
        """Explicit --format is always honoured regardless of write_mode."""
        mocks = self._patch_exporters(monkeypatch)
        run_fn(
            [_doc], format_name="csv", extractors=_mock_extractors(), write_mode=None
        )

        kwargs = mocks["stdout"].call_args[1]
        fmt = kwargs["formatter"]
        assert type(fmt).__name__ == "CsvFormatter"
