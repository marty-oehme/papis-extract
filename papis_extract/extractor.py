from pathlib import Path
from typing import Any, Optional

import Levenshtein
import fitz_new as fitz
import papis.logging
import papis.config

from papis_extract.annotation_data import Annotation

logger = papis.logging.get_logger(__name__)


def start(filename: Path) -> list[Annotation]:
    """Extract annotations from a file.

    Returns all readable annotations contained in the file
    passed in. Only returns Highlight or Text annotations.
    """
    annotations = []
    with fitz.Document(filename) as doc:
        for page in doc:
            for annot in page.annots():
                quote, note = _retrieve_annotation_content(page, annot)
                if not quote and not note:
                    continue
                a = Annotation(
                    file=str(filename),
                    text=quote or "",
                    content=note or "",
                    colors=annot.colors,
                    type=annot.type[1],
                    page=(page.number or 0) + 1,
                )
                a.tag = _tag_from_colorname(a.colorname or "")
                annotations.append(a)
    logger.debug(
        f"Found {len(annotations)} "
        f"{'annotation' if len(annotations) == 1 else 'annotations'} for {filename}."
    )
    return annotations


def _tag_from_colorname(colorname: str) -> str:
    color_mapping: dict[str,str] = getdict("tags", "plugins.extract")
    if not color_mapping:
        return ""

    return color_mapping.get(colorname, "")


def _retrieve_annotation_content(
    page: fitz.Page, annotation: fitz.Annot
) -> tuple[str | None, str | None]:
    """Gets the text content of an annotation.

    Returns the actual content of an annotation. Sometimes
    that is only the written words, sometimes that is only
    annotation notes, sometimes it is both. Runs a similarity
    comparison between strings to find out whether they
    should both be included or are the same, using
    Levenshtein distance.
    """
    content = annotation.info["content"].replace("\n", " ")
    written = page.get_textbox(annotation.rect).replace("\n", " ")

    # highlight with selection in note
    minimum_similarity = (
        papis.config.getfloat("minimum_similarity_content", "plugins.extract") or 1.0
    )
    if Levenshtein.ratio(content, written) > minimum_similarity:
        return (content, None)
    # both a highlight and a note
    elif content and written:
        return (written, content)
    # an independent note, not a highlight
    elif content:
        return (None, content)
    # highlight with selection not in note
    elif written:
        return (written, None)
    # just a highlight without any text
    return (None, None)

# mimics the functions in papis.config.{getlist,getint,getfloat} etc.
def getdict(key: str, section: Optional[str] = None) -> dict[str, str]:
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
            "The key '{}' must be a valid Python object: {}"
            .format(key, rawvalue))
    else:
        if not isinstance(rawvalue, dict):
            raise SyntaxError(
                "The key '{}' must be a valid Python dict. Got: {} (type {!r})"
                .format(key, rawvalue, type(rawvalue).__name__))

        return rawvalue

