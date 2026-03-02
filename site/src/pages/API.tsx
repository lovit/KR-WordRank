export default function API() {
  return (
    <>
      <h1>API · 설치</h1>

      <section>
        <h2>설치</h2>
        <pre>
          <code>{`# uv (권장)
uv venv --python 3.12
uv sync

# pip
pip install krwordrank`}</code>
        </pre>
        <p>Python ≥ 3.12 필요.</p>
      </section>

      <section>
        <h2>키워드 추출</h2>
        <pre>
          <code>{`from krwordrank.word import KRWordRank, summarize_with_keywords

# 한 번에 추출 (stopwords 제외)
keywords = summarize_with_keywords(
    texts,
    num_keywords=100,
    min_count=5,
    max_length=10,
    stopwords={"영화", "너무", "정말"},
)

# 클래스로 세밀 제어
wordrank_extractor = KRWordRank(min_count=5, max_length=10)
keywords, rank, graph = wordrank_extractor.extract(texts, beta=0.85, max_iter=10)`}</code>
        </pre>
      </section>

      <section>
        <h2>핵심 문장 추출</h2>
        <pre>
          <code>{`from krwordrank.sentence import summarize_with_sentences

keywords, sents = summarize_with_sentences(
    texts,
    num_keywords=100,
    num_keysents=10,
    stopwords={"영화", "너무"},
    diversity=0.3,
)
# return_indices=True → (keywords, sents, indices)`}</code>
        </pre>
      </section>

      <section>
        <h2>Requirements</h2>
        <ul>
          <li>numpy ≥ 1.18.4</li>
          <li>scipy ≥ 1.4.1</li>
          <li>scikit-learn ≥ 0.22.1</li>
        </ul>
      </section>
    </>
  );
}
