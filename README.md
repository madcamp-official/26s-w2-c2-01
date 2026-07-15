# 26s-w2-c2-01

## 공통과제 II : 협업형 실전 산출물 제작 (2인 1팀)

**목적:** 실시간 인터랙션, LLM Wrapper, Cross-Platform 중 하나의 옵션을 선택해 구현하며, 선택한 기술을 실제로 동작하는 형태의 산출물로 완성한다.

**선택 옵션:**

| 옵션 | 설명 |
|---|---|
| 실시간 인터랙션 | 사용자 간 상태 변화, 실시간 데이터 흐름, 스트리밍 응답 등 실시간성이 드러나는 기능을 구현 |
| LLM Wrapper | LLM API를 활용하여 AI 기능이 포함된 산출물을 구현 |
| Cross-Platform | 하나의 산출물을 여러 실행 환경에서 사용할 수 있도록 구현* |

> *데스크톱 앱 ↔ 모바일 앱; 혹은 다른 폼팩터에서의 앱; 웹만/웹 기반 프레임워크(Electron, Tauri 등) 대신 다른 프레임워크를 시도해보는 것을 적극 권장

**결과물:** 선택한 옵션이 적용된 작동 가능한 산출물, 실행 가능한 코드, 시연 자료 및 관련 문서

---

## 팀원

| 이름 | 학교 | GitHub | 역할 |
|---|---|---|---|
| 김도연 | HYU |  |  |
| 원건희 | KAIST |  |  |
| 황시우 | YONSEI |  |  |

---

## 선택 옵션

- [x] 실시간 인터랙션
- [x] LLM Wrapper
- [x] Cross-Platform

---

## 기획안

- **산출물 주제:** 주식 시장 시황 확인
- **제작 목적:** 일을 하거나 잠을 자고 있을 때 발생한 수많은 사건들을 정리, 투자 결정의 도움을 주기 위함
- **선택 옵션:** 관심 종목 랭킹, 모바일 반응형 UI, 실시간 정보 반영
- **핵심 구현 요소:**
  - 종목별 섹터 분류
  - 탐색 렌즈 설정
  - 오늘의 시황 요약
- **사용 / 시연 시나리오:**

  **[전날 밤]**

  사용자는 관심종목만 등록해두고 잠든다.  
  예: AAPL, NVDA, TSLA

  ▼  
  미국 장이 밤새 돌아가고,  
  시스템이 마감 후 브리핑을 생성한다.

  **[아침 08:00]**

  사용자가 웹을 연다.

  ① 밤사이 미장 요약  
  "나스닥 +1.2%, 반도체 강세…"

  ② 관심종목별 핵심 이슈  
  "NVDA — 긍정 ↑  실적 가이던스 상향 이슈"  
  "TSLA — 주의 ⚠  인도량 둔화 우려"

  ③ 각 항목의 근거 뉴스 원문 펼쳐보기

  ④ 오늘 확인할 것  
  "NVDA 컨퍼런스콜 코멘트"  
  "반도체 섹터 동반 흐름"

  ▼

  **[3분 후]**

  사용자는 직접 뉴스를 뒤지지 않고도  
  오늘 미장 흐름을 빠르게 파악했다.
- **팀원별 역할:** 협업

### 개발 일정

| 날짜 | 목표 |
|---|---|
| 07.09 | 주제 정하기 |
| 07.10 | 계획 구체화하기 |
| 07.11 | 기본 MVP 생성 |
| 07.13 | 어플리케이션 개발 |
| 07.14 | ML+GEMINI API로 변경 |
| 07.15 | 문서 작성 |

---

## 구현 명세서

| 구현 요소        | 설명                                                 | 우선순위 |
| ------------ | -------------------------------------------------- | ---- |
| 회원별 관심 종목 관리 | 회원이 미국 주식 티커를 검색하고 관심 종목으로 등록·삭제할 수 있도록 구현         | 필수   |
| 종목별 섹터 분류    | 등록된 관심 종목을 정적 매핑 테이블을 기준으로 섹터별 분류                  | 필수   |
| 뉴스·시황 데이터 입력 | 종목 및 섹터와 관련된 뉴스, 시세, 시장 지표 데이터를 API 또는 사용자 입력으로 수집 | 필수   |
| 오늘의 시황 요약    | 수집한 데이터를 기반으로 LLM이 미국 시장과 주요 섹터의 흐름을 한국어로 요약       | 필수   |
| 종목 영향 요인 분석  | 관심 종목별 긍정 요인, 부정 요인, 주의할 이슈를 근거와 함께 정리             | 필수   |
| 관심 종목 랭킹     | 전체 사용자의 관심 종목 등록 수를 집계하여 인기 종목 순위를 제공              | 선택   |
| 모바일 반응형 UI   | 모바일과 데스크톱 화면 크기에 맞춰 브리핑 화면이 반응형으로 표시되도록 구현         | 선택   |
| 실시간 정보 반영    | 새로운 뉴스 또는 관심 종목 등록 수의 변화를 반영해 브리핑과 랭킹을 업데이트        | 선택   |

