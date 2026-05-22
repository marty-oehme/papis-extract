"""Export formatted annotations to an arbitrary file path."""

from dataclasses import dataclass
from pathlib import Path

import papis.config
from papis.document import Document
from papis.logging import get_logger

from papis_extract.annotation import Annotation
from papis_extract.exporters._io import write_annotations_to_file
from papis_extract.formatter import Formatter

logger = get_logger(__name__)


@dataclass
class FileExporter:
    """Write formatted annotations to a user-supplied file path.

    Operates identically to ``NotesExporter`` except it writes to an
    explicit file path instead of resolving through papis notes.  Each
    document's annotations are appended with per-document headers and
    the same deduplication logic.
    """

    formatter: Formatter
    file_path: Path
    duplicates: bool = False

    def run(self, annot_docs: list[tuple[Document, list[Annotation]]]) -> None:
        """Write annotations into *file_path*.

        Formats each document's annotations, prepends the formatter
        header (if any), and appends to the target file. Skips
        duplicate annotations when *duplicates* is ``False``.
        """
        # Ensure the target directory exists before writing.
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        minimum_similarity = (
            papis.config.getfloat("minimum_similarity", "plugins.extract") or 1.0
        )

        for doc, annots in annot_docs:
            output = self.formatter(doc, annots)
            if not output:
                logger.debug(
                    f"No annotations found, writing no annotations to {self.file_path}"
                )
                continue

            header = self.formatter.header
            if header:
                output = f"{header}\n{output}"

            formatted_annotations: list[str] = output.split("\n")
            if not formatted_annotations:
                continue

            written = write_annotations_to_file(
                self.file_path,
                formatted_annotations,
                duplicates=self.duplicates,
                minimum_similarity=minimum_similarity,
            )
            if written:
                logger.info(
                    f"Wrote {written} "
                    f"{'line' if written == 1 else 'lines'} "
                    f"to {self.file_path}"
                )
