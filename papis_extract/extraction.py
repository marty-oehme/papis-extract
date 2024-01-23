import re
from pathlib import Path
from typing import Protocol

import fitz
import papis.config
import papis.document
import papis.logging
from papis.document import Document

from papis_extract.annotation import Annotation
from papis_extract.extractors.pdf import PdfExtractor

logger = papis.logging.get_logger(__name__)


class Extractor(Protocol):
    def can_process(self, filename: Path) -> bool:
        ...

    def run(self, filename: Path) -> list[Annotation]:
        ...


def start(
    extractor: Extractor,
    document: Document,
) -> list[Annotation]:
    """Extract all annotations from passed documents.

    Returns all annotations contained in the papis
    documents passed in.
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
        except fitz.FileDataError as e:
            print(f"File structure errors for {file}.\n{e}")

    if not file_available:
        # have to remove curlys or papis logger gets upset
        desc = re.sub("[{}]", "", papis.document.describe(document))
        logger.warning("Did not find suitable file for document: " f"{desc}")

    return annotations


extractors: dict[str, Extractor] = {
    "pdf": PdfExtractor(),
}