---

## 아키텍처

<!-- 실시간 인터랙션: WebSocket/SSE/WebRTC 구조도 / LLM Wrapper: API 연동 흐름도 / Cross-Platform: 플랫폼 구성도 -->

![Trend Chaser 시스템 아키텍처](<docs/ChatGPT Image 2026년 7월 15일 오후 07_39_24.png>)

---

## 설계 문서

> 프로젝트 성격에 따라 필요한 항목만 작성

### 화면 / 인터페이스 설계

<!-- Figma 링크, 화면 이미지, CLI 사용 예시, 앱 화면 등 -->

notion 참고

### 데이터 구조

[DB스키마](DB스키마.md)

### API / 외부 서비스 연동

#### REST API

| Method | Endpoint | 설명 | 주요 요청 | 주요 응답 | 인증 |
|---|---|---|---|---|---|
| `POST` | `/auth/register` | 회원가입 | `email`, `password`, `nickname` | JWT access token | 불필요 |
| `POST` | `/auth/login` | 로그인 | `email`, `password` | JWT access token | 불필요 |
| `GET` / `PATCH` | `/users/me` | 내 정보 조회·수정 | 수정 시 `nickname` 등 | 사용자 정보 | 필요 |
| `GET` | `/stocks` | 종목 검색·목록 조회 | `search`, `limit` query | 섹터를 포함한 종목 목록 | 불필요 |
| `GET` | `/stocks/{ticker}` | 종목 단건 조회 | ticker path | 섹터를 포함한 종목 정보 | 불필요 |
| `GET` | `/sectors` | 섹터 목록 조회 | 없음 | 섹터 목록 | 불필요 |
| `GET` | `/stocks/volatility/today` | 오늘의 변동성 스캔 결과 조회 | 없음 | Daily·Premarket 변동성 종목 | 불필요 |
| `GET` / `POST` | `/watchlist` | 관심 종목 조회·등록 | 등록 시 `ticker` | 관심 종목 목록 또는 등록 결과 | 필요 |
| `DELETE` | `/watchlist/{ticker}` | 관심 종목 삭제 | ticker path | `204 No Content` | 필요 |
| `GET` | `/watchlist/ranking/top` | 전체 사용자 기준 인기 종목 조회 | `limit` query | 관심 등록 순위 | 불필요 |
| `GET` / `POST` | `/sector-watchlist` | 관심 섹터 조회·등록 | 등록 시 `sector_id` | 관심 섹터 목록 또는 등록 결과 | 필요 |
| `DELETE` | `/sector-watchlist/{sector_id}` | 관심 섹터 삭제 | sector ID path | `204 No Content` | 필요 |
| `GET` | `/analysis-categories` | 분석 렌즈 카테고리 조회 | 없음 | 분석 카테고리 목록 | 불필요 |
| `GET` | `/analysis-presets` | 분석 렌즈 프리셋 조회 | 없음 | 분석 프리셋 목록 | 불필요 |
| `GET` | `/briefings/today` | 현재 세션의 전체·섹터·관심 종목 브리핑 조회 | 없음 | 브리핑, 세션, 미생성 항목 | 필요 |
| `POST` | `/briefings/refresh` | 관심 항목과 전체 시황을 수동 재생성 | 없음 | 갱신된 오늘의 브리핑 | 필요 |
| `POST` | `/briefings/refresh/stocks/{ticker}` | 관심 종목 하나의 뉴스 수집·브리핑 재생성 | ticker path | 종목 브리핑 | 필요 |
| `POST` | `/briefings/refresh/sectors/{sector_id}` | 관심 섹터 하나의 브리핑 재생성 | sector ID path | 섹터 브리핑 | 필요 |
| `POST` | `/briefings/refresh/overview` | 전체 시황 생성을 백그라운드에서 시작 | 없음 | `202 Accepted`, `job_id`, 상태 | 필요 |
| `GET` | `/briefings/refresh/overview/status/{job_id}` | 전체 시황 생성 작업 상태 폴링 | job ID path | `running`, `completed`, `failed` | 필요 |
| `GET` | `/briefings/history` | 관심 종목 브리핑 이력 조회 | 없음 | 날짜 역순 종목 브리핑 | 필요 |
| `GET` | `/briefings/history/sectors` | 관심 섹터 브리핑 이력 조회 | 없음 | 날짜 역순 섹터 브리핑 | 필요 |
| `GET` | `/briefings/history/overview` | 전체 시황 이력 조회 | 없음 | 날짜 역순 전체 시황 | 불필요 |


