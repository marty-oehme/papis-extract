import chevron

from papis_extract.annotation_data import Markdown

def test_markdown_default():
    fmt = Markdown()
    assert chevron.render(fmt.string, {
        "file": "somefile/somewhere.pdf",
        "quote": "I am quote",
        "note": "and including note.",
        "page": 46,
        "tag": "important",
        "type": "highlight",
    }) == "#important\n> I am quote [p. 46]\n  NOTE: and including note."
