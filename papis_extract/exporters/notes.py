"""Export formatted annotations into papis document notes."""

from dataclasses import dataclass
from pathlib import Path

import papis.commands.edit
import papis.config
import papis.document
import papis.git
import papis.notes
from papis.document import Document
from papis.logging import get_logger

from papis_extract.annotation import Annotation
from papis_extract.exporters._io import (
    check_similarity,
    drop_existing_annotations,
    write_annotations_to_file,
)
from papis_extract.formatter import Formatter

logger = get_logger(__name__)


@dataclass
class NotesExporter:
    """Write formatted annotations into papis document notes files.

    Appends formatted annotations to each document's notes file.
    Supports deduplication (skip annotations that already exist),
    optional editing after writing, and git integration. Format-level
    headers (e.g., CSV column names) are prepended per file.
    """

    formatter: Formatter
    edit: bool = False
    git: bool = False
    duplicates: bool = False

    def run(self, annot_docs: list[tuple[Document, list[Annotation]]]) -> None:
        """Write annotations into document notes.

        Permanently writes the given annotations into notes
        belonging to papis documents. Creates new notes for
        documents missing a note field or appends to existing.
        """
        for doc, annots in annot_docs:
            output = self.formatter(doc, annots)
            if not output:
                logger.debug(
                    f"No annotations found, writing no note for {papis.document.describe(doc)}"
                )
                continue
            header = self.formatter.header
            if header:
                output = f"{header}\n{output}"
            formatted_annotations: list[str] = output.split("\n")
            if formatted_annotations:
                self._add_annots_to_note(
                    doc, formatted_annotations, git=self.git, duplicates=self.duplicates
                )

            if self.edit:
                papis.commands.edit.edit_notes(doc, git=self.git)

    def _add_annots_to_note(
        self,
        document: Document,
        formatted_annotations: list[str],
        git: bool = False,
        duplicates: bool = False,
    ) -> None:
        """Append new annotations to the end of a note.

        Delegates the read / dedup / write work to
        ``write_annotations_to_file``, then optionally commits via git.
        """
        logger.debug("Adding annotations to note...")
        notes_path = Path(papis.notes.notes_path_ensured(document))

        minimum_similarity = (
            papis.config.getfloat("minimum_similarity", "plugins.extract") or 1.0
        )

        written = write_annotations_to_file(
            notes_path,
            formatted_annotations,
            duplicates=duplicates,
            minimum_similarity=minimum_similarity,
        )
        if written:
            logger.info(
                f"Wrote {written} "
                f"{'line' if written == 1 else 'lines'} "
                f"to {papis.document.describe(document)}"
            )

        if git:
            msg = f"Update annotations for '{papis.document.describe(document)}'"
            folder = document.get_main_folder()
            if folder:
                papis.git.add_and_commit_resources(
                    folder, [str(notes_path), document.get_info_file()], msg
                )

    def _drop_existing_annotations(
        self, formatted_annotations: list[str], file_lines: list[str]
    ) -> list[str]:
        """Return the input annotations, dropping any that already exist.

        Thin wrapper around ``drop_existing_annotations`` from ``_io``
        that reads the similarity threshold from papis config first.
        """
        minimum_similarity = (
            papis.config.getfloat("minimum_similarity", "plugins.extract") or 1.0
        )
        return drop_existing_annotations(
            formatted_annotations, file_lines, minimum_similarity
        )

    def _test_similarity(
        self, string: str, lines: list[str], minimum_similarity: float = 1.0
    ) -> bool:
        """Thin wrapper around ``check_similarity`` from ``_io``."""
        return check_similarity(string, lines, minimum_similarity)
