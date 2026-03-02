# KR-WordRank GitHub Pages (React + TypeScript)

이 디렉터리는 [GitHub Pages](https://pages.github.com/)용 문서 사이트 소스입니다.

## 개발

```bash
cd site
npm install
npm run dev
```

## 빌드 (결과물은 `../docs`)

```bash
cd site
npm run build
```

빌드 후 `docs/` 디렉터리에 정적 파일이 생성됩니다. GitHub 저장소 설정에서 **Pages → Source: Deploy from a branch** → **Branch: main** → **Folder: /docs** 로 지정하면 `https://<username>.github.io/KR-WordRank/` 에서 확인할 수 있습니다.
