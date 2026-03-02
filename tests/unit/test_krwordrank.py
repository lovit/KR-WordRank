from pathlib import Path

import pytest

from krwordrank.hangle import initialize_pattern, normalize

DATA_PATH = Path(__file__).parent.parent / "integration" / "data" / "134963.txt"


@pytest.mark.parametrize(
    "english, number, punctuation, expected",
    [
        (False, False, False, "한글과 으로 이뤄진 글자에 가까운 문장이에요"),
        (True, False, False, "한글과 alphabet 으로 이뤄진 글자에 가까운 문장이에요"),
        (True, True, False, "한글과 alphabet 으로 이뤄진 20글자에 가까운 문장이에요"),
        (True, True, True, "한글과 alphabet 으로 이뤄진 20글자에 가까운.. 문장이에요"),
    ],
    ids=["hangle", "hangle+english", "hangle+english+number", "hangle+english+number+punctuation"],
)
def test_normalize(english, number, punctuation, expected):
    input_str = "한글과 alphabet 으로 이뤄진 20글자에 가까운..   문장이에요"
    pattern = initialize_pattern(english, number, punctuation, remains=None)
    assert normalize(input_str, pattern=pattern) == expected
