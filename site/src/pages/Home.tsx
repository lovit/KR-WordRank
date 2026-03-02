export default function Home() {
  return (
    <>
      <h1>KR-WordRank</h1>
      <p>
        <strong>KR-WordRank</strong>는 형태소 분석기 없이 한국어 텍스트에서 단어와
        키워드를 추출하는 비지도 학습 기반 라이브러리입니다.
      </p>
      <p>
        Kim, H. J., Cho, S., & Kang, P. (2014). &quot;KR-WordRank: An Unsupervised
        Korean Word Extraction Method Based on WordRank.&quot; Journal of Korean
        Institute of Industrial Engineers, 40(1), 18-33.
      </p>

      <section>
        <h2>특징</h2>
        <ul>
          <li>순수 Python, 형태소 분석기 불필요</li>
          <li>키워드 추출: substring 그래프 + HITS 랭킹</li>
          <li>핵심 문장 추출: 키워드 벡터와 코사인 유사도</li>
          <li>CLI 제공: <code>krwordrank keywords</code>, <code>krwordrank keysents</code></li>
        </ul>
      </section>

      <section>
        <h2>빠른 시작</h2>
        <pre>
          <code>{`# 설치 (uv)
uv venv --python 3.12
uv sync

# CLI: 키워드 15개 추출
krwordrank keywords -i sentences.txt -n 15

# Python
from krwordrank.word import summarize_with_keywords
keywords = summarize_with_keywords(texts, num_keywords=100)`}</code>
        </pre>
      </section>

      <p>
        <a href="https://github.com/lovit/KR-WordRank" target="_blank" rel="noreferrer">
          GitHub 저장소 →
        </a>
      </p>
    </>
  );
}
