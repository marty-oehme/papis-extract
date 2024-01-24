from papis_extract.extraction import Extractor
from papis_extract.extractors import pdf
from papis_extract.extractors.pocketbook import PocketBookExtractor

all_extractors: dict[str, Extractor] = {
    "pdf": pdf.PdfExtractor(),
    "pocketbook": PocketBookExtractor(),
}
