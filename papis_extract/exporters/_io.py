"""Shared file I/O utilities for annotation exporters.

Package-private module. Functions here are used by Exporters such as
NotesExporter and FileExporter to avoid duplicating read/dedup/append logic.
"""

from pathlib import Path

import Levenshtein
from papis.logging import get_logger

logger = get_logger(__name__)


def check_similarity(
    string: str,
    lines: list[str],
    minimum_similarity: float = 1.0,
) -> bool:
    """Return True if *string* is similar to any line in *lines*.

    Uses Levenshtein ratio with ``>=`` threshold comparison.
    """
    return any(Levenshtein.ratio(string, line) >= minimum_similarity for line in lines)


def drop_existing_annotations(
    formatted_annotations: list[str],
    file_lines: list[str],
    minimum_similarity: float = 1.0,
) -> list[str]:
    """Filter out annotations whose first line matches an existing file line.

    Only the *first* line of each formatted annotation is compared against
    *file_lines* using ``check_similarity``.  Annotations whose first line
    matches any existing line are dropped.
    """
    remaining: list[str] = []
    for an in formatted_annotations:
        an_split = an.splitlines()
        if an_split and not check_similarity(
            an_split[0], file_lines, minimum_similarity
        ):
            remaining.append(an)
    return remaining


def write_annotations_to_file(
    path: Path,
    formatted_annotations: list[str],
    *,
    duplicates: bool = False,
    minimum_similarity: float = 1.0,
) -> int:
    """Read *path*, deduplicate, and append *formatted_annotations*.

    If *duplicates* is ``True``, all annotations are appended without dedup.
    Otherwise, annotations whose first line matches an existing file line
    (above *minimum_similarity*) are skipped.

    Returns:
        Number of non-empty annotation lines written (0 if nothing new).
    """
    existing: list[str] = []
    if path.exists():
        with path.open("r") as f:
            existing = f.readlines()

    new_annotations: list[str] = formatted_annotations
    if not duplicates:
        new_annotations = drop_existing_annotations(
            formatted_annotations, existing, minimum_similarity
        )

    if not new_annotations:
        logger.debug("No new annotations to be added.")
        return 0

    filtered = [a for a in new_annotations if a != ""]
    with path.open("a") as f:
        # add newline if there's no empty space at file end
        if existing and existing[-1].strip() != "":
            f.write("\n")
        f.write("\n\n".join(filtered))

    return len(filtered)
