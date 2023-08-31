from dataclasses import dataclass
from typing import Protocol


@dataclass
class Templating(Protocol):
    string: str


@dataclass
class Markdown:
    string: str = (
        "{{#tag}}#{{tag}}\n{{/tag}}"
        "{{#quote}}> {{quote}}{{/quote}} {{#page}}[p. {{page}}]{{/page}}\n"
        "{{#note}}  NOTE: {{note}}{{/note}}"
    )
