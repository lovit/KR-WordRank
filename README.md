# KR-WordRank: Unsupervised Korean Word & Keyword Extractor

- pure Python code
- author: Lovit (Hyunjoong Kim)
- reference: [Kim, H. J., Cho, S., & Kang, P. (2014). KR-WordRank: An Unsupervised Korean Word Extraction Method Based on WordRank. Journal of Korean Institute of Industrial Engineers, 40(1), 18-33][paper]

## Usage

Substring graph를 만들기 위하여 substring의 최소 등장 빈도수 (min count)와 substring의 최대 길이 (max length)를 입력해야 합니다. 

	min_count = 5   # 단어의 최소 출현 빈도수 (그래프 생성 시)
	max_length = 10 # 단어의 최대 길이
	wordrank_extractor = KRWordRank(min_count, max_length)

KR-WordRank는 PageRank 와 비슷한 graph ranking 알고리즘을 이용하여 단어를 추출합니다 (HITS algorithm 을 이용합니다). Substring graph에서 node (substrig) 랭킹을 계산하기 위하여 graph  ranking 알고리즘의 parameters 가 입력되야 합니다. 

	beta = 0.85    # PageRank의 decaying factor beta
	max_iter = 10
	verbose = True
	texts = ['예시 문장 입니다', '여러 문장의 list of str 입니다', ... ]
	keywords, rank, graph = wordrank_extractor.extract(texts, beta, max_iter, verbose)

Graph ranking 이 높은 노드들(substrings)이 후처리 과정을 거쳐 단어로 출력됩니다. 영화 '라라랜드'의 영화 평 데이터에서 키워드 (단어) 추출을 한 결과 예시가 tutorials에 있습니다.

	for word, r in sorted(keywords.items(), key=lambda x:x[1], reverse=True)[:30]:
    	    print('%8s:\t%.4f' % (word, r))

	      영화:	229.7889
	     관람객:	112.3404
	      너무:	78.4055
	      음악:	37.6247
	      정말:	37.2504
	            ....

## Setup

	pip install krwordrank


## Require

- numpy 

[paper]: https://github.com/lovit/KR-WordRank/raw/master/reference/2014_JKIIE_KimETAL_KR-WordRank.pdf
