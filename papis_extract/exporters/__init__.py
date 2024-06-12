import papis.logging

from papis_extract.exporter import Exporter
from papis_extract.exporters.notes import NotesExporter
from papis_extract.exporters.stdout import StdoutExporter


logger = papis.logging.get_logger(__name__)

all_exporters: dict[str, type[Exporter]] = {}

all_exporters["stdout"] = StdoutExporter
all_exporters["notes"] = NotesExporter
