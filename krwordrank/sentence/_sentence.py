import numpy as np
from scipy.sparse import csr_matrix


class Summarizer:
    def __init__(self, num_keywords=100, num_sents=10, diversity=0.3, penalty=None):
        self.num_keywords = num_keywords
        self.num_sents = num_sents
        self.diversity = diversity
        self.penalty = penalty


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
        self.idx_to_vocab = [vocab for vocab in sorted(vocab_score, key=lambda x:-keywords[x])]
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


def keysentence(keywords, texts, topk=10, diversity=0.3, penalty=None):
    raise NotImplemented


def highlight_keyword(sent, keywords):
    for keyword, score in keywords.items():
        if score > 0:
            sent = sent.replace(keyword, '[%s]' % keyword)
    return sent