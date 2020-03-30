import os
import sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root)
import krwordrank
from krwordrank.hangle import initialize_pattern
from krwordrank.hangle import normalize

def test_config():
    return {
        'data_path': '{}/data/134963_norm.txt' # La La Land movie comments
    }


def test_normalize():
    input_str = '한글과 alphabet 으로 이뤄진 20글자에 가까운..   문장이에요'
    form = '\npassed case: {}\ninput : {}\noutput: {}'
    settings = [
        ('Hangle', False, False, False, '한글과 으로 이뤄진 글자에 가까운 문장이에요'),
        ('Hangle + English', True, False, False, '한글과 alphabet 으로 이뤄진 글자에 가까운 문장이에요'),
        ('Hangle + English + Number', True, True, False, '한글과 alphabet 으로 이뤄진 20글자에 가까운 문장이에요'),
        ('Hangle + English + Number + Punctuation', True, True, True, '한글과 alphabet 으로 이뤄진 20글자에 가까운.. 문장이에요')
    ]
    for name, english, number, punctuation, expected in settings:
        pattern = initialize_pattern(english, number, punctuation, remains=None)
        output_str = normalize(input_str, pattern=pattern)
        assert output_str == expected
        message = form.format(name, input_str, output_str)
        print(message)
