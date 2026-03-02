"""
Integration tests using La La Land movie review data (134963.txt).
Each line is tab-separated: <review_text>\t<rating>
"""

from pathlib import Path

import pytest

from krwordrank.sentence import summarize_with_sentences
from krwordrank.word import KRWordRank, summarize_with_keywords

DATA_PATH = Path(__file__).parent / "data" / "134963.txt"

EXPECTED_TOP5 = ["영화", "너무", "정말", "음악", "마지막"]


@pytest.fixture(scope="module")
def texts():
    with open(DATA_PATH, encoding="utf-8") as f:
        return [line.rsplit("\t")[0].strip() for line in f]


# ---------------------------------------------------------------------------
# KRWordRank.extract
# ---------------------------------------------------------------------------


def test_keyword_top5(texts):
    extractor = KRWordRank(min_count=5, max_length=10)
    keywords, _, _ = extractor.extract(texts, beta=0.85, max_iter=10)
    top5 = [w for w, _ in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]]
    assert top5 == EXPECTED_TOP5


def test_keyword_returns_nonempty_graph(texts):
    extractor = KRWordRank(min_count=5, max_length=10)
    _, rank, graph = extractor.extract(texts, beta=0.85, max_iter=10)
    assert len(rank) > 0
    assert len(graph) > 0


def test_keyword_num_keywords_limit(texts):
    extractor = KRWordRank(min_count=5, max_length=10)
    keywords, _, _ = extractor.extract(texts, beta=0.85, max_iter=10, num_keywords=30)
    assert len(keywords) == 30


# ---------------------------------------------------------------------------
# summarize_with_keywords
# ---------------------------------------------------------------------------


def test_summarize_with_keywords_count(texts):
    keywords = summarize_with_keywords(texts, num_keywords=50, min_count=5)
    assert len(keywords) == 50


def test_summarize_with_keywords_contains_top_words(texts):
    keywords = summarize_with_keywords(texts, num_keywords=100, min_count=5)
    for word in EXPECTED_TOP5:
        assert word in keywords


def test_summarize_with_keywords_stopwords_excluded(texts):
    stopwords = {"영화", "너무", "정말"}
    keywords = summarize_with_keywords(texts, num_keywords=100, min_count=5, stopwords=stopwords)
    for word in stopwords:
        assert word not in keywords


# ---------------------------------------------------------------------------
# summarize_with_sentences
# ---------------------------------------------------------------------------


def test_keysentence_count(texts):
    _, sents = summarize_with_sentences(texts, num_keywords=100, num_keysents=10)
    assert len(sents) == 10


def test_keysentence_keywords_contain_top_words(texts):
    keywords, _ = summarize_with_sentences(texts, num_keywords=100, num_keysents=10)
    for word in EXPECTED_TOP5:
        assert word in keywords


def test_keysentence_stopwords_excluded_from_keywords(texts):
    stopwords = {"영화", "너무", "정말", "진짜"}
    keywords, _ = summarize_with_sentences(texts, num_keywords=100, num_keysents=10, stopwords=stopwords)
    for word in stopwords:
        assert word not in keywords


def test_keysentence_penalty_filters_short_sentences(texts):
    def penalty(x):
        return 0 if 20 <= len(x) <= 100 else 1

    _, sents = summarize_with_sentences(texts, num_keywords=100, num_keysents=10, penalty=penalty)
    assert all(20 <= len(s) <= 100 for s in sents)


def test_keysentence_diversity_changes_results(texts):
    _, sents_low = summarize_with_sentences(texts, num_keywords=100, num_keysents=10, diversity=0.1)
    _, sents_high = summarize_with_sentences(texts, num_keywords=100, num_keysents=10, diversity=0.8)
    assert sents_low != sents_high


def test_keysentence_return_indices(texts):
    keywords, sents, idxs = summarize_with_sentences(texts, num_keywords=100, num_keysents=10, return_indices=True)
    assert len(sents) == len(idxs) == 10
    assert all(0 <= i < len(texts) for i in idxs)
    assert all(texts[i] == s for i, s in zip(idxs, sents))
