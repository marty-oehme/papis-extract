"""CLI entry point and orchestration for annotation extraction.

This module defines the ``papis extract`` subcommand via Click and the
``run()`` function that wires together extractors, formatters, and exporters.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from papis_extract.exporter import Exporter

import click
import papis.cli
import papis.config
import papis.logging
import papis.strings
from papis.document import Document

from papis_extract import extraction
from papis_extract.exporters import all_exporters
from papis_extract.extractors import all_extractors
from papis_extract.formatter import Formatter, formatter_classes

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
    "--format",
    "-t",
    "format_",
    type=click.Choice(
        list(formatter_classes.keys()),
        case_sensitive=False,
    ),
    help="Output format for annotations.",
    show_default=True,
)
# NOTE: Deprecated option, to be removed in upcoming release
@click.option(
    "--output",
    "output",
    type=click.Choice(
        list(formatter_classes.keys()),
        case_sensitive=False,
    ),
    hidden=True,
    help="Choose which format to output annotations in.",
    deprecated="Instead of '--output', use `--format`.",
)
@click.option(
    "--input",
    "-i",
    "extractors",
    type=click.Choice(
        list(all_extractors.keys()),
        case_sensitive=False,
    ),
    default=list(all_extractors.keys()),
    multiple=True,
    help="Choose which input formats to gather annotations from.  [default: all]",
)
@click.option(
    "--duplicates/--no-duplicates",
    "-d",
    help="Do not drop any annotations because they already exist.",
    show_default=True,
)
def main(
    query: str,
    # _papis_id: bool,
    # _file: bool,
    # _dir: bool,
    _all: bool,
    doc_folder: str | None,
    manual: bool,
    write: bool,
    extractors: list[str],
    format_: str | None,
    output: str | None,
    git: bool,
    duplicates: bool,
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
        query,
        doc_folder,  # ty:ignore[invalid-argument-type] (CAN be None in papis)
        sort_field=None,
        sort_reverse=False,
        _all=_all,
    )
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    # NOTE: Guard for deprecated --output option. Can be removed on option removal
    if output and not format_:
        format_ = output

    run(
        documents,
        format_name=format_,
        edit=manual,
        write=write,
        git=git,
        extractors=[all_extractors.get(e) for e in extractors],
        duplicates=duplicates,
    )


def _instantiate_formatter(format_name: str, template: str | None) -> Formatter:
    """Create a formatter instance from the registry with resolved config."""
    cls = formatter_classes[format_name]
    kwargs: dict[str, Any] = {}
    if template:
        kwargs["template"] = template
    if format_name.startswith("markdown"):
        suffix = format_name.removeprefix("markdown")
        if suffix.startswith("-"):
            kwargs["headings"] = suffix[1:]  # "atx" or "setext"
        else:
            kwargs["headings"] = "setext"
    return cls(**kwargs)


def run(
    documents: list[Document],
    format_name: str | None,
    extractors: list[extraction.Extractor | None],
    edit: bool = False,
    write: bool = False,
    git: bool = False,
    duplicates: bool = False,
) -> None:
    """Extract annotations from documents and export them.

    Picks the right exporter (notes vs stdout) based on the *write* flag,
    extracts annotations from all documents using the given extractors,
    and runs the exporter with the chosen formatter.
    Picks a markdown formatter if none is given depending on exporter,
    with notes defaulting to markdown-atx and stdout to markdown-setext.
    """
    if not format_name:
        format_name = "markdown-atx" if write else "markdown-setext"
    formatter = _instantiate_formatter(format_name, template=None)

    exporter: Exporter
    if write:
        exporter = all_exporters["notes"](
            formatter=formatter,
            edit=edit,
            git=git,
            duplicates=duplicates,
        )
    else:
        exporter = all_exporters["stdout"](formatter=formatter)

    valid_extractors = [e for e in extractors if e is not None]
    doc_annots = extraction.extract_all(documents, valid_extractors)
    exporter.run(doc_annots)
