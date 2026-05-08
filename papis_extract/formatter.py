"""Formatters that convert annotations into output strings.

Each formatter receives a document and its annotations and returns
a single formatted string. Formatter classes are registered in the
``formatter_classes`` dict and selected via the ``--format`` CLI flag.
"""

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


class MarkdownFormatter:
    """Format annotations as Markdown with a document heading.

    Supports setext-style (underlined) and ATX-style (``#``-prefixed)
    headings, configurable via the ``headings`` parameter.
    """

    header: str = ""
    _DEFAULT_TEMPLATE: str = (
        "{{#tag}}#{{tag}}\n{{/tag}}"
        "{{#quote}}> {{quote}}{{/quote}}{{#page}} [p. {{page}}]{{/page}}"
        "{{#note}}\n  NOTE: {{note}}{{/note}}"
    )

    def __init__(self, template: str | None = None, headings: str = "setext") -> None:
        """Create a Markdown formatter.

        Args:
            template: Mustache template for individual annotations.
                Defaults to ``_DEFAULT_TEMPLATE``.
            headings: ``"setext"`` (underlined) or ``"atx"`` (``#``-prefixed).
        """
        self._template: str = template or self._DEFAULT_TEMPLATE
        self._headings: str = headings

    def __call__(
        self,
        document: Document,
        annotations: list[Annotation],
    ) -> str:
        """Format annotations as Markdown with a document heading."""
        if not annotations:
            return ""
        output = ""

        heading = f"{document.get('title', '')} - {document.get('author', '')}"
        if self._headings == "atx":
            output += f"# {heading}\n\n"
        elif self._headings == "setext":
            title_decoration = (
                f"{'=' * len(document.get('title', ''))}   "
                f"{'-' * len(document.get('author', ''))}"
            )
            output += f"{title_decoration}\n{heading}\n{title_decoration}\n\n"

        for a in annotations:
            output += format_annotation(a, self._template)
            output += "\n\n"

        output += "\n\n\n"

        return output.rstrip()


class CountFormatter:
    """Format a single-line summary with annotation count and document info.

    This formatter does not use a Mustache template. The ``template``
    constructor parameter is accepted for interface uniformity and ignored.
    """

    header: str = ""

    def __init__(self, template: str | None = None) -> None:
        """Create a count formatter.

        The ``template`` parameter is accepted for interface uniformity
        but ignored — this formatter does not use Mustache.
        """

    def __call__(
        self,
        document: Document,
        annotations: list[Annotation],
    ) -> str:
        """Return a single-line summary of annotation count and document info."""
        if not annotations:
            return ""

        count = 0
        for _ in annotations:
            count += 1

        return (
            f"{count} "
            f"{document.get('author', '')}"
            f"{': ' if 'author' in document else ''}"
            f"{document.get('title', '')}"
        ).rstrip()


class CsvFormatter:
    """Format annotations as CSV rows.

    Provides a header with column names and formats each
    annotation as a single CSV row.
    """

    header: str = "type,tag,page,quote,note,author,title,ref,file"
    _DEFAULT_TEMPLATE: str = (
        '{{type}},{{tag}},{{page}},"{{quote}}","{{note}}",'
        '"{{doc.author}}","{{doc.title}}","{{doc.ref}}","{{file}}"'
    )

    def __init__(self, template: str | None = None) -> None:
        """Create a CSV formatter.

        Args:
            template: Mustache template for individual annotation rows.
                Defaults to ``_DEFAULT_TEMPLATE``.
        """
        self._template: str = template or self._DEFAULT_TEMPLATE

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


formatter_classes: dict[str, type[Formatter]] = {
    "count": CountFormatter,
    "csv": CsvFormatter,
    "markdown": MarkdownFormatter,
    "markdown-atx": MarkdownFormatter,
    "markdown-setext": MarkdownFormatter,
}
