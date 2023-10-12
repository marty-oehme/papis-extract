from papis.document import Document
from papis_extract.annotation import AnnotatedDocument, Annotation

from papis_extract.formatter import (
    format_count,
    format_csv,
    format_markdown,
    format_markdown_atx,
    format_markdown_setext,
)

an_doc: AnnotatedDocument = AnnotatedDocument(
    Document(data={"author": "document-author", "title": "document-title"}),
    [
        Annotation("myfile.pdf", text="my lovely text"),
        Annotation("myfile.pdf", text="my second text", content="with note"),
    ],
)
md_default_output = """==============   ---------------
document-title - document-author
==============   ---------------

> my lovely text

> my second text
  NOTE: with note"""


def test_markdown_default():
    fmt = format_markdown
    assert fmt([an_doc]) == md_default_output


def test_markdown_atx():
    fmt = format_markdown_atx
    assert fmt([an_doc]) == (
        """# document-title - document-author

> my lovely text

> my second text
  NOTE: with note"""
    )


def test_markdown_setext():
    fmt = format_markdown_setext
    assert fmt([an_doc]) == md_default_output


def test_count_default():
    fmt = format_count
    assert fmt([an_doc]) == ("""document-author - document-title: 2""")


def test_csv_default():
    fmt = format_csv
    assert fmt([an_doc]) == (
        "type,tag,page,quote,note,author,title,ref,file\n"
        'Highlight,,0,"my lovely text","","document-author",'
        '"document-title","","myfile.pdf"\n'
        'Highlight,,0,"my second text","with note","document-author",'
        '"document-title","","myfile.pdf"'
    )


# sadpath - no annotations contained for each format
def test_markdown_no_annotations():
    d: AnnotatedDocument = AnnotatedDocument(Document(data={}), [])
    assert format_markdown([d]) == ""


def test_count_no_annotations():
    d: AnnotatedDocument = AnnotatedDocument(Document(data={}), [])
    assert format_count([d]) == ""


def test_csv_no_annotations():
    d: AnnotatedDocument = AnnotatedDocument(Document(data={}), [])
    assert format_csv([d]) == "type,tag,page,quote,note,author,title,ref,file"
