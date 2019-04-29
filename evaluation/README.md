# Evaluation for key-sentences extraction

ROUGE-1 을 이용한 sentence extraction based summarization performance evaluation 입니다.

## Key-sentences extraction in KR-WordRank

TextRank 와 KR-WordRank 는 keyword extraction 기능과 key-sentence extracion 기능을 모두 제공합니다. 단, TextRank 는 잘 구축된 토크나이저가 필요합니다. 만약 미등록단어 문제가 발생할 경우에는 해당 단어가 키워드로 추출되지 않습니다. KR-WordRank 는 이러한 문제를 해결하기 위하여 제안된 방법으로, 한국어 텍스트에서 데이터 기반으로 단어를 추출함과 동시에 해당 문장 집합을 잘 설명할 수 있는 키워드를 추출합니다.

KR-WordRank >= 1.0.0 부터는 핵심 문장을 추출하는 기능도 추가되었으며, 이 역시 어떠한 토크나이저도 필요로 하지 않습니다.

KR-WordRank 가 핵심 문장을 추출하는 원리는 아래와 같습니다. KR-WordRank 가 추출한 키워드들의 ranks 를 이용하여 keyword vector 를 만듭니다. 그리고 문장에서 키워드 점수를 단어 점수로 이용하여 soynlp 의 MaxScoreTokenizer 를 이용하여 문장을 토크나이징 합니다. 즉 데이터 기반으로 단어를 추출하고, 이를 이용하여 토크나이징을 하는 개념입니다. 모든 문장들을 키워드의 포함 유무를 표현하는 Boolean vector 로 만든 뒤, keyword vector 와의 거리를 계산합니다. 거리가 가까운 문장은 키워드들을 많이 포함하고 있는 문장입니다. 이를 핵심 문장으로 선택합니다.

단, 이 방법은 비슷한 문장들을 핵심 문장으로 선택할 가능성이 있습니다. 그렇기 때문에 처음 한 문장은 keyword vector 와의 거리가 가장 짧은 문장을 선택합니다. 그 뒤 선택된 문장과 나머지 모든 문장간의 코싸인 거리를 계산하고, 그 거리가 사용자가 지정한 임계값 (threshold, argument name = diversity) 보다 작은 경우에는 모두 2 를 더합니다. 2 는 코싸인 거리가 가질 수 있는 최대값이기 때문입니다. 그 뒤, 다시 한 번 거리의 누적값이 가장 작은 문장을 선택하며, 이를 문장 개수만큼 반복합니다.

## Evaluation logic

핵심 문장 추출은 주어진 문서 혹은 문장 집합의 요약에 이용됩니다. 문서 요약 (summarization) 분야에서 자주 이용되는 성능 평가 척도로는 ROGUE-N 이 있습니다. ROGUE-N 은 reference summaries 와 system summaries 간의 n-gram recall 을 성능 평가 척도로 이용합니다.

예를 들어 아래의 문장이 한 문서의 요약문이라고 가정합니다.

```
the cat was under the bed
```

그리고 아래의 문장이 시스템에 의하여 추출된 핵심 문장이라고 가정합니다.

```
the cat was found under the bed
```

추출된 핵심 문장이 좋은 문장이라면, 정답 요약 문장의 단어들을 많이 포함해야 합니다. ROGUE-1 은 unigram 에서의 recall 값입니다. 추출된 문장에는 정답 요약 문장의 모든 단어가 포함되어 있기 때문에 recall = 1 입니다. ROGUE-2 는 bigram 에서의 recall 값입니다. 아래는 정답 문장에서의 bigrams 입니다.

```
the cat
cat was
was under
under the
the bed
```

아래는 추출된 핵심 문장에서의 bigrams 입니다.

```
the cat
cat was
was found
found under
under the
the bed
```

'was under' 라는 bigram 이 recall 되지 않았기 때문에 recall = 4/5 입니다.

물론 ROGUE measurement 는 그 성능의 신뢰성에 대해 고민할 부분이 많기는 하지만, 그 외에 이용할 수 있는 적절한 성능 평가 지표가 많지 않습니다. 그렇기 때문에 이번 실험에서도 ROGUE 를 이용하였습니다.

하지만 한 가지 문제가 더 발생합니다. 적절한 정답 문장을 만들 수가 없습니다. 그래서 생각한 방법은 각각의 알고리즘이 추출한 핵심 단어를 references 로 이용하는 것입니다. 알고리즘이 추출한 핵심 단어 집합을 좋은 summarization keywords 라 가정할 때, 추출된 핵심 문장들은 이 키워드들을 다수 포함해야 합니다. 그리고 KR-WordRank 는 unigram extraction 을 하기 때문에 ROUGE-1 을 이용하였습니다.

아래의 디렉토리에는 각각의 데이터셋에 따른 ROGUE-1 성능을 측정합니다.

