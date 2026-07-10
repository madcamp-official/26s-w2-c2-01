# TRADE CHASER — DB 스키마

- DBMS: **PostgreSQL** (JSONB로 브리핑 구조 저장, 관계형 무결성 동시 확보)
- 문서 버전: v1.0 (2026-07-10)
- 관련 문서: [기획서.md](기획서.md)

---

## 1. ERD 개요

```
users ──< watchlists >── stocks ──> sectors
  │                        │
  │                        ├──< price_snapshots
  │                        ├──< news_articles
  │                        └──< daily_briefings
  │
  └──< stock_comments >── stocks

market_overviews   (날짜별 전체 시황 · 종목 무관)

── 커스터마이즈 분석 렌즈 ──
users ──< user_preferences >── analysis_presets
document_analyses ──< analysis_renders >── analysis_presets
   (1단계 팩트 캐시)        (2단계 성향 렌더 캐시)
analysis_categories  (지수/지표/섹터/테마 마스터)
```

관계 요약:
- `users` N:M `stocks` → **`watchlists`** (관심 종목)
- `stocks` N:1 `sectors` (섹터 분류, 정적 매핑)
- `stocks` 1:N `daily_briefings` / `price_snapshots` / `news_articles`
- `users` 1:N `stock_comments` (선택 기능)
- `market_overviews` 는 종목과 무관한 일별 전체 시황 (브리핑 ①단)

---

## 2. 테이블 상세

### 2-1. `users` — 회원
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | BIGSERIAL | PK | 사용자 ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 로그인 이메일 |
| password_hash | VARCHAR(255) | NULL | 비번 해시(OAuth면 NULL) |
| nickname | VARCHAR(50) | NOT NULL | 표시 이름 |
| investor_type | VARCHAR(20) | DEFAULT 'balanced' | 투자 유형: `stable`/`balanced`/`aggressive` (유형별 브리핑) |
| created_at | TIMESTAMPTZ | DEFAULT now() | 가입 시각 |
| updated_at | TIMESTAMPTZ | DEFAULT now() | 수정 시각 |

