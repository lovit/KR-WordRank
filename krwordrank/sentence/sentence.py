from __future__ import annotations

from collections.abc import Callable
from typing import Literal, overload

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics import pairwise_distances

from ..word import KRWordRank
from .tokenizer import MaxScoreTokenizer


class KeywordVectorizer:
    """Vectorizer that encodes sentences as keyword presence/absence vectors.

    Builds a vocabulary from *vocab_score*, tokenizes each sentence, and
    represents it as a sparse Boolean row in a (n_sentences × n_keywords)
    matrix.  The keyword reference vector is the L2-normalised array of scores.

    Attributes:
        tokenize: Tokenizer callable ``(str) -> list[str]``.
        idx_to_vocab: Keywords sorted by descending score.
        vocab_to_idx: Inverse mapping from keyword string to column index.
        keyword_vector: L2-normalised 1-D array of keyword scores, shape
            ``(n_keywords,)``.

    Args:
        tokenize: Callable that splits a sentence into subword strings.
        vocab_score: Mapping from keyword string to its rank score.
    """

    def __init__(self, tokenize: Callable[[str], list[str]], vocab_score: dict[str, float]) -> None:
        self.tokenize = tokenize
        self.idx_to_vocab = [vocab for vocab in sorted(vocab_score, key=lambda x: -vocab_score[x])]
        self.vocab_to_idx = {vocab: idx for idx, vocab in enumerate(self.idx_to_vocab)}
        self.keyword_vector = np.asarray([score for _, score in sorted(vocab_score.items(), key=lambda x: -x[1])])
        self.keyword_vector = self._L2_normalize(self.keyword_vector)

    def _L2_normalize(self, vectors: np.ndarray) -> np.ndarray:
        return vectors / np.sqrt((vectors**2).sum())

    def vectorize(self, sents: list[str]) -> csr_matrix:
        """Encode sentences as a sparse keyword presence matrix.

        Args:
            sents: List of sentence strings to vectorize.

        Returns:
            Sparse Boolean CSR matrix of shape ``(n_sents, n_keywords)``.
            Entry ``[i, j]`` is 1 if keyword ``idx_to_vocab[j]`` appears in
            ``sents[i]``, otherwise 0.
        """
        rows, cols, data = [], [], []
        for i, sent in enumerate(sents):
            terms = set(self.tokenize(sent))
            for term in terms:
                j = self.vocab_to_idx.get(term, -1)
                if j == -1:
                    continue
                rows.append(i)
                cols.append(j)
                data.append(1)
        n_docs = len(sents)
        n_terms = len(self.idx_to_vocab)
        return csr_matrix((data, (rows, cols)), shape=(n_docs, n_terms))


@overload
def summarize_with_sentences(
    texts: list[str],
    num_keywords: int = ...,
    num_keysents: int = ...,
    diversity: float = ...,
    stopwords: set[str] | None = ...,
    scaling: Callable[[float], float] | None = ...,
    penalty: Callable[[str], float] | None = ...,
    min_count: int = ...,
    max_length: int = ...,
    beta: float = ...,
    max_iter: int = ...,
    num_rset: int = ...,
    verbose: bool = ...,
    bias: dict[str, float] | None = ...,
    return_indices: Literal[False] = ...,
) -> tuple[dict[str, float], list[str]]: ...


@overload
def summarize_with_sentences(
    texts: list[str],
    num_keywords: int = ...,
    num_keysents: int = ...,
    diversity: float = ...,
    stopwords: set[str] | None = ...,
    scaling: Callable[[float], float] | None = ...,
    penalty: Callable[[str], float] | None = ...,
    min_count: int = ...,
    max_length: int = ...,
    beta: float = ...,
    max_iter: int = ...,
    num_rset: int = ...,
    verbose: bool = ...,
    bias: dict[str, float] | None = ...,
    return_indices: Literal[True] = ...,
) -> tuple[dict[str, float], list[str], list[int]]: ...


