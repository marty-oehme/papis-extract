from pathlib import Path
from typing import Protocol

import papis.config
import papis.document
import papis.logging
from papis.document import Document

from papis_extract.annotation import Annotation
from papis_extract.exceptions import ExtractionError

logger = papis.logging.get_logger(__name__)


class Extractor(Protocol):
    def can_process(self, filename: Path) -> bool: ...

    def run(self, filename: Path) -> list[Annotation]: ...


def start(
    extractor: Extractor,
    document: Document,
) -> list[Annotation] | None:
    """Extract all annotations from passed documents.

    Returns all annotations contained in the papis
    documents passed in (empty list if no annotations).
    If there are no files that the extractor can process,
    returns None instead.
    """
    annotations: list[Annotation] = []
    file_available: bool = False

    for file in document.get_files():
        fname = Path(file)
        if not extractor.can_process(fname):
            continue
        file_available = True

        try:
            annotations.extend(extractor.run(fname))
        except ExtractionError as e:
            logger.error(f"File extraction errors for {file}. File may be damaged.\n{e}")

    if not file_available:
        return None

    return annotations