```sql
CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    nickname      VARCHAR(50) NOT NULL,
    investor_type VARCHAR(20) NOT NULL DEFAULT 'balanced'
                  CHECK (investor_type IN ('stable','balanced','aggressive')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2-2. `sectors` — 섹터
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | SERIAL | PK | 섹터 ID |
| name_ko | VARCHAR(50) | NOT NULL | 한글명 (반도체, 빅테크…) |
| name_en | VARCHAR(50) | NOT NULL | 영문명 (Semiconductors…) |

```sql
CREATE TABLE sectors (
    id      SERIAL PRIMARY KEY,
    name_ko VARCHAR(50) NOT NULL,
    name_en VARCHAR(50) NOT NULL
);
```

### 2-3. `stocks` — 종목 마스터
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| ticker | VARCHAR(10) | PK | 티커 (AAPL, NVDA) |
| name_ko | VARCHAR(100) | | 한글명 (애플) |
| name_en | VARCHAR(100) | NOT NULL | 영문명 (Apple Inc.) |
| exchange | VARCHAR(20) | | 거래소 (NASDAQ, NYSE) |
| sector_id | INT | FK→sectors | 섹터 |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

```sql
CREATE TABLE stocks (
    ticker     VARCHAR(10) PRIMARY KEY,
    name_ko    VARCHAR(100),
    name_en    VARCHAR(100) NOT NULL,
    exchange   VARCHAR(20),
    sector_id  INT REFERENCES sectors(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2-4. `watchlists` — 관심 종목 (users N:M stocks)
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | BIGSERIAL | PK | |
| user_id | BIGINT | FK→users, NOT NULL | |
| ticker | VARCHAR(10) | FK→stocks, NOT NULL | |
| created_at | TIMESTAMPTZ | DEFAULT now() | 등록 시각 |

```sql
CREATE TABLE watchlists (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker     VARCHAR(10) NOT NULL REFERENCES stocks(ticker) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, ticker)          -- 같은 종목 중복 등록 방지
);
CREATE INDEX idx_watchlists_user   ON watchlists(user_id);
CREATE INDEX idx_watchlists_ticker ON watchlists(ticker);   -- 랭킹 집계용
```

### 2-5. `price_snapshots` — 일별 종가 스냅샷
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | BIGSERIAL | PK | |
| ticker | VARCHAR(10) | FK→stocks, NOT NULL | |
| trade_date | DATE | NOT NULL | 장 마감 날짜(미국 기준) |
| close | NUMERIC(14,4) | | 종가 |
| change_pct | NUMERIC(7,3) | | 전일 대비 등락률(%) |
| volume | BIGINT | | 거래량 |
| fetched_at | TIMESTAMPTZ | DEFAULT now() | 수집 시각 |

```sql
CREATE TABLE price_snapshots (
    id         BIGSERIAL PRIMARY KEY,
    ticker     VARCHAR(10) NOT NULL REFERENCES stocks(ticker) ON DELETE CASCADE,
    trade_date DATE NOT NULL,
    close      NUMERIC(14,4),
    change_pct NUMERIC(7,3),
    volume     BIGINT,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ticker, trade_date)
);
CREATE INDEX idx_price_ticker_date ON price_snapshots(ticker, trade_date DESC);
```

### 2-6. `news_articles` — 수집 뉴스 (LLM 입력 원재료)
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | BIGSERIAL | PK | |
| ticker | VARCHAR(10) | FK→stocks | 관련 종목(전체 시황이면 NULL) |
| title | TEXT | NOT NULL | 기사 제목 |
| url | TEXT | UNIQUE | 원문 링크(근거·중복 방지) |
| source | VARCHAR(100) | | 매체명 |
| summary | TEXT | | 원문 요약/발췌 |
| sentiment | VARCHAR(10) | | API 제공 감성(있으면) |
| published_at | TIMESTAMPTZ | | 발행 시각 |
| fetched_at | TIMESTAMPTZ | DEFAULT now() | 수집 시각 |

```sql
CREATE TABLE news_articles (
    id           BIGSERIAL PRIMARY KEY,
    ticker       VARCHAR(10) REFERENCES stocks(ticker) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    url          TEXT UNIQUE,
    source       VARCHAR(100),
    summary      TEXT,
    sentiment    VARCHAR(10),
    published_at TIMESTAMPTZ,
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_news_ticker_pub ON news_articles(ticker, published_at DESC);
```

### 2-7. `daily_briefings` — 종목별 일일 브리핑 (LLM 산출 · 캐싱 핵심)
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | BIGSERIAL | PK | |
| ticker | VARCHAR(10) | FK→stocks, NOT NULL | |
| briefing_date | DATE | NOT NULL | 브리핑 기준일 |
| sentiment | VARCHAR(10) | | 종합 감성 positive/neutral/negative |
| summary | TEXT | | 종목 요약 |
| positive_factors | JSONB | | 긍정 요인 배열 |
| negative_factors | JSONB | | 부정 요인 배열 |
| watch_issues | JSONB | | 주의할 이슈 배열 |
| reasons | JSONB | | `[{factor,impact,explain,source_url}]` (근거+원문) |
| today_actions | JSONB | | "오늘 확인할 것"(매매지시 아님) |
| model | VARCHAR(50) | | 사용 모델(claude-opus-4-8 등) |
| generated_at | TIMESTAMPTZ | DEFAULT now() | 생성 시각 |

```sql
CREATE TABLE daily_briefings (
    id               BIGSERIAL PRIMARY KEY,
    ticker           VARCHAR(10) NOT NULL REFERENCES stocks(ticker) ON DELETE CASCADE,
    briefing_date    DATE NOT NULL,
    sentiment        VARCHAR(10) CHECK (sentiment IN ('positive','neutral','negative')),
    summary          TEXT,
    positive_factors JSONB DEFAULT '[]',
    negative_factors JSONB DEFAULT '[]',
    watch_issues     JSONB DEFAULT '[]',
    reasons          JSONB DEFAULT '[]',
    today_actions    JSONB DEFAULT '[]',
    model            VARCHAR(50),
    generated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ticker, briefing_date)     -- 하루 1건 캐싱 키
);
CREATE INDEX idx_briefing_ticker_date ON daily_briefings(ticker, briefing_date DESC);
```

> **캐싱 전략:** 조회 시 `(ticker, briefing_date=오늘)` 로 SELECT → 있으면 그대로 반환(LLM 재호출 X), 없으면 생성 후 INSERT. `UNIQUE(ticker, briefing_date)` 가 캐시 키 역할.

### 2-8. `market_overviews` — 일별 전체 시황 (브리핑 ①단)
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | BIGSERIAL | PK | |
| briefing_date | DATE | UNIQUE, NOT NULL | 기준일 |
| summary | TEXT | | 지수·섹터 큰 흐름 요약 |
| indices | JSONB | | `{nasdaq:+1.2, sp500:+0.8, dow:-0.1}` |
| sector_moves | JSONB | | 섹터별 강약 |
| model | VARCHAR(50) | | |
| generated_at | TIMESTAMPTZ | DEFAULT now() | |

```sql
CREATE TABLE market_overviews (
    id            BIGSERIAL PRIMARY KEY,
    briefing_date DATE UNIQUE NOT NULL,
    summary       TEXT,
    indices       JSONB DEFAULT '{}',
    sector_moves  JSONB DEFAULT '{}',
    model         VARCHAR(50),
    generated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2-9. `stock_comments` — 종목 코멘트 (선택 기능 · 다중 사용자)
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | BIGSERIAL | PK | |
| ticker | VARCHAR(10) | FK→stocks, NOT NULL | |
| user_id | BIGINT | FK→users, NOT NULL | |
| content | VARCHAR(500) | NOT NULL | 의견 |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

```sql
CREATE TABLE stock_comments (
    id         BIGSERIAL PRIMARY KEY,
    ticker     VARCHAR(10) NOT NULL REFERENCES stocks(ticker) ON DELETE CASCADE,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content    VARCHAR(500) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_comments_ticker ON stock_comments(ticker, created_at DESC);
```

### 2-10. `analysis_categories` — 카테고리 마스터 (지수/지표/섹터/테마)
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | SERIAL | PK | |
| code | VARCHAR(20) | UNIQUE, NOT NULL | 코드 (SOX, US10Y, SEMI…) |
| name_ko | VARCHAR(50) | NOT NULL | 한글명 |
| name_en | VARCHAR(80) | | 영문명 |
| type | VARCHAR(12) | NOT NULL | index/indicator/sector/theme |
| description | TEXT | | 설명 |

```sql
CREATE TABLE analysis_categories (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,
    name_ko     VARCHAR(50) NOT NULL,
    name_en     VARCHAR(80),
    type        VARCHAR(12) NOT NULL
                CHECK (type IN ('index','indicator','sector','theme')),
    description TEXT
);
```

### 2-11. `analysis_presets` — 분석 성향(톤) 프리셋
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | SERIAL | PK | |
| code | VARCHAR(20) | UNIQUE, NOT NULL | MACRO/VALUE/MOMENTUM/FACT/BEGINNER |
| name_ko | VARCHAR(50) | NOT NULL | 표시명 |
| persona_text | TEXT | NOT NULL | 프롬프트에 주입될 성향 서술 |
| is_default | BOOLEAN | DEFAULT false | 기본값 여부 |

```sql
CREATE TABLE analysis_presets (
    id           SERIAL PRIMARY KEY,
    code         VARCHAR(20) UNIQUE NOT NULL,
    name_ko      VARCHAR(50) NOT NULL,
    persona_text TEXT NOT NULL,
    is_default   BOOLEAN NOT NULL DEFAULT false
);
```

### 2-12. `user_preferences` — 사용자 기본 렌즈 설정
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| user_id | BIGINT | PK, FK→users | 1:1 |
| default_preset_id | INT | FK→analysis_presets | 기본 성향 |
| default_categories | JSONB | DEFAULT '[]' | 기본 카테고리 코드 배열 |
| depth | VARCHAR(10) | DEFAULT 'standard' | brief/standard/deep |
| language | VARCHAR(5) | DEFAULT 'ko' | ko/en |

```sql
CREATE TABLE user_preferences (
    user_id            BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    default_preset_id  INT REFERENCES analysis_presets(id),
    default_categories JSONB NOT NULL DEFAULT '[]',
    depth              VARCHAR(10) NOT NULL DEFAULT 'standard'
                       CHECK (depth IN ('brief','standard','deep')),
    language           VARCHAR(5) NOT NULL DEFAULT 'ko'
);
```

### 2-13. `document_analyses` — 1단계 팩트 추출 캐시
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | BIGSERIAL | PK | |
| source_type | VARCHAR(10) | NOT NULL | news/report/paste |
| source_ref | TEXT | | 원문 URL·식별자 |
| content_hash | CHAR(64) | UNIQUE, NOT NULL | 원문 SHA-256 (캐시 키) |
| tickers | JSONB | DEFAULT '[]' | 관련 종목 |
| facts | JSONB | NOT NULL | 추출된 사실 JSON (근거 포함) |
| model | VARCHAR(50) | | |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

```sql
CREATE TABLE document_analyses (
    id           BIGSERIAL PRIMARY KEY,
    source_type  VARCHAR(10) NOT NULL CHECK (source_type IN ('news','report','paste')),
    source_ref   TEXT,
    content_hash CHAR(64) UNIQUE NOT NULL,   -- 같은 원문이면 1단계 재사용
    tickers      JSONB NOT NULL DEFAULT '[]',
    facts        JSONB NOT NULL,
    model        VARCHAR(50),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2-14. `analysis_renders` — 2단계 성향 렌더 캐시
| 컬럼 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | BIGSERIAL | PK | |
| document_analysis_id | BIGINT | FK→document_analyses, NOT NULL | 1단계 결과 |
| preset_id | INT | FK→analysis_presets, NOT NULL | 성향 |
| category_codes | JSONB | DEFAULT '[]' | 적용 카테고리 |
| depth | VARCHAR(10) | | brief/standard/deep |
| language | VARCHAR(5) | | ko/en |
| result | JSONB | NOT NULL | 최종 브리핑 JSON |
| model | VARCHAR(50) | | |
| generated_at | TIMESTAMPTZ | DEFAULT now() | |

```sql
CREATE TABLE analysis_renders (
    id                   BIGSERIAL PRIMARY KEY,
    document_analysis_id BIGINT NOT NULL REFERENCES document_analyses(id) ON DELETE CASCADE,
    preset_id            INT NOT NULL REFERENCES analysis_presets(id),
    category_codes       JSONB NOT NULL DEFAULT '[]',
    depth                VARCHAR(10),
    language             VARCHAR(5),
    result               JSONB NOT NULL,
    model                VARCHAR(50),
    generated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- 같은 문서 + 같은 렌즈 조합이면 캐시 재사용
    UNIQUE (document_analysis_id, preset_id, category_codes, depth, language)
);
```

> **2단계 캐싱 핵심:** 1단계는 `content_hash` 로, 2단계는 `(문서, 성향, 카테고리, 심층도, 언어)` 조합으로 캐싱. 프리셋이 유한하므로 조합 수가 통제되어 LLM 재호출이 최소화된다.

---

## 3. 주요 쿼리 예시

### 3-1. 관심종목 랭킹 (많이 등록한 종목 Top 10)
```sql
SELECT s.ticker, s.name_ko, COUNT(*) AS fans
FROM watchlists w
JOIN stocks s ON s.ticker = w.ticker
GROUP BY s.ticker, s.name_ko
ORDER BY fans DESC
LIMIT 10;
```

### 3-2. 내 오늘의 브리핑 조회 (관심종목별)
```sql
SELECT b.*
FROM watchlists w
JOIN daily_briefings b
  ON b.ticker = w.ticker AND b.briefing_date = CURRENT_DATE
WHERE w.user_id = $1
ORDER BY b.sentiment;
```

### 3-3. 브리핑 캐시 유무 확인 (배치/온디맨드 공통)
```sql
SELECT 1 FROM daily_briefings
WHERE ticker = $1 AND briefing_date = CURRENT_DATE;
```

### 3-4. 오늘 브리핑 생성 대상 = 활성 관심종목
```sql
SELECT DISTINCT w.ticker
FROM watchlists w
LEFT JOIN daily_briefings b
  ON b.ticker = w.ticker AND b.briefing_date = CURRENT_DATE
WHERE b.id IS NULL;   -- 아직 오늘 브리핑 없는 종목만
```

---

## 4. 초기 시드 데이터 (예시)

```sql
INSERT INTO sectors (name_ko, name_en) VALUES
  ('반도체','Semiconductors'), ('빅테크','Big Tech'),
  ('전기차','EV'), ('금융','Financials');

INSERT INTO stocks (ticker, name_ko, name_en, exchange, sector_id) VALUES
  ('AAPL','애플','Apple Inc.','NASDAQ', 2),
  ('NVDA','엔비디아','NVIDIA Corp.','NASDAQ', 1),
  ('TSLA','테슬라','Tesla Inc.','NASDAQ', 3);

-- 분석 카테고리 (일부 · 전체는 분석카테고리.md)
INSERT INTO analysis_categories (code, name_ko, name_en, type) VALUES
  ('SOX','필라델피아 반도체지수','PHLX Semiconductor','index'),
  ('VIX','변동성 지수','Volatility Index','index'),
  ('US10Y','미 국채 10년물','US 10Y Treasury','indicator'),
  ('CPI','소비자물가지수','CPI','indicator'),
  ('SEMI','반도체·AI','Semiconductors/AI','sector'),
  ('AI_DC','AI·데이터센터','AI/Datacenter','theme');

-- 분석 성향 프리셋
INSERT INTO analysis_presets (code, name_ko, persona_text, is_default) VALUES
  ('MACRO','냉정한 거시 분석','감정을 배제하고 금리·거시·수급 중심으로 분석한다.', false),
  ('VALUE','장기 가치투자','펀더멘털·밸류에이션·현금흐름 중심, 단기 노이즈는 무시한다.', true),
  ('MOMENTUM','단기 모멘텀','수급·모멘텀·촉매 이벤트와 단기 변동성에 주목한다.', false),
  ('FACT','팩트 브리핑','해석을 최소화하고 사실·수치·원문 인용만 제시한다.', false),
  ('BEGINNER','입문자용 쉬운 설명','용어를 풀어주고 비유로 배경부터 친절히 설명한다.', false);
```

---

## 5. 설계 노트
- **JSONB 활용:** 브리핑의 요인/근거/액션은 개수가 가변적이라 JSONB로 저장 → 스키마 유연성 + `->>` 조회 가능. 정규화가 필요해지면 `briefing_reasons` 별도 테이블로 분리 가능.
- **캐싱 = 유니크 제약:** `daily_briefings(ticker, briefing_date)` 와 `market_overviews(briefing_date)` 의 UNIQUE가 "하루 1건" 캐시를 DB 레벨에서 보장.
- **비용 통제:** 브리핑은 종목 단위로 캐싱되므로, 100명이 같은 AAPL을 봐도 LLM 호출은 하루 1회.
- **섹터는 정적 매핑:** 매번 LLM으로 분류하지 않고 `stocks.sector_id` 로 고정 → 비용·속도 절감.
- **확장 지점:** 알림(`notifications`), 브리핑 히스토리 회고, 멀티마켓(한국주식·코인)은 `stocks.exchange`/`market` 컬럼 확장으로 흡수 가능.
```
