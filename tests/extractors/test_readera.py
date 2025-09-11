from pathlib import Path

from papis_extract.extractors.readera import ReadEraExtractor

valid_file = Path("tests/resources/ReadEra_sample.txt")
invalid_file = Path("tests/resources/Readest_sample.txt")


def test_identifies_readera_exports():
    ex = ReadEraExtractor()
    assert ex.can_process(valid_file)


# Readest exports are very similar so we should ensure it ignores them
def test_ignores_readest_exports():
    ex = ReadEraExtractor()
    assert not ex.can_process(invalid_file)
