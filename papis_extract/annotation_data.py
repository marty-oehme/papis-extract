import math
from dataclasses import dataclass, field

import papis.config
from papis.document import Document
import chevron

from papis_extract.templating import Templating

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
    colors: tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
    content: str = ""
    page: int = 0
    tag: str = ""
    text: str = ""
    type: str = "Highlight"
    minimum_similarity_color: float = 1.0

    def format(self, template: Templating):
        """Return a formatted string of the annotation.

        Given a provided formatting pattern, this method returns the annotation
        formatted with the correct marker replacements and removals, ready
        for display or writing.
        """
        data = {
            "file": self.file,
            "quote": self.text,
            "note": self.content,
            "page": self.page,
            "tag": self.tag,
            "type": self.type,
        }
        return chevron.render(template.string, data)

    @property
    def colorname(self):
        """Return the stringified version of the annotation color.

        Finds the closest named color to the annotation and returns it,
        using euclidian distance between the two color vectors.
        """
        annot_colors = self.colors or (0.0, 0.0, 0.0)
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

