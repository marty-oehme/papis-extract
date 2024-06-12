from papis.document import Document
from papis_extract.annotation import Annotation

from papis_extract.formatter import (
    format_count,
    format_csv,
    format_markdown,
    format_markdown_atx,
    format_markdown_setext,
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
    fmt = format_markdown
    assert fmt(document, annotations) == md_default_output


def test_markdown_atx():
    fmt = format_markdown_atx
    assert fmt(document, annotations) == (
        """# document-title - document-author

> my lovely text

> my second text
  NOTE: with note"""
    )


def test_markdown_setext():
    fmt = format_markdown_setext
    assert fmt(document, annotations) == md_default_output


def test_count_default():
    fmt = format_count
    assert fmt(document, annotations) == ("""2 document-author: document-title""")


def test_csv_default():
    fmt = format_csv
    assert fmt(document, annotations) == (
        "type,tag,page,quote,note,author,title,ref,file\n"
        'Highlight,,0,"my lovely text","","document-author",'
        '"document-title","","myfile.pdf"\n'
        'Highlight,,0,"my second text","with note","document-author",'
        '"document-title","","myfile.pdf"'
    )


# sadpath - no annotations contained for each format
def test_markdown_no_annotations():
    assert format_markdown(document, []) == ""


def test_count_no_annotations():
    assert format_count(document, []) == ""


def test_csv_no_annotations():
    assert format_csv(document, []) == ""
