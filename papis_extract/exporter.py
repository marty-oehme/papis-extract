import papis.logging
import papis.document
import papis.notes
import papis.commands.edit
import papis.api
import papis.git
import papis.config
import Levenshtein

from papis_extract.annotation_data import AnnotatedDocument
from papis_extract.model.templating import Templating

logger = papis.logging.get_logger(__name__)


def to_stdout(annots: list[AnnotatedDocument], template: Templating) -> None:
    """Pretty print annotations to stdout.

    Gives a nice human-readable representations of
    the annotations in somewhat of a list form.
    Not intended for machine-readability.
    """
    if not annots:
        return

    last = annots[-1]
    for entry in annots:
        if not entry.annotations:
            continue

        title_decoration = (
            f"{'=' * len(entry.document.get('title', ''))}   "
            f"{'-' * len(entry.document.get('author', ''))}"
        )
        print(
            f"{title_decoration}\n{papis.document.describe(entry.document)}\n{title_decoration}\n"
        )
        for a in entry.annotations:
            print(a.format(template.string))

        if entry != last:
            print("\n")


def to_notes(
    annots: list[AnnotatedDocument], template: Templating, edit: bool, git: bool
) -> None:
    """Write annotations into document notes.

    Permanently writes the given annotations into notes
    belonging to papis documents. Creates new notes for
    documents missing a note field or appends to existing.
    """
    if not annots:
        return

    for entry in annots:
        if not entry.annotations:
            continue

        formatted_annotations: list[str] = []
        for a in entry.annotations:
            formatted_annotations.append(a.format(template.string))

        _add_annots_to_note(entry.document, formatted_annotations)

        if edit:
            papis.commands.edit.edit_notes(entry.document, git=git)


def _add_annots_to_note(
    document: papis.document.Document,
    formatted_annotations: list[str],
    git: bool = False,
) -> None:
    """Append new annotations to the end of a note.

    Looks through note to determine any new annotations which should be
    added and adds them to the end of the note file.
    """
    logger.debug("Adding annotations to note.")
    notes_path = papis.notes.notes_path_ensured(document)

    existing: list[str] = []
    with open(notes_path, "r") as file_read:
        existing = file_read.readlines()

    new_annotations: list[str] = _drop_existing_annotations(
        formatted_annotations, existing
    )
    if not new_annotations:
        return

    with open(notes_path, "a") as f:
        # add newline if theres no empty space at file end
        if len(existing) > 0 and existing[-1].strip() != "":
            f.write("\n")
        f.write("\n".join(new_annotations))
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
    minimum_similarity = (
        papis.config.getfloat("minimum_similarity", "plugins.extract") or 1.0
    )

    remaining: list[str] = []
    for an in formatted_annotations:
        an_split = an.splitlines()
        if not _test_similarity(an_split[0], file_lines, minimum_similarity):
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
