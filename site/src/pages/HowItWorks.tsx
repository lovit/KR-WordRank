export default function HowItWorks() {
  return (
    <>
      <h1>동작 원리</h1>

      <section>
        <h2>키워드 추출</h2>
        <p>
          문장의 <strong>어절</strong>(공백 기준 토큰)을 substring으로 분해해 그래프를
          만듭니다. PageRank와 유사한 <strong>HITS</strong> 알고리즘으로 각 substring의
          중요도를 계산하고, 랭크가 높은 substring을 후처리해 단어로 확정합니다.
        </p>
        <p>
          가정: 단어 주변에는 단어가 등장하고, 올바른 단어는 주변 단어들과 많이
          연결되어 있어 점수가 보강(reinforced)됩니다.
        </p>
      </section>

      <section>
        <h2>핵심 문장 추출</h2>
        <p>
          추출된 키워드의 랭크값으로 <strong>키워드 벡터</strong>를 만든 뒤, 각 문장과
          키워드 벡터 간의 <strong>코사인 유사도</strong>를 계산합니다. 유사도가 높은
          문장을 순서대로 선택하고, diversity 옵션으로 문장 간 중복을 줄입니다.
        </p>
      </section>
    </>
  );
}
