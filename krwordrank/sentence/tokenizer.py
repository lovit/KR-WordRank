type Token = tuple[str, int, int, float, int]
"""A scored subtoken span: ``(text, begin, end, score, length)``."""


class MaxScoreTokenizer:
    """Greedy tokenizer that selects non-overlapping subtokens by score.

    At each step the highest-scoring (longest, leftmost as tiebreakers)
    subtoken is selected, all overlapping candidates are discarded, and the
    process repeats until the entire input token is covered.

    Transplanted from ``soynlp.tokenizer.MaxScoreTokenizer``.

    Attributes:
        _scores: Mapping from subword string to its score.
        _max_length: Maximum subtoken length considered during candidate
            generation.
        _ds: Default score used for subtokens absent from *_scores*.

    Example:
        >>> word_score = {"term": 0.8}
        >>> tokenizer = MaxScoreTokenizer(word_score)
        >>> tokenizer.tokenize("example term")
        ['example', 'term']
    """

    def __init__(
        self,
        scores: dict[str, float] | None = None,
        max_length: int = 10,
        default_score: float = 0.0,
    ) -> None:
        """Initialise the tokenizer.

        Args:
            scores: Mapping from subword string to score. Defaults to an empty
                dict (all subtokens receive *default_score*).
            max_length: Maximum subtoken length to consider.
            default_score: Score assigned to subtokens not present in *scores*.
        """
        self._scores = scores if scores else {}
        self._max_length = max_length
        self._ds = default_score

    def __call__(self, sentence: str, flatten: bool = True) -> list[str] | list[list[Token]]:
        """Tokenize *sentence* (alias for :meth:`tokenize`).

        Args:
            sentence: Input sentence string.
            flatten: See :meth:`tokenize`.

        Returns:
            See :meth:`tokenize`.
        """
        return self.tokenize(sentence, flatten)

    def tokenize(self, sentence: str, flatten: bool = True) -> list[str] | list[list[Token]]:
        """Tokenize a sentence into subword tokens.

        Args:
            sentence: Input sentence string (space-separated words).
            flatten: If True, return a flat ``list[str]`` of subtoken strings.
                If False, return a ``list[list[Token]]`` grouped by input word.

        Returns:
            Flat list of subtoken strings when *flatten* is True; otherwise a
            nested list of :data:`Token` tuples grouped by whitespace-delimited
            word.
        """
        tokens = [self._recursive_tokenize(token) for token in sentence.split()]
        if flatten:
            tokens = [subtoken[0] for token in tokens for subtoken in token]
        return tokens

    def _recursive_tokenize(self, token: str, range_l: int = 0, debug: bool = False) -> list[Token]:
        length = len(token)
        if length <= 2:
            return [(token, 0, length, self._ds, length)]

        if range_l == 0:
            range_l = min(self._max_length, length)

        scores = self._initialize(token, range_l, length)
        if debug:
            from pprint import pprint

            pprint(scores)

        result = self._find(scores)

        adds = self._add_inter_subtokens(token, result)

        if result[-1][2] != length:
            adds += self._add_last_subtoken(token, result)

        if result[0][1] != 0:
            adds += self._add_first_subtoken(token, result)

        return sorted(result + adds, key=lambda x: x[1])

    def _initialize(self, token: str, range_l: int, length: int) -> list[Token]:
        scores = []
        for b in range(0, length - 1):
            for r in range(2, range_l + 1):
                e = b + r

                if e > length:
                    continue

                subtoken = token[b:e]
                score = self._scores.get(subtoken, self._ds)
                scores.append((subtoken, b, e, score, r))

        return sorted(scores, key=lambda x: (-x[3], -x[4], x[1]))

    def _find(self, scores: list[Token]) -> list[Token]:
        result = []
        num_iter = 0

        while scores:
            word, b, e, score, r = scores.pop(0)
            result.append((word, b, e, score, r))

            if not scores:
                break

            removals = []
            for i, (_1, b_, e_, _2, _3) in enumerate(scores):
                if (b_ < e and b < e_) or (b_ < e and e_ > b):
                    removals.append(i)

            for i in reversed(removals):
                del scores[i]

            num_iter += 1
            if num_iter > 100:
                break

        return sorted(result, key=lambda x: x[1])

    def _add_inter_subtokens(self, token: str, result: list[Token]) -> list[Token]:
        adds = []
        for i, base in enumerate(result[:-1]):
            if base[2] == result[i + 1][1]:
                continue

            b = base[2]
            e = result[i + 1][1]
            subtoken = token[b:e]
            adds.append((subtoken, b, e, self._ds, e - b))

        return adds

    def _add_first_subtoken(self, token: str, result: list[Token]) -> list[Token]:
        e = result[0][1]
        subtoken = token[0:e]
        score = self._scores.get(subtoken, self._ds)
        return [(subtoken, 0, e, score, e)]

    def _add_last_subtoken(self, token: str, result: list[Token]) -> list[Token]:
        b = result[-1][2]
        subtoken = token[b:]
        score = self._scores.get(subtoken, self._ds)
        return [(subtoken, b, len(token), score, len(subtoken))]
