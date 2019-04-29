from collections import namedtuple

Performance = namedtuple('Performance', 'n_keywords n_keysents rouge1'.split())

def rouge1(keywords, keysents, tokenize, n_keywords=None, n_keysents=None):
    """
    Arguments
    ---------
    keywords : dict
        {keyword : rank} dictionary
    keysents : list of str
        Keysentence list
    tokenize : callable
        tokenize(str) = list of str
    n_keywords : list of int or None
        If None, n_keywords = [10, 20, 30, 50, 100]
    n_keysents: list of int or None
        If None, n_keysents = [3, 5, 10, 20, 30]

    Returns
    -------
    list of namedtuple
        Performance(n_keywords, n_keysents, rouge1)
    """
    if n_keywords is None:
        n_keywords = [10, 20, 30, 50, 100]
    if n_keysents is None:
        n_keysents = [3, 5, 10, 20, 30]

    keysents = [tokenize(sent) for sent in keysents]
    performance = []
    for n_keyword in n_keywords:
        keywords_ = {w for w, _ in sorted(keywords.items(), key=lambda x:-x[1])[:n_keyword]}
        for n_keysent in n_keysents:
            sents = keysents[:n_keysent]
            word_set = {w for sent in sents for w in sent}
            word_set = {w for w in word_set if w in keywords_}
            recall = len(word_set) / n_keyword
            performance.append(Performance(n_keyword, n_keysent, recall))
    return performance
