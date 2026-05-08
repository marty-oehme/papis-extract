"""Exporter Protocol is the final stage of the extraction pipeline.

Exporters receive document/annotation pairs and write them to a
destination (stdout, notes files, etc.).
"""

from typing import Protocol

import papis.document

from papis_extract.annotation import Annotation


class Exporter(Protocol):
    """Export formatted annotations to a destination.

    An exporter receives document-annotation pairs and writes them
    somewhere — stdout, a notes file, etc. Each implementation
    declares its own configuration fields as needed.
    """

    def run(
        self, annot_docs: list[tuple[papis.document.Document, list[Annotation]]]
    ) -> None:
        """Write formatted annotations to the configured destination."""
        ...
