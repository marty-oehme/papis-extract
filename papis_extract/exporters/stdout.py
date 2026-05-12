"""Export formatted annotations to standard output."""

from dataclasses import dataclass

from papis.document import Document

from papis_extract.annotation import Annotation
from papis_extract.formatter import Formatter


@dataclass
class StdoutExporter:
    """Write formatted annotations to stdout.

    Formats each document's annotations using the configured formatter
    and prints them to stdout. Format-level headers (e.g., CSV column
    names) are emitted once before the first document. Document blocks
    are separated by the formatter's ``document_separator``.
    """

    formatter: Formatter

    def run(self, annot_docs: list[tuple[Document, list[Annotation]]]) -> None:
        """Print annotations to stdout.

        Formats each document/annotation pair, filters empty outputs,
        then prints the header (if any) and the joined outputs.
        Document blocks are separated by ``self.formatter.document_separator``.
        """
        outputs = [self.formatter(doc, annots) for doc, annots in annot_docs]
        outputs = [o for o in outputs if o]
        if not outputs:
            return
        if self.formatter.header:
            print(self.formatter.header)
        print(self.formatter.document_separator.join(outputs))