#### 외부 서비스 연동

| 방식 / 서비스 | 사용 목적 | 설정 | 호출 위치 | 장애·미설정 시 동작 |
|---|---|---|---|---|
| REST · Finnhub | 관심 종목 시세와 기업 뉴스 수집 | `FINNHUB_API_KEY` | `finnhub_client.py`, `collect_news.py`, `market_data.py` | 수집을 건너뛰고 DB의 기존 뉴스로 브리핑 생성을 계속 시도 |
| RSS · CNBC | 전체 시장 브리핑용 금융·경제·실적 뉴스 수집 | `ENABLE_CNBC_MARKET_RSS` 및 `CNBC_MARKET_NEWS_*` | `cnbc_rss_client.py`, `market_overview_pipeline.py` | 피드가 비활성·실패·부족하면 Finnhub 시장 뉴스로 폴백 |
| REST · Polygon.io | 미국 전체 종목의 일봉 OHLCV를 묶음 조회하여 변동성 1차 스캔 | `POLYGON_API_KEY` | `polygon_client.py`, `scan_volatility.py` | 키가 없으면 yfinance 청크 다운로드로 폴백 |
| HTTPS · yfinance | 변동성 스캔의 일봉·분봉 데이터 조회 | 별도 키 없음 | `volatility_scanner.py` | 요청 실패 종목은 재시도 후 해당 스캔에서 제외 |
| REST · Anthropic Claude | 브리핑의 사실 추출 또는 해석·렌더링 | `ANTHROPIC_API_KEY` | `services/llm/claude_client.py` | 설정된 다른 LLM을 사용하며, 모든 키가 없으면 Stub 사용 |
| REST · Google Gemini | 브리핑의 사실 추출 또는 해석·렌더링 | `GEMINI_API_KEY`, `GEMINI_MODEL` | `services/llm/gemini_client.py` | Claude·Ollama 설정에 따라 단독 또는 Hybrid 구성 |
| HTTP · Ollama | 자체 호스팅 모델(Gemma2)의 브리핑 사실 추출·생성 | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | `services/llm/ollama_client.py` | URL이 없으면 Claude 또는 Gemini 사용 |
| PostgreSQL 16 | 사용자·관심 목록·시세·뉴스·브리핑·분석 데이터 저장 | `DATABASE_URL` | SQLAlchemy models/CRUD, Alembic | Docker Compose에서 DB healthcheck 통과 후 백엔드 시작 |


---

## 산출물 및 실행 방법

- **산출물 설명:** 수많은 주식 정보를 꾸준히 브리핑해줌
- **실행 환경:** website, android application
- **실행 방법:** website는 링크 타고 들어가기, app은 파일 다운로드
- **시연 영상 / 이미지:** (선택)

### 실행 방법

```bash
# 환경 설정
cp .env.example .env

# 의존성 설치
npm install   # 또는 pip install -r requirements.txt 등

# 실행
npm run dev   # 또는 python main.py 등
```



---

## 회고 문서

