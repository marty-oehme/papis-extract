import pytest
from papis_extract.annotation_data import Annotation


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
def test_formatting(fmt_string, expected):
    sut = Annotation(
        "myfile",
        text="I am the text value",
        content="Whereas I represent the note",
    )

    assert sut.format(fmt_string) == expected

def test_colorname_matches_exact():
    sut = Annotation(
        "testfile", colors={"stroke": (1.0,0.0,0.0)}, minimum_similarity_color=1.0
    )
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
    sut = Annotation(
        "testfile", colors={"stroke": color_value}, minimum_similarity_color=0.833
    )
    c_name = sut.colorname
    assert c_name == "red"
