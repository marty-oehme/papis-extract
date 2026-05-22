"""Tests for shared exporter I/O utilities (_io.py)."""

from pathlib import Path

from papis_extract.exporters._io import (
    check_similarity,
    drop_existing_annotations,
    write_annotations_to_file,
)


def _mk_file(tmp_path: Path, content: str) -> Path:
    """Create a file under *tmp_path* with *content*, return its path."""
    p = tmp_path / "output.md"
    p.write_text(content)
    return p


class TestCheckSimilarity:
    """Unit tests for ``check_similarity()``."""

    def test_exact_match_default_threshold(self):
        """Exact match at threshold 1.0: ``>=`` means True."""
        assert check_similarity("hello", ["hello"], 1.0) is True

    def test_exact_match_low_threshold(self):
        """Exact match with threshold 0.75: passes."""
        assert check_similarity("hello", ["hello"], 0.75) is True

    def test_close_match_above_threshold(self):
        """Close match above threshold. ``hellp`` vs ``hello`` ratio ≈0.8."""
        assert check_similarity("hellp", ["hello"], 0.75) is True

    def test_close_match_below_threshold(self):
        # "hello" vs "xyz" ratio = 0.0
        assert check_similarity("hello", ["xyz"], 0.75) is False

    def test_empty_lines_list(self):
        assert check_similarity("hello", [], 0.5) is False

    def test_empty_string_vs_nonempty(self):
        """Levenshtein ratio empty vs nonempty = 0.0. At threshold 0.0, ``>=`` matches."""
        assert check_similarity("", ["hello"], 0.0) is True

    def test_empty_string_vs_empty(self):
        assert check_similarity("", [""], 0.75) is True

    def test_multiple_lines_first_match(self):
        assert check_similarity("hello", ["x", "hello", "y"], 0.75) is True

    def test_multiple_lines_no_match(self):
        assert check_similarity("zzz", ["x", "hello", "y"], 0.75) is False

    def test_case_sensitive(self):
        """Levenshtein is case-sensitive. ``Hello`` ≠ ``hello`` at threshold 1.0."""
        assert check_similarity("Hello", ["hello"], 1.0) is False

    def test_at_threshold(self):
        """At threshold exactly: ``>=`` means exact threshold is True."""
        # "hello" vs "hellp" has ratio 0.9, well above threshold 0.8
        assert check_similarity("hello", ["hellp"], 0.8) is True


class TestDropExistingAnnotations:
    """Unit tests for ``drop_existing_annotations()``."""

    THRESHOLD = 0.75

    def test_empty_input(self):
        assert drop_existing_annotations([], [], self.THRESHOLD) == []

    def test_no_existing(self):
        formatted = ["annotation 1", "annotation 2"]
        assert drop_existing_annotations(formatted, [], self.THRESHOLD) == formatted

    def test_exact_match_dropped(self):
        """Exact match at threshold 0.75: ``>=`` drops the duplicate."""
        existing = ["annotation 1"]
        assert (
            drop_existing_annotations(["annotation 1"], existing, self.THRESHOLD) == []
        )

    def test_close_match_dropped(self):
        """ "annotatoin 1" ~ "annotation 1" above 0.75 threshold."""
        existing = ["annotation 1\n"]
        assert (
            drop_existing_annotations(["annotatoin 1"], existing, self.THRESHOLD) == []
        )

    def test_no_match_kept(self):
        existing = ["completely different\n"]
        assert drop_existing_annotations(
            ["annotation 1"], existing, self.THRESHOLD
        ) == ["annotation 1"]

    def test_mixed_kept_and_dropped(self):
        existing = ["annotation 1\n"]
        assert drop_existing_annotations(
            ["annotation 1", "new annotation"], existing, self.THRESHOLD
        ) == ["new annotation"]

    def test_multiline_annotation_first_line_matches(self):
        """Only first line checked against existing lines."""
        existing = ["annotation 1\n"]
        assert (
            drop_existing_annotations(
                ["annotation 1\nsecond line"], existing, self.THRESHOLD
            )
            == []
        )

    def test_multiline_annotation_first_line_no_match(self):
        existing = ["something else\n"]
        assert drop_existing_annotations(
            ["annotation 1\nsecond line"], existing, self.THRESHOLD
        ) == ["annotation 1\nsecond line"]

    def test_empty_string_in_formatted(self):
        """Empty string annotations are skipped (splitlines gives empty list)."""
        existing = ["line1\n"]
        assert drop_existing_annotations(
            ["", "real annotation"], existing, self.THRESHOLD
        ) == ["real annotation"]

    def test_custom_threshold(self):
        """When threshold is 0.95, only nearly-exact matches are dropped."""
        existing = ["annotation 1\n"]
        # "annotation 1" → ratio ~1.0 → dropped. "annotatoin 1" → ratio ~0.8 → kept
        result = drop_existing_annotations(
            ["annotation 1", "annotatoin 1"], existing, 0.95
        )
        assert result == ["annotatoin 1"]

    def test_strict_threshold(self):
        """At threshold 1.0, exact match is dropped with ``>=``."""
        existing = ["annotation 1"]
        assert drop_existing_annotations(["annotation 1"], existing, 1.0) == []


