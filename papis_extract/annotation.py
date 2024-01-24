import math
from dataclasses import dataclass
from typing import Any, Optional

import chevron
import papis.config
from papis.document import Document

TEXT_SIMILARITY_MINIMUM = 0.75
COLOR_SIMILARITY_MINIMUM = 0.833

COLORS: dict[str, tuple[float, float, float]] = {
    "blue": (0, 0, 1),
    "green": (0, 1, 0),
    "red": (1, 0, 0),
    "cyan": (0, 1, 1),
    "yellow": (1, 1, 0),
    "magenta": (1, 0, 1),
    "purple": (0.5, 0, 0.5),
    "pink": (1, 0.75, 0.8),
    "orange": (1, 0.65, 0),
}


@dataclass
class Annotation:
    """A PDF annotation object.

    Contains all information necessary for the annotation itself, content and metadata.
    """

    def __init__(
        self,
        file: str,
        color: tuple[float, float, float] = (0.0, 0.0, 0.0),
        content: str = "",
        note: str = "",
        page: int = 0,
        tag: str = "",
        type: str = "Highlight",
        minimum_similarity_color: float = 1.0,
    ) -> None:
        self.minimum_similarity_color = minimum_similarity_color
        self.file = file
        self._color = color
        self.content = content
        self.note = note
        self.page = page
        self.tag = tag or self._tag_from_colorname(self.colorname or "")
        self.type = type

    def format(self, formatting: str, doc: Document = Document()):
        """Return a formatted string of the annotation.

        Given a provided formatting pattern, this method returns the annotation
        formatted with the correct marker replacements and removals, ready
        for display or writing.
        """
        data = {
            "file": self.file,
            "quote": self.content,
            "note": self.note,
            "page": self.page,
            "tag": self.tag,
            "type": self.type,
            "doc": doc,
        }
        return chevron.render(formatting, data)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value: tuple[float, float, float]):
        self._color = value
        self.tag = self._tag_from_colorname(self.colorname or "")

    @property
    def colorname(self):
        """Return the stringified version of the annotation color.

        Finds the closest named color to the annotation and returns it,
        using euclidian distance between the two color vectors.
        """
        annot_colors = self.color or (0.0, 0.0, 0.0)
        nearest = None
        minimum_similarity = (
            papis.config.getfloat("minimum_similarity_color", "plugins.extract") or 1.0
        )
        minimum_similarity = self.minimum_similarity_color
        for name, values in COLORS.items():
            similarity_ratio = self._color_similarity_ratio(values, annot_colors)
            if similarity_ratio >= minimum_similarity:
                minimum_similarity = similarity_ratio
                nearest = name
        return nearest

    def _color_similarity_ratio(
        self,
        color_one: tuple[float, float, float],
        color_two: tuple[float, float, float],
    ) -> float:
        """Return the similarity of two colors between 0 and 1.

        Takes two rgb color tuples made of floats between 0 and 1,
        e.g. (1, 0.65, 0) for orange, and returns the similarity
        between them, with 1 being the same color and 0 being the
        difference between full black and full white, as a float.
        """
        return 1 - (abs(math.dist([*color_one], [*color_two])) / 3)

    def _tag_from_colorname(self, colorname: str) -> str:
        color_mapping: dict[str, str] = self._getdict("tags", "plugins.extract")
        if not color_mapping:
            return ""

        return color_mapping.get(colorname, "")

    # mimics the functions in papis.config.{getlist,getint,getfloat} etc.
    def _getdict(self, key: str, section: Optional[str] = None) -> dict[str, str]:
        """Dict getter

        :returns: A python dict
        :raises SyntaxError: Whenever the parsed syntax is either not a valid
            python object or a valid python dict.
        """
        rawvalue: Any = papis.config.general_get(key, section=section)
        if isinstance(rawvalue, dict):
            return rawvalue
        try:
            rawvalue = eval(rawvalue)
        except Exception:
            raise SyntaxError(
                "The key '{}' must be a valid Python object: {}".format(key, rawvalue)
            )
        else:
            if not isinstance(rawvalue, dict):
                raise SyntaxError(
                    "The key '{}' must be a valid Python dict. Got: {} (type {!r})".format(
                        key, rawvalue, type(rawvalue).__name__
                    )
                )

            return rawvalue
