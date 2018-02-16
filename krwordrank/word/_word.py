from collections import defaultdict
import math

import numpy as np

class KRWordRank:
    """Unsupervised Korean Keyword Extractor

    Implementation of Kim, H. J., Cho, S., & Kang, P. (2014). KR-WordRank: 
    An Unsupervised Korean Word Extraction Method Based on WordRank. 
    Journal of Korean Institute of Industrial Engineers, 40(1), 18-33.
    """
    def __init__(self, min_count=5, max_length=10, verbose=False):
        self.min_count = min_count
        self.max_length = max_length
        self.verbose = verbose
        self.sum_weight = 1
        self.vocabulary = {}
        self.index2vocab = []

    def scan_vocabs(self, docs):
        self.vocabulary = {}
        if self.verbose:
            print('scan vocabs ... ')
        
        counter = {}        
        for doc in docs:
            
            for token in doc.split():
                len_token = len(token)
                counter[(token, 'L')] = counter.get((token, 'L'), 0) + 1
                
                for e in range(1, min(len(token), self.max_length)):
                    if (len_token - e) > self.max_length:
                        continue
                        
                    l_sub = (token[:e], 'L')
                    r_sub = (token[e:], 'R')
                    counter[l_sub] = counter.get(l_sub, 0) + 1
                    counter[r_sub] = counter.get(r_sub, 0) + 1
        
        counter = {token:freq for token, freq in counter.items() if freq >= self.min_count}
        for token, _ in sorted(counter.items(), key=lambda x:x[1], reverse=True):
            self.vocabulary[token] = len(self.vocabulary)
            
        self._build_index2vocab()
        
        if self.verbose:
            print('num vocabs = %d' % len(counter))        
        return counter
    
    def _build_index2vocab(self):
        self.index2vocab = [vocab for vocab, index in sorted(self.vocabulary.items(), key=lambda x:x[1])]
        self.sum_weight = len(self.index2vocab)
    
    def extract(self, docs, beta=0.85, max_iter=10, vocabulary=None, bias=None, rset=None):
        rank, graph = self.train(docs, beta, max_iter, vocabulary, bias)
        
        lset = {self.int2token(idx)[0]:r for idx, r in rank.items() if self.int2token(idx)[1] == 'L'}
        if not rset:
            rset = {self.int2token(idx)[0]:r for idx, r in rank.items() if self.int2token(idx)[1] == 'R'}
        
        keywords = self._select_keywords(lset, rset)
        keywords = self._filter_compounds(keywords)
        keywords = self._filter_subtokens(keywords)
        
        return keywords, rank, graph
        
    def _select_keywords(self, lset, rset):
        keywords = {}
        for word, r in sorted(lset.items(), key=lambda x:x[1], reverse=True):
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
    
    def _filter_compounds(self, keywords):
        keywords_= {}
        for word, r in sorted(keywords.items(), key=lambda x:x[1], reverse=True):
            len_word = len(word)

            if len_word <= 2:
                keywords_[word] = r
                continue

            if len_word == 3:
                if word[:2] in keywords_:
                    continue

            is_compound = False
            for e in range(2, len_word - 1):
                if (word[:e] in keywords) and (word[:e] in keywords):
                    is_compound = True
                    break

            if not is_compound:
                keywords_[word] = r
        
        return keywords_

    def _filter_subtokens(self, keywords):
        subtokens = set()
        keywords_ = {}

        for word, r in sorted(keywords.items(), key=lambda x:x[1], reverse=True):
            subs = {word[:e] for e in range(2, len(word)+1)}
            
            is_subtoken = False
            for sub in subs:
                if sub in subtokens:
                    is_subtoken = True
                    break
            
            if not is_subtoken:
                keywords_[word] = r
                subtokens.update(subs)

        return keywords_
    
    def train(self, docs, beta=0.85, max_iter=10, vocabulary=None, bias=None):
        if (not vocabulary) and (not self.vocabulary):
            self.scan_vocabs(docs)
        elif (not vocabulary):
            self.vocabulary = vocabulary
            self._build_index2vocab()

        if not bias:
            bias = {}
        
        graph = self._construct_word_graph(docs)       
        
        dw = self.sum_weight / len(self.vocabulary)
        rank = {node:dw for node in graph.keys()}
        
        for num_iter in range(1, max_iter + 1):
            rank = self._update(rank, graph, bias, dw, beta)
            if self.verbose:
                print('\riter = %d' % num_iter, end='', flush=True)
        if self.verbose:
            print('\rdone')
        
        return rank, graph
            
    def token2int(self, token):
        return self.vocabulary.get(token, -1)

    def int2token(self, index):
        return self.index2vocab[index] if (0 <= index < len(self.index2vocab)) else None
    
    def _construct_word_graph(self, docs):
        def normalize(graph):
            graph_ = defaultdict(lambda: defaultdict(lambda: 0))
            for from_, to_dict in graph.items():
                sum_ = sum(to_dict.values())
                for to_, w in to_dict.items():
                    graph_[to_][from_] = w / sum_
            return graph_
        
        graph = defaultdict(lambda: defaultdict(lambda: 0))        
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
            
        graph = normalize(graph)        
        return graph
    
    def _intra_link(self, token):
        links = []
        len_token = len(token)
        for e in range(1, min(len_token, 10)):
            if (len_token - e) > self.max_length:
                continue
            links.append( ((token[:e], 'L'), (token[e:], 'R')) )            
        return links
    
    def _inter_link(self, tokens):
        def rsub_to_token(t_left, t_curr):
            return [((t_left[-b:], 'R'), (t_curr, 'L')) for b in range(1, min(10, len(t_left)))]
        def token_to_lsub(t_curr, t_rigt):
            return [((t_curr, 'L'), (t_rigt[:e], 'L')) for e in range(1, min(10, len(t_rigt)))]

        links = []
        for i in range(1, len(tokens)-1):
            links += rsub_to_token(tokens[i-1], tokens[i])
            links += token_to_lsub(tokens[i], tokens[i+1])
        return links
    
    def _check_token(self, token_list):
        return [(token[0], token[1]) for token in token_list if (token[0] in self.vocabulary and token[1] in self.vocabulary)]
    
    def _encode_token(self, token_list):
        return [(self.vocabulary[token[0]],self.vocabulary[token[1]]) for token in token_list]
    
    def _update(self, rank, graph, bias, dw, beta):
        rank_new = {}
        for to_node, from_dict in graph.items():
            rank_new[to_node] = sum([w * rank[from_node] for from_node, w in from_dict.items()])
            rank_new[to_node] = beta * rank_new[to_node] + (1 - beta) * bias.get(to_node, dw)
        return rank_new