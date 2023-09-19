from dataclasses import dataclass
from typing import Protocol


@dataclass
class Templating(Protocol):
    header: str
    string: str
    footer: str


@dataclass
class Markdown:
    header: str = ""
    string: str = (
        "{{#tag}}#{{tag}}\n{{/tag}}"
        "{{#quote}}> {{quote}}{{/quote}} {{#page}}[p. {{page}}]{{/page}}\n"
        "{{#note}}  NOTE: {{note}}{{/note}}"
    )
    footer: str = ""


@dataclass
class Csv:
    header: str = "type, tag, page, quote, note, file"
    string: str = "{{type}}, {{tag}}, {{page}}, {{quote}}, {{note}}, {{file}}"
    footer: str = ""


@dataclass
class Custom:
    def __init__(self, header: str = "", string: str = "", footer: str = "") -> None:
        self.header = header
        self.string = string
        self.footer = footer
