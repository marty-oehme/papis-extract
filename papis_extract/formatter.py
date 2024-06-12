from typing import Protocol
from papis.document import Document

from papis_extract.annotation import Annotation

class Formatter(Protocol):
    """Basic formatter protocol.

    Every valid formatter must implement at least this protocol.
    A formatter is a function which receives a document and a list
    of annotations and spits them out in some formatted way.

    Formatters additionally must take the (often optional) passed
    parameter 'first' which signals to the formatter that the current
    document entry is the very first one to be printed in whatever
    exporter is used, if multiple entries are printed.
    This can be useful for adding a header if necessary for the format.
    """
    def __call__(self, document: Document, annotations: list[Annotation], first: bool) -> str:
        ...


def format_markdown(
    document: Document = Document(),
    annotations: list[Annotation] = [],
    first: bool = False,
    headings: str = "setext",  # setext | atx | None
) -> str:
    if not annotations:
        return ""
    template = (
        "{{#tag}}#{{tag}}\n{{/tag}}"
        "{{#quote}}> {{quote}}{{/quote}}{{#page}} [p. {{page}}]{{/page}}"
        "{{#note}}\n  NOTE: {{note}}{{/note}}"
    )
    output = ""

    heading = f"{document.get('title', '')} - {document.get('author', '')}"
    if headings == "atx":
        output += f"# {heading}\n\n"
    elif headings == "setext":
        title_decoration = (
            f"{'=' * len(document.get('title', ''))}   "
            f"{'-' * len(document.get('author', ''))}"
        )
        output += f"{title_decoration}\n{heading}\n{title_decoration}\n\n"

    for a in annotations:
        output += a.format(template)
        output += "\n\n"

    output += "\n\n\n"

    return output.rstrip()


def format_markdown_atx(
    document: Document = Document(),
    annotations: list[Annotation] = [],
    first: bool = False,
) -> str:
    return format_markdown(document, annotations, headings="atx")


def format_markdown_setext(
    document: Document = Document(),
    annotations: list[Annotation] = [],
    first: bool = False,
) -> str:
    return format_markdown(document, annotations, headings="setext")


def format_count(
    document: Document = Document(),
    annotations: list[Annotation] = [],
    first: bool = False,
) -> str:
    if not annotations:
        return ""

    count = 0
    for _ in annotations:
        count += 1

    return (
        f"{count} "
        f"{document.get('author', '')}"
        f"{': ' if 'author' in document else ''}"  # only put separator if author
        f"{document.get('title', '')}"
    ).rstrip()


def format_csv(
    document: Document = Document(),
    annotations: list[Annotation] = [],
    first: bool = False,
) -> str:
    header: str = "type,tag,page,quote,note,author,title,ref,file"
    template: str = (
        '{{type}},{{tag}},{{page}},"{{quote}}","{{note}}",'
        '"{{doc.author}}","{{doc.title}}","{{doc.ref}}","{{file}}"'
    )
    output = f"{header}\n" if first else ""
    if not annotations:
        return ""

    for a in annotations:
        output += a.format(template, doc=document)
        output += "\n"

    return output.rstrip()


formatters: dict[str, Formatter] = {
    "count": format_count,
    "csv": format_csv,
    "markdown": format_markdown,
    "markdown-atx": format_markdown_atx,
    "markdown-setext": format_markdown_setext,
}
