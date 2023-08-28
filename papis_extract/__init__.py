from pathlib import Path
import re

import click
import fitz_new as fitz
import magic
import papis.cli
import papis.config
import papis.document
from papis.document import Document
import papis.logging
import papis.notes
import papis.strings

from papis_extract import extractor, exporter
from papis_extract.annotation_data import Annotation, AnnotatedDocument

logger = papis.logging.get_logger(__name__)

DEFAULT_OPTIONS = {
    "plugins.extract": {
        "tags": {"important": "red", "toread": "blue"},
        "on_import": False,
        "minimum_similarity": 0.75, # for checking against existing annotations
        "minimum_similarity_content": 0.9, # for checking if highlight or note
        "minimum_similarity_color": 0.833 # for matching tag to color
    }
}
papis.config.register_default_settings(DEFAULT_OPTIONS)


@click.command("extract")
@click.help_option("-h", "--help")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.git_option(help="Add changes made to the notes files")
@papis.cli.all_option()
@click.option(
    "--manual/--no-manual",
    "-m",
    help="Open each note in editor for manual editing after extracting its annotations",
)
@click.option(
    "--write/--no-write",
    "-w",
    help="Do not write annotations to notes only print results to stdout",
)
def main(
    query: str,
    # info: bool,
    # _papis_id: bool,
    # _file: bool,
    # notes: bool,
    # _dir: bool,
    # _format: str,
    _all: bool,
    doc_folder: str,
    manual: bool,
    write: bool,
    git: bool,
) -> None:
    """Extract annotations from any pdf document

    The extract plugin allows manual or automatic extraction of all annotations
    contained in the pdf documents belonging to entries of the pubs library.
    It can write those changes to stdout or directly create and update notes
    for papis documents.

    It adds a `papis extract` subcommand through which it is invoked, but can
    optionally run whenever a new document is imported for a pubs entry.
    """
    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field=None, sort_reverse=False, _all=_all
    )
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    doc_annotations: list[AnnotatedDocument] = _get_annotations_for_documents(documents)

    if write:
        exporter.to_notes(doc_annotations, edit=manual, git=git)
    else:
        exporter.to_stdout(doc_annotations)

    # note_file: Path = Path(papis.notes.notes_path_ensured(documents[0]))


def is_pdf(fname: Path) -> bool:
    return magic.from_file(fname, mime=True) == "application/pdf"


def _get_annotations_for_documents(
    documents: list[Document],
) -> list[AnnotatedDocument]:
    output: list[AnnotatedDocument] = []
    for doc in documents:
        annotations: list[Annotation] = []
        found_pdf: bool = False
        for file in doc.get_files():
            fname = Path(file)
            if not _is_file_processable(fname):
                break
            found_pdf = True

            try:
                annotations.extend(extractor.start(fname))
            except fitz.FileDataError as e:
                print(f"File structure errors for {file}.\n{e}")

        if not found_pdf:
            # have to remove curlys or papis logger gets upset
            desc = re.sub("[{}]", "", papis.document.describe(doc))
            logger.warning("Did not find suitable PDF file for document: " f"{desc}")
        output.append(AnnotatedDocument(doc, annotations))
    return output


def _is_file_processable(fname: Path) -> bool:
    if not fname.is_file():
        logger.error(f"File {str(fname)} not readable.")
        return False
    if not is_pdf(fname):
        return False
    return True