def summarize_with_sentences(
    texts: list[str],
    num_keywords: int = 100,
    num_keysents: int = 10,
    diversity: float = 0.3,
    stopwords: set[str] | None = None,
    scaling: Callable[[float], float] | None = None,
    penalty: Callable[[str], float] | None = None,
    min_count: int = 5,
    max_length: int = 10,
    beta: float = 0.85,
    max_iter: int = 10,
    num_rset: int = -1,
    verbose: bool = False,
    bias: dict[str, float] | None = None,
    return_indices: bool = False,
) -> tuple[dict[str, float], list[str]] | tuple[dict[str, float], list[str], list[int]]:
    """Extract keywords and key sentences from a collection of texts.

    Trains KR-WordRank to obtain keyword rankings, then selects the most
    representative sentences based on cosine similarity to the keyword vector.

    Args:
        texts: List of input sentences.
        num_keywords: Number of keywords to extract (after stopword removal).
        num_keysents: Number of key sentences to return.
        diversity: Minimum cosine distance between any two selected sentences.
            Higher values produce more topically diverse results. Must be in
            ``[0, 1]``.
        stopwords: Words to exclude from the keyword vocabulary and the keyword
            vector used for sentence scoring.
        scaling: Rank transformation applied before building the keyword vector,
            e.g. ``lambda x: x ** 0.5``. Defaults to ``np.sqrt``.
        penalty: Sentence filter function ``(sentence) -> float``. A return
            value of ``0`` keeps the sentence; ``1`` (or any positive value)
            penalises it. Example — prefer sentences of 25–80 characters::

                def penalty(x):
                    return 0 if 25 <= len(x) <= 80 else 1

        min_count: Minimum subword frequency for graph construction.
        max_length: Maximum subword length for graph construction.
        beta: PageRank damping factor (0 < beta < 1).
        max_iter: Maximum HITS iterations.
        num_rset: Number of top-ranked R-set words used for L-part filtering.
            ``-1`` uses all R-set words.
        verbose: If True, prints training progress.
        bias: Custom HITS bias as ``{word: value}``.
        return_indices: If True, also return the original indices of the
            selected sentences in *texts*.

    Returns:
        ``(keywords, sentences)`` when *return_indices* is False, where
        *keywords* is ``{word: rank}`` and *sentences* is a list of selected
        sentence strings.

        ``(keywords, sentences, indices)`` when *return_indices* is True, where
        *indices[i]* is the position of ``sentences[i]`` in the original
        *texts* list.

    Example:
        >>> from krwordrank.sentence import summarize_with_sentences
        >>> texts = [...]  # list of str
        >>> keywords, sents = summarize_with_sentences(texts, num_keywords=100, num_keysents=10)
    """
    # train KR-WordRank
    wordrank_extractor = KRWordRank(min_count=min_count, max_length=max_length, verbose=verbose)

    num_keywords_ = num_keywords
    if stopwords is not None:
        num_keywords_ += len(stopwords)

    keywords, rank, graph = wordrank_extractor.extract(
        texts, beta, max_iter, num_keywords=num_keywords_, num_rset=num_rset, bias=bias
    )

    # build tokenizer
    if scaling is None:

        def scaling(x):
            return np.sqrt(x)

    if stopwords is None:
        stopwords = {}
    vocab_score = make_vocab_score(keywords, stopwords, scaling=scaling, topk=num_keywords)
    tokenizer = MaxScoreTokenizer(scores=vocab_score)

    # find key-sentences
    keywords_ = {vocab: keywords[vocab] for vocab in vocab_score}
    if return_indices is True:
        sents, idxs = keysentence(
            vocab_score,
            texts,
            tokenizer.tokenize,
            num_keysents,
            diversity,
            penalty,
            return_indices=return_indices,
        )
        return keywords_, sents, idxs
    else:
        sents = keysentence(
            vocab_score,
            texts,
            tokenizer.tokenize,
            num_keysents,
            diversity,
            penalty,
            return_indices=return_indices,
        )
        return keywords_, sents


@overload
def keysentence(
    vocab_score: dict[str, float],
    texts: list[str],
    tokenize: Callable[[str], list[str]],
    topk: int = ...,
    diversity: float = ...,
    penalty: Callable[[str], float] | None = ...,
    return_indices: Literal[False] = ...,
) -> list[str]: ...


@overload
def keysentence(
    vocab_score: dict[str, float],
    texts: list[str],
    tokenize: Callable[[str], list[str]],
    topk: int = ...,
    diversity: float = ...,
    penalty: Callable[[str], float] | None = ...,
    return_indices: Literal[True] = ...,
) -> tuple[list[str], list[int]]: ...


