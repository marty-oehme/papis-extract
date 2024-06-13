import click
import papis.cli
import papis.config
import papis.document
import papis.logging
import papis.notes
import papis.strings
from papis.document import Document

from papis_extract import extraction
from papis_extract.annotation import Annotation
from papis_extract.exporter import Exporter
from papis_extract.exporters import all_exporters
from papis_extract.extractors import all_extractors
from papis_extract.formatter import Formatter, formatters

logger = papis.logging.get_logger(__name__)

DEFAULT_OPTIONS: dict[str, dict[str, bool | float | dict[str, str]]] = {
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
    help="Write extracted annotations into papis notes.",
    show_default=True,
)
@click.option(
    "--manual/--no-manual",
    "-m",
    help="Open note in editor for manual editing after annotation extraction.",
    show_default=True,
)
@click.option(
    "--template",
    "-t",
    type=click.Choice(
        list(formatters.keys()),
        case_sensitive=False,
    ),
    help="Choose an output template to format annotations with.",
    show_default=True,
)
@click.option(
    "--extractor",
    "-e",
    "extractors",
    type=click.Choice(
        list(all_extractors.keys()),
        case_sensitive=False,
    ),
    default=list(all_extractors.keys()),
    multiple=True,
    help="Choose an extractor to apply to the selected documents.  [default: all]",
)
@click.option(
    "--force/--no-force",
    "-f",
    help="Do not drop any annotations because they already exist.",
    show_default=True,
)
def main(
    query: str,
    # _papis_id: bool,
    # _file: bool,
    # _dir: bool,
    _all: bool,
    doc_folder: str,
    manual: bool,
    write: bool,
    extractors: list[str],
    template: str,
    git: bool,
    force: bool,
) -> None:
    """Extract annotations from any documents.

    The extract plugin allows manual or automatic extraction of all annotations
    contained in the documents belonging to entries of the papis library,
    primarily targeting PDF documents currently.
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

    formatter = formatters.get(template)

    run(
        documents,
        edit=manual,
        write=write,
        git=git,
        formatter=formatter,
        extractors=[all_extractors.get(e) for e in extractors],
        force=force,
    )


def run(
    documents: list[Document],
    formatter: Formatter | None,
    extractors: list[extraction.Extractor | None],
    edit: bool = False,
    write: bool = False,
    git: bool = False,
    force: bool = False,
) -> None:
    exporter: Exporter
    if write:
        exporter = all_exporters["notes"](
            formatter=formatter or formatters["markdown-atx"],
            edit=edit,
            git=git,
            force=force,
        )
    else:
        exporter = all_exporters["stdout"](
            formatter=formatter or formatters["markdown"]
        )

    doc_annots: list[tuple[Document, list[Annotation]]] = []
    for doc in documents:
        annotations: list[Annotation] = []
        for ext in extractors:
            if not ext:
                continue
            annotations.extend(extraction.start(ext, doc))
        doc_annots.append((doc, annotations))

    exporter.run(doc_annots)
