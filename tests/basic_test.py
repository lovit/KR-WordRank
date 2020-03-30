import os
import pytest
import sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root)

import krwordrank
from krwordrank.hangle import initialize_pattern
from krwordrank.hangle import normalize
from krwordrank.word import KRWordRank


@pytest.fixture
def test_config():
    return {
        'data_path': '{}/data/134963_norm.txt'.format(root) # La La Land movie comments
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


def test_keyword(test_config):
    data_path = test_config['data_path']
    with open(data_path, encoding='utf-8') as f:
        texts = [line.rsplit('\t')[0].strip() for line in f]

    wordrank_extractor = KRWordRank(min_count = 5, max_length = 10)
    keywords, rank, graph = wordrank_extractor.extract(texts, beta = 0.85, max_iter = 10)
    selected_keywords = [word for word, r in sorted(keywords.items(), key=lambda x:x[1], reverse=True)[:30]]
    assert selected_keywords[:5] == ['영화', '너무', '정말', '음악', '마지막']
    print('\nKR-WordRank 라라랜드 영화 리뷰 30 개 키워드\n{}\n'.format(selected_keywords))
