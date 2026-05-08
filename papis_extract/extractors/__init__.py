"""Built-in extractor registry.

Extractors are stateless singletons — they have no mutable state
and are instantiated once at import time. This is intentional:
extractors only depend on the file path passed to ``run()``,
not on any per-invocation configuration.

New extractors should be added here by importing the class,
instantiating it, and registering it in ``all_extractors``.
"""

from importlib.util import find_spec

import papis.logging

from papis_extract.extraction import Extractor
from papis_extract.extractors import pdf, readera, readest
from papis_extract.extractors.pocketbook import PocketBookExtractor

logger = papis.logging.get_logger(__name__)

all_extractors: dict[str, Extractor] = {}

# Stateless singletons — instantiated once, reused across all invocations.
all_extractors["pdf"] = pdf.PdfExtractor()
all_extractors["readera"] = readera.ReadEraExtractor()
all_extractors["readest"] = readest.ReadestExtractor()

if find_spec("bs4") and find_spec("magic"):
    all_extractors["pocketbook"] = PocketBookExtractor()
else:
    logger.debug("pocketbook extractor not activated.")
