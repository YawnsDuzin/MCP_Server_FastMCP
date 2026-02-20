# 프로젝트 구조 이해하기

## 전체 디렉토리 구조

```
MCP_Server_FastMCP/
│
├── 📄 README.md                      # 프로젝트 소개 및 빠른 시작
├── 📄 pyproject.toml                  # Python 프로젝트 설정
├── 📄 requirements.txt               # pip 의존성 목록
├── 📄 .env.example                   # 환경변수 템플릿
├── 📄 .gitignore                     # Git 제외 파일 목록
│
├── 📁 docs/                          # 📚 문서
│   ├── 📄 index.md                   # 문서 메인 페이지
│   │
│   ├── 📁 getting-started/           # 시작하기 가이드
│   │   ├── 📄 what-is-mcp.md        # MCP 개념 설명
│   │   ├── 📄 environment-setup.md   # 환경 설정 가이드
│   │   └── 📄 project-structure.md   # 프로젝트 구조 (이 문서)
│   │
│   ├── 📁 tutorials/                 # 튜토리얼 상세 문서
│   │   ├── 📄 01-hello-mcp.md       # Tutorial 01 상세 가이드
│   │   ├── 📄 02-weather-server.md  # Tutorial 02 상세 가이드
│   │   ├── 📄 03-file-manager.md    # Tutorial 03 상세 가이드
│   │   ├── 📄 04-database-server.md # Tutorial 04 상세 가이드
│   │   └── 📄 05-memo-app.md        # Tutorial 05 상세 가이드
│   │
│   └── 📁 reference/                 # 참조 문서
│       ├── 📄 fastmcp-api.md        # FastMCP API 레퍼런스
│       └── 📄 claude-integration.md  # Claude 연동 가이드
│
└── 📁 tutorials/                     # 💻 튜토리얼 소스 코드
    ├── 📁 01_hello_mcp/              # Tutorial 01: 첫 번째 서버
    │   └── 📄 server.py
    │
    ├── 📁 02_weather_server/         # Tutorial 02: 날씨 서버
    │   └── 📄 server.py
    │
    ├── 📁 03_file_manager/           # Tutorial 03: 파일 관리
    │   └── 📄 server.py
    │
    ├── 📁 04_database_server/        # Tutorial 04: DB 서버
    │   └── 📄 server.py
    │
    └── 📁 05_memo_app/               # Tutorial 05: 메모 앱
        └── 📄 server.py
```

## 튜토리얼별 개요

### 난이도 로드맵

```
입문 ─────────────────────────────────────────────── 실전
 │                                                    │
 ▼                                                    ▼
 01          02          03          04          05
 Hello MCP → 날씨 서버 → 파일 관리 → DB 서버  → 메모 앱
 (기초)     (API 연동)  (파일 I/O)  (MSSQL)    (CRUD)
```

| Tutorial | 제목 | 핵심 학습 | 난이도 |
|----------|------|----------|--------|
| 01 | Hello MCP | Tool, Resource, Prompt 기초 | ★☆☆☆☆ |
| 02 | 날씨 서버 | 외부 API, 비동기, 에러 처리 | ★★☆☆☆ |
| 03 | 파일 관리 | 파일 시스템, 보안, 경로 처리 | ★★★☆☆ |
| 04 | DB 서버 | MSSQL, SQLAlchemy, 실전 패턴 | ★★★★☆ |
| 05 | 메모 앱 | SQLite, CRUD, 태그 시스템 | ★★★★☆ |

### 각 튜토리얼에서 배우는 것

#### Tutorial 01: Hello MCP - 첫 번째 서버
- `FastMCP` 인스턴스 생성
- `@mcp.tool` 데코레이터로 도구 정의
- `@mcp.resource` 데코레이터로 리소스 정의
- `@mcp.prompt` 데코레이터로 프롬프트 정의
- 서버 실행 및 Claude 연결

#### Tutorial 02: 날씨 정보 서버
- `async` 비동기 도구 정의
- `httpx`로 외부 API 호출
- `.env` 환경변수 관리
- API 키 없이도 작동하는 데모 모드 패턴
- 에러 처리 (HTTP 에러, 네트워크 에러)

#### Tutorial 03: 파일 관리 서버
- `pathlib`으로 파일 시스템 작업
- Path Traversal 공격 방지 (보안)
- 파일 읽기/쓰기/검색 구현
- 안전한 작업 디렉토리 제한

#### Tutorial 04: MSSQL 데이터베이스 서버
- SQLAlchemy로 MSSQL 연결
- SQL Injection 방지 (파라미터 바인딩)
- 읽기 전용 쿼리 제한 (보안)
- 실무 데이터 모델 (현장-카메라-이벤트)
- 대시보드 형태의 요약 도구

#### Tutorial 05: 메모/노트 앱
- SQLite 데이터베이스 (표준 라이브러리)
- 완전한 CRUD 작업
- 태그 시스템 (다대다 관계)
- 검색 기능
- 통계 및 카테고리 관리

## MCP 서버 코드의 기본 구조

모든 튜토리얼은 동일한 기본 구조를 따릅니다:

```python
# ① 임포트
from fastmcp import FastMCP

# ② 서버 인스턴스 생성
mcp = FastMCP("서버 이름")

# ③ Tool 정의
@mcp.tool
def my_tool(param: str) -> str:
    """도구 설명 (Claude가 이 설명을 읽고 도구 사용 여부를 결정)"""
    return "결과"

# ④ Resource 정의 (선택사항)
@mcp.resource("my://resource")
def my_resource() -> str:
    """리소스 설명"""
    return "데이터"

# ⑤ Prompt 정의 (선택사항)
@mcp.prompt
def my_prompt(topic: str) -> str:
    """프롬프트 설명"""
    return f"{topic}에 대해 알려주세요."

# ⑥ 서버 실행
if __name__ == "__main__":
    mcp.run()
```

## 다음 단계

프로젝트 구조를 이해했다면, 첫 번째 튜토리얼을 시작하세요!

➡️ [Tutorial 01: Hello MCP](../tutorials/01-hello-mcp.md)로 이동하세요.
