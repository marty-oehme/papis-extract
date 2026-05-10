"""Tests for the Readest annotation extractor."""

from pathlib import Path

import pytest

from papis_extract.annotation import Annotation
from papis_extract.extractors.readest import ReadestExtractor


# ── Fixture builder ──────────────────────────────────────────────


def _write_fixture(tmp_path: Path, name: str, content: str) -> Path:
    """Write content to a file in tmp_path and return its Path."""
    filepath = tmp_path / name
    filepath.write_text(content)
    return filepath


# ── can_process() positive ───────────────────────────────────────


# general happy path integration test
def test_can_process_valid_export(tmp_path: Path) -> None:
    """Existing sample file is recognized."""
    ext = ReadestExtractor()
    assert ext.can_process(Path("tests/resources/Readest_sample.txt"))


def test_can_process_marker_on_first_line(tmp_path: Path) -> None:
    """Export where **Exported from Readest** is on the very first line."""
    content = (
        "**Exported from Readest**: 2026-05-10\n"
        "\n"
        "---\n"
        "\n"
        "## Highlights & Annotations\n"
        "\n"
        "> What the teachings do offer is wisdom.\n"
    )
    f = _write_fixture(tmp_path, "export.txt", content)
    ext = ReadestExtractor()
    assert ext.can_process(f)


@pytest.mark.parametrize("ext", [".md", ".txt", ".qmd", ".rmd"])
def test_can_process_accepted_extensions(tmp_path: Path, ext: str) -> None:
    """All accepted extensions are recognized."""
    content = "\n**Exported from Readest**: 2026-05-10\n\n---\n\n> A quote.\n"
    f = _write_fixture(tmp_path, f"export{ext}", content)
    extractor = ReadestExtractor()
    assert extractor.can_process(f)


# ── can_process() negative ───────────────────────────────────────


def test_can_process_rejects_readera_export() -> None:
    """ReadEra exports must not be mistaken for Readest."""
    ext = ReadestExtractor()
    assert not ext.can_process(Path("tests/resources/ReadEra_sample.txt"))


@pytest.mark.parametrize("ext", [".epub", ".pdf"])
def test_can_process_rejects_wrong_extension(tmp_path: Path, ext: str) -> None:
    """Files with non-accepted extensions are rejected."""
    content = "**Exported from Readest**: 2026-05-10\n\n---\n\n> A quote.\n"
    f = _write_fixture(tmp_path, f"export{ext}", content)
    ext_obj = ReadestExtractor()
    assert not ext_obj.can_process(f)


def test_can_process_rejects_binary_file(tmp_path: Path) -> None:
    """Binary files are rejected."""
    f = tmp_path / "binary.txt"
    f.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
    ext = ReadestExtractor()
    assert not ext.can_process(f)


def test_can_process_rejects_nonexistent_file(tmp_path: Path) -> None:
    """Non-existent files are rejected."""
    ext = ReadestExtractor()
    assert not ext.can_process(tmp_path / "does_not_exist.txt")


def test_can_process_rejects_plain_text(tmp_path: Path) -> None:
    """A text file without the Readest export marker is rejected."""
    f = _write_fixture(
        tmp_path, "plain.txt", "Just some plain text.\nNo marker here.\n"
    )
    ext = ReadestExtractor()
    assert not ext.can_process(f)


def test_can_process_rejects_empty_file(tmp_path: Path) -> None:
    """An empty file is rejected."""
    f = _write_fixture(tmp_path, "empty.txt", "")
    ext = ReadestExtractor()
    assert not ext.can_process(f)


# ── run() integration ────────────────────────────────────────────


def test_run_extracts_all_annotations_from_sample() -> None:
    """Full integration test with the existing Readest_sample.txt."""
    ext = ReadestExtractor()
    result = ext.run(Path("tests/resources/Readest_sample.txt"))
    # The sample has 23 "> " lines → 23 annotations
    assert len(result) == 23
    # First annotation
    assert result[0].content == (
        "As an ideological response, this \u201cescapist defeatism\u201d contains elements "
        "of cynicism, in that it also involves an outward rejection of normal social "
        "demands and a pessimistic outlook. The difference between it and cynical "
        "self-interest, however, is that the defeatist doesn\u2019t still want to thrive "
        "within the existing order. Whereas cynical self-interest distances behaviour "
        "from moral values only to really enjoy following dominant demands after all, "
        "the defeatist is less excited by regular notions of success, but cannot "
        "imagine a way out. I believe this position embodies various features of what "
        "Mark Fisher calls \u201ccapitalist realism,\u201d which is less about competitive "
        "spirit or \u201cmaking it\u201d and more a kind of depressed state of low expectation "
        "within a totalizing capitalist reality."
    )
    assert result[0].note == ""
    assert result[0].file == "tests/resources/Readest_sample.txt"