def keysentence(
    vocab_score: dict[str, float],
    texts: list[str],
    tokenize: Callable[[str], list[str]],
    topk: int = 10,
    diversity: float = 0.3,
    penalty: Callable[[str], float] | None = None,
    return_indices: bool = False,
) -> list[str] | tuple[list[str], list[int]]:
    """Select the most representative key sentences from *texts*.

    Sentences are ranked by cosine distance to the keyword vector and selected
    greedily while enforcing pairwise diversity.

    Args:
        vocab_score: Mapping ``{word: score}`` produced by
            :func:`make_vocab_score`.
        texts: Candidate sentence strings.
        tokenize: Callable ``(sentence) -> list[str]`` used to split sentences
            into subword tokens.
        topk: Number of key sentences to return.
        diversity: Minimum cosine distance between any two selected sentences
            (must be in ``[0, 1]``).
        penalty: Optional sentence filter. Returns ``0`` to keep a sentence or
            a positive float to penalise it.
        return_indices: If True, also return the original indices of selected
            sentences in *texts*.

    Returns:
        List of *topk* key sentence strings when *return_indices* is False.
        ``(sentences, indices)`` tuple when *return_indices* is True.

    Raises:
        ValueError: If *diversity* is outside ``[0, 1]``.
    """
    if not callable(penalty):

        def penalty(x):
            return 0

    if not 0 <= diversity <= 1:
        raise ValueError("Diversity must be [0, 1] float value")

    vectorizer = KeywordVectorizer(tokenize, vocab_score)
    x = vectorizer.vectorize(texts)
    keyvec = vectorizer.keyword_vector.reshape(1, -1)
    initial_penalty = np.asarray([penalty(sent) for sent in texts])
    idxs = select(x, keyvec, texts, initial_penalty, topk, diversity)
    if return_indices is True:
        return [texts[idx] for idx in idxs], idxs
    else:
        return [texts[idx] for idx in idxs]


def select(
    x: csr_matrix,
    keyvec: np.ndarray,
    texts: list[str],
    initial_penalty: np.ndarray,
    topk: int = 10,
    diversity: float = 0.3,
) -> list[int]:
    """Greedy diverse sentence selection based on cosine distance.

    Iteratively picks the sentence with the smallest cosine distance to
    *keyvec*, then penalises all remaining sentences that are within
    *diversity* distance of the chosen one.

    Args:
        x: Sparse Boolean matrix of shape ``(n_docs, n_keywords)``.
        keyvec: Reference keyword vector of shape ``(1, n_keywords)``.
        texts: Original sentence strings (used only for length information).
        initial_penalty: Pre-computed penalty array of shape ``(n_docs,)``
            derived from a user-supplied penalty function.
        topk: Number of sentences to select.
        diversity: Minimum cosine distance between any two selected sentences.

    Returns:
        List of *topk* sentence indices into *texts*, ordered by selection
        priority.
    """
    dist = pairwise_distances(x, keyvec, metric="cosine").reshape(-1)
    dist = dist + initial_penalty

    idxs = []
    for _ in range(topk):
        idx = dist.argmin()
        idxs.append(idx)
        dist[idx] += 2  # maximum distance of cosine is 2
        idx_all_distance = pairwise_distances(x, x[idx].reshape(1, -1), metric="cosine").reshape(-1)
        penalty = np.zeros(idx_all_distance.shape[0])
        penalty[np.where(idx_all_distance < diversity)[0]] = 2
        dist += penalty
    return idxs


def make_vocab_score(
    keywords: dict[str, float],
    stopwords: set[str] | dict[str, float],
    negatives: dict[str, float] | None = None,
    scaling: Callable[[float], float] = lambda x: x,
    topk: int = 100,
) -> dict[str, float]:
    """Filter and re-scale keyword ranks into a vocabulary score mapping.

    Iterates over *keywords* in descending rank order, skips stopwords,
    optionally replaces scores with values from *negatives*, and returns the
    top *topk* entries after applying *scaling*.

    Args:
        keywords: Raw ``{word: rank}`` output from KR-WordRank.
        stopwords: Words to exclude from the result.
        negatives: Optional penalty mapping. When a word appears here its score
            is replaced with ``negatives[word]`` instead of being scaled.
        scaling: Monotone function applied to each rank value before storing.
            Defaults to the identity function.
        topk: Maximum number of entries in the returned dict.

    Returns:
        Refined ``{word: score}`` mapping with at most *topk* entries.
    """
    if negatives is None:
        negatives = {}
    keywords_ = {}
    for word, rank in sorted(keywords.items(), key=lambda x: -x[1]):
        if len(keywords_) >= topk:
            break
        if word in stopwords:
            continue
        if word in negatives:
            keywords_[word] = negatives[word]
        else:
            keywords_[word] = scaling(rank)
    return keywords_


def highlight_keyword(sent: str, keywords: dict[str, float]) -> str:
    """Wrap positively-scored keywords in square brackets.

    Args:
        sent: Input sentence string.
        keywords: Mapping ``{word: score}``; words with ``score > 0`` are
            highlighted.

    Returns:
        Sentence string with each positive-scored keyword replaced by
        ``[keyword]``.
    """
    for keyword, score in keywords.items():
        if score > 0:
            sent = sent.replace(keyword, "[%s]" % keyword)
    return sent
