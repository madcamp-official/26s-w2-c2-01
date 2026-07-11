# Trade Chaser Backend

FastAPI + PostgreSQL. 스키마는 [../DB스키마.md](../DB스키마.md) 기준.

## 로컬 실행

```bash
# 1. Postgres 실행 (Docker)
docker compose up -d

# 2. 가상환경 + 의존성
python -m venv .venv
.venv\Scripts\activate        # (Windows) / source .venv/bin/activate (mac/linux)
pip install -r requirements.txt

# 3. 환경변수
cp .env.example .env

# 4. 마이그레이션
alembic revision --autogenerate -m "init"
alembic upgrade head

# 5. 시드 데이터
python -m app.seed.seed_data

# 6. 서버 실행
uvicorn app.main:app --reload
```

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI 확인 가능.

## 구현 범위 (현재)

- 회원가입/로그인 (JWT)
- 관심 종목 등록/삭제/조회, 인기 종목 랭킹
- 종목 검색, 섹터 목록
- 분석 카테고리/성향 프리셋 목록 (커스터마이즈 렌즈 UI용 마스터 데이터)
- 오늘의 브리핑 조회 — `daily_briefings` 캐시를 읽기만 함. 캐시가 없는 종목은
  `missing_tickers` 로 내려줌 (뉴스 수집·Claude 파이프라인·스케줄러는 아직 미구현)

## 다음 단계

- Finnhub 뉴스/시세 수집 배치
- Claude 2단계 브리핑 파이프라인 ([../프롬프트템플릿.md](../프롬프트템플릿.md))
- APScheduler 매일 07:00 KST 트리거
- 커스터마이즈 렌즈 문서 분석 엔드포인트 (`document_analyses`/`analysis_renders`)
