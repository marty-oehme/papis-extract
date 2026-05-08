"""Extraction orchestration: protocol, extract_all(), and start()."""

import re
from pathlib import Path
from typing import Protocol

import papis.document
import papis.logging
from papis.document import Document

from papis_extract.annotation import Annotation
from papis_extract.exceptions import ExtractionError

logger = papis.logging.get_logger(__name__)


class Extractor(Protocol):
    """Protocol that all annotation extractors must implement."""

    def can_process(self, filename: Path) -> bool:
        """Return ``True`` if this extractor can handle the given file."""
        ...

    def run(self, filename: Path) -> list[Annotation]:
        """Extract annotations from the given file."""
        ...


def extract_all(
    documents: list[Document],
    extractors: list[Extractor],
) -> list[tuple[Document, list[Annotation]]]:
    """Extract annotations from all documents using all given extractors.

    Returns a list of (document, annotations) pairs. Logs an info
    for documents where no extractor could process any files.
    """
    results: list[tuple[Document, list[Annotation]]] = []
    for doc in documents:
        annotations: list[Annotation] = []
        valid_files = 0
        for ext in extractors:
            added = start(ext, doc)
            if added is not None:
                valid_files += 1
                annotations.extend(added)
        if valid_files == 0:
            desc = re.sub("[{}]", "", papis.document.describe(doc))
            logger.info(
                f"Document {desc} has no valid extractors for any of its files."
            )
        results.append((doc, annotations))
    return results


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
            logger.error(
                f"File extraction errors for {file}. File may be damaged.\n{e}"
            )

    if not file_available:
        return None

    return annotations
