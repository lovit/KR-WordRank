class MaxScoreTokenizer:
    """
    Transplanted from soynlp.tokenizer.MaxScoreTokenizer

    >>> word_score = {'term':0.8, ...}
    >>> tokenizer = MaxScoreTokenizer(word_score)
    >>> tokenizer.tokenize('Example sentence')
    """

    def __init__(self, scores=None, max_length=10, default_score=0.0):
        self._scores = scores if scores else {}
        self._max_length = max_length
        self._ds = default_score

    def __call__(self, sentence, flatten=True):
        return self.tokenize(sentence, flatten)

    def tokenize(self, sentence, flatten=True):
        tokens = [self._recursive_tokenize(token) for token in sentence.split()]
        if flatten:
            tokens = [subtoken[0] for token in tokens for subtoken in token]
        return tokens

    def _recursive_tokenize(self, token, range_l=0, debug=False):

        length = len(token)
        if length <= 2:
            return [(token, 0, length, self._ds, length)]

        if range_l == 0:
            range_l = min(self._max_length, length)

        scores = self._initialize(token, range_l, length)
        if debug:
            pprint(scores)

        result = self._find(scores)

        adds = self._add_inter_subtokens(token, result)

        if result[-1][2] != length:
            adds += self._add_last_subtoken(token, result)

        if result[0][1] != 0:
            adds += self._add_first_subtoken(token, result)

        return sorted(result + adds, key=lambda x:x[1])

    def _initialize(self, token, range_l, length):
        scores = []
        for b in range(0, length - 1):
            for r in range(2, range_l + 1):
                e = b + r

                if e > length:
                    continue

                subtoken = token[b:e]
                score = self._scores.get(subtoken, self._ds)
                scores.append((subtoken, b, e, score, r))

        return sorted(scores, key=lambda x:(-x[3], -x[4], x[1]))

    def _find(self, scores):
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
            if num_iter > 100: break

        return sorted(result, key=lambda x:x[1])

    def _add_inter_subtokens(self, token, result):
        adds = []
        for i, base in enumerate(result[:-1]):
            if base[2] == result[i+1][1]:
                continue

            b = base[2]
            e = result[i+1][1]
            subtoken = token[b:e]
            adds.append((subtoken, b, e, self._ds, e - b))

        return adds

    def _add_first_subtoken(self, token, result):
        e = result[0][1]
        subtoken = token[0:e]
        score = self._scores.get(subtoken, self._ds)
        return [(subtoken, 0, e, score, e)]

    def _add_last_subtoken(self, token, result):
        b = result[-1][2]
        subtoken = token[b:]
        score = self._scores.get(subtoken, self._ds)
        return [(subtoken, b, len(token), score, len(subtoken))]
