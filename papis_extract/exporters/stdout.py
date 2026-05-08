from dataclasses import dataclass

from papis.document import Document

from papis_extract.annotation import Annotation
from papis_extract.formatter import Formatter


@dataclass
class StdoutExporter:
    formatter: Formatter

    def run(self, annot_docs: list[tuple[Document, list[Annotation]]]) -> None:
        """Pretty print annotations to stdout.

        Gives a nice human-readable representations of
        the annotations in somewhat of a list form.
        Not intended for machine-readability.
        """
        header_emitted = False
        for doc, annots in annot_docs:
            output: str = self.formatter(doc, annots)
            if output:
                if not header_emitted:
                    h = getattr(self.formatter, "header", None)
                    if h:
                        print(h)
                    header_emitted = True
                print("{output}\n".format(output=output.rstrip("\n")))
