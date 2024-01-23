from papis_extract.extraction import Extractor
from papis_extract.extractors import pdf

all_extractors: dict[str, Extractor] = {
    "pdf": pdf.PdfExtractor(),
}