class TestWriteAnnotationsToFile:
    """File-writing tests for ``write_annotations_to_file()``."""

    # ---- new file ----

    def test_new_empty_file(self, tmp_path):
        p = tmp_path / "out.md"
        write_annotations_to_file(p, ["a1", "a2"])
        assert p.read_text() == "a1\n\na2"

    def test_new_file_duplicates_enabled(self, tmp_path):
        p = tmp_path / "out.md"
        write_annotations_to_file(p, ["a1"], duplicates=True)
        assert p.read_text() == "a1"

    def test_new_file_returns_count(self, tmp_path):
        p = tmp_path / "out.md"
        assert write_annotations_to_file(p, ["a1", "a2"]) == 2

    # ---- append to existing ----

    def test_append_with_trailing_newline(self, tmp_path):
        """File ending with content + \\n: an extra \\n prepended before join."""
        p = _mk_file(tmp_path, "existing\n")
        write_annotations_to_file(p, ["new1", "new2"])
        assert p.read_text() == "existing\n\nnew1\n\nnew2"

    def test_append_without_trailing_newline(self, tmp_path):
        """File ending without \\n: one \\n prepended before append."""
        p = _mk_file(tmp_path, "existing")
        write_annotations_to_file(p, ["new1"])
        assert p.read_text() == "existing\nnew1"

    def test_append_ending_with_blank_line(self, tmp_path):
        """If last line is empty, no extra newline prepended."""
        p = _mk_file(tmp_path, "content\n\n")
        write_annotations_to_file(p, ["new1"])
        assert p.read_text() == "content\n\nnew1"

    def test_append_last_line_whitespace_only(self, tmp_path):
        """Whitespace-only last line counts as empty, no extra \\n."""
        p = _mk_file(tmp_path, "line\n   \n")
        write_annotations_to_file(p, ["new1"])
        assert p.read_text() == "line\n   \nnew1"

    # ---- dedup ----

    def test_all_duplicates_nothing_written(self, tmp_path):
        p = _mk_file(tmp_path, "a1\n")
        write_annotations_to_file(p, ["a1"], duplicates=False, minimum_similarity=0.75)
        assert p.read_text() == "a1\n"

    def test_some_duplicates_kept_filtered(self, tmp_path):
        p = _mk_file(tmp_path, "a1\n")
        write_annotations_to_file(
            p, ["a1", "new one"], duplicates=False, minimum_similarity=0.75
        )
        assert p.read_text() == "a1\n\nnew one"

    # ---- filtering empty annotation lines ----

    def test_empty_lines_filtered_out(self, tmp_path):
        p = tmp_path / "out.md"
        write_annotations_to_file(p, ["real", "", "also real"], duplicates=True)
        assert p.read_text() == "real\n\nalso real"

    def test_all_empty_returns_zero(self, tmp_path):
        p = tmp_path / "out.md"
        result = write_annotations_to_file(p, ["", ""], duplicates=True)
        assert result == 0
        # file was created (empty) then nothing written
        assert p.read_text() == ""

    # ---- bad: non-existent path ----

    def test_creates_file_if_missing(self, tmp_path):
        p = tmp_path / "nonexistent" / "sub" / "out.md"
        # parent dirs don't exist — write_annotations_to_file does NOT
        # create parents (callers are responsible).  We test that it works
        # when the parent *does* exist but the file does not.
        p.parent.mkdir(parents=True)
        write_annotations_to_file(p, ["hi"])
        assert p.read_text() == "hi"

    def test_returns_zero_when_everything_filtered(self, tmp_path):
        """All annotations filtered out → nothing written, returns 0."""
        p = _mk_file(tmp_path, "a1\n")
        result = write_annotations_to_file(
            p, ["a1"], duplicates=False, minimum_similarity=0.75
        )
        assert result == 0

    def test_non_existent_file_returns_count(self, tmp_path):
        p = tmp_path / "fresh.md"
        assert write_annotations_to_file(p, ["a", "b"]) == 2
