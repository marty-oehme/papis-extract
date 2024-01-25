from dataclasses import dataclass

from papis.document import Document

from papis_extract.annotation import Annotation
from papis_extract.formatter import Formatter


@dataclass
class StdoutExporter:
    formatter: Formatter
    edit: bool = False
    git: bool = False
    force: bool = False

    def run(self, annot_docs: list[tuple[Document, list[Annotation]]]) -> None:
        """Pretty print annotations to stdout.

        Gives a nice human-readable representations of
        the annotations in somewhat of a list form.
        Not intended for machine-readability.
        """
        for doc, annots in annot_docs:
            output: str = self.formatter(doc, annots)
            if output:
                print("{output}\n".format(output=output.rstrip("\n")))
