# Integration Tests

라라랜드 영화 리뷰 15,603개를 실제 데이터로 사용해서 세 가지 공개 API를 end-to-end로 검증합니다.

## 데이터

`data/134963.txt`: 라라랜드 영화 리뷰 데이터. 각 줄은 탭으로 구분된 `<리뷰 텍스트>\t<평점>` 형식입니다.

## 테스트 목록

### `KRWordRank.extract` (3개)

| 테스트 | 검증 내용 |
|---|---|
| `test_keyword_top5` | 실제 데이터에서 추출한 상위 5개 키워드가 `["영화", "너무", "정말", "음악", "마지막"]`과 정확히 일치하는지 |
| `test_keyword_returns_nonempty_graph` | 학습 후 rank dict와 graph가 비어있지 않은지 (알고리즘이 정상 동작했는지) |
| `test_keyword_num_keywords_limit` | `num_keywords=30` 지정 시 반환 키워드 수가 정확히 30개인지 |

### `summarize_with_keywords` (3개)

| 테스트 | 검증 내용 |
|---|---|
| `test_summarize_with_keywords_count` | `num_keywords=50` 지정 시 반환 수가 정확히 50개인지 |
| `test_summarize_with_keywords_contains_top_words` | 상위 키워드 5개가 결과에 포함되는지 |
| `test_summarize_with_keywords_stopwords_excluded` | stopwords로 지정한 단어가 결과에서 완전히 제외되는지 |

### `summarize_with_sentences` (6개)

| 테스트 | 검증 내용 |
|---|---|
| `test_keysentence_count` | `num_keysents=10` 지정 시 핵심 문장이 정확히 10개 반환되는지 |
| `test_keysentence_keywords_contain_top_words` | 반환된 키워드 dict에 상위 5개 단어가 포함되는지 |
| `test_keysentence_stopwords_excluded_from_keywords` | stopwords가 키워드 dict에서 제외되는지 |
| `test_keysentence_penalty_filters_short_sentences` | penalty 함수(`20 ≤ len ≤ 100`) 적용 시 그 범위를 벗어난 문장이 선택되지 않는지 |
| `test_keysentence_diversity_changes_results` | `diversity=0.1`과 `diversity=0.8`의 결과가 서로 다른지 (파라미터가 실제로 동작하는지) |
| `test_keysentence_return_indices` | `return_indices=True` 시 반환된 인덱스가 유효한 범위인지, 인덱스로 texts를 조회하면 반환된 문장과 일치하는지 |
