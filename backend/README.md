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

# 5. 섹터·분석 기준 데이터와 미국 주식 종목
python -m app.seed.seed_data
python -m app.seed.import_us_stocks

# 6. 서버 실행 (Docker Compose로 실행할 때는 4~5단계가 자동 수행됨)
uvicorn app.main:app --reload
```

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI 확인 가능.

Docker Compose로 처음 실행할 때 변동성 캐시가 없거나 DB의 종목 universe가 바뀌었으면
백엔드가 기동된 뒤 `daily → premarket` 전체 스캔을 백그라운드에서 최초 1회 자동 실행한다.
정상 캐시가 있으면 재시작 시에는 건너뛰며, 이후에는 평일 정기 스케줄로 갱신한다.

## 구현 범위 (현재)

- 회원가입/로그인 (JWT)
- 관심 종목 등록/삭제/조회, 인기 종목 랭킹
- 종목 검색, 섹터 목록
- 분석 카테고리/성향 프리셋 목록 (커스터마이즈 렌즈 UI용 마스터 데이터)
- Finnhub 시세·뉴스 수집 (`app/services/finnhub_client.py`, `app/services/market_data.py`)
  — `FINNHUB_API_KEY` 설정 후 `python -m app.jobs.collect_market_data` 로 관심종목
  전체의 종가·뉴스를 수집
- 브리핑 생성 파이프라인 (`app/services/briefing_pipeline.py`) — 뉴스를 모아
  1단계(팩트 추출) → 2단계(성향 렌더링)를 거쳐 `daily_briefings` 에 저장.
  **LLM API 종류를 아직 정하지 못해서 지금은 스텁(`app/services/llm/stub_client.py`)이
  더미 데이터를 생성**한다. 파이프라인 구조·저장 로직은 실제 API와 동일하게 동작하므로,
  나중에 `app/services/llm/claude_client.py` 두 메서드만 구현하고
  `app/services/llm/factory.py` 분기를 켜면 그대로 실제 브리핑으로 전환된다.
- `GET /briefings/today` — 캐시가 없는 관심종목은 요청 안에서 온디맨드로
  파이프라인을 돌려 채운다 (기획서.md 7-1절 "on-demand 보완")

## 잡 스크립트 (아직 스케줄러에 연결 안 됨 — 수동 실행용)

```bash
python -m app.jobs.collect_market_data   # 관심종목 시세·뉴스 수집
python -m app.jobs.generate_briefings    # 오늘자 브리핑 없는 관심종목 전체 생성
```

두 스크립트의 `run()` 함수가 나중에 APScheduler 크론 잡이 매일 07:00 KST에
호출할 대상이다.

## 다음 단계

- LLM API 종류 확정 → `app/services/llm/claude_client.py` 구현
- APScheduler 매일 07:00 KST 트리거 (`app/jobs/*.run()` 호출)
- 커스터마이즈 렌즈 문서 분석 엔드포인트 (`document_analyses`/`analysis_renders`)
- market_overviews(전체 시황) 생성 — 현재는 읽기 전용, 채우는 로직 없음
