from papis_extract.exporters.notes import NotesExporter
from papis_extract.exporters.stdout import StdoutExporter

all_exporters: dict[str, type] = {
    "stdout": StdoutExporter,
    "notes": NotesExporter,
}
