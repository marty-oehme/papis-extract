from pathlib import Path

import fitz
import Levenshtein
import magic
import papis.config
import papis.logging

from papis_extract.annotation import Annotation
from papis_extract.extractors import ExtractionError

logger = papis.logging.get_logger(__name__)


class PdfExtractor:
    def can_process(self, filename: Path) -> bool:
        if not filename.is_file():
            logger.error(f"File {str(filename)} not readable.")
            return False
        if not self._is_pdf(filename):
            return False
        return True

    def run(self, filename: Path) -> list[Annotation]:
        """Extract annotations from a file.

        Returns all readable annotations contained in the file
        passed in. Only returns Highlight or Text annotations.
        """
        annotations: list[Annotation] = []
        try:
            with mu.Document(filename) as doc:
                for page in doc:  # pyright: ignore [reportUnknownVariableType] - missing stub
                    page = cast(mu.Page, page)
                    annot: mu.Annot
                    for annot in page.annots():
                        quote, note = self._retrieve_annotation_content(page, annot)
                        if not quote and not note:
                            continue
                        color: tuple[float, float, float] = cast(
                            tuple[float, float, float],
                            (
                                annot.colors.get("fill")
                                or annot.colors.get("stroke")
                                or (0.0, 0.0, 0.0)
                            ),
                        )
                        page_nr: int = cast(int, page.number or 0)
                        highlight_type: str = cast(str, annot.type[1] or "")
                        a = Annotation(
                            file=str(filename),
                            content=quote or "",
                            note=note or "",
                            color=color,
                            type=highlight_type,
                            page=page_nr,
                        )
                        annotations.append(a)
            logger.debug(
                f"Found {len(annotations)} "
                f"{'annotation' if len(annotations) == 1 else 'annotations'} for {filename}."
            )

        except mu.FileDataError as e:
            raise ExtractionError

        return annotations

    def _is_pdf(self, fname: Path) -> bool:
        """Check if file is a pdf, using mime type."""
        return magic.from_file(fname, mime=True) == "application/pdf"

    def _retrieve_annotation_content(
        self, page: mu.Page, annotation: mu.Annot
    ) -> tuple[str | None, str | None]:
        """Gets the text content of an annotation.

        Returns the actual content of an annotation. Sometimes
        that is only the written words, sometimes that is only
        annotation notes, sometimes it is both. Runs a similarity
        comparison between strings to find out whether they
        should both be included or are the same, using
        Levenshtein distance.
        """
        content = annotation.info["content"].replace("\n", " ")
        written = page.get_textbox(annotation.rect).replace("\n", " ")

        # highlight with selection in note
        minimum_similarity = (
            papis.config.getfloat("minimum_similarity_content", "plugins.extract")
            or 1.0
        )
        if Levenshtein.ratio(content, written) > minimum_similarity:
            return (content, None)
        # both a highlight and a note
        elif content and written:
            return (written, content)
        # an independent note, not a highlight
        elif content:
            return (None, content)
        # highlight with selection not in note
        elif written:
            return (written, None)
        # just a highlight without any text
        return (None, None)
