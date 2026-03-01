from collections import defaultdict

from krwordrank.graph import hits

type SubwordToken = tuple[str, str]
"""A subword token: ``(subword_string, position)`` where position is ``'L'`` or ``'R'``."""

type WordGraph = dict[int, dict[int, float]]
"""Adjacency graph: ``graph[to_node][from_node] = normalised_weight``."""


def summarize_with_keywords(
    texts: list[str],
    num_keywords: int = 100,
    stopwords: set[str] | None = None,
    min_count: int = 5,
    max_length: int = 10,
    beta: float = 0.85,
    max_iter: int = 10,
    num_rset: int = -1,
    verbose: bool = False,
) -> dict[str, float]:
    """Extract the top-ranked keywords from a collection of texts.

    Trains :class:`KRWordRank` on *texts*, removes *stopwords*, and returns
    the *num_keywords* highest-ranked words.

    Args:
        texts: List of input sentences.
        num_keywords: Maximum number of keywords to return.
        stopwords: Words to exclude from the result.
        min_count: Minimum subword frequency for graph construction.
        max_length: Maximum subword length for graph construction.
        beta: PageRank damping factor (0 < beta < 1).
        max_iter: Maximum HITS iterations.
        num_rset: Number of top-ranked R-set words used for L-part filtering.
            ``-1`` uses all.
        verbose: If True, prints training progress.

    Returns:
        Mapping ``{word: rank}`` for the top *num_keywords* keywords.

    Example:
        >>> from krwordrank.word import summarize_with_keywords
        >>> texts = [...]  # list of str
        >>> keywords = summarize_with_keywords(texts, num_keywords=100, min_count=5)
    """
    wordrank_extractor = KRWordRank(min_count=min_count, max_length=max_length, verbose=verbose)

    keywords, rank, graph = wordrank_extractor.extract(texts, beta, max_iter, num_rset=num_rset)

    if stopwords is None:
        stopwords = {}
    keywords = {word: r for word, r in keywords.items() if word not in stopwords}

    if num_keywords > 0:
        keywords = {word: r for word, r in sorted(keywords.items(), key=lambda x: -x[1])[:num_keywords]}

    return keywords