def test_run_extracts_from_marker_on_first_line(tmp_path: Path) -> None:
    """Export with marker on first line yields correct annotations."""
    content = (
        "**Exported from Readest**: 2026-05-10\n"
        "\n"
        "---\n"
        "\n"
        "## Highlights & Annotations\n"
        "\n"
        "> What the teachings do offer is wisdom, but this good thing is always bought "
        "at the price of some discomfort. The human appetite for wisdom, and its "
        "tolerance for discomfort, has never been great, in ancient times or ours. \n"
        "\n"
    )
    f = _write_fixture(tmp_path, "export.txt", content)
    ext = ReadestExtractor()
    result = ext.run(f)
    assert len(result) == 1
    assert result[0].content == (
        "What the teachings do offer is wisdom, but this good thing is always bought "
        "at the price of some discomfort. The human appetite for wisdom, and its "
        "tolerance for discomfort, has never been great, in ancient times or ours."
    )
    assert result[0].note == ""
    assert result[0].file == str(f)


# ── run() edge cases ─────────────────────────────────────────────


def test_run_quote_with_note(tmp_path: Path) -> None:
    """A "> " line followed by **Note**:: captures the note."""
    content = (
        "**Exported from Readest**: 2026-05-10\n"
        "\n"
        "---\n"
        "\n"
        "## Highlights & Annotations\n"
        "\n"
        '> "A quote with a note"\n'
        "**Note**:: This is a note\n"
    )
    f = _write_fixture(tmp_path, "export.txt", content)
    ext = ReadestExtractor()
    result = ext.run(f)
    assert len(result) == 1
    assert result[0].content == "A quote with a note"
    assert result[0].note == "This is a note"


def test_run_quote_without_note(tmp_path: Path) -> None:
    """A "> " line NOT followed by **Note**:: has an empty note."""
    content = (
        "**Exported from Readest**: 2026-05-10\n"
        "\n"
        "---\n"
        "\n"
        "## Highlights & Annotations\n"
        "\n"
        '> "A quote without a note"\n'
        "\n"
    )
    f = _write_fixture(tmp_path, "export.txt", content)
    ext = ReadestExtractor()
    result = ext.run(f)
    assert len(result) == 1
    assert result[0].content == "A quote without a note"
    assert result[0].note == ""


def test_run_empty_file(tmp_path: Path) -> None:
    """An empty file returns an empty list."""
    f = _write_fixture(tmp_path, "empty.txt", "")
    ext = ReadestExtractor()
    assert ext.run(f) == []


def test_run_file_without_quote_lines(tmp_path: Path) -> None:
    """A valid Readest export with no "> " lines returns an empty list."""
    content = (
        "**Exported from Readest**: 2026-05-10\n"
        "\n"
        "---\n"
        "\n"
        "## Highlights & Annotations\n"
        "\n"
        "This chapter has no highlights.\n"
    )
    f = _write_fixture(tmp_path, "export.txt", content)
    ext = ReadestExtractor()
    assert ext.run(f) == []


def test_run_multiple_quotes(tmp_path: Path) -> None:
    """Multiple quotes with mixed notes are correctly extracted."""
    content = (
        "**Exported from Readest**: 2026-05-10\n"
        "\n"
        "---\n"
        "\n"
        "## Highlights & Annotations\n"
        "\n"
        '> "First quote"\n'
        "\n"
        '> "Second quote"\n'
        "**Note**:: Note for second\n"
        "\n"
        '> "Third quote"\n'
        "\n"
    )
    f = _write_fixture(tmp_path, "export.txt", content)
    ext = ReadestExtractor()
    result = ext.run(f)
    assert len(result) == 3
    assert result[0].content == "First quote"
    assert result[0].note == ""
    assert result[1].content == "Second quote"
    assert result[1].note == "Note for second"
    assert result[2].content == "Third quote"
    assert result[2].note == ""
