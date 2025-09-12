# pyright: strict, reportUnknownMemberType=false
import re
from pathlib import Path

import papis.logging

from papis_extract.annotation import Annotation

logger = papis.logging.get_logger(__name__)

ACCEPTED_EXTENSIONS = [".txt", ".md", ".qmd", ".rmd"]
TEXTCHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F})


class ReadestExtractor:
    """Extracts exported annotations from the FOSS Readest book reading app.

    https://readest.com/
    """

    def can_process(self, filename: Path) -> bool:
        if not self._is_readable_text(filename):
            return False

        content = self._read_file(filename)
        if not content:
            return False

        # look for star-shaped divider pattern
        if not re.search(
            r"\n\*\*Exported from Readest\*\*: \d{4}-\d{2}-\d{2}\n", "".join(content)
        ):
            return False

        logger.debug(f"Found processable annotation file: {filename}")
        return True

    def _is_readable_text(self, filename: Path) -> bool:
        """Checks whether a file has a valid text extension and is not a binary file.

        A file is considered a valid text file if its extension is in
        :data:`ACCEPTED_EXTENSIONS` and does not contain any non-text characters.

        :returns: A boolean indicating whether the file is a valid text file.
        """
        if filename.suffix not in ACCEPTED_EXTENSIONS:
            return False
        try:
            with filename.open("rb") as rb:
                return not bool(rb.read(1024).translate(None, TEXTCHARS))
        except (FileNotFoundError, PermissionError):
            return False

    def run(self, filename: Path) -> list[Annotation]:
        """Extract annotations from readest txt file.

        Returns all readable annotations contained in the file passed in, with
        highlights and notes if available.
        """
        content = self._read_file(filename)[2:]
        if not content:
            return []

        annotations: list[Annotation] = []

        for i, line in enumerate(content):
            entry_content: str = ""
            entry_note: str = ""
            if line.startswith("> "):
                entry_content = line.lstrip('> "').rstrip('\n" ')
                nextline = content[i + 1]
                if nextline.startswith("**Note**:: "):
                    entry_note = nextline.removeprefix("**Note**:: ").strip()

                a = Annotation(
                    file=str(filename),
                    content=entry_content,
                    note=entry_note,
                    # NOTE: Unfortunately Readest currently does not export color information
                    # color=color,
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
