from papis.document import Document
import pytest
from papis_extract.annotation import Annotation


@pytest.mark.parametrize(
    "fmt_string,expected",
    [
        ("{{quote}}", "I am the text value"),
        (
            "> {{quote}}\n{{#note}}Note: {{note}}{{/note}}",
            "> I am the text value\nNote: Whereas I represent the note",
        ),
        (
            "{{#note}}Note: {{note}}{{/note}}{{#page}}, p. {{page}}{{/page}}",
            "Note: Whereas I represent the note",
        ),
    ],
)
def test_formatting_replacements(fmt_string, expected):
    sut = Annotation(
        "myfile",
        text="I am the text value",
        content="Whereas I represent the note",
    )

    assert sut.format(fmt_string) == expected

@pytest.mark.parametrize(
    "fmt_string,expected",
    [
        ("{{doc.title}}", "document-title"),
        ("{{doc.title}}-{{doc.author}}", "document-title-document-author"),
        ("{{quote}} ({{doc.author}})", "I am the text value (document-author)"),
    ]
)
def test_formatting_document_access(fmt_string, expected):
    sut = Annotation(
        "myfile",
        text="I am the text value",
        content="Whereas I represent the note",
    )
    doc = Document(data= {"title": "document-title", "author": "document-author"})

    assert sut.format(fmt_string, doc=doc) == expected

def test_colorname_matches_exact():
    sut = Annotation("testfile", colors=(1.0, 0.0, 0.0), minimum_similarity_color=1.0)
    c_name = sut.colorname
    assert c_name == "red"


# TODO inject closeness value instead of relying on default
@pytest.mark.parametrize(
    "color_value",
    [
        (1.0, 0.0, 0.0),
        (0.9, 0.0, 0.0),
        (0.8, 0.0, 0.0),
        (0.7, 0.0, 0.0),
        (0.51, 0.0, 0.0),
    ],
)
def test_matches_inexact_colorname(color_value):
    sut = Annotation("testfile", colors=color_value, minimum_similarity_color=0.833)
    c_name = sut.colorname
    assert c_name == "red"
