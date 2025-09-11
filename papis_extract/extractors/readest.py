# pyright: strict, reportUnknownMemberType=false
import re
from pathlib import Path

import magic
import papis.logging

from papis_extract.annotation import Annotation

logger = papis.logging.get_logger(__name__)


class ReadestExtractor:
    """Extracts exported annotations from the FOSS Readest book reading app.

    https://readest.com/
    """

    def can_process(self, filename: Path) -> bool:
        if magic.from_file(filename, mime=True) != "text/plain":
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
