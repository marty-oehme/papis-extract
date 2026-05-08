"""Exceptions for the papis-extract plugin."""


class ExtractionError(Exception):
    """Raised for exceptions during extraction.

    Something went wrong during the extraction process in the extractor
    run routine itself.
    """

    pass
