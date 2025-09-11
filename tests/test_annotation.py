import pytest
from papis.document import Document

from papis_extract.annotation import Annotation


def test_value_inequality_comparison():
    sut = Annotation("myfile", content="Here be content!", note="and a note")
    other = Annotation(
        "myfile", content="Here be different content!", note="but still a note"
    )
    assert sut != other


def test_oder_lt_comparison():
    sut = Annotation("myfile", content="Here be content!", note="and a note", page=2)
    other = Annotation(
        "myfile", content="Here be different content!", note="but still a note", page=10
    )
    assert sut < other


def test_oder_ge_comparison():
    big = Annotation("mf", content="ct", note="nt", page=10)
    small = Annotation("mf", content="ct", note="nt", page=2)
    alsosmall = Annotation("mf", content="ct", note="nt", page=2)
    assert big >= small
    assert small >= alsosmall


def test_oder_gt_comparison_single_nopage():
    zeropage = Annotation("mf", content="ct", note="nt", page=0)
    small = Annotation("mf", content="ct", note="nt", page=2)
    assert zeropage > small


def test_oder_le_comparison_all_nopage():
    zeropage = Annotation("mf", content="ct", note="nt", page=0)
    small = Annotation("mf", content="ct", note="nt", page=0)
    assert zeropage <= small


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
def test_formatting_replacements(fmt_string: str, expected: str):
    sut = Annotation(
        "myfile",
        content="I am the text value",
        note="Whereas I represent the note",
    )

    assert sut.format(fmt_string) == expected


@pytest.mark.parametrize(
    "fmt_string,expected",
    [
        ("{{doc.title}}", "document-title"),
        ("{{doc.title}}-{{doc.author}}", "document-title-document-author"),
        ("{{quote}} ({{doc.author}})", "I am the text value (document-author)"),
    ],
)
def test_formatting_document_access(fmt_string: str, expected: str):
    sut = Annotation(
        "myfile",
        content="I am the text value",
        note="Whereas I represent the note",
    )
    doc = Document(data={"title": "document-title", "author": "document-author"})

    assert sut.format(fmt_string, doc=doc) == expected


def test_colorname_matches_exact():
    sut = Annotation("testfile", color=(1.0, 0.0, 0.0), minimum_similarity_color=1.0)
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
def test_matches_inexact_colorname(color_value: tuple[float, float, float]):
    sut = Annotation("testfile", color=color_value, minimum_similarity_color=0.833)
    c_name = sut.colorname
    assert c_name == "red"
