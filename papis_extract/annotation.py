"""Annotation data model and color-tag mapping utilities.

Provides the ``Annotation`` class for representing PDF annotations
and helper functions for mapping annotation colors to user-defined tags.
"""

import ast
import math
from functools import total_ordering
from types import NotImplementedType
from typing import Any, cast

import chevron
import papis.config
from papis.document import Document

COLOR_SIMILARITY_MINIMUM_FALLBACK = 0.833

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


def get_color_tag_mapping() -> dict[str, str]:
    """Read the color-to-tag mapping from papis configuration.

    Returns the mapping from color names to user-defined tag strings.
    Returns an empty dict if no mapping is configured or if the
    configuration value is invalid.
    """
    rawvalue: Any = papis.config.general_get("tags", section="plugins.extract")
    if isinstance(rawvalue, dict):
        return cast("dict[str, str]", rawvalue)
    if rawvalue is None:
        return {}
    try:
        parsed = ast.literal_eval(rawvalue)
    except (ValueError, SyntaxError):
        return {}
    if isinstance(parsed, dict):
        return cast("dict[str, str]", parsed)
    return {}


def tag_from_color(
    color: tuple[float, float, float],
    color_mapping: dict[str, str] | None = None,
    minimum_similarity: float = COLOR_SIMILARITY_MINIMUM_FALLBACK,
) -> str:
    """Derive a tag string from an annotation color.

    Finds the closest named color and maps it to a user-defined tag
    using the provided color_mapping. If no mapping is provided,
    returns an empty string.

    :param color: RGB color tuple with values between 0 and 1.
    :param color_mapping: Mapping from color names to tag strings.
        If None, returns an empty string.
    :param minimum_similarity: Minimum similarity ratio for color matching.
    """
    if not color_mapping:
        return ""

    nearest: str | None = None
    best_similarity = minimum_similarity
    for name, values in COLORS.items():
        similarity = 1 - (abs(math.dist([*values], [*color])) / 3)
        if similarity >= best_similarity:
            best_similarity = similarity
            nearest = name

    if nearest is None:
        return ""
    return color_mapping.get(nearest, "")


@total_ordering
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
        minimum_similarity_color: float = COLOR_SIMILARITY_MINIMUM_FALLBACK,
    ) -> None:
        """Initialize an Annotation.

        Args:
            file: Path to the source file containing the annotation.
            color: RGB color tuple with values between 0 and 1.
            content: The highlighted or annotated text.
            note: A user-written note attached to the annotation.
            page: The page number where the annotation appears.
            tag: A user-defined tag derived from the annotation color.
            type: The annotation type, e.g. ``"Highlight"`` or ``"Note"``.
            minimum_similarity_color: Minimum color similarity ratio for
                matching the annotation color to a named color.
        """
        self.file = file
        self._color = color
        self.content = content
        self.note = note
        self.page = page
        self.minimum_similarity_color = minimum_similarity_color
        self.tag = tag
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
        """Return the RGB color tuple of the annotation."""
        return self._color

    @color.setter
    def color(self, value: tuple[float, float, float]):
        self._color = value

    @property
    def colorname(self):
        """Return the stringified version of the annotation color.

        Finds the closest named color to the annotation and returns it,
        using euclidian distance between the two color vectors.
        """
        annot_colors = self.color or (0.0, 0.0, 0.0)
        nearest = None
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

    def __str__(self) -> str:
        """Return a human-readable string representation of the annotation."""
        return f"Annotation({self.type}: '{self.file}', color: {self.color}, tag: '{self.tag}', page: {self.page}, content: '{self.content}', note: '{self.note}', minimum_similarity_color: {self.minimum_similarity_color})"

    def __repr__(self) -> str:
        """Return an unambiguous developer-oriented string representation."""
        return f"Annotation(type={self.type}, file='{self.file}', color={self.color}, tag='{self.tag}', page={self.page}, content='{self.content}', note='{self.note}', minimum_similarity_color={self.minimum_similarity_color})"

    def __eq__(self, other: object) -> bool | NotImplementedType:
        """Return True if two annotations have identical content and metadata.

        Comparison is case-insensitive for ``content`` and ``note`` fields.
        """
        if not isinstance(other, Annotation):
            return NotImplemented

        return (
            self.content.lower(),
            self.note.lower(),
            self.type,
            self.file,
            self.color,
            self.tag,
            self.page,
        ) == (
            other.content.lower(),
            other.note.lower(),
            other.type,
            other.file,
            other.color,
            other.tag,
            other.page,
        )

    def __lt__(self, other: object) -> bool:
        """Return True if this annotation appears earlier in the document than *other*.

        Annotations with ``page == 0`` (unknown page) are sorted to the end.
        """
        if not hasattr(other, "page"):
            return NotImplemented

        other = cast("Annotation", other)
        selfpage = self.page if self.page != 0 else float("inf")
        otherpage = other.page if other.page != 0 else float("inf")

        return selfpage < otherpage
