# pyright: strict, reportUnknownMemberType=false
from pathlib import Path

import magic
import papis.config
import papis.logging
from bs4 import BeautifulSoup

from papis_extract.annotation import COLORS, Annotation

logger = papis.logging.get_logger(__name__)


class PocketBookExtractor:
    def can_process(self, filename: Path) -> bool:
        if not magic.from_file(filename, mime=True) == "text/xml":
            return False

        content = self._read_file(filename)
        if not content:
            return False

        html = BeautifulSoup(content, features="xml")
        if not html.find(
            "meta", {"name": "generator", "content": "PocketBook Bookmarks Export"}
        ):
            return False
        return True

    def run(self, filename: Path) -> list[Annotation]:
        """Extract annotations from pocketbook html file.

        Export annotations from pocketbook app and load add them
        to a papis document as the exported html file.

        Returns all readable annotations contained in the file
        passed in, with highlights, notes and pages if available.
        """
        content = self._read_file(filename)
        if not content:
            return []
        html = BeautifulSoup(content, features="xml")

        annotations: list[Annotation] = []
        for bm in html.select("div.bookmark"):
            content = str(
                (bm.select_one("div.bm-text>p") or html.new_string("")).text
                or ""  # pyright: ignore [reportUnknownArgumentType]
            )
            note = str(
                (bm.select_one("div.bm-note>p") or html.new_string("")).text
                or ""  # pyright: ignore [reportUnknownArgumentType]
            )
            page = int(
                (bm.select_one("p.bm-page") or html.new_string("")).text
                or 0  # pyright: ignore [reportUnknownArgumentType]
            )

            el_classes = bm.attrs.get("class", "").split(" ")
            color = (0, 0, 0)
            for c in el_classes:
                if "bm-color-" in c:
                    color = COLORS.get(c.removeprefix("bm-color-"), (0, 0, 0))
                    break

            a = Annotation(
                file=str(filename),
                content=content,
                note=note,
                color=color,
                type="Highlight",
                page=page,
            )
            annotations.append(a)

        logger.debug(
            f"Found {len(annotations)} "
            f"{'annotation' if len(annotations) == 1 else 'annotations'} for {filename}."
        )
        return annotations

    def _read_file(self, filename: Path) -> str:
        try:
            with open(filename) as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Could not open file {filename} for extraction.")
            return ""
