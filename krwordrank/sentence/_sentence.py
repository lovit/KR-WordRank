import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics import pairwise_distances

from ._tokenizer import MaxScoreTokenizer
from ..word import KRWordRank


class KeywordVectorizer:
    """
    Arguments
    ---------
    tokenize : callable
        Input format is str, output format is list of str (list of terms)
    vocab_score : dict
        {str:float} form keyword vector

    Attributes
    ----------
    tokenize : callable
        Tokenizer function
    idx_to_vocab : list of str
        Vocab list
    vocab_to_idx : dict
        {str:int} Vocab to index mapper
    keyword_vector : numpy.ndarray
        shape (len(idx_to_vocab),) vector
    """

    def __init__(self, tokenize, vocab_score):
        self.tokenize = tokenize
        self.idx_to_vocab = [vocab for vocab in sorted(vocab_score, key=lambda x:-vocab_score[x])]
        self.vocab_to_idx = {vocab:idx for idx, vocab in enumerate(self.idx_to_vocab)}
        self.keyword_vector = np.asarray(
            [score for _, score in sorted(vocab_score.items(), key=lambda x:-x[1])])
        self.keyword_vector = self._L2_normalize(self.keyword_vector)

    def _L2_normalize(self, vectors):
        return vectors / np.sqrt((vectors ** 2).sum())

    def vectorize(self, sents):
        """
        Argument
        --------
        sents : list of str
            Each str is sentence

        Returns
        -------
        scipy.sparse.csr_matrix
            (n sents, n keywords) shape Boolean matrix
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


def summarize_with_sentences(texts, num_keywords=100, num_keysents=10, diversity=0.3, stopwords=None, scaling=None,
    penalty=None, min_count=5, max_length=10, beta=0.85, max_iter=10, num_rset=-1, verbose=False):
    """
    It train KR-WordRank to extract keywords and selects key-sentences to summzriaze inserted texts.

        >>> from krwordrank.sentence import summarize_with_sentences

        >>> texts = [] # list of str
        >>> keywords, sents = summarize_with_sentences(texts, num_keywords=100, num_keysents=10)

    Arguments
    ---------
    texts : list of str
        Each str is a sentence.
    num_keywords : int
        Number of keywords extracted from KR-WordRank
        Default is 100.
    num_keysents : int
        Number of key-sentences selected from keyword vector maching
        Default is 10.
    diversity : float
        Minimum cosine distance between top ranked sentence and others.
        Large value makes this function select various sentence.
        The value must be [0, 1]
    stopwords : None or set of str
        Stopwords list for keyword and key-sentence extraction
    scaling : callable
        Ranking transform function.
        scaling(float) = float
        Default is lambda x:np.sqrt(x)
    penalty : callable
        Penalty function. str -> float
        Default is no penalty
        If you use only sentence whose length is in [25, 40],
        set penalty like following example.

            >>> penalty = lambda x: 0 if 25 <= len(x) <= 40 else 1

    min_count : int
        Minimum frequency of subwords used to construct subword graph
        Default is 5
    max_length : int
        Maximum length of subwords used to construct subword graph
        Default is 10
    beta : float
        PageRank damping factor. 0 < beta < 1
        Default is 0.85
    max_iter : int
        Maximum number of iterations of HITS algorithm.
        Default is 10
    num_rset : int
        Number of R set words sorted by rank. It will be used to L-part word filtering.
        Default is -1.
    verbose : Boolean
        If True, it shows training status
        Default is False

    Returns
    -------
    keysentences : list of str

    Usage
    -----
        >>> from krwordrank.sentence import summarize_with_sentences

        >>> texts = [] # list of str
        >>> keywords, sents = summarize_with_sentences(texts, num_keywords=100, num_keysents=10)
    """

    # train KR-WordRank
    wordrank_extractor = KRWordRank(
        min_count = min_count,
        max_length = max_length,
        verbose = verbose
        )

    num_keywords_ = num_keywords
    if stopwords is not None:
        num_keywords_ += len(stopwords)

    keywords, rank, graph = wordrank_extractor.extract(texts,
        beta, max_iter, num_keywords=num_keywords_, num_rset=num_rset)

    # build tokenizer
    if scaling is None:
        scaling = lambda x:np.sqrt(x)
    if stopwords is None:
        stopwords = {}
    vocab_score = make_vocab_score(keywords, stopwords, scaling=scaling, topk=num_keywords)
    tokenizer = MaxScoreTokenizer(scores=vocab_score)

    # find key-sentences
    sents = keysentence(vocab_score, texts, tokenizer.tokenize, num_keysents, diversity, penalty)
    keywords_ = {vocab:keywords[vocab] for vocab in vocab_score}
    return keywords_, sents

def keysentence(vocab_score, texts, tokenize, topk=10, diversity=0.3, penalty=None):
    """
    Arguments
    ---------
    keywords : {str:int}
        {word:rank} trained from KR-WordRank.
        texts will be tokenized using keywords
    texts : list of str
        Each str is a sentence.
    tokenize : callble
        Tokenize function. Input form is str and output form is list of str
    topk : int
        Number of key sentences
    diversity : float
        Minimum cosine distance between top ranked sentence and others.
        Large value makes this function select various sentence.
        The value must be [0, 1]
    penalty : callable
        Penalty function. str -> float
        Default is no penalty
        If you use only sentence whose length is in [25, 40],
        set penalty like following example.

            >>> penalty = lambda x: 0 if 25 <= len(x) <= 40 else 1

    Returns
    -------
    keysentences : list of str
    """
    if not callable(penalty):
        penalty = lambda x: 0

    if not 0 <= diversity <= 1:
        raise ValueError('Diversity must be [0, 1] float value')

    vectorizer = KeywordVectorizer(tokenize, vocab_score)
    x = vectorizer.vectorize(texts)
    keyvec = vectorizer.keyword_vector.reshape(1,-1)
    initial_penalty = np.asarray([penalty(sent) for sent in texts])
    idxs = select(x, keyvec, texts, initial_penalty, topk, diversity)
    return [texts[idx] for idx in idxs]

def select(x, keyvec, texts, initial_penalty, topk=10, diversity=0.3):
    """
    Arguments
    ---------
    x : scipy.sparse.csr_matrix
        (n docs, n keywords) Boolean matrix
    keyvec : numpy.ndarray
        (1, n keywords) rank vector
    texts : list of str
        Each str is a sentence
    initial_penalty : numpy.ndarray
        (n docs,) shape. Defined from penalty function
    topk : int
        Number of key sentences
    diversity : float
        Minimum cosine distance between top ranked sentence and others.
        Large value makes this function select various sentence.
        The value must be [0, 1]

    Returns
    -------
    keysentence indices : list of int
        The length of keysentences is topk at most.
    """

    dist = pairwise_distances(x, keyvec, metric='cosine').reshape(-1)
    dist = dist + initial_penalty

    idxs = []
    for _ in range(topk):
        idx = dist.argmin()
        idxs.append(idx)
        dist[idx] += 2 # maximum distance of cosine is 2
        idx_all_distance = pairwise_distances(
            x, x[idx].reshape(1,-1), metric='cosine').reshape(-1)
        penalty = np.zeros(idx_all_distance.shape[0])
        penalty[np.where(idx_all_distance < diversity)[0]] = 2
        dist += penalty
    return idxs

def make_vocab_score(keywords, stopwords, negatives=None, scaling=lambda x:x, topk=100):
    """
    Arguments
    ---------
    keywords : dict
        {str:float} word to rank mapper that trained from KR-WordRank
    stopwords : set or dict of str
        Stopword set
    negatives : dict or None
        Penalty term set
    scaling : callable
        number to number. It re-scale rank value of keywords.
    topk : int
        Number of keywords

    Returns
    -------
    keywords_ : dict
        Refined word to score mapper
    """
    if negatives is None:
        negatives = {}
    keywords_ = {}
    for word, rank in sorted(keywords.items(), key=lambda x:-x[1]):
        if len(keywords_) >= topk:
            break
        if word in stopwords:
            continue
        if word in negatives:
            keywords_[word] = negative[word]
        else:
            keywords_[word] = scaling(rank)
    return keywords_

def highlight_keyword(sent, keywords):
    for keyword, score in keywords.items():
        if score > 0:
            sent = sent.replace(keyword, '[%s]' % keyword)
    return sent