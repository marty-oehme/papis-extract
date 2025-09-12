# pyright: strict, reportUnknownMemberType=false
import mimetypes
import re
from pathlib import Path

import papis.logging

from papis_extract.annotation import Annotation

logger = papis.logging.get_logger(__name__)


class ReadEraExtractor:
    """Extracts exported annotations from the ReadEra book reading app for Android and iOS.

    https://readera.org/
    """

    def can_process(self, filename: Path) -> bool:
        if not self._is_txt(filename):
            return False

        content = self._read_file(filename)
        if not content:
            return False

        # look for title and author lines up top
        if not content[0] or not content[1]:
            return False

        # look for star-shaped divider pattern
        if not re.search(r"\n\*\*\*\*\*\n", "".join(content)):
            return False

        # look for star-shaped pattern at end of file
        if not re.search(r"\n\*\*\*\*\*\n\n$", "".join(content)):
            return False

        logger.debug(f"Found processable annotation file: {filename}")
        return True

    def _is_txt(self, filename: Path) -> bool:
        return mimetypes.guess_type(filename)[0] == "text/plain"

    def run(self, filename: Path) -> list[Annotation]:
        """Extract annotations from readera txt file.

        Returns all readable annotations contained in the file passed in, with
        highlights and notes if available. Could theoretically return the
        annotation color but I do not have access to a premium version of
        ReadEra so I cannot add this feature.
        """
        content = self._read_file(filename)[2:]
        if not content:
            return []

        annotations: list[Annotation] = []

        # split for *** separators and remove the last entry since it is always
        # empty
        split = "\n".join(content).split("\n*****\n")[:-1]
        note_pattern = re.compile(r"\n--.*")
        for entry in split:
            entry = entry.strip()
            note = note_pattern.search(entry)
            if note:
                entry = note_pattern.sub("", entry)
                note = re.sub(r"\n--", "", note.group())

            entry = re.sub(r"\n", " ", entry)

            a = Annotation(
                file=str(filename),
                content=entry,
                note=note if note else "",
                # color=color, # TODO: Implement for premium ReadEra version
            )
            annotations.append(a)

        logger.debug(
            f"Found {len(annotations)} "
            f"{'annotation' if len(annotations) == 1 else 'annotations'} for {filename}."
        )
        return annotations

    def _read_file(self, filename: Path) -> list[str]:
        try:
            with filename.open("r") as fr:
                return fr.readlines()
        except FileNotFoundError:
            logger.error(f"Could not open file {filename} for extraction.")
            return []
