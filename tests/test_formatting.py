from papis.document import Document

from papis_extract.annotation import Annotation
from papis_extract.formatter import (
    CountFormatter,
    CsvFormatter,
    MarkdownFormatter,
)

document = Document(data={"author": "document-author", "title": "document-title"})
annotations = [
    Annotation("myfile.pdf", content="my lovely text"),
    Annotation("myfile.pdf", content="my second text", note="with note"),
]
md_default_output = """==============   ---------------
document-title - document-author
==============   ---------------

> my lovely text

> my second text
  NOTE: with note"""


def test_markdown_default():
    fmt = MarkdownFormatter()
    assert fmt(document, annotations) == md_default_output


def test_markdown_atx():
    fmt = MarkdownFormatter(headings="atx")
    assert fmt(document, annotations) == (
        """# document-title - document-author

> my lovely text

> my second text
  NOTE: with note"""
    )


def test_markdown_setext():
    fmt = MarkdownFormatter(headings="setext")
    assert fmt(document, annotations) == md_default_output


def test_count_default():
    fmt = CountFormatter()
    assert fmt(document, annotations) == ("""2 document-author: document-title""")


def test_csv_default():
    fmt = CsvFormatter()
    assert fmt(document, annotations) == (
        'Highlight,,0,"my lovely text","","document-author",'
        '"document-title","","myfile.pdf"\n'
        'Highlight,,0,"my second text","with note","document-author",'
        '"document-title","","myfile.pdf"'
    )


def test_csv_header():
    fmt = CsvFormatter()
    assert fmt.header == "type,tag,page,quote,note,author,title,ref,file"


def test_csv_with_header():
    fmt = CsvFormatter()
    body = fmt(document, annotations)
    assert fmt.header + "\n" + body == (
        "type,tag,page,quote,note,author,title,ref,file\n"
        'Highlight,,0,"my lovely text","","document-author",'
        '"document-title","","myfile.pdf"\n'
        'Highlight,,0,"my second text","with note","document-author",'
        '"document-title","","myfile.pdf"'
    )


# sadpath - no annotations contained for each format
def test_markdown_no_annotations():
    assert MarkdownFormatter()(document, []) == ""


def test_count_no_annotations():
    assert CountFormatter()(document, []) == ""


def test_csv_no_annotations():
    assert CsvFormatter()(document, []) == ""


def test_markdown_header_empty():
    assert MarkdownFormatter().header == ""


def test_count_header_empty():
    assert CountFormatter().header == ""


class TestSeparators:
    """Integration-style checks with real formatters."""

    def test_csv_separator_is_newline(self):
        """CSV uses newline separator to avoid blank rows between docs."""
        from papis_extract.formatter import CsvFormatter

        assert CsvFormatter.document_separator == "\n"

    def test_markdown_separator_is_double_newline(self):
        """Markdown uses double-newline for spacing between doc blocks."""
        from papis_extract.formatter import MarkdownFormatter

        assert MarkdownFormatter.document_separator == "\n\n"

    def test_count_separator_is_newline(self):
        from papis_extract.formatter import CountFormatter

        assert CountFormatter.document_separator == "\n"
