from dataclasses import dataclass
from typing import Protocol

import papis.document
import papis.logging

from papis_extract.annotation import Annotation
from papis_extract.formatter import Formatter

logger = papis.logging.get_logger(__name__)


@dataclass
class Exporter(Protocol):
    formatter: Formatter
    edit: bool = False
    git: bool = False
    duplicates: bool = False

    def run(
        self, annot_docs: list[tuple[papis.document.Document, list[Annotation]]]
    ) -> None: ...
