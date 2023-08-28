import re
import math
from dataclasses import dataclass, field

import papis.config
from papis.document import Document

TEXT_SIMILARITY_MINIMUM = 0.75
COLOR_SIMILARITY_MINIMUM = 0.833

COLORS = {
    "red": (1, 0, 0),
    "green": (0, 1, 0),
    "blue": (0, 0, 1),
    "yellow": (1, 1, 0),
    "purple": (0.5, 0, 0.5),
    "orange": (1, 0.65, 0),
}


@dataclass
class Annotation:
    """A PDF annotation object"""

    file: str
    type: str = "Highlight"
    text: str = ""
    content: str = ""
    page: int = 1
    colors: dict = field(default_factory=lambda: {"stroke": (0.0, 0.0, 0.0)})
    tag: str = ""

    def format(self, formatting):
        """Return a formatted string of the annotation.

        Given a provided formatting pattern, this method returns the annotation
        formatted with the correct marker replacements and removals, ready
        for display or writing.
        """
        output = formatting
        replacements = {
            r"{quote}": self.text,
            r"{note}": self.content,
            r"{page}": str(self.page),
            r"{newline}": "\n",
            r"{tag}": self.tag,
        }
        pattern = re.compile(
            "|".join(
                [re.escape(k) for k in sorted(replacements, key=len, reverse=True)]
            ),
            flags=re.DOTALL,
        )
        patt_quote_container = re.compile(r"{%quote_container(.*?)%}")
        patt_note_container = re.compile(r"{%note_container(.*?)%}")
        patt_tag_container = re.compile(r"{%tag_container(.*?)%}")
        output = patt_quote_container.sub(r"\1" if self.text else "", output)
        output = patt_note_container.sub(r"\1" if self.content else "", output)
        output = patt_tag_container.sub(r"\1" if self.tag else "", output)
        return pattern.sub(lambda x: replacements[x.group(0)], output)

    @property
    def colorname(self):
        """Return the stringified version of the annotation color.

        Finds the closest named color to the annotation and returns it,
        using euclidian distance between the two color vectors.
        """
        annot_colors = (
            self.colors.get("stroke") or self.colors.get("fill") or (0.0, 0.0, 0.0)
        )
        nearest = None
        minimum_similarity = (
            papis.config.getfloat("minimum_similarity_color", "plugins.extract")
            or 1.0
        )
        for name, values in COLORS.items():
            similarity_ratio = self._color_similarity_ratio(values, annot_colors)
            if similarity_ratio > minimum_similarity:
                minimum_similarity = similarity_ratio
                nearest = name
        return nearest

    def _color_similarity_ratio(self, color_one, color_two):
        """Return the similarity of two colors between 0 and 1.

        Takes two rgb color tuples made of floats between 0 and 1,
        e.g. (1, 0.65, 0) for orange, and returns the similarity
        between them, with 1 being the same color and 0 being the
        difference between full black and full white, as a float.
        """
        return 1 - (abs(math.dist([*color_one], [*color_two])) / 3)


@dataclass
class AnnotatedDocument:
    document: Document
    annotations: list[Annotation]
