from importlib.util import find_spec

import papis.logging

from papis_extract.extraction import Extractor
from papis_extract.extractors import pdf
from papis_extract.extractors.pocketbook import PocketBookExtractor

logger = papis.logging.get_logger(__name__)

all_extractors: dict[str, Extractor] = {}

all_extractors["pdf"] = pdf.PdfExtractor()

if find_spec("bs4") and find_spec("magic"):
    all_extractors["pocketbook"] = PocketBookExtractor()
else:
    logger.debug("pocketbook extractor not activated.")


class ExtractionError(Exception):
    """Raised for exceptions during extraction.

    Something went wrong during the extraction process in the extractor
    run routine itself.
    """

    pass
