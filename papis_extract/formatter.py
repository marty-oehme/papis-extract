from dataclasses import dataclass, field
from typing import Protocol

from papis_extract.annotation_data import AnnotatedDocument


@dataclass
class Formatter(Protocol):
    annotated_docs: list[AnnotatedDocument]
    header: str
    string: str
    footer: str

    def execute(self, doc: AnnotatedDocument | None = None) -> str:
        raise NotImplementedError


@dataclass
class MarkdownFormatter:
    annotated_docs: list[AnnotatedDocument] = field(default_factory=lambda: list())
    header: str = ""
    string: str = (
        "{{#tag}}#{{tag}}\n{{/tag}}"
        "{{#quote}}> {{quote}}{{/quote}} {{#page}}[p. {{page}}]{{/page}}\n"
        "{{#note}}  NOTE: {{note}}{{/note}}"
    )
    footer: str = ""

    def execute(self, doc: AnnotatedDocument | None = None) -> str:
        output = ""
        documents = self.annotated_docs if doc is None else [doc]
        last = documents[-1]
        for entry in documents:
            if not entry.annotations:
                continue

            title_decoration = (
                f"{'=' * len(entry.document.get('title', ''))}   "
                f"{'-' * len(entry.document.get('author', ''))}"
            )
            output += (
                f"{title_decoration}\n"
                f"{entry.document['title']} - {entry.document['author']}\n"
                f"{title_decoration}\n\n"
            )
            for a in entry.annotations:
                output += a.format(self.string)

            if entry != last:
                output += "\n\n\n"

        return output


@dataclass
class CountFormatter:
    annotated_docs: list[AnnotatedDocument] = field(default_factory=lambda: list())
    header: str = ""
    string: str = ""
    footer: str = ""

    def execute(self, doc: AnnotatedDocument | None = None) -> str:
        documents = self.annotated_docs if doc is None else [doc]
        output = ""
        for entry in documents:
            if not entry.annotations:
                continue

            count = 0
            for _ in entry.annotations:
                count += 1

            d = entry.document
            output += (
                f"{d['author'] if 'author' in d else ''}"
                f"{' - ' if 'author' in d else ''}" # only put separator if author
                f"{entry.document['title'] if 'title' in d else ''}: "
                f"{count}\n"
            )

        return output


@dataclass
class CsvFormatter:
    header: str = "type, tag, page, quote, note, file"
    string: str = "{{type}}, {{tag}}, {{page}}, {{quote}}, {{note}}, {{file}}"
    footer: str = ""


@dataclass
class CustomFormatter:
    def __init__(self, header: str = "", string: str = "", footer: str = "") -> None:
        self.header = header
        self.string = string
        self.footer = footer
