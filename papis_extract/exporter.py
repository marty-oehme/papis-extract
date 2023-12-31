import papis.logging
import papis.document
import papis.notes
import papis.commands.edit
import papis.api
import papis.git
import papis.config
import Levenshtein
from papis_extract.annotation import AnnotatedDocument

from papis_extract.formatter import Formatter

logger = papis.logging.get_logger(__name__)


def to_stdout(formatter: Formatter, annotated_docs: list[AnnotatedDocument]) -> None:
    """Pretty print annotations to stdout.

    Gives a nice human-readable representations of
    the annotations in somewhat of a list form.
    Not intended for machine-readability.
    """
    output: str = formatter(annotated_docs)
    print(output.rstrip("\n"))


def to_notes(
    formatter: Formatter,
    annotated_docs: list[AnnotatedDocument],
    edit: bool,
    git: bool,
    force: bool,
) -> None:
    """Write annotations into document notes.

    Permanently writes the given annotations into notes
    belonging to papis documents. Creates new notes for
    documents missing a note field or appends to existing.
    """
    for entry in annotated_docs:
        formatted_annotations = formatter([entry]).split("\n")
        if formatted_annotations:
            _add_annots_to_note(entry.document, formatted_annotations, force=force)

        if edit:
            papis.commands.edit.edit_notes(entry.document, git=git)


def _add_annots_to_note(
    document: papis.document.Document,
    formatted_annotations: list[str],
    git: bool = False,
    force: bool = False,
) -> None:
    """
    Append new annotations to the end of a note.

    This function appends new annotations to the end of a note file. It takes in a
    document object containing the note, a list of formatted annotations to be
    added, and optional flags git and force. If git is True, the changes will be
    committed to git. If force is True, the annotations will be added even if they
    already exist in the note.

    :param document: The document object representing the note
    :type document: class:`papis.document.Document`
    :param formatted_annotations: A list of already formatted annotations to be added
    :type formatted_annotations: list[str]
    :param git: Flag indicating whether to commit changes to git, defaults to False.
    :type git: bool, optional
    :param force:  Flag indicating whether to force adding annotations even if they
        already exist, defaults to False.
    :type force: bool, optional
    """
    logger.debug("Adding annotations to note.")
    notes_path = papis.notes.notes_path_ensured(document)

    existing: list[str] = []
    with open(notes_path, "r") as file_read:
        existing = file_read.readlines()

    new_annotations: list[str] = []
    if not force:
        new_annotations = _drop_existing_annotations(formatted_annotations, existing)
    if not new_annotations:
        return

    with open(notes_path, "a") as f:
        # add newline if theres no empty space at file end
        if len(existing) > 0 and existing[-1].strip() != "":
            f.write("\n")
        print(new_annotations)
        f.write("\n\n".join(new_annotations))
        f.write("\n")
        logger.info(
            f"Wrote {len(new_annotations)} "
            f"{'annotation' if len(new_annotations) == 1 else 'annotations'} "
            f"to {papis.document.describe(document)}"
        )

    if git:
        msg = "Update notes for '{0}'".format(papis.document.describe(document))
        folder = document.get_main_folder()
        if folder:
            papis.git.add_and_commit_resources(
                folder, [notes_path, document.get_info_file()], msg
            )


def _drop_existing_annotations(
    formatted_annotations: list[str], file_lines: list[str]
) -> list[str]:
    """Returns the input annotations dropping any existing.

    Takes a list of formatted annotations and a list of strings
    (most probably existing lines in a file). If anny annotations
    match an existing line closely enough, they will be dropped.

    Returns list of annotations without duplicates.
    """
    minimum_similarity = (
        papis.config.getfloat("minimum_similarity", "plugins.extract") or 1.0
    )

    remaining: list[str] = []
    for an in formatted_annotations:
        an_split = an.splitlines()
        if an_split and not _test_similarity(
            an_split[0], file_lines, minimum_similarity
        ):
            remaining.append(an)

    return remaining


def _test_similarity(
    string: str, lines: list[str], minimum_similarity: float = 1.0
) -> bool:
    for line in lines:
        ratio = Levenshtein.ratio(string, line)
        if ratio > minimum_similarity:
            return True
    return False
