import click
import papis.cli
import papis.config
import papis.document
import papis.logging
import papis.notes
import papis.strings
from papis.document import Document

from papis_extract import extractor, exporter
from papis_extract.formatter import (
    CountFormatter,
    CsvFormatter,
    MarkdownFormatter,
    Formatter,
)

logger = papis.logging.get_logger(__name__)

DEFAULT_OPTIONS = {
    "plugins.extract": {
        "tags": {},
        "on_import": False,
        "minimum_similarity": 0.75,  # for checking against existing annotations
        "minimum_similarity_content": 0.9,  # for checking if highlight or note
        "minimum_similarity_color": 0.833,  # for matching tag to color
    }
}
papis.config.register_default_settings(DEFAULT_OPTIONS)


@click.command("extract")
@click.help_option("-h", "--help")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.git_option(help="Commit changes made to the notes files.")
@papis.cli.all_option()
@click.option(
    "--write/--no-write",
    "-w",
    help="Do not write annotations to notes only print results to stdout.",
)
@click.option(
    "--manual/--no-manual",
    "-m",
    help="Open note in editor for manual editing after annotation extraction.",
)
@click.option(
    "--template",
    "-t",
    type=click.Choice(["markdown", "count", "csv"], case_sensitive=False),
    help="Choose an output template to format annotations with.",
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
    template: str,
    git: bool,
) -> None:
    """Extract annotations from any pdf document.

    The extract plugin allows manual or automatic extraction of all annotations
    contained in the pdf documents belonging to entries of the papis library.
    It can write those changes to stdout or directly create and update notes
    for papis documents.

    It adds a `papis extract` subcommand through which it is invoked, but can
    optionally run whenever a new document is imported for a papis entry,
    if set in the plugin configuration.
    """
    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field=None, sort_reverse=False, _all=_all
    )
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if template == "csv":
        formatter = CsvFormatter()
    elif template == "count":
        formatter = CountFormatter()
    else:
        formatter = MarkdownFormatter()

    run(documents, edit=manual, write=write, git=git, formatter=formatter)


def run(
    documents: list[Document],
    formatter: Formatter,
    edit: bool = False,
    write: bool = False,
    git: bool = False,
) -> None:
    formatter.annotated_docs = extractor.start(documents)
    if write:
        exporter.to_notes(formatter, edit=edit, git=git)
    else:
        exporter.to_stdout(formatter)
