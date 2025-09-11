from pathlib import Path

from papis_extract.annotation import Annotation
from papis_extract.extractors.readera import ReadEraExtractor

valid_file = Path("tests/resources/ReadEra_sample.txt")
invalid_file = Path("tests/resources/Readest_sample.txt")

expected = [
    Annotation(
        file="tests/resources/ReadEra_sample.txt",
        content="digital technologies of the twenty-first century can only exist thanks to this kind of outsourced labor. The relative invisibility of the tech supply chain is part of the ruse; American consumers do not see where smartphones come from.",
    ),
    Annotation(
        file="tests/resources/ReadEra_sample.txt",
        content="We don’t necessarily want our leaders to be average persons like us, even though we often enjoy hearing that famous celebrities eat the same fast food as regular people. ",
        note="We continuously demystify our leaders - first through television, now through social media",
    ),
    Annotation(
        file="tests/resources/ReadEra_sample.txt",
        content="Initially, the Internet was praised as a freer way to encounter information.  In the early 1990s, digital theorist George Landow saw hypertext as a liberatory reading strategy.",
    ),
]


def test_identifies_readera_exports():
    ex = ReadEraExtractor()
    assert ex.can_process(valid_file)


# Readest exports are very similar so we should ensure it ignores them
def test_ignores_readest_exports():
    ex = ReadEraExtractor()
    assert not ex.can_process(invalid_file)


def test_entry_extractions():
    ex = ReadEraExtractor()
    result = ex.run(valid_file)
    assert result == expected
