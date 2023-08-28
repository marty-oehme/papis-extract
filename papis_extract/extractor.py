from pathlib import Path

import Levenshtein
import fitz_new as fitz
import papis.config

from papis_extract.annotation_data import Annotation

COLOR_MAPPING = {}


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
                a = Annotation(
                    file=str(filename),
                    text=quote,
                    content=note,
                    colors=annot.colors,
                    type=annot.type[1],
                    page=(page.number or 0) + 1,
                )
                a.tag = _tag_from_colorname(a.colorname)
                annotations.append(a)
    return annotations


def _tag_from_colorname(colorname):
    return COLOR_MAPPING.get(colorname, "")


def _retrieve_annotation_content(page, annotation):
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
        return (content, "")
    # an independent note, not a highlight
    elif content and not written:
        return ("", content)
    # both a highlight and a note
    elif content:
        return (written, content)
    # highlight with selection not in note
    return (written, "")
