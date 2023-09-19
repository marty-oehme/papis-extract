import chevron

from papis_extract.templating import Markdown, Csv


def test_template_markers():
    ...


def test_markdown_default():
    fmt = Markdown()
    assert (
        chevron.render(
            fmt.string,
            {
                "file": "somefile/somewhere.pdf",
                "quote": "I am quote",
                "note": "and including note.",
                "page": 46,
                "tag": "important",
                "type": "highlight",
            },
        )
        == "#important\n> I am quote [p. 46]\n  NOTE: and including note."
    )


def test_csv_string():
    fmt = Csv()
    assert (
        chevron.render(
            fmt.string,
            {
                "file": "somefile/somewhere.pdf",
                "quote": "I am quote",
                "note": "and including note.",
                "page": 46,
                "tag": "important",
                "type": "highlight",
            },
        )
        == "highlight, important, 46, "
        "I am quote, and including note., somefile/somewhere.pdf"
    )


def test_csv_header():
    fmt = Csv()
    assert chevron.render(fmt.header, {}) == "type, tag, page, quote, note, file"