> [KPT 방법론 참고](https://velog.io/@habwa/%EB%8B%A8%EA%B8%B0-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8-%ED%9A%8C%EA%B3%A0-KPT-%EB%B0%A9%EB%B2%95%EB%A1%A0)

### Keep — 잘 된 점, 다음에도 유지할 것

-
-
-

### Problem — 아쉬웠던 점, 개선이 필요한 것

-
-
-

### Try — 다음번에 시도해볼 것

-
-
-

### 팀원별 소감

https://app.notion.com/p/398994da1b5c800fb2f2fd27b4b90b6d?v=398994da1b5c806b8751000c0b4eb381&p=399994da1b5c8015a302e9df94eb58ae&pm=s

---

## 참고 자료

### 실시간 인터랙션

**WebSocket**
- https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API
- https://techblog.woowahan.com/5268/
- https://tech.kakao.com/posts/391
- https://daleseo.com/websocket/
- https://kakaoentertainment-tech.tistory.com/110

**Socket.IO**
- https://socket.io/docs/v4/
- https://inpa.tistory.com/entry/SOCKET-%F0%9F%93%9A-Namespace-Room-%EA%B8%B0%EB%8A%A5
- https://adjh54.tistory.com/549
- https://fred16157.github.io/node.js/nodejs-socketio-communication-room-and-namespace/

**SSE (Server-Sent Events)**
- https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- https://developer.mozilla.org/ko/docs/Web/API/Server-sent_events/Using_server-sent_events
- https://api7.ai/ko/blog/what-is-sse

**TCP / UDP Socket**
- https://docs.python.org/3/library/socket.html
- https://inpa.tistory.com/entry/NW-%F0%9F%8C%90-%EC%95%84%EC%A7%81%EB%8F%84-%EB%AA%A8%ED%98%B8%ED%95%9C-TCP-UDP-%EA%B0%9C%EB%85%90-%E2%9D%93-%EC%89%BD%EA%B2%8C-%EC%9D%B4%ED%95%B4%ED%95%98%EC%9E%90

**gRPC Streaming**
- https://grpc.io/docs/what-is-grpc/core-concepts/
- https://tech.ktcloud.com/entry/gRPC%EC%9D%98-%EB%82%B4%EB%B6%80-%EA%B5%AC%EC%A1%B0-%ED%8C%8C%ED%97%A4%EC%B9%98%EA%B8%B0-HTTP2-Protobuf-%EA%B7%B8%EB%A6%AC%EA%B3%A0-%EC%8A%A4%ED%8A%B8%EB%A6%AC%EB%B0%8D
- https://tech.ktcloud.com/entry/gRPC%EC%9D%98-%EB%82%B4%EB%B6%80-%EA%B5%AC%EC%A1%B0-%ED%8C%8C%ED%97%A4%EC%B9%98%EA%B8%B02-Channel-Stub
- https://inspirit941.tistory.com/371
- https://devocean.sk.com/blog/techBoardDetail.do?ID=167433

**WebRTC**
- https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API
- https://webrtc.org/getting-started/overview
- https://web.dev/articles/webrtc-basics?hl=ko
- https://devocean.sk.com/blog/techBoardDetail.do?ID=164885
- https://beomkey-nkb.github.io/%EA%B0%9C%EB%85%90%EC%A0%95%EB%A6%AC/webRTC%EC%A0%95%EB%A6%AC/
- https://gh402.tistory.com/45
- https://on.com2us.com/tech/webrtc-coturn-turn-stun-server-setup-guide/

**QUIC / WebTransport**
- https://developer.mozilla.org/en-US/docs/Web/API/WebTransport_API
- https://datatracker.ietf.org/doc/html/rfc9000
- https://news.hada.io/topic?id=13888

#### KCLOUD VM / Cloudflare Tunnel 환경별 주의사항

| 환경 | 사용 가능(권장) 기술 | 포트/조건 | 주의할 기술 |
|---|---|---|---|
| **로컬 / 일반 VM** | HTTP/REST, WebSocket, Socket.IO, SSE, TCP Socket, gRPC Streaming, WebRTC, QUIC/WebTransport 등 대부분 가능 | 직접 포트 개방 가능. 예: 3000, 5000, 8000, 8080, 9000 등. 외부 공개 시 방화벽/보안그룹/공인 IP 설정 필요 | WebRTC는 STUN/TURN 필요 가능. QUIC/WebTransport는 HTTP/3 · UDP 지원 필요 |
| **KCLOUD VM (VPN 내부)** | HTTP/REST, WebSocket, Socket.IO, SSE, WebRTC 시그널링 | 접속 기기 VPN 필요. 기본 허용 포트: **22, 80, 443**. 개발 포트(3000, 8000, 8080 등)는 직접 접근 제한 가능 | TCP Socket은 포트 제한 있음. gRPC는 HTTP/2 설정 필요. WebRTC 미디어·UDP·QUIC/WebTransport 비권장 |
| **KCLOUD VM + Tunnel** | HTTP/REST, WebSocket, Socket.IO, SSE, WebRTC 시그널링 | VM의 `localhost:<port>`를 도메인에 연결. `localPort`는 **1024~65535**. 예: 3000, 8000, 8080 가능 | 순수 TCP Socket, UDP, WebRTC 미디어/DataChannel, QUIC/WebTransport 불가. gRPC 보장 어려움 |
| **외부 서비스 + 우리 도메인** | HTTP/REST, WebSocket, Socket.IO, SSE, WebRTC 시그널링 | Vercel/Netlify/Railway/Render/AWS/GCP 등에 배포 후 CNAME/A 레코드 연결. 보통 외부는 **443** 사용 | WebSocket/gRPC/TCP/UDP는 플랫폼 지원 여부 확인 필요. 서버리스 플랫폼은 장시간 연결 제한 가능 |
| **서버 없이 외부 SaaS 사용** | Supabase Realtime, Firebase, Pusher/Ably, LLM API Streaming | 직접 포트 관리 불필요. 각 서비스 SDK/API 사용 | 커스텀 TCP/UDP 서버 구현 불가. WebRTC는 STUN/TURN 필요할 수 있음 |

### LLM Wrapper

- https://github.com/teddylee777/openai-api-kr
- https://github.com/teddylee777/langchain-kr
- https://devocean.sk.com/blog/techBoardDetail.do?ID=167407
- https://mastra.ai/docs

### Cross-Platform

- https://flutter.dev/
- https://reactnative.dev/
- https://docs.expo.dev/
- https://kotlinlang.org/multiplatform/
