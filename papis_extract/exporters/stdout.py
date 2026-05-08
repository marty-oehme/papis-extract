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
    names) are emitted once before the first document.
    """

    formatter: Formatter

    def run(self, annot_docs: list[tuple[Document, list[Annotation]]]) -> None:
        """Print annotations to stdout.

        Iterates over document/annotation pairs, formats each via
        the configured formatter, and prints the result to stdout.
        If the formatter provides a header, it is printed once
        before the first non-empty document output.
        """
        header_emitted = False
        for doc, annots in annot_docs:
            output: str = self.formatter(doc, annots)
            if output:
                if not header_emitted:
                    header = self.formatter.header
                    if header:
                        print(header)
                    header_emitted = True
                print("{output}\n".format(output=output.rstrip("\n")))
