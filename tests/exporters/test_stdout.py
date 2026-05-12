"""Tests for StdoutExporter."""

import pytest

from papis.document import Document

from papis_extract.annotation import Annotation
from papis_extract.exporters.stdout import StdoutExporter


# Helpers
_doc_a = Document(data={"title": "Doc A"})
_doc_b = Document(data={"title": "Doc B"})
_annots = [Annotation("file.pdf", content="highlighted text")]


class MockFormatter:
    """Controllable formatter for testing exporters.

    Returns predetermined outputs in sequence. Once exhausted, returns ``""``.
    Tracks calls for assertion.
    """

    def __init__(
        self,
        header: str = "",
        document_separator: str = "\n",
        outputs: list[str] | None = None,
    ) -> None:
        self.header = header
        self.document_separator = document_separator
        self._outputs: list[str] = outputs or []
        self._idx: int = 0
        self.calls: list[tuple[Document, list[Annotation]]] = []

    def __call__(self, document: Document, annotations: list[Annotation]) -> str:
        self.calls.append((document, annotations))
        if self._idx < len(self._outputs):
            result = self._outputs[self._idx]
        else:
            result = ""
        self._idx += 1
        return result


def _make_exporter(
    header: str = "",
    separator: str = "\n",
    outputs: list[str] | None = None,
) -> tuple[StdoutExporter, MockFormatter]:
    fmt = MockFormatter(
        header=header, document_separator=separator, outputs=outputs or []
    )
    return StdoutExporter(formatter=fmt), fmt


# Tests
class TestEmpty:
    """Edge cases that produce no output."""

    def test_empty_doc_list(self, capsys):
        """Nothing printed when the document list is empty."""
        exporter, fmt = _make_exporter()
        exporter.run([])
        captured = capsys.readouterr()
        assert captured.out == ""
        assert fmt.calls == []

    def test_single_doc_empty_output(self, capsys):
        """When formatter returns empty string, nothing is printed."""
        exporter, fmt = _make_exporter(outputs=[""])
        exporter.run([(_doc_a, _annots)])
        captured = capsys.readouterr()
        assert captured.out == ""
        assert len(fmt.calls) == 1

    def test_all_docs_empty(self, capsys):
        """No header and no output when all documents produce empty strings."""
        exporter, fmt = _make_exporter(header="HEADER", outputs=["", "", ""])
        exporter.run([(_doc_a, _annots), (_doc_b, _annots), (_doc_a, _annots)])
        captured = capsys.readouterr()
        assert captured.out == ""
        assert len(fmt.calls) == 3


class TestSingleDoc:
    """Single document with annotations."""

    def test_no_header(self, capsys):
        """Output printed without a header line."""
        exporter, _ = _make_exporter(outputs=["hello world"])
        exporter.run([(_doc_a, _annots)])
        captured = capsys.readouterr()
        assert captured.out == "hello world\n"

    def test_with_header(self, capsys):
        """Header printed once before the output."""
        exporter, _ = _make_exporter(
            header="type,tag,page,quote", outputs=["Highlight,,1"]
        )
        exporter.run([(_doc_a, _annots)])
        captured = capsys.readouterr()
        assert captured.out == "type,tag,page,quote\nHighlight,,1\n"


class TestMultipleDocs:
    """Multiple documents — header emission and separator behavior."""

    def test_header_emitted_only_once(self, capsys):
        """Header appears only before the first document block."""
        exporter, fmt = _make_exporter(
            header="HEADER", separator="\n", outputs=["doc1-out", "doc2-out"]
        )
        exporter.run([(_doc_a, _annots), (_doc_b, _annots)])
        captured = capsys.readouterr()
        assert captured.out == "HEADER\ndoc1-out\ndoc2-out\n"
        assert len(fmt.calls) == 2

    def test_separator_blank_line_between_docs(self, capsys):
        """Using ``\\n\\n`` separator creates a blank line between doc blocks."""
        exporter, fmt = _make_exporter(
            header="HEADER", separator="\n\n", outputs=["first", "second"]
        )
        exporter.run([(_doc_a, _annots), (_doc_b, _annots)])
        captured = capsys.readouterr()
        assert captured.out == "HEADER\nfirst\n\nsecond\n"
        assert len(fmt.calls) == 2

    def test_first_doc_empty_second_has_output(self, capsys):
        """Header deferred until the first non-empty document."""
        exporter, fmt = _make_exporter(
            header="HEADER", separator="\n", outputs=["", "real-output"]
        )
        exporter.run([(_doc_a, _annots), (_doc_b, _annots)])
        captured = capsys.readouterr()
        assert captured.out == "HEADER\nreal-output\n"
        assert len(fmt.calls) == 2

    def test_mixed_empty_and_non_empty(self, capsys):
        """Empty outputs filtered out; non-empty joined with separator."""
        exporter, fmt = _make_exporter(
            header="H", separator="\n", outputs=["hello", "", "world"]
        )
        exporter.run([(_doc_a, _annots), (_doc_b, _annots), (_doc_a, _annots)])
        captured = capsys.readouterr()
        assert captured.out == "H\nhello\nworld\n"
        assert len(fmt.calls) == 3
