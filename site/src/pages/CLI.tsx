export default function CLI() {
  return (
    <>
      <h1>CLI</h1>
      <p>
        <code>krwordrank keywords</code>, <code>krwordrank keysents</code>로 키워드와
        핵심 문장을 추출할 수 있습니다. 입력은 한 줄에 한 문서(텍스트 파일 또는
        JSONL)입니다.
      </p>

      <section>
        <h2>입력 형식</h2>
        <ul>
          <li>
            <strong>text</strong> (기본): 한 줄에 한 문서. 탭이 있으면 첫 번째 컬럼만
            사용(TSV 호환).
          </li>
          <li>
            <strong>jsonl</strong>: JSON Lines. <code>--field</code>로 문서 텍스트가
            들어 있는 키를 지정.
          </li>
        </ul>
      </section>

      <section>
        <h2>키워드 추출</h2>
        <pre>
          <code>{`krwordrank keywords -i sentences.txt -n 50
krwordrank keywords -i reviews.jsonl --format jsonl --field text -n 50`}</code>
        </pre>
        <p>
          옵션: <code>-n</code> 개수, <code>-s</code> stopwords(쉼표 구분),{" "}
          <code>--min-count</code>, <code>--max-length</code>, <code>--json</code>
        </p>
      </section>

      <section>
        <h2>핵심 문장 추출</h2>
        <pre>
          <code>{`krwordrank keysents -i sentences.txt -k 10
krwordrank keysents -k 5 --keywords-only --number`}</code>
        </pre>
        <p>
          옵션: <code>-n</code> 키워드 수, <code>-k</code> 핵심 문장 수,{" "}
          <code>--diversity</code>, <code>--min-len</code>/<code>--max-len</code>,{" "}
          <code>--show-indices</code>
        </p>
      </section>

      <p>
        자세한 옵션: <code>krwordrank keywords --help</code>,{" "}
        <code>krwordrank keysents --help</code>
      </p>
    </>
  );
}
