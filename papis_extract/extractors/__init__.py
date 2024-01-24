import papis.logging

from papis_extract.extraction import Extractor
from papis_extract.extractors import pdf
from papis_extract.extractors.pocketbook import PocketBookExtractor

logger = papis.logging.get_logger(__name__)

all_extractors: dict[str, Extractor] = {
    "pdf": pdf.PdfExtractor(),
}

try:
    import bs4
    import magic

    all_extractors["pocketbook"] = PocketBookExtractor()
except ImportError:
    logger.debug("pocketbook extractor not activated.")
