from papis_extract.annotation_data import Annotation


def test_matches_colorname_exact():
    sut = Annotation("testfile", colors={"stroke": (1.0, 0.0, 0.0)})
    c_name = sut.colorname
    assert c_name == "red"
