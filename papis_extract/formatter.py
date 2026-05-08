"""Formatters that convert annotations into output strings.

Each formatter receives a document and its annotations and returns
a single formatted string. Formatters are registered in the
``formatters`` dict and selected via the ``--format`` CLI flag.
"""

from collections.abc import Callable
from typing import Protocol

import chevron
from papis.document import Document

from papis_extract.annotation import Annotation


def format_annotation(
    annotation: Annotation,
    template: str,
    doc: Document | None = None,
) -> str:
    """Render an annotation against a Mustache template.

    Builds a data dictionary from the annotation's fields and the
    optional document, then renders it through ``chevron``.

    The template may reference annotation fields directly (e.g.,
    ``{{quote}}``, ``{{tag}}``, ``{{page}}``, ``{{note}}``,
    ``{{type}}``, ``{{file}}``) and document fields via ``{{doc.*}}``
    (e.g. ``{{doc.author}}``, ``{{doc.title}}``, ``{{doc.ref}}``).
    """
    if doc is None:
        doc = Document()
    data = {
        "file": annotation.file,
        "quote": annotation.content,
        "note": annotation.note,
        "page": annotation.page,
        "tag": annotation.tag,
        "type": annotation.type,
        "doc": doc,
    }
    return chevron.render(template, data)


class Formatter(Protocol):
    """Format annotations for a single document.

    A formatter receives a single document and its annotations and returns
    a formatted string. Some formatters may additionally provide a
    header (e.g. CSV column names) via a 'header' property.
    """

    header: str

    def __call__(self, document: Document, annotations: list[Annotation]) -> str:
        """Format annotations for a single document into a string.

        Args:
            document: The papis document containing metadata.
            annotations: The list of annotations to format.

        Returns:
            A formatted string, or empty string if there are no annotations.
        """
        ...


def format_markdown(
    document: Document = Document(),
    annotations: list[Annotation] = [],
    headings: str = "setext",  # setext | atx | None
) -> str:
    """Format annotations as Markdown with a document heading.

    Args:
        document: The papis document containing metadata.
        annotations: The list of annotations to format.
        headings: Heading style — ``"setext"`` for underlined titles,
            ``"atx"`` for ``#``-prefixed titles.

    Returns:
        A Markdown-formatted string, or empty string if there are no annotations.
    """
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
        output += format_annotation(a, template)
        output += "\n\n"

    output += "\n\n\n"

    return output.rstrip()


def format_markdown_atx(
    document: Document = Document(),
    annotations: list[Annotation] = [],
) -> str:
    """Format annotations as Markdown with ATX-style (``#``) headings.

    Args:
        document: The papis document containing metadata.
        annotations: The list of annotations to format.

    Returns:
        A Markdown-formatted string, or empty string if there are no annotations.
    """
    return format_markdown(document, annotations, headings="atx")


def format_markdown_setext(
    document: Document = Document(),
    annotations: list[Annotation] = [],
) -> str:
    """Format annotations as Markdown with Setext-style underlined headings.

    Args:
        document: The papis document containing metadata.
        annotations: The list of annotations to format.

    Returns:
        A Markdown-formatted string, or empty string if there are no annotations.
    """
    return format_markdown(document, annotations, headings="setext")


def format_count(
    document: Document = Document(),
    annotations: list[Annotation] = [],
) -> str:
    """Format a single-line summary with annotation count and document info.

    Args:
        document: The papis document containing metadata.
        annotations: The list of annotations to count.

    Returns:
        A string like ``"3 Author: Title"``, or empty string if there are
        no annotations.
    """
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


class CsvFormatter:
    """Format annotations as CSV rows.

    Provides a header property with column names and formats each
    annotation as a single CSV row.
    """

    header: str = "type,tag,page,quote,note,author,title,ref,file"
    _template: str = (
        '{{type}},{{tag}},{{page}},"{{quote}}","{{note}}",'
        '"{{doc.author}}","{{doc.title}}","{{doc.ref}}","{{file}}"'
    )

    def __call__(self, document: Document, annotations: list[Annotation]) -> str:
        """Format annotations as CSV rows.

        Args:
            document: The papis document containing metadata.
            annotations: The list of annotations to format.

        Returns:
            CSV-formatted rows, or empty string if there are no annotations.
        """
        if not annotations:
            return ""

        output = ""
        for a in annotations:
            output += format_annotation(a, self._template, doc=document)
            output += "\n"

        return output.rstrip()


class _FormatterWrapper:
    """Adapts a bare function to the Formatter interface with header."""

    header: str = ""

    def __init__(self, fn: Callable[[Document, list[Annotation]], str]) -> None:
        self.__wrapped__ = fn

    def __call__(self, document: Document, annotations: list[Annotation]) -> str:
        return self.__wrapped__(document, annotations)


formatters: dict[str, Formatter] = {
    "count": _FormatterWrapper(format_count),
    "csv": CsvFormatter(),
    "markdown": _FormatterWrapper(format_markdown),
    "markdown-atx": _FormatterWrapper(format_markdown_atx),
    "markdown-setext": _FormatterWrapper(format_markdown_setext),
}
