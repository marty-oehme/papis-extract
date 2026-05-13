"""Tests for NotesExporter."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from papis.document import Document

from papis_extract.annotation import Annotation
from papis_extract.exporters.notes import NotesExporter


# Helpers
_doc = Document(data={"title": "The Book", "author": "Someone"})
_annots = [Annotation("file.pdf", content="highlighted text")]


def _make_exporter(
    *,
    edit: bool = False,
    git: bool = False,
    duplicates: bool = False,
    formatter=None,
) -> NotesExporter:
    """Create a NotesExporter with optional overrides.

    If *formatter* is not given, a simple mock is used that returns
    ``"line1\\nline2"`` for any non-empty annotation list and ``""``
    for empty lists.
    """
    if formatter is None:

        class _Fmt:
            header = ""
            document_separator = "\n"

            def __call__(self, doc, annots):
                return "line1\nline2" if annots else ""

        formatter = _Fmt()
    return NotesExporter(formatter=formatter, edit=edit, git=git, duplicates=duplicates)


def _mk_notes_file(tmp_path: Path, content: str) -> Path:
    """Create a temporary notes file, return its path."""
    notes = tmp_path / "notes.md"
    notes.write_text(content)
    return notes


class TestTestSimilarity:
    """Unit tests for ``NotesExporter._test_similarity()``."""

    @pytest.fixture
    def exporter(self):
        return _make_exporter()

    def test_exact_match_default_threshold(self, exporter):
        """Exact match at threshold 1.0: ``>=`` means True."""
        assert exporter._test_similarity("hello", ["hello"], 1.0) is True

    def test_exact_match_low_threshold(self, exporter):
        """Exact match with threshold 0.75: passes."""
        assert exporter._test_similarity("hello", ["hello"], 0.75) is True

    def test_close_match_above_threshold(self, exporter):
        """Close match above threshold. ``hellp`` vs ``hello`` ratio ≈0.8."""
        assert exporter._test_similarity("hellp", ["hello"], 0.75) is True

    def test_close_match_below_threshold(self, exporter):
        # "hello" vs "xyz" ratio = 0.0
        assert exporter._test_similarity("hello", ["xyz"], 0.75) is False

    def test_empty_lines_list(self, exporter):
        assert exporter._test_similarity("hello", [], 0.5) is False

    def test_empty_string_vs_nonempty(self, exporter):
        """Levenshtein ratio empty vs nonempty = 0.0. At threshold 0.0, ``>=`` matches."""
        assert exporter._test_similarity("", ["hello"], 0.0) is True

    def test_empty_string_vs_empty(self, exporter):
        assert exporter._test_similarity("", [""], 0.75) is True

    def test_multiple_lines_first_match(self, exporter):
        assert exporter._test_similarity("hello", ["x", "hello", "y"], 0.75) is True

    def test_multiple_lines_no_match(self, exporter):
        assert exporter._test_similarity("zzz", ["x", "hello", "y"], 0.75) is False

    def test_case_sensitive(self, exporter):
        """Levenshtein is case-sensitive. ``Hello`` ≠ ``hello`` at threshold 1.0."""
        assert exporter._test_similarity("Hello", ["hello"], 1.0) is False

    def test_at_threshold(self, exporter):
        """At threshold exactly: ``>=`` means exact threshold is True."""
        # "hello" vs "hellp" has ratio 0.9, well above threshold 0.8
        assert exporter._test_similarity("hello", ["hellp"], 0.8) is True


class TestDropExistingAnnotations:
    """Unit tests for ``NotesExporter._drop_existing_annotations()``."""

    @pytest.fixture(autouse=True)
    def _set_similarity(self, monkeypatch):
        monkeypatch.setattr("papis.config.getfloat", lambda k, s: 0.75)

    @pytest.fixture
    def exporter(self):
        return _make_exporter()

    def test_empty_input(self, exporter):
        assert exporter._drop_existing_annotations([], []) == []

    def test_no_existing(self, exporter):
        formatted = ["annotation 1", "annotation 2"]
        assert exporter._drop_existing_annotations(formatted, []) == formatted

    def test_exact_match_dropped(self, exporter):
        """Exact match at threshold 0.75: ``>=`` drops the duplicate."""
        existing = ["annotation 1"]
        assert exporter._drop_existing_annotations(["annotation 1"], existing) == []

    def test_close_match_dropped(self, exporter):
        """ "annotatoin 1" ~ "annotation 1" above 0.75 threshold."""
        existing = ["annotation 1\n"]
        assert exporter._drop_existing_annotations(["annotatoin 1"], existing) == []

    def test_no_match_kept(self, exporter):
        existing = ["completely different\n"]
        assert exporter._drop_existing_annotations(["annotation 1"], existing) == [
            "annotation 1"
        ]

    def test_mixed_kept_and_dropped(self, exporter):
        existing = ["annotation 1\n"]
        assert exporter._drop_existing_annotations(
            ["annotation 1", "new annotation"], existing
        ) == ["new annotation"]

    # TODO: This will be changed in refactor
    def test_multiline_annotation_first_line_matches(self, exporter):
        """Only first line checked against existing lines."""
        existing = ["annotation 1\n"]
        assert (
            exporter._drop_existing_annotations(["annotation 1\nsecond line"], existing)
            == []
        )

    def test_multiline_annotation_first_line_no_match(self, exporter):
        existing = ["something else\n"]
        assert exporter._drop_existing_annotations(
            ["annotation 1\nsecond line"], existing
        ) == ["annotation 1\nsecond line"]

    def test_empty_string_in_formatted(self, exporter):
        """Empty string annotations are skipped (splitlines gives empty list)."""
        existing = ["line1\n"]
        assert exporter._drop_existing_annotations(
            ["", "real annotation"], existing
        ) == ["real annotation"]

    def test_custom_threshold_from_config(self, monkeypatch, exporter):
        """When config returns 0.95, only nearly-exact matches are dropped."""
        monkeypatch.setattr("papis.config.getfloat", lambda k, s: 0.95)
        existing = ["annotation 1\n"]
        # "annotation 1" → ratio ~1.0 → dropped. "annotatoin 1" → ratio ~0.8 → kept
        result = exporter._drop_existing_annotations(
            ["annotation 1", "annotatoin 1"], existing
        )
        assert result == ["annotatoin 1"]

    def test_config_returns_none_uses_1_0(self, monkeypatch, exporter):
        """None from config → defaults to 1.0. Exact match is dropped with ``>=``."""
        monkeypatch.setattr("papis.config.getfloat", lambda k, s: None)
        existing = ["annotation 1"]
        assert exporter._drop_existing_annotations(["annotation 1"], existing) == []


# _add_annots_to_note: file I/O tests
class TestAddAnnotsToNote:
    """File-writing tests for ``NotesExporter._add_annots_to_note()``."""

    @pytest.fixture(autouse=True)
    def _mock_describe(self, monkeypatch):
        monkeypatch.setattr("papis.document.describe", lambda doc: "The Book - Someone")

    @pytest.fixture
    def notes_file(self, tmp_path):
        return _mk_notes_file(tmp_path, "")

    @pytest.fixture
    def exporter(self):
        return _make_exporter()

    @staticmethod
    def _patch_notes_path(monkeypatch, notes_file):
        monkeypatch.setattr(
            "papis.notes.notes_path_ensured", lambda doc: str(notes_file)
        )

    # ---- new file ----

    def test_new_empty_file(self, monkeypatch, exporter, notes_file):
        self._patch_notes_path(monkeypatch, notes_file)
        exporter._add_annots_to_note(_doc, ["a1", "a2"])
        assert notes_file.read_text() == "a1\n\na2"

    def test_new_file_duplicates_enabled(self, monkeypatch, exporter, notes_file):
        self._patch_notes_path(monkeypatch, notes_file)
        exporter._add_annots_to_note(_doc, ["a1"], duplicates=True)
        assert notes_file.read_text() == "a1"

    # ---- append to existing ----

    def test_append_with_trailing_newline(self, monkeypatch, exporter, tmp_path):
        """File ending with content + \\n: an extra \\n prepended before join."""
        notes = _mk_notes_file(tmp_path, "existing\n")
        self._patch_notes_path(monkeypatch, notes)
        exporter._add_annots_to_note(_doc, ["new1", "new2"])
        # existing (with \n) + \n (prepended) + annotations
        assert notes.read_text() == "existing\n\nnew1\n\nnew2"

    def test_append_without_trailing_newline(self, monkeypatch, exporter, tmp_path):
        """File ending without \\n: one \\n prepended before append."""
        notes = _mk_notes_file(tmp_path, "existing")
        self._patch_notes_path(monkeypatch, notes)
        exporter._add_annots_to_note(_doc, ["new1"])
        assert notes.read_text() == "existing\nnew1"

    def test_append_ending_with_blank_line(self, monkeypatch, exporter, tmp_path):
        """If last line is empty, no extra newline prepended."""
        notes = _mk_notes_file(tmp_path, "content\n\n")
        self._patch_notes_path(monkeypatch, notes)
        exporter._add_annots_to_note(_doc, ["new1"])
        assert notes.read_text() == "content\n\nnew1"

    def test_append_last_line_whitespace_only(self, monkeypatch, exporter, tmp_path):
        """Whitespace-only last line counts as empty, no extra \\n."""
        notes = _mk_notes_file(tmp_path, "line\n   \n")
        self._patch_notes_path(monkeypatch, notes)
        exporter._add_annots_to_note(_doc, ["new1"])
        assert notes.read_text() == "line\n   \nnew1"

    # ---- dedup ----

    def test_all_duplicates_nothing_written(self, monkeypatch, exporter, tmp_path):
        notes = _mk_notes_file(tmp_path, "a1\n")
        self._patch_notes_path(monkeypatch, notes)
        monkeypatch.setattr("papis.config.getfloat", lambda k, s: 0.75)
        exporter._add_annots_to_note(_doc, ["a1"], duplicates=False)
        assert notes.read_text() == "a1\n"

    def test_some_duplicates_kept_filtered(self, monkeypatch, exporter, tmp_path):
        notes = _mk_notes_file(tmp_path, "a1\n")
        self._patch_notes_path(monkeypatch, notes)
        monkeypatch.setattr("papis.config.getfloat", lambda k, s: 0.75)
        exporter._add_annots_to_note(_doc, ["a1", "new one"], duplicates=False)
        # existing ends with \n → prepend \n → write non-duplicate
        assert notes.read_text() == "a1\n\nnew one"

    # ---- filtering empty annotation lines ----

    def test_empty_lines_filtered_out(self, monkeypatch, exporter, notes_file):
        self._patch_notes_path(monkeypatch, notes_file)
        exporter._add_annots_to_note(_doc, ["real", "", "also real"], duplicates=True)
        assert notes_file.read_text() == "real\n\nalso real"

    # ---- git ----

    def test_git_commit(self, monkeypatch, exporter, notes_file):
        self._patch_notes_path(monkeypatch, notes_file)
        monkeypatch.setattr("papis.document.describe", lambda doc: "Test Doc")

        doc = Document(data={"title": "T"})
        doc.get_main_folder = MagicMock(return_value=Path("/folder"))
        doc.get_info_file = MagicMock(return_value=Path("/folder/info.yaml"))

        mock_commit = MagicMock()
        monkeypatch.setattr("papis.git.add_and_commit_resources", mock_commit)

        exporter._add_annots_to_note(doc, ["a"], git=True)

        mock_commit.assert_called_once_with(
            Path("/folder"),
            [str(notes_file), Path("/folder/info.yaml")],
            "Update annotations for 'Test Doc'",
        )

    def test_git_no_folder_skipped(self, monkeypatch, exporter, notes_file):
        self._patch_notes_path(monkeypatch, notes_file)

        doc = Document(data={"title": "T"})
        doc.get_main_folder = MagicMock(return_value=None)

        mock_commit = MagicMock()
        monkeypatch.setattr("papis.git.add_and_commit_resources", mock_commit)

        exporter._add_annots_to_note(doc, ["a"], git=True)
        mock_commit.assert_not_called()


class TestRun:
    """Orchestration tests for ``NotesExporter.run()``."""

    @pytest.fixture
    def exporter(self):
        return _make_exporter()

    def test_empty_doc_list(self, exporter):
        """Smoketest: Does not crash on empty list"""
        exporter.run([])

    def test_single_doc_with_annotations(self, exporter):
        mock_add = MagicMock()
        exporter._add_annots_to_note = mock_add
        exporter.run([(_doc, _annots)])
        mock_add.assert_called_once()
        args = mock_add.call_args[0]
        assert args[0] is _doc
        assert args[1] == ["line1", "line2"]  # "line1\nline2".split("\n")
        assert mock_add.call_args[1] == {"duplicates": False}

    def test_single_doc_empty_annotations(self, exporter):
        """Empty annotations → formatter returns '' → split("\\n")=[""] → called."""
        mock_add = MagicMock()
        exporter._add_annots_to_note = mock_add
        exporter.run([(_doc, [])])
        mock_add.assert_called_once_with(_doc, [""], duplicates=False)

    def test_multiple_docs(self, exporter):
        mock_add = MagicMock()
        exporter._add_annots_to_note = mock_add
        exporter.run([(_doc, _annots), (_doc, _annots)])
        assert mock_add.call_count == 2

    def test_duplicates_flag_passed(self, exporter):
        exporter.duplicates = True
        mock_add = MagicMock()
        exporter._add_annots_to_note = mock_add
        exporter.run([(_doc, _annots)])
        assert mock_add.call_args[1] == {"duplicates": True}

    def test_edit_flag(self, monkeypatch):
        mock_edit = MagicMock()
        monkeypatch.setattr("papis.commands.edit.edit_notes", mock_edit)
        exporter = _make_exporter(edit=True)
        mock_add = MagicMock()
        exporter._add_annots_to_note = mock_add
        exporter.run([(_doc, _annots)])
        mock_edit.assert_called_once_with(_doc, git=False)

    def test_edit_with_git_flag(self, monkeypatch):
        mock_edit = MagicMock()
        monkeypatch.setattr("papis.commands.edit.edit_notes", mock_edit)
        exporter = _make_exporter(edit=True, git=True)
        mock_add = MagicMock()
        exporter._add_annots_to_note = mock_add
        exporter.run([(_doc, _annots)])
        mock_edit.assert_called_once_with(_doc, git=True)

    def test_edit_not_called_when_false(self):
        """When edit=False, edit_notes() is never invoked."""
        exporter = _make_exporter(edit=False)
        mock_add = MagicMock()
        exporter._add_annots_to_note = mock_add
        exporter.run([(_doc, _annots)])
        # passes if no exception (edit_notes would crash without DB)

    def test_header_prepended_to_output(self):
        class _Fmt:
            header = "COL1,COL2"
            document_separator = "\n"

            def __call__(self, doc, annots):
                return "row1" if annots else ""

        exporter = _make_exporter(formatter=_Fmt())
        mock_add = MagicMock()
        exporter._add_annots_to_note = mock_add
        exporter.run([(_doc, _annots)])
        # "COL1,COL2\nrow1".split("\n") = ["COL1,COL2", "row1"]
        assert mock_add.call_args[0][1] == ["COL1,COL2", "row1"]

    def test_header_but_empty_formatter_output(self):
        """Header only: formatter returns '' but header prepended and passed.

        An empty formatter output fed to ``run()`` results in the header line being
        passed to ``_add_annots_to_note`` even if there are no annotation rows.
        """

        class _Fmt:
            header = "COL1,COL2"
            document_separator = "\n"

            def __call__(self, doc, annots):
                return ""

        exporter = _make_exporter(formatter=_Fmt())
        mock_add = MagicMock()
        exporter._add_annots_to_note = mock_add
        exporter.run([(_doc, [])])
        # "COL1,COL2\n".split("\n") = ["COL1,COL2", ""]
        mock_add.assert_called_once()

    def test_formatter_output_only_whitespace(self):
        """Edge case: output is only newlines."""

        class _Fmt:
            header = ""
            document_separator = "\n"

            def __call__(self, doc, annots):
                return "\n\n"

        exporter = _make_exporter(formatter=_Fmt())
        mock_add = MagicMock()
        exporter._add_annots_to_note = mock_add
        exporter.run([(_doc, _annots)])
        # "\n\n".split("\n") = ["", "", ""] → truthy → called
        mock_add.assert_called_once()
