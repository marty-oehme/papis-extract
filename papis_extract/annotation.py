"""Annotation data model and color-tag mapping utilities.

Provides the ``Annotation`` class for representing PDF annotations
and helper functions for mapping annotation colors to user-defined tags.
"""

import ast
import math
from functools import total_ordering
from types import NotImplementedType
from typing import Any, cast


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


def _hex_to_rgb(hex_str: str) -> tuple[float, float, float] | None:
    """Convert a hex color string to an RGB tuple.

    Supports 6-digit (``#ff0000``) and 3-digit (``#f00``) formats
    with or without a leading ``#``. Matching is case-insensitive.

    Returns ``None`` if the string is not a valid hex color.

    >>> _hex_to_rgb("#ff0000")
    (1.0, 0.0, 0.0)
    >>> _hex_to_rgb("#f00")
    (1.0, 0.0, 0.0)
    >>> _hex_to_rgb("ff0000")
    (1.0, 0.0, 0.0)
    >>> _hex_to_rgb("#gg0000")
    None
    """
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    if len(hex_str) != 6:
        return None
    try:
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        return (r, g, b)
    except ValueError:
        return None


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

    Finds the closest matching color from the mapping (either a named
    color like ``"red"`` or a hex color like ``"#ff0000"``) and maps it
    to a user-defined tag. If no mapping is provided, returns an empty
    string.

    :param color: RGB color tuple with values between 0 and 1.
    :param color_mapping: Mapping from color name or hex string keys
        to tag strings. If None, returns an empty string.
    :param minimum_similarity: Minimum similarity ratio for color matching.
    """
    if not color_mapping:
        return ""

    nearest: str | None = None
    best_similarity = minimum_similarity
    for name in color_mapping:
        target_rgb: tuple[float, float, float] | None = None
        stripped = name.strip()
        if stripped.startswith("#"):
            target_rgb = _hex_to_rgb(stripped)
            if target_rgb is None:
                continue
        else:
            target_rgb = COLORS.get(stripped)
            if target_rgb is None:
                continue

        similarity = 1 - (abs(math.dist([*target_rgb], [*color])) / 3)
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
        """
        self.file = file
        self._color = color
        self.content = content
        self.note = note
        self.page = page
        self.tag = tag
        self.type = type

    @property
    def color(self):
        """Return the RGB color tuple of the annotation."""
        return self._color

    @color.setter
    def color(self, value: tuple[float, float, float]):
        self._color = value

    def __str__(self) -> str:
        """Return a human-readable string representation of the annotation."""
        return f"Annotation({self.type}: '{self.file}', color: {self.color}, tag: '{self.tag}', page: {self.page}, content: '{self.content}', note: '{self.note}')"

    def __repr__(self) -> str:
        """Return an unambiguous developer-oriented string representation."""
        return f"Annotation(type={self.type}, file='{self.file}', color={self.color}, tag='{self.tag}', page={self.page}, content='{self.content}', note='{self.note}')"

    def __eq__(self, other: object) -> bool:
        """Return True if two annotations have identical content and metadata.

        Comparison is case-insensitive for ``content`` and ``note`` fields.
        """
        if not isinstance(other, Annotation):
            raise NotImplementedError

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
            raise NotImplementedError

        other = cast("Annotation", other)
        selfpage = self.page if self.page != 0 else float("inf")
        otherpage = other.page if other.page != 0 else float("inf")

        return selfpage < otherpage
