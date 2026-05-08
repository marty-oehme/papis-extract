"""Built-in exporter registry.

Exporters are registered as classes, not instances. This is intentional:
exporters carry per-invocation configuration (which formatter to use,
whether to edit notes, etc.) and are instantiated at call time with
those arguments.

New exporters should be added here by importing the class and
registering it in ``all_exporters``.
"""

from papis_extract.exporter import Exporter
from papis_extract.exporters.notes import NotesExporter
from papis_extract.exporters.stdout import StdoutExporter

# Classes, not instances — exporters are parameterized per invocation.
all_exporters: dict[str, type[Exporter]] = {
    "stdout": StdoutExporter,
    "notes": NotesExporter,
}
