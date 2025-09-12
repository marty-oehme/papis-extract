# pyright: strict, reportUnknownMemberType=false
import mimetypes
from pathlib import Path
from typing import cast

import papis.logging
from bs4 import BeautifulSoup

from papis_extract.annotation import COLORS, Annotation

logger = papis.logging.get_logger(__name__)


class PocketBookExtractor:
    def can_process(self, filename: Path) -> bool:
        if not self._is_html(filename):
            return False

        content = self._read_file(filename)
        if not content:
            return False

        html = BeautifulSoup(content, features="xml")
        if not html.find(
            "meta", {"name": "generator", "content": "PocketBook Bookmarks Export"}
        ):
            return False

        logger.debug(f"Found processable annotation file: {filename}")
        return True

    def _is_html(self, filename: Path) -> bool:
        return mimetypes.guess_type(filename)[0] == "text/html"

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
                (bm.select_one("div.bm-text>p") or html.new_string("")).text or ""
            )
            note = str(
                (bm.select_one("div.bm-note>p") or html.new_string("")).text or ""
            )
            page = int((bm.select_one("p.bm-page") or html.new_string("")).text or 0)

            el_classes = cast("str", bm.attrs.get("class", "")).split(" ")
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
            with filename.open("r") as fr:
                return fr.read()
        except FileNotFoundError:
            logger.error(f"Could not open file {filename} for extraction.")
            return ""