class KRWordRank:
    """Unsupervised Korean keyword extractor based on the HITS algorithm.

    Implements Kim, H. J., Cho, S., & Kang, P. (2014). *KR-WordRank: An
    Unsupervised Korean Word Extraction Method Based on WordRank.* Journal of
    Korean Institute of Industrial Engineers, 40(1), 18-33.

    Each eojeol (whitespace-delimited token) is split into L-subword and
    R-subword pairs. These pairs form nodes in a graph; edges are added for
    intra-token L/R splits and inter-token adjacency.  Node ranks are trained
    with the HITS algorithm and then filtered to retain high-quality words.

    Attributes:
        min_count: Minimum subword frequency for graph construction.
        max_length: Maximum subword length for graph construction.
        verbose: If True, prints training progress.
        sum_weight: Total node weight (equals vocabulary size after training).
        vocabulary: Mapping ``{(subword, position): node_index}``.
        index2vocab: Inverse list; ``index2vocab[i]`` is the token at index *i*.

    Example:
        >>> from krwordrank.word import KRWordRank
        >>> texts = ["예시 문장 입니다", "여러 문장의 list of str 입니다"]
        >>> extractor = KRWordRank()
        >>> keywords, rank, graph = extractor.extract(texts, beta=0.85, max_iter=10)
    """

    def __init__(self, min_count: int = 5, max_length: int = 10, verbose: bool = False) -> None:
        """Initialise KRWordRank.

        Args:
            min_count: Minimum subword frequency for graph construction.
            max_length: Maximum subword length for graph construction.
            verbose: If True, prints progress during training.
        """
        self.min_count = min_count
        self.max_length = max_length
        self.verbose = verbose
        self.sum_weight: int = 1
        self.vocabulary: dict[SubwordToken, int] = {}
        self.index2vocab: list[SubwordToken] = []

    def scan_vocabs(self, docs: list[str]) -> dict[SubwordToken, int]:
        """Scan subword L/R tokens from *docs* and build the vocabulary.

        Iterates over every whitespace-delimited token in *docs*, generates all
        valid L/R split pairs within ``max_length``, counts their frequencies,
        and keeps only those that appear at least ``min_count`` times.

        Args:
            docs: List of sentence strings.

        Returns:
            Frequency counter ``{(subword, position): count}`` for all
            subwords that passed the ``min_count`` threshold.
        """
        self.vocabulary = {}
        if self.verbose:
            print("scan vocabs ... ")

        counter: dict[SubwordToken, int] = {}
        for doc in docs:
            for token in doc.split():
                len_token = len(token)
                counter[(token, "L")] = counter.get((token, "L"), 0) + 1

                for e in range(1, min(len(token), self.max_length)):
                    if (len_token - e) > self.max_length:
                        continue

                    l_sub = (token[:e], "L")
                    r_sub = (token[e:], "R")
                    counter[l_sub] = counter.get(l_sub, 0) + 1
                    counter[r_sub] = counter.get(r_sub, 0) + 1

        counter = {token: freq for token, freq in counter.items() if freq >= self.min_count}
        for token, _ in sorted(counter.items(), key=lambda x: x[1], reverse=True):
            self.vocabulary[token] = len(self.vocabulary)

        self._build_index2vocab()

        if self.verbose:
            print("num vocabs = %d" % len(counter))
        return counter

    def _build_index2vocab(self) -> None:
        self.index2vocab = [vocab for vocab, index in sorted(self.vocabulary.items(), key=lambda x: x[1])]
        self.sum_weight = len(self.index2vocab)

    def extract(
        self,
        docs: list[str],
        beta: float = 0.85,
        max_iter: int = 10,
        num_keywords: int = -1,
        num_rset: int = -1,
        vocabulary: dict[SubwordToken, int] | None = None,
        bias: dict[str, float] | None = None,
        rset: dict[str, float] | None = None,
    ) -> tuple[dict[str, float], dict[int, float], WordGraph]:
        """Build the subword graph, train HITS ranks, and extract keywords.

        Args:
            docs: List of sentence strings.
            beta: PageRank damping factor (0 < beta < 1).
            max_iter: Maximum HITS iterations.
            num_keywords: Maximum keywords to return. ``-1`` returns all.
            num_rset: Number of top-ranked R-set words used for L-part
                filtering. ``-1`` uses all.
            vocabulary: Custom ``{(subword, position): index}`` mapping.
                When provided, skips :meth:`scan_vocabs`.
            bias: Custom HITS bias as ``{word: value}`` (L-position assumed).
            rset: Custom R-set as ``{word: rank}``.  When provided, the
                R-set derived from training is not used.

        Returns:
            A three-tuple ``(keywords, rank, graph)`` where:

            - *keywords*: ``{word: rank}`` for extracted words.
            - *rank*: ``{node_index: rank_value}`` for all subword nodes.
            - *graph*: Normalised adjacency dict ``{to_node: {from_node: weight}}``.

        Example:
            >>> extractor = KRWordRank()
            >>> keywords, rank, graph = extractor.extract(texts, beta=0.85, max_iter=10)
        """
        rank, graph = self.train(docs, beta, max_iter, vocabulary, bias)

        lset = {self.int2token(idx)[0]: r for idx, r in rank.items() if self.int2token(idx)[1] == "L"}
        if not rset:
            rset = {self.int2token(idx)[0]: r for idx, r in rank.items() if self.int2token(idx)[1] == "R"}

        if num_rset > 0:
            rset = {token: r for token, r in sorted(rset.items(), key=lambda x: -x[1])[:num_rset]}

        keywords = self._select_keywords(lset, rset)
        keywords = self._filter_compounds(keywords)
        keywords = self._filter_subtokens(keywords)

        if num_keywords > 0:
            keywords = {token: r for token, r in sorted(keywords.items(), key=lambda x: -x[1])[:num_keywords]}

        return keywords, rank, graph

    def _select_keywords(self, lset: dict[str, float], rset: dict[str, float]) -> dict[str, float]:
        keywords: dict[str, float] = {}
        for word, r in sorted(lset.items(), key=lambda x: x[1], reverse=True):
            len_word = len(word)
            if len_word == 1:
                continue

            is_compound = False
            for e in range(2, len_word):
                if (word[:e] in keywords) and (word[:e] in rset):
                    is_compound = True
                    break

            if not is_compound:
                keywords[word] = r

        return keywords

    def _filter_compounds(self, keywords: dict[str, float]) -> dict[str, float]:
        keywords_: dict[str, float] = {}
        for word, r in sorted(keywords.items(), key=lambda x: x[1], reverse=True):
            len_word = len(word)

            if len_word <= 2:
                keywords_[word] = r
                continue

            if len_word == 3:
                if word[:2] in keywords_:
                    continue

            is_compound = False
            for e in range(2, len_word - 1):
                # fixed. comment from Y. cho
                if (word[:e] in keywords) and (word[e:] in keywords):
                    is_compound = True
                    break

            if not is_compound:
                keywords_[word] = r

        return keywords_

    def _filter_subtokens(self, keywords: dict[str, float]) -> dict[str, float]:
        subtokens: set[str] = set()
        keywords_: dict[str, float] = {}

        for word, r in sorted(keywords.items(), key=lambda x: x[1], reverse=True):
            subs = {word[:e] for e in range(2, len(word) + 1)}

            is_subtoken = False
            for sub in subs:
                if sub in subtokens:
                    is_subtoken = True
                    break

            if not is_subtoken:
                keywords_[word] = r
                subtokens.update(subs)

        return keywords_

    def train(
        self,
        docs: list[str],
        beta: float = 0.85,
        max_iter: int = 10,
        vocabulary: dict[SubwordToken, int] | None = None,
        bias: dict[str, float] | None = None,
    ) -> tuple[dict[int, float], WordGraph]:
        """Build the subword graph and train HITS node ranks.

        Use this method when you only need the raw subword ranks and graph
        without keyword post-processing.

        Args:
            docs: List of sentence strings.
            beta: PageRank damping factor (0 < beta < 1).
            max_iter: Maximum HITS iterations.
            vocabulary: Custom ``{(subword, position): index}`` mapping.
                When provided, skips :meth:`scan_vocabs`.
            bias: Custom HITS bias as ``{word: value}`` (L-position assumed).
                Format: ``{str: float}``.

        Returns:
            A two-tuple ``(rank, graph)`` where:

            - *rank*: ``{node_index: rank_value}`` for all subword nodes.
            - *graph*: Normalised adjacency dict
              ``{to_node: {from_node: weight}}``.
        """
        if (not vocabulary) and (not self.vocabulary):
            self.scan_vocabs(docs)
        elif not vocabulary:
            self.vocabulary = vocabulary
            self._build_index2vocab()

        graph = self._construct_word_graph(docs)

        encoded_bias: dict[int, float] = {}
        if bias:
            for word, value in bias.items():
                encoded_word = self.token2int((word, "L"))
                if encoded_word != -1:
                    encoded_bias[encoded_word] = value

        rank = hits(
            graph,
            beta,
            max_iter,
            encoded_bias,
            sum_weight=self.sum_weight,
            number_of_nodes=len(self.vocabulary),
            verbose=self.verbose,
        )

        return rank, graph

    def token2int(self, token: SubwordToken) -> int:
        """Convert a subword token to its vocabulary index.

        Args:
            token: ``(subword, position)`` tuple, e.g. ``('이것', 'L')`` or
                ``('은', 'R')``.

        Returns:
            Integer index of *token* in the vocabulary, or ``-1`` if unknown.
        """
        return self.vocabulary.get(token, -1)

    def int2token(self, index: int) -> SubwordToken | None:
        """Convert a vocabulary index back to its subword token.

        Args:
            index: Node index to look up.

        Returns:
            ``(subword, position)`` tuple, e.g. ``('이것', 'L')``, or ``None``
            if *index* is out of range.
        """
        return self.index2vocab[index] if (0 <= index < len(self.index2vocab)) else None

    def _construct_word_graph(self, docs: list[str]) -> WordGraph:
        def normalize(graph: defaultdict) -> WordGraph:
            graph_: defaultdict = defaultdict(lambda: defaultdict(lambda: 0))
            for from_, to_dict in graph.items():
                sum_ = sum(to_dict.values())
                for to_, w in to_dict.items():
                    graph_[to_][from_] = w / sum_
            return {t: dict(fd) for t, fd in graph_.items()}

        graph: defaultdict = defaultdict(lambda: defaultdict(lambda: 0))
        for doc in docs:
            tokens = doc.split()

            if not tokens:
                continue

            links = []
            for token in tokens:
                links += self._intra_link(token)

            if len(tokens) > 1:
                tokens = [tokens[-1]] + tokens + [tokens[0]]
                links += self._inter_link(tokens)

            links = self._check_token(links)
            if not links:
                continue

            links = self._encode_token(links)
            for l_node, r_node in links:
                graph[l_node][r_node] += 1
                graph[r_node][l_node] += 1

        return normalize(graph)

    def _intra_link(self, token: str) -> list[tuple[SubwordToken, SubwordToken]]:
        links = []
        len_token = len(token)
        for e in range(1, min(len_token, 10)):
            if (len_token - e) > self.max_length:
                continue
            links.append(((token[:e], "L"), (token[e:], "R")))
        return links

    def _inter_link(self, tokens: list[str]) -> list[tuple[SubwordToken, SubwordToken]]:
        def rsub_to_token(t_left: str, t_curr: str) -> list[tuple[SubwordToken, SubwordToken]]:
            return [((t_left[-b:], "R"), (t_curr, "L")) for b in range(1, min(10, len(t_left)))]

        def token_to_lsub(t_curr: str, t_rigt: str) -> list[tuple[SubwordToken, SubwordToken]]:
            return [((t_curr, "L"), (t_rigt[:e], "L")) for e in range(1, min(10, len(t_rigt)))]

        links: list[tuple[SubwordToken, SubwordToken]] = []
        for i in range(1, len(tokens) - 1):
            links += rsub_to_token(tokens[i - 1], tokens[i])
            links += token_to_lsub(tokens[i], tokens[i + 1])
        return links

    def _check_token(self, token_list: list[tuple[SubwordToken, SubwordToken]]) -> list[tuple[SubwordToken, SubwordToken]]:
        return [(token[0], token[1]) for token in token_list if (token[0] in self.vocabulary and token[1] in self.vocabulary)]

    def _encode_token(self, token_list: list[tuple[SubwordToken, SubwordToken]]) -> list[tuple[int, int]]:
        return [(self.vocabulary[token[0]], self.vocabulary[token[1]]) for token in token_list]
